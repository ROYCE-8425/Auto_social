"""Lưu trữ SQLite WAL cho Fanpage Care (events, drafts, actions, CRM, rate, windows, cursors).

Vị trí mặc định: STATE_DIR / "fanpage_care.sqlite3".
Không dùng FTS v1 - search LIKE trên phones và name.
Gộp danh tính:
- fb_comment_from + page_id: page-scoped
- fb_psid + page_id: page-scoped
- phone: GLOBAL (page_id = '' bắt buộc)
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from config import STATE_DIR
except ImportError:
    STATE_DIR = Path(__file__).resolve().parent

DEFAULT_DB_PATH = STATE_DIR / "fanpage_care.sqlite3"


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Mở kết nối SQLite WAL, row_factory là Row để truy xuất dict-like."""
    p = Path(db_path or DEFAULT_DB_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str | None = None) -> None:
    """Khởi tạo toàn bộ schema bảng nếu chưa tồn tại."""
    with get_connection(db_path) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          kind TEXT NOT NULL,          -- comment | message | echo | action
          platform TEXT NOT NULL DEFAULT 'facebook', -- facebook | tiktok | messenger
          page_id TEXT NOT NULL,
          object_id TEXT NOT NULL,     -- comment_id | message_id
          thread_id TEXT,
          from_id TEXT,
          from_name TEXT,
          body TEXT,
          class TEXT,
          faq_intent TEXT,
          created_ts REAL,
          ingested_ts REAL,
          UNIQUE(kind, object_id)
        );

        CREATE TABLE IF NOT EXISTS drafts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          event_id INTEGER,
          page_id TEXT,
          target_id TEXT,              -- comment_id or psid
          proposed TEXT,
          class TEXT,
          status TEXT DEFAULT 'pending', -- pending | approved | rejected | sent | expired
          created_ts REAL
        );

        CREATE TABLE IF NOT EXISTS actions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          event_id INTEGER,
          action TEXT,                 -- reply | hide | like | send | skip
          graph_id TEXT,
          mode TEXT,
          actor TEXT,                  -- care-worker | user | agent
          ts REAL
        );

        CREATE TABLE IF NOT EXISTS customers (
          crm_id TEXT PRIMARY KEY,
          name TEXT,
          phones TEXT,                 -- JSON array
          tags TEXT,                   -- JSON array
          course_interest TEXT,
          campus TEXT,
          page_ids TEXT,               -- JSON array
          md_path TEXT,
          updated_ts REAL
        );

        CREATE TABLE IF NOT EXISTS identities (
          kind TEXT NOT NULL,          -- fb_comment_from | fb_psid | phone
          page_id TEXT NOT NULL,       -- '' (chuỗi rỗng) KHI kind=phone; else Page ID
          ext_id TEXT NOT NULL,
          crm_id TEXT NOT NULL,
          PRIMARY KEY (kind, page_id, ext_id)
        );

        CREATE TABLE IF NOT EXISTS page_cursors (
          page_id TEXT,
          post_id TEXT,
          last_count INTEGER,
          last_comment_id TEXT,
          PRIMARY KEY (page_id, post_id)
        );

        CREATE TABLE IF NOT EXISTS messaging_windows (
          page_id TEXT,
          psid TEXT,
          last_user_ts REAL,
          last_page_ts REAL,
          takeover_until REAL,         -- human takeover cooldown
          PRIMARY KEY (page_id, psid)
        );

        CREATE TABLE IF NOT EXISTS rate_buckets (
          page_id TEXT,
          hour_key TEXT,               -- YYYY-MM-DDTHH
          replies INTEGER DEFAULT 0,
          PRIMARY KEY (page_id, hour_key)
        );

        CREATE INDEX IF NOT EXISTS idx_events_page_ts ON events(page_id, created_ts);
        CREATE INDEX IF NOT EXISTS idx_identities_crm ON identities(crm_id);
        CREATE INDEX IF NOT EXISTS idx_customers_updated ON customers(updated_ts);
        CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status, created_ts);
        """)

        # Migration: add platform column if table already existed without it
        cur = conn.execute("PRAGMA table_info(events)")
        cols = [r["name"] for r in cur.fetchall()]
        if cols and "platform" not in cols:
            conn.execute("ALTER TABLE events ADD COLUMN platform TEXT NOT NULL DEFAULT 'facebook'")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_platform_ts ON events(platform, created_ts)")


def _parse_ts(val: Any, default: float) -> float:
    """Chuyển timestamp thành float, hỗ trợ cả int/float, epoch string và ISO-8601 string (Facebook Graph API)."""
    if val is None or val == "":
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        s = val.strip()
        try:
            return float(s)
        except ValueError:
            pass
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
        except Exception:
            return default
    return default


def record_event(
    event: dict[str, Any], db_path: Path | str | None = None
) -> tuple[int, bool]:
    """Ghi event vào SQLite. Trả (id, is_new). Dedup qua UNIQUE(kind, object_id)."""
    init_db(db_path)
    now = time.time()
    kind = str(event.get("kind") or "comment").strip()
    platform = str(event.get("platform") or "facebook").strip().lower()
    if platform not in ("facebook", "tiktok", "messenger"):
        platform = "facebook"
    page_id = str(event.get("page_id") or "").strip()
    object_id = str(event.get("object_id") or "").strip()
    thread_id = str(event.get("thread_id") or "").strip() or None
    from_id = str(event.get("from_id") or "").strip() or None
    from_name = str(event.get("from_name") or "").strip() or None
    body = str(event.get("body") or "").strip()
    cls = str(event.get("class") or "").strip() or None
    faq_intent = str(event.get("faq_intent") or "").strip() or None
    created_ts = _parse_ts(event.get("created_ts"), now)
    ingested_ts = _parse_ts(event.get("ingested_ts"), now)

    with get_connection(db_path) as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO events (
                    kind, platform, page_id, object_id, thread_id, from_id, from_name,
                    body, class, faq_intent, created_ts, ingested_ts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    kind, platform, page_id, object_id, thread_id, from_id, from_name,
                    body, cls, faq_intent, created_ts, ingested_ts,
                ),
            )
            return cur.lastrowid, True
        except sqlite3.IntegrityError:
            # Đã tồn tại -> lấy id cũ
            row = conn.execute(
                "SELECT id FROM events WHERE kind = ? AND object_id = ?",
                (kind, object_id),
            ).fetchone()
            return (row["id"] if row else -1), False


def update_event_body(
    kind: str,
    object_id: str,
    body: str,
    from_name: str | None = None,
    db_path: Path | str | None = None,
) -> bool:
    """Cập nhật nội dung bình luận khi có webhook verb=edited."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        if from_name is not None:
            cur = conn.execute(
                "UPDATE events SET body = ?, from_name = ? WHERE kind = ? AND object_id = ?",
                (str(body), str(from_name), str(kind), str(object_id)),
            )
        else:
            cur = conn.execute(
                "UPDATE events SET body = ? WHERE kind = ? AND object_id = ?",
                (str(body), str(kind), str(object_id)),
            )
        return cur.rowcount > 0


def find_identity(
    kind: str, page_id: str, ext_id: str, db_path: Path | str | None = None
) -> str | None:
    """Tìm crm_id theo định danh. kind=phone bắt buộc page_id = ''."""
    init_db(db_path)
    k = str(kind).strip()
    p = "" if k == "phone" else str(page_id or "").strip()
    x = str(ext_id or "").strip()
    if not x:
        return None

    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT crm_id FROM identities WHERE kind = ? AND page_id = ? AND ext_id = ?",
            (k, p, x),
        ).fetchone()
        return row["crm_id"] if row else None


def link_identity(
    kind: str,
    page_id: str,
    ext_id: str,
    crm_id: str,
    db_path: Path | str | None = None,
) -> None:
    """Gắn một định danh vào crm_id."""
    init_db(db_path)
    k = str(kind).strip()
    p = "" if k == "phone" else str(page_id or "").strip()
    x = str(ext_id or "").strip()
    c = str(crm_id).strip()
    if not x or not c:
        return

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO identities (kind, page_id, ext_id, crm_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(kind, page_id, ext_id) DO UPDATE SET crm_id = excluded.crm_id
            """,
            (k, p, x, c),
        )


def get_customer(crm_id: str, db_path: Path | str | None = None) -> dict[str, Any] | None:
    """Đọc thông tin khách hàng từ SQLite theo crm_id."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM customers WHERE crm_id = ?", (crm_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["phones"] = json.loads(d.get("phones") or "[]")
        d["tags"] = json.loads(d.get("tags") or "[]")
        d["page_ids"] = json.loads(d.get("page_ids") or "[]")
        return d


def get_or_create_customer(
    *,
    name: str | None = None,
    phones: list[str] | None = None,
    page_id: str | None = None,
    from_id: str | None = None,
    psid: str | None = None,
    course_interest: str | None = None,
    campus: str | None = None,
    tag: str = "lead",
    db_path: Path | str | None = None,
) -> tuple[dict[str, Any], bool]:
    """Tìm hoặc tạo mới khách hàng (gộp mạnh theo phone, gộp page theo from_id/psid).

    Trả (customer_dict, is_new).
    """
    init_db(db_path)
    phones = [str(p).strip() for p in (phones or []) if str(p).strip()]
    crm_id = None

    # 1. Tìm theo SĐT trước (GLOBAL xuyên page)
    for p in phones:
        cid = find_identity("phone", "", p, db_path)
        if cid:
            crm_id = cid
            break

    # 2. Tìm theo from_id (page-scoped)
    if not crm_id and page_id and from_id:
        crm_id = find_identity("fb_comment_from", page_id, from_id, db_path)

    # 3. Tìm theo psid (page-scoped)
    if not crm_id and page_id and psid:
        crm_id = find_identity("fb_psid", page_id, psid, db_path)

    now = time.time()
    is_new = False

    if crm_id:
        existing = get_customer(crm_id, db_path)
    else:
        existing = None

    if not existing:
        is_new = True
        crm_id = "c_" + uuid.uuid4().hex[:12]
        cust_name = str(name or "Ẩn danh").strip()
        merged_phones = list(dict.fromkeys(phones))
        merged_pages = [str(page_id)] if page_id else []
        tags = [tag] if tag else []
        md_path = f"crm/customers/{crm_id}.md"

        cust_dict = {
            "crm_id": crm_id,
            "name": cust_name,
            "phones": merged_phones,
            "tags": tags,
            "course_interest": course_interest or "",
            "campus": campus or "",
            "page_ids": merged_pages,
            "md_path": md_path,
            "updated_ts": now,
        }
        with get_connection(db_path) as conn:
            conn.execute(
                """
                INSERT INTO customers (
                    crm_id, name, phones, tags, course_interest, campus, page_ids, md_path, updated_ts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    crm_id,
                    cust_name,
                    json.dumps(merged_phones, ensure_ascii=False),
                    json.dumps(tags, ensure_ascii=False),
                    course_interest or "",
                    campus or "",
                    json.dumps(merged_pages, ensure_ascii=False),
                    md_path,
                    now,
                ),
            )
    else:
        # Cập nhật thông tin khách cũ
        cust_name = existing.get("name") or "Ẩn danh"
        if cust_name in ("Ẩn danh", "") and name and name not in ("Ẩn danh", ""):
            cust_name = str(name).strip()

        old_phones = existing.get("phones") or []
        merged_phones = list(dict.fromkeys(old_phones + phones))

        old_pages = existing.get("page_ids") or []
        merged_pages = list(dict.fromkeys(old_pages + ([str(page_id)] if page_id else [])))

        old_tags = existing.get("tags") or []
        if tag and tag not in old_tags:
            old_tags.append(tag)

        cust_course = existing.get("course_interest") or course_interest or ""
        cust_campus = existing.get("campus") or campus or ""
        md_path = existing.get("md_path") or f"crm/customers/{crm_id}.md"

        cust_dict = {
            "crm_id": crm_id,
            "name": cust_name,
            "phones": merged_phones,
            "tags": old_tags,
            "course_interest": cust_course,
            "campus": cust_campus,
            "page_ids": merged_pages,
            "md_path": md_path,
            "updated_ts": now,
        }
        with get_connection(db_path) as conn:
            conn.execute(
                """
                UPDATE customers SET
                    name = ?, phones = ?, tags = ?, course_interest = ?, campus = ?,
                    page_ids = ?, md_path = ?, updated_ts = ?
                WHERE crm_id = ?
                """,
                (
                    cust_name,
                    json.dumps(merged_phones, ensure_ascii=False),
                    json.dumps(old_tags, ensure_ascii=False),
                    cust_course,
                    cust_campus,
                    json.dumps(merged_pages, ensure_ascii=False),
                    md_path,
                    now,
                    crm_id,
                ),
            )

    # Gắn mọi định danh cung cấp vào crm_id này
    for p in merged_phones:
        link_identity("phone", "", p, crm_id, db_path)
    if page_id and from_id:
        link_identity("fb_comment_from", page_id, from_id, crm_id, db_path)
    if page_id and psid:
        link_identity("fb_psid", page_id, psid, crm_id, db_path)

    return cust_dict, is_new


def search_customers(
    query: str, db_path: Path | str | None = None, limit: int = 50
) -> list[dict[str, Any]]:
    """Tìm kiếm khách hàng bằng LIKE trên phones và name (không FTS5 v1)."""
    init_db(db_path)
    q = f"%{str(query or '').strip()}%"
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM customers
            WHERE name LIKE ? OR phones LIKE ?
            ORDER BY updated_ts DESC
            LIMIT ?
            """,
            (q, q, limit),
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["phones"] = json.loads(d.get("phones") or "[]")
            d["tags"] = json.loads(d.get("tags") or "[]")
            d["page_ids"] = json.loads(d.get("page_ids") or "[]")
            out.append(d)
        return out


def delete_customer(crm_id: str, db_path: Path | str | None = None) -> bool:
    """Xóa khách theo chuẩn PDPD (xóa identities, customers, ẩn SĐT trong events)."""
    init_db(db_path)
    c = str(crm_id).strip()
    cust = get_customer(c, db_path)
    if not cust:
        return False

    phones = cust.get("phones") or []

    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM identities WHERE crm_id = ?", (c,))
        conn.execute("DELETE FROM customers WHERE crm_id = ?", (c,))
        # Ẩn SĐT trong events còn lại
        for p in phones:
            if p:
                conn.execute(
                    "UPDATE events SET body = REPLACE(body, ?, '[redacted]') WHERE body LIKE ?",
                    (p, f"%{p}%"),
                )
    return True


def create_draft(
    event_id: int | None,
    page_id: str,
    target_id: str,
    proposed: str,
    class_name: str,
    db_path: Path | str | None = None,
) -> int:
    """Tạo bản ghi draft chờ nhân viên duyệt."""
    init_db(db_path)
    now = time.time()
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO drafts (event_id, page_id, target_id, proposed, class, status, created_ts)
            VALUES (?, ?, ?, ?, ?, 'pending', ?)
            """,
            (event_id, str(page_id), str(target_id), str(proposed), str(class_name), now),
        )
        return cur.lastrowid


def list_drafts(
    page_id: str | None = None,
    status: str = "pending",
    kind: str | None = None,
    db_path: Path | str | None = None,
    limit: int = 50,
    page_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Liệt kê danh sách draft. Hỗ trợ lọc theo channel kind ('comment' hoặc 'message') và page_ids."""
    init_db(db_path)
    conds = ["d.status = ?"]
    params: list[Any] = [status]
    if page_id:
        conds.append("d.page_id = ?")
        params.append(str(page_id))
    elif page_ids is not None:
        pids = [str(p).strip() for p in page_ids if str(p).strip()]
        if pids:
            placeholders = ",".join("?" * len(pids))
            conds.append(f"d.page_id IN ({placeholders})")
            params.extend(pids)
        else:
            conds.append("1 = 0")
    if kind:
        k = str(kind).strip().lower()
        if k == "comment":
            conds.append("(e.kind = 'comment' OR (e.kind IS NULL AND d.target_id LIKE '%_%'))")
        elif k in ("message", "messenger"):
            conds.append("(e.kind = 'message' OR e.platform = 'messenger' OR (e.kind IS NULL AND d.target_id NOT LIKE '%_%'))")
    where = f"WHERE {' AND '.join(conds)}"
    sql = f"""
        SELECT 
            d.*,
            COALESCE(e.kind, CASE WHEN d.target_id NOT LIKE '%_%' AND length(d.target_id) > 14 THEN 'message' ELSE 'comment' END) as event_kind,
            COALESCE(e.platform, CASE WHEN d.target_id NOT LIKE '%_%' AND length(d.target_id) > 14 THEN 'messenger' ELSE 'facebook' END) as event_platform,
            e.from_name as from_name,
            e.from_id as from_id,
            e.body as source_body,
            e.created_ts as event_created_ts
        FROM drafts d
        LEFT JOIN events e ON d.event_id = e.id
        {where}
        ORDER BY d.created_ts DESC LIMIT ?
    """
    params.append(limit)
    with get_connection(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def update_draft_status(
    draft_id: int, status: str, db_path: Path | str | None = None
) -> bool:
    """Cập nhật trạng thái draft (approved | rejected | sent | expired)."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "UPDATE drafts SET status = ? WHERE id = ?", (status, draft_id)
        )
        return cur.rowcount > 0


def record_action(
    event_id: int | None,
    action: str,
    graph_id: str | None,
    mode: str,
    actor: str,
    db_path: Path | str | None = None,
) -> int:
    """Ghi nhận hành động đã thực hiện (reply/hide/like/send/skip)."""
    init_db(db_path)
    now = time.time()
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO actions (event_id, action, graph_id, mode, actor, ts)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_id, action, graph_id, mode, actor, now),
        )
        return cur.lastrowid


def get_rate_count(page_id: str, hour_key: str, db_path: Path | str | None = None) -> int:
    """Lấy số lượng replies đã gửi trong 1 giờ."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT replies FROM rate_buckets WHERE page_id = ? AND hour_key = ?",
            (str(page_id), str(hour_key)),
        ).fetchone()
        return int(row["replies"]) if row else 0


def increment_rate_count(
    page_id: str, hour_key: str, db_path: Path | str | None = None
) -> int:
    """Tăng số lượng replies trong 1 giờ thêm 1."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO rate_buckets (page_id, hour_key, replies)
            VALUES (?, ?, 1)
            ON CONFLICT(page_id, hour_key) DO UPDATE SET replies = replies + 1
            """,
            (str(page_id), str(hour_key)),
        )
        row = conn.execute(
            "SELECT replies FROM rate_buckets WHERE page_id = ? AND hour_key = ?",
            (str(page_id), str(hour_key)),
        ).fetchone()
        return int(row["replies"]) if row else 1


def get_messaging_window(
    page_id: str, psid: str, db_path: Path | str | None = None
) -> dict[str, Any] | None:
    """Đọc thông tin cửa sổ 24h và takeover của PSID."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM messaging_windows WHERE page_id = ? AND psid = ?",
            (str(page_id), str(psid)),
        ).fetchone()
        return dict(row) if row else None


def update_messaging_window(
    page_id: str,
    psid: str,
    *,
    user_ts: float | None = None,
    page_ts: float | None = None,
    takeover_until: float | None = None,
    db_path: Path | str | None = None,
) -> None:
    """Cập nhật thời điểm user nhắn, page nhắn, hoặc takeover."""
    init_db(db_path)
    now = time.time()
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "SELECT * FROM messaging_windows WHERE page_id = ? AND psid = ?",
            (str(page_id), str(psid)),
        ).fetchone()
        if not cur:
            conn.execute(
                """
                INSERT INTO messaging_windows (page_id, psid, last_user_ts, last_page_ts, takeover_until)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(page_id),
                    str(psid),
                    user_ts or now,
                    page_ts or 0.0,
                    takeover_until or 0.0,
                ),
            )
        else:
            sets = []
            vals = []
            if user_ts is not None:
                sets.append("last_user_ts = ?")
                vals.append(user_ts)
            if page_ts is not None:
                sets.append("last_page_ts = ?")
                vals.append(page_ts)
            if takeover_until is not None:
                sets.append("takeover_until = ?")
                vals.append(takeover_until)
            if sets:
                vals.extend([str(page_id), str(psid)])
                conn.execute(
                    f"UPDATE messaging_windows SET {', '.join(sets)} WHERE page_id = ? AND psid = ?",
                    vals,
                )


def get_cursor(
    page_id: str, post_id: str, db_path: Path | str | None = None
) -> dict[str, Any] | None:
    """Đọc cursor quét post (last_count, last_comment_id)."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM page_cursors WHERE page_id = ? AND post_id = ?",
            (str(page_id), str(post_id)),
        ).fetchone()
        return dict(row) if row else None


def set_cursor(
    page_id: str,
    post_id: str,
    last_count: int,
    last_comment_id: str,
    db_path: Path | str | None = None,
) -> None:
    """Cập nhật cursor quét post."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO page_cursors (page_id, post_id, last_count, last_comment_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(page_id, post_id) DO UPDATE SET
                last_count = excluded.last_count,
                last_comment_id = excluded.last_comment_id
            """,
            (str(page_id), str(post_id), int(last_count), str(last_comment_id)),
        )


def gc_events(older_than_days: int = 90, db_path: Path | str | None = None) -> int:
    """Xóa các events cũ hơn N ngày để giải phóng dung lượng."""
    init_db(db_path)
    threshold = time.time() - (older_than_days * 86400.0)
    with get_connection(db_path) as conn:
        cur = conn.execute("DELETE FROM events WHERE created_ts < ?", (threshold,))
        return cur.rowcount


def list_events(
    page_id: str | None = None,
    class_name: str | None = None,
    platform: str | None = None,
    kind: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db_path: Path | str | None = None,
    page_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Truy vấn danh sách sự kiện từ bảng events."""
    init_db(db_path)
    conds = []
    params: list[Any] = []
    if page_id:
        conds.append("page_id = ?")
        params.append(str(page_id))
    elif page_ids is not None:
        pids = [str(p).strip() for p in page_ids if str(p).strip()]
        if pids:
            placeholders = ",".join("?" * len(pids))
            conds.append(f"page_id IN ({placeholders})")
            params.extend(pids)
        else:
            conds.append("1 = 0")
    if class_name:
        conds.append("class = ?")
        params.append(str(class_name))
    if platform:
        conds.append("platform = ?")
        params.append(str(platform).strip().lower())
    if kind:
        conds.append("kind = ?")
        params.append(str(kind).strip().lower())

    where = f"WHERE {' AND '.join(conds)}" if conds else ""
    sql = f"SELECT * FROM events {where} ORDER BY created_ts DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_connection(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def get_event(event_id: int, db_path: Path | str | None = None) -> dict[str, Any] | None:
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM events WHERE id = ?", (int(event_id),)).fetchone()
        return dict(row) if row else None


def customer_behavior(crm_id: str, db_path: Path | str | None = None) -> dict[str, Any]:
    """Tóm tắt hành vi khách từ events gắn identity (comment + messenger)."""
    init_db(db_path)
    crm_id = str(crm_id)
    with get_connection(db_path) as conn:
        ids = conn.execute(
            "SELECT kind, page_id, ext_id FROM identities WHERE crm_id = ?",
            (crm_id,),
        ).fetchall()
        cust = conn.execute("SELECT * FROM customers WHERE crm_id = ?", (crm_id,)).fetchone()
        ext_ids = [str(r["ext_id"]) for r in ids]
        page_ids = list({str(r["page_id"]) for r in ids if r["page_id"]})
        events: list[dict[str, Any]] = []
        if ext_ids:
            placeholders = ",".join("?" * len(ext_ids))
            events = [
                dict(r)
                for r in conn.execute(
                    f"SELECT * FROM events WHERE from_id IN ({placeholders}) "
                    "ORDER BY created_ts DESC LIMIT 200",
                    ext_ids,
                ).fetchall()
            ]
        elif page_ids:
            events = [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM events WHERE page_id = ? ORDER BY created_ts DESC LIMIT 80",
                    (page_ids[0],),
                ).fetchall()
            ]

    by_platform: dict[str, int] = {}
    by_class: dict[str, int] = {}
    msg_n = 0
    cmt_n = 0
    last_intent = None
    last_body = ""
    last_ts = 0.0
    for e in events:
        plat = str(e.get("platform") or "facebook")
        by_platform[plat] = by_platform.get(plat, 0) + 1
        cl = str(e.get("class") or "unknown")
        by_class[cl] = by_class.get(cl, 0) + 1
        if e.get("kind") == "message":
            msg_n += 1
        elif e.get("kind") == "comment":
            cmt_n += 1
        ts = float(e.get("created_ts") or 0)
        if ts >= last_ts:
            last_ts = ts
            last_intent = e.get("faq_intent") or e.get("class")
            last_body = str(e.get("body") or "")[:180]

    stage = "moi_tiep_can"
    if msg_n >= 3 or cmt_n >= 3:
        stage = "dang_tu_van"
    if by_class.get("lead", 0) > 0:
        stage = "lead"
    if last_ts and (time.time() - last_ts) > 7 * 86400 and by_class.get("lead", 0) == 0:
        stage = "im_lang"

    return {
        "crm_id": crm_id,
        "stage": stage,
        "message_count": msg_n,
        "comment_count": cmt_n,
        "by_platform": by_platform,
        "by_class": by_class,
        "last_intent": last_intent,
        "last_body": last_body,
        "last_ts": last_ts,
        "phones": json.loads((cust["phones"] if cust else None) or "[]") if cust else [],
        "campus": (cust["campus"] if cust else "") or "",
        "course_interest": (cust["course_interest"] if cust else "") or "",
    }


def get_draft(draft_id: int, db_path: Path | str | None = None) -> dict[str, Any] | None:
    """Đọc 1 draft theo ID, kèm thông tin event liên quan."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT 
                d.*,
                COALESCE(e.kind, CASE WHEN d.target_id NOT LIKE '%_%' AND length(d.target_id) > 14 THEN 'message' ELSE 'comment' END) as event_kind,
                COALESCE(e.platform, CASE WHEN d.target_id NOT LIKE '%_%' AND length(d.target_id) > 14 THEN 'messenger' ELSE 'facebook' END) as event_platform,
                e.from_name as from_name,
                e.from_id as from_id,
                e.body as source_body,
                e.created_ts as event_created_ts
            FROM drafts d
            LEFT JOIN events e ON d.event_id = e.id
            WHERE d.id = ?
            """,
            (draft_id,),
        ).fetchone()
        return dict(row) if row else None


def get_identities_for_customer(
    crm_id: str, db_path: Path | str | None = None
) -> list[dict[str, Any]]:
    """Đọc danh sách identities của 1 khách hàng."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM identities WHERE crm_id = ?", (str(crm_id),)
        ).fetchall()
        return [dict(r) for r in rows]


def get_stats(
    page_ids: list[str] | None = None, db_path: Path | str | None = None
) -> dict[str, Any]:
    """Lấy số liệu tổng quan nhanh cho dashboard. Hỗ trợ lọc theo page_ids."""
    init_db(db_path)
    now = time.time()
    day_ago = now - 86400.0

    p_filter = ""
    p_params: list[Any] = []
    if page_ids is not None:
        pids = [str(p).strip() for p in page_ids if str(p).strip()]
        if pids:
            placeholders = ",".join("?" * len(pids))
            p_filter = f" AND page_id IN ({placeholders})"
            p_params = pids
        else:
            return {
                "total_events": 0,
                "events_24h": 0,
                "leads_24h": 0,
                "human_needed_24h": 0,
                "replies_24h": 0,
                "spam_hidden_24h": 0,
                "pending_drafts": 0,
                "pending_comment_drafts": 0,
                "pending_message_drafts": 0,
                "total_customers": 0,
            }

    with get_connection(db_path) as conn:
        ev_where = f"WHERE 1=1{p_filter}"
        total_ev = conn.execute(f"SELECT COUNT(*) FROM events {ev_where}", p_params).fetchone()[0]
        ev_24h = conn.execute(
            f"SELECT COUNT(*) FROM events WHERE ingested_ts >= ?{p_filter}",
            [day_ago] + p_params,
        ).fetchone()[0]
        leads_24h = conn.execute(
            f"SELECT COUNT(*) FROM events WHERE ingested_ts >= ? AND class = 'lead'{p_filter}",
            [day_ago] + p_params,
        ).fetchone()[0]
        human_24h = conn.execute(
            f"SELECT COUNT(*) FROM events WHERE ingested_ts >= ? AND class IN ('ambiguous', 'ky_thuat'){p_filter}",
            [day_ago] + p_params,
        ).fetchone()[0]

        if p_filter:
            act_p_filter = f" AND e.page_id IN ({','.join('?' * len(p_params))})"
            replies_24h = conn.execute(
                f"SELECT COUNT(*) FROM actions a JOIN events e ON a.event_id = e.id WHERE a.action = 'reply' AND a.ts >= ?{act_p_filter}",
                [day_ago] + p_params,
            ).fetchone()[0]
            spam_hidden_24h = conn.execute(
                f"SELECT COUNT(*) FROM actions a JOIN events e ON a.event_id = e.id WHERE a.action = 'hide' AND a.ts >= ?{act_p_filter}",
                [day_ago] + p_params,
            ).fetchone()[0]
        else:
            replies_24h = conn.execute(
                "SELECT COUNT(*) FROM actions WHERE action = 'reply' AND ts >= ?",
                (day_ago,),
            ).fetchone()[0]
            spam_hidden_24h = conn.execute(
                "SELECT COUNT(*) FROM actions WHERE action = 'hide' AND ts >= ?",
                (day_ago,),
            ).fetchone()[0]

        dr_where = f"WHERE d.status = 'pending'{p_filter.replace('page_id', 'd.page_id')}"
        pending_dr = conn.execute(
            f"SELECT COUNT(*) FROM drafts d {dr_where}", p_params
        ).fetchone()[0]
        pending_cmt_dr = conn.execute(
            f"""
            SELECT COUNT(*) FROM drafts d
            LEFT JOIN events e ON d.event_id = e.id
            {dr_where} AND (e.kind = 'comment' OR (e.kind IS NULL AND d.target_id LIKE '%_%'))
            """,
            p_params,
        ).fetchone()[0]
        pending_msg_dr = conn.execute(
            f"""
            SELECT COUNT(*) FROM drafts d
            LEFT JOIN events e ON d.event_id = e.id
            {dr_where} AND (e.kind = 'message' OR e.platform = 'messenger' OR (e.kind IS NULL AND d.target_id NOT LIKE '%_%'))
            """,
            p_params,
        ).fetchone()[0]

        if p_filter:
            total_cust = conn.execute(
                f"SELECT COUNT(DISTINCT crm_id) FROM identities WHERE page_id IN ({','.join('?' * len(p_params))})",
                p_params,
            ).fetchone()[0]
        else:
            total_cust = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

        return {
            "total_events": total_ev,
            "events_24h": ev_24h,
            "leads_24h": leads_24h,
            "human_needed_24h": human_24h,
            "replies_24h": replies_24h,
            "spam_hidden_24h": spam_hidden_24h,
            "pending_drafts": pending_dr,
            "pending_comment_drafts": pending_cmt_dr,
            "pending_message_drafts": pending_msg_dr,
            "total_customers": total_cust,
        }


def get_messaging_window(
    page_id: str, psid: str, db_path: Path | str | None = None
) -> dict[str, Any] | None:
    """Lấy thông tin cửa sổ 24h và takeover của một cuộc trò chuyện Messenger."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT page_id, psid, last_user_ts, last_page_ts, takeover_until FROM messaging_windows WHERE page_id = ? AND psid = ?",
            (str(page_id), str(psid)),
        ).fetchone()
        if not row:
            return None
        return dict(row)


def update_messaging_window(
    page_id: str,
    psid: str,
    *,
    is_user: bool = True,
    user_ts: float | None = None,
    page_ts: float | None = None,
    takeover_until: float | None = None,
    db_path: Path | str | None = None,
) -> None:
    """Cập nhật timestamp tin nhắn mới (user hoặc page) và takeover_until nếu có."""
    init_db(db_path)
    now = time.time()
    pid = str(page_id)
    sid = str(psid)

    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT last_user_ts, last_page_ts, takeover_until FROM messaging_windows WHERE page_id = ? AND psid = ?",
            (pid, sid),
        ).fetchone()

        if row:
            curr_user = row["last_user_ts"] or 0.0
            curr_page = row["last_page_ts"] or 0.0
            if user_ts is not None:
                l_user = max(curr_user, float(user_ts))
            elif is_user:
                l_user = max(curr_user, now)
            else:
                l_user = curr_user

            if page_ts is not None:
                l_page = max(curr_page, float(page_ts))
            elif not is_user:
                l_page = max(curr_page, now)
            else:
                l_page = curr_page

            t_until = takeover_until if takeover_until is not None else (row["takeover_until"] or 0.0)
            conn.execute(
                "UPDATE messaging_windows SET last_user_ts = ?, last_page_ts = ?, takeover_until = ? WHERE page_id = ? AND psid = ?",
                (l_user, l_page, t_until, pid, sid),
            )
        else:
            l_user = float(user_ts) if user_ts is not None else (now if is_user else 0.0)
            l_page = float(page_ts) if page_ts is not None else (now if not is_user else 0.0)
            t_until = takeover_until if takeover_until is not None else 0.0
            conn.execute(
                "INSERT INTO messaging_windows (page_id, psid, last_user_ts, last_page_ts, takeover_until) VALUES (?, ?, ?, ?, ?)",
                (pid, sid, l_user, l_page, t_until),
            )


def set_human_takeover(
    page_id: str, psid: str, duration_hours: float = 4.0, db_path: Path | str | None = None
) -> float:
    """Đóng băng tự động cho thread khi nhân viên can thiệp (takeover_until = now + 4h)."""
    now = time.time()
    until = now + (duration_hours * 3600.0)
    update_messaging_window(page_id, psid, is_user=False, takeover_until=until, db_path=db_path)
    return until


def release_human_takeover(page_id: str, psid: str, db_path: Path | str | None = None) -> None:
    """Gỡ bỏ takeover (Javis nhận lại) -> takeover_until = 0."""
    update_messaging_window(page_id, psid, is_user=False, takeover_until=0.0, db_path=db_path)


def is_in_24h_window(page_id: str, psid: str, db_path: Path | str | None = None) -> bool:
    """Kiểm tra tin nhắn người dùng gần nhất có trong vòng 24 giờ hay không."""
    win = get_messaging_window(page_id, psid, db_path)
    if not win or not win.get("last_user_ts"):
        return False
    return (time.time() - float(win["last_user_ts"])) < (24.0 * 3600.0)


def is_under_takeover(page_id: str, psid: str, db_path: Path | str | None = None) -> bool:
    """Kiểm tra thread có đang bị nhân viên takeover không."""
    win = get_messaging_window(page_id, psid, db_path)
    if not win or not win.get("takeover_until"):
        return False
    return float(win["takeover_until"]) > time.time()


def get_recent_conversations(
    page_id: str | None = None,
    page_ids: list[str] | None = None,
    limit: int = 50,
    db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Danh sách các cuộc hội thoại Messenger gần đây kèm tên khách và trạng thái takeover."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        if page_id:
            rows = conn.execute(
                "SELECT page_id, psid, last_user_ts, last_page_ts, takeover_until FROM messaging_windows "
                "WHERE page_id = ? "
                "ORDER BY COALESCE(last_user_ts,0) DESC, COALESCE(last_page_ts,0) DESC LIMIT ?",
                (str(page_id), int(limit)),
            ).fetchall()
        elif page_ids is not None:
            if not page_ids:
                return []
            p_holders = ",".join("?" for _ in page_ids)
            rows = conn.execute(
                f"SELECT page_id, psid, last_user_ts, last_page_ts, takeover_until FROM messaging_windows "
                f"WHERE page_id IN ({p_holders}) "
                f"ORDER BY COALESCE(last_user_ts,0) DESC, COALESCE(last_page_ts,0) DESC LIMIT ?",
                (*[str(x) for x in page_ids], int(limit)),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT page_id, psid, last_user_ts, last_page_ts, takeover_until FROM messaging_windows "
                "ORDER BY COALESCE(last_user_ts,0) DESC, COALESCE(last_page_ts,0) DESC LIMIT ?",
                (int(limit),),
            ).fetchall()

        out = []
        for r in rows:
            d = dict(r)
            pid = d["page_id"]
            sid = d["psid"]

            last = conn.execute(
                "SELECT body, class, created_ts, from_name FROM events "
                "WHERE page_id = ? AND (from_id = ? OR thread_id = ?) AND kind IN ('message','echo') "
                "ORDER BY created_ts DESC LIMIT 1",
                (pid, sid, sid),
            ).fetchone()
            if last:
                d["last_body"] = last["body"]
                d["last_class"] = last["class"]
                d["last_event_ts"] = last["created_ts"]

            # Lấy tên khách hàng
            name_row = conn.execute(
                "SELECT from_name FROM events "
                "WHERE page_id = ? AND from_id = ? AND kind = 'message' AND from_name IS NOT NULL "
                "AND from_name != '' AND from_name NOT LIKE 'Khách Messenger%' "
                "ORDER BY created_ts DESC LIMIT 1",
                (pid, sid),
            ).fetchone()

            if name_row and name_row["from_name"]:
                d["customer_name"] = name_row["from_name"]
            else:
                ident = conn.execute(
                    "SELECT crm_id FROM identities WHERE kind = 'fb_psid' AND page_id = ? AND ext_id = ?",
                    (pid, sid),
                ).fetchone()
                if ident:
                    c_row = conn.execute("SELECT name FROM customers WHERE crm_id = ?", (ident["crm_id"],)).fetchone()
                    if c_row and c_row["name"] and not c_row["name"].startswith("Khách Messenger"):
                        d["customer_name"] = c_row["name"]

            if not d.get("customer_name"):
                d["customer_name"] = f"Khách Messenger {sid[-4:] if len(sid) >= 4 else sid}"

            out.append(d)
        return out


def ensure_conversation(
    page_id: str,
    psid: str,
    customer_name: str | None = None,
    last_ts: float | None = None,
    snippet: str | None = None,
    db_path: Path | str | None = None,
) -> None:
    """Đảm bảo một cuộc hội thoại từ Graph API được lưu vào messaging_windows và customers."""
    init_db(db_path)
    pid = str(page_id)
    sid = str(psid)
    now = time.time()
    ts = float(last_ts) if last_ts else now

    update_messaging_window(pid, sid, is_user=True, user_ts=ts, db_path=db_path)

    with get_connection(db_path) as conn:
        if customer_name and not customer_name.startswith("Khách Messenger"):
            get_or_create_customer(
                name=customer_name,
                page_id=pid,
                psid=sid,
                db_path=db_path,
            )

        if snippet:
            existing = conn.execute(
                "SELECT id FROM events WHERE page_id = ? AND (from_id = ? OR thread_id = ?) AND kind IN ('message','echo') LIMIT 1",
                (pid, sid, sid),
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO events (kind, platform, page_id, object_id, thread_id, from_id, from_name, body, created_ts, ingested_ts) "
                    "VALUES ('message', 'messenger', ?, ?, ?, ?, ?, ?, ?, ?)",
                    (pid, f"conv_{sid}_{int(ts)}", sid, sid, customer_name or f"Khách {sid[-4:]}", snippet, ts, now),
                )


def get_conversation_thread_events(
    page_id: str,
    psid: str,
    limit: int = 50,
    db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Lấy danh sách tin nhắn / echoes trong thread giữa page_id và psid."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT id, kind, platform, page_id, object_id, thread_id, from_id, from_name, body, class, created_ts "
            "FROM events WHERE page_id = ? AND (from_id = ? OR thread_id = ?) AND kind IN ('message','echo') "
            "ORDER BY created_ts ASC LIMIT ?",
            (str(page_id), str(psid), str(psid), int(limit)),
        ).fetchall()
        return [dict(r) for r in rows]
