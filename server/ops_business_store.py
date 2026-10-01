# -*- coding: utf-8 -*-
"""Durable SQLite Store for Javis Business Operational Modules.

Cơ sở dữ liệu vận hành chuẩn hóa cho các phân hệ doanh nghiệp:
- business_modules: Danh mục và cấu hình phân hệ nghiệp vụ
- module_records: Hồ sơ phát sinh thật của từng phân hệ (Tuyển dụng, Hợp đồng, SOP, KPI...)
- module_activities: Nhật ký vết kiểm toán (Audit Trail)
- module_comments: Bình luận & trao đổi nội bộ trên từng hồ sơ
- module_attachments: Tệp đính kèm & tài liệu liên kết

Database: STATE_DIR / "business_modules.sqlite3"
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

import config

DEFAULT_DB_PATH = config.STATE_DIR / "business_modules.sqlite3"

# Bản đồ ánh xạ alias để tương thích cả ID từ giao diện Hub và Code chuẩn
ALIAS_MAP: Dict[str, str] = {
    "pipe_lead": "crm_lead",
    "pipe_order": "orders",
    "pipe_orders": "orders",
    "pipe_task": "kanban",
    "pipe_kanban": "kanban",
    "people_recruitment": "recruitment",
    "people_contract": "contract",
    "people_sop": "sop",
    "exec_inbox": "inbox",
    "exec_kpi": "kpi",
    "exec_projects": "projects",
    "exec_finance": "finance",
    "exec_calendar": "calendar",
}

# 11 Phân hệ vận hành chuẩn của Javis OS
DEFAULT_MODULES = [
    {
        "id": "mod_pipe_lead",
        "code": "crm_lead",
        "name": "Lead, tư vấn và chăm sóc lại",
        "category": "pipeline",
        "description": "Phân loại, nuôi dưỡng và kích hoạt lại tệp khách hàng tiềm năng đa kênh.",
        "icon": "Users",
        "color": "emerald",
        "status": "has_data",
        "is_connected": 1,
    },
    {
        "id": "mod_pipe_orders",
        "code": "orders",
        "name": "Đơn hàng & Chốt sale",
        "category": "pipeline",
        "description": "Đơn hàng phát sinh từ hội thoại tư vấn và quản lý doanh thu chốt đơn.",
        "icon": "ShoppingBag",
        "color": "amber",
        "status": "has_data",
        "is_connected": 1,
    },
    {
        "id": "mod_pipe_kanban",
        "code": "kanban",
        "name": "Kanban công việc",
        "category": "pipeline",
        "description": "Bảng việc trực quan, phân công nhiệm vụ cứu lead và theo dõi tiến độ.",
        "icon": "CheckSquare",
        "color": "purple",
        "status": "has_data",
        "is_connected": 1,
    },
    {
        "id": "mod_people_recruitment",
        "code": "recruitment",
        "name": "Tuyển dụng & Nhân sự",
        "category": "people_knowledge",
        "description": "Chuẩn hóa quy trình tiếp nhận ứng viên, lưu trữ CV, phỏng vấn và hội nhập nhân sự mới.",
        "icon": "Users",
        "color": "purple",
        "status": "connected",
        "is_connected": 1,
    },
    {
        "id": "mod_people_contract",
        "code": "contract",
        "name": "Hợp đồng & Tài liệu",
        "category": "people_knowledge",
        "description": "Quản lý hợp đồng đối tác, biểu mẫu pháp lý và theo dõi hiệu lực ký duyệt định kỳ.",
        "icon": "FileText",
        "color": "amber",
        "status": "connected",
        "is_connected": 1,
    },
    {
        "id": "mod_people_sop",
        "code": "sop",
        "name": "SOP & Tài liệu nội bộ",
        "category": "people_knowledge",
        "description": "Hệ thống quy trình tác nghiệp chuẩn (SOP), bảng giá dịch vụ và chính sách công ty.",
        "icon": "BookOpen",
        "color": "emerald",
        "status": "connected",
        "is_connected": 1,
    },
    {
        "id": "mod_exec_inbox",
        "code": "inbox",
        "name": "Hộp thư xử lý",
        "category": "executive",
        "description": "Quản lý luồng xử lý email và tin nhắn Fanpage tập trung, phân luồng yêu cầu hỗ trợ.",
        "icon": "Mail",
        "color": "blue",
        "status": "has_data",
        "is_connected": 1,
    },
    {
        "id": "mod_exec_kpi",
        "code": "kpi",
        "name": "KPI & Báo cáo",
        "category": "executive",
        "description": "Khung chỉ số đánh giá hiệu quả vận hành: thời gian phản hồi, tỷ lệ xử lý và kết quả kinh doanh.",
        "icon": "BarChart3",
        "color": "rose",
        "status": "connected",
        "is_connected": 1,
    },
    {
        "id": "mod_exec_projects",
        "code": "projects",
        "name": "Dự án",
        "category": "executive",
        "description": "Theo dõi tiến độ các dự án và sáng kiến trọng điểm theo từng mốc thời gian.",
        "icon": "FolderGit2",
        "color": "emerald",
        "status": "connected",
        "is_connected": 1,
    },
    {
        "id": "mod_exec_finance",
        "code": "finance",
        "name": "Tài chính",
        "category": "executive",
        "description": "Chuẩn hóa quy trình ghi nhận thu chi, đề xuất tạm ứng và lưu trữ chứng từ thanh toán.",
        "icon": "DollarSign",
        "color": "emerald",
        "status": "connected",
        "is_connected": 1,
    },
    {
        "id": "mod_exec_calendar",
        "code": "calendar",
        "name": "Lịch & nhắc việc",
        "category": "executive",
        "description": "Quản lý lịch làm việc chung, các mốc thời hạn báo cáo và lịch hẹn công tác.",
        "icon": "Calendar",
        "color": "teal",
        "status": "connected",
        "is_connected": 1,
    },
]

# Định nghĩa workflow trạng thái chi tiết theo từng phân hệ
MODULE_WORKFLOWS: Dict[str, List[Dict[str, str]]] = {
    "recruitment": [
        {"id": "new", "label": "Mới ứng tuyển", "color": "blue"},
        {"id": "interviewing", "label": "Đang phỏng vấn", "color": "purple"},
        {"id": "passed", "label": "Đạt tuyển dụng", "color": "emerald"},
        {"id": "onboarded", "label": "Đã Onboarding", "color": "teal"},
        {"id": "rejected", "label": "Không đạt", "color": "rose"},
    ],
    "contract": [
        {"id": "draft", "label": "Bản nháp", "color": "slate"},
        {"id": "pending_approval", "label": "Chờ duyệt", "color": "amber"},
        {"id": "signed", "label": "Đã ký kết", "color": "emerald"},
        {"id": "expired", "label": "Hết hạn", "color": "rose"},
        {"id": "cancelled", "label": "Đã hủy", "color": "zinc"},
    ],
    "sop": [
        {"id": "draft", "label": "Bản thảo", "color": "slate"},
        {"id": "reviewing", "label": "Đang thẩm định", "color": "purple"},
        {"id": "published", "label": "Đã ban hành", "color": "emerald"},
        {"id": "archived", "label": "Lưu trữ", "color": "zinc"},
    ],
    "kpi": [
        {"id": "on_track", "label": "Đạt tiến độ", "color": "emerald"},
        {"id": "at_risk", "label": "Có rủi ro", "color": "amber"},
        {"id": "behind", "label": "Chưa đạt", "color": "rose"},
        {"id": "completed", "label": "Đã hoàn thành", "color": "teal"},
    ],
    "projects": [
        {"id": "planning", "label": "Lập kế hoạch", "color": "blue"},
        {"id": "in_progress", "label": "Đang triển khai", "color": "purple"},
        {"id": "review", "label": "Nghiệm thu", "color": "amber"},
        {"id": "done", "label": "Hoàn thành", "color": "emerald"},
        {"id": "paused", "label": "Tạm dừng", "color": "slate"},
    ],
    "finance": [
        {"id": "pending", "label": "Chờ phê duyệt", "color": "amber"},
        {"id": "approved", "label": "Đã phê duyệt", "color": "blue"},
        {"id": "paid", "label": "Đã chi / Đã thu", "color": "emerald"},
        {"id": "rejected", "label": "Từ chối", "color": "rose"},
    ],
    "calendar": [
        {"id": "scheduled", "label": "Đã lên lịch", "color": "blue"},
        {"id": "in_progress", "label": "Đang diễn ra", "color": "purple"},
        {"id": "completed", "label": "Đã hoàn tất", "color": "emerald"},
        {"id": "cancelled", "label": "Đã hủy", "color": "slate"},
    ],
}


def resolve_module_code(code_or_id: str) -> str:
    """Quy chuẩn mã phân hệ từ alias hoặc ID."""
    cleaned = str(code_or_id or "").strip().lower()
    if cleaned.startswith("mod_"):
        cleaned = cleaned[4:]
    return ALIAS_MAP.get(cleaned, cleaned)


@contextmanager
def get_connection(db_path: Path | str | None = None) -> Generator[sqlite3.Connection, None, None]:
    p = Path(db_path) if db_path else DEFAULT_DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: Path | str | None = None) -> None:
    """Khởi tạo cấu trúc bảng SQLite và nạp dữ liệu định chuẩn ban đầu."""
    with get_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS business_modules (
                id TEXT PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                icon TEXT NOT NULL DEFAULT 'Layers',
                color TEXT NOT NULL DEFAULT 'blue',
                status TEXT NOT NULL DEFAULT 'catalog',
                is_connected INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS module_records (
                id TEXT PRIMARY KEY,
                module_code TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'new',
                priority TEXT NOT NULL DEFAULT 'normal',
                owner_id TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'manual',
                payload_json TEXT NOT NULL DEFAULT '{}',
                due_at TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS module_activities (
                id TEXT PRIMARY KEY,
                record_id TEXT NOT NULL,
                action TEXT NOT NULL,
                actor_id TEXT NOT NULL DEFAULT 'staff',
                before_json TEXT NOT NULL DEFAULT '{}',
                after_json TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                FOREIGN KEY (record_id) REFERENCES module_records(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS module_comments (
                id TEXT PRIMARY KEY,
                record_id TEXT NOT NULL,
                actor_id TEXT NOT NULL DEFAULT 'staff',
                content TEXT NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY (record_id) REFERENCES module_records(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS module_attachments (
                id TEXT PRIMARY KEY,
                record_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_url TEXT NOT NULL,
                file_type TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                FOREIGN KEY (record_id) REFERENCES module_records(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_records_module_code ON module_records(module_code);
            CREATE INDEX IF NOT EXISTS idx_records_status ON module_records(status);
            CREATE INDEX IF NOT EXISTS idx_records_owner ON module_records(owner_id);
            CREATE INDEX IF NOT EXISTS idx_activities_record_id ON module_activities(record_id);
            CREATE INDEX IF NOT EXISTS idx_comments_record_id ON module_comments(record_id);
            CREATE INDEX IF NOT EXISTS idx_attachments_record_id ON module_attachments(record_id);
            """
        )

        # Seed các module mặc định nếu chưa tồn tại
        now = time.time()
        for mod in DEFAULT_MODULES:
            cur = conn.execute("SELECT id FROM business_modules WHERE code = ?", (mod["code"],))
            if not cur.fetchone():
                conn.execute(
                    """
                    INSERT INTO business_modules (
                        id, code, name, category, description, icon, color, status, is_connected, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        mod["id"],
                        mod["code"],
                        mod["name"],
                        mod["category"],
                        mod["description"],
                        mod["icon"],
                        mod["color"],
                        mod["status"],
                        mod["is_connected"],
                        now,
                        now,
                    ),
                )
        conn.commit()


def list_modules(
    category: Optional[str] = None,
    status: Optional[str] = None,
    db_path: Path | str | None = None,
) -> List[Dict[str, Any]]:
    """Lấy danh sách phân hệ kèm số lượng bản ghi thực tế và trạng thái động."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        query = "SELECT * FROM business_modules WHERE 1=1"
        params: List[Any] = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY rowid ASC"

        rows = conn.execute(query, params).fetchall()
        modules = [dict(r) for r in rows]

        # Đếm số lượng record thực tế cho mỗi phân hệ
        counts_cur = conn.execute(
            "SELECT module_code, COUNT(*) as count FROM module_records GROUP BY module_code"
        ).fetchall()
        counts_map = {r["module_code"]: r["count"] for r in counts_cur}

        for m in modules:
            code = m["code"]
            rec_count = counts_map.get(code, 0)
            m["record_count"] = rec_count

            # Tính trạng thái hiển thị động
            if not m.get("is_connected"):
                m["computed_status"] = "needs_config"
                m["status_label"] = "Cần cấu hình"
            elif rec_count > 0:
                m["computed_status"] = "has_data"
                m["status_label"] = f"Có dữ liệu ({rec_count})"
            elif m.get("status") in ("needs_config", "sync_error"):
                m["computed_status"] = m["status"]
                m["status_label"] = "Cần cấu hình" if m["status"] == "needs_config" else "Lỗi đồng bộ"
            else:
                m["computed_status"] = "connected"
                m["status_label"] = "Đã kết nối"

            m["workflows"] = MODULE_WORKFLOWS.get(code, [
                {"id": "new", "label": "Mới tạo", "color": "blue"},
                {"id": "in_progress", "label": "Đang xử lý", "color": "purple"},
                {"id": "done", "label": "Hoàn tất", "color": "emerald"},
                {"id": "cancelled", "label": "Đã hủy", "color": "rose"},
            ])

        return modules


def get_module(code_or_id: str, db_path: Path | str | None = None) -> Optional[Dict[str, Any]]:
    """Lấy chi tiết một phân hệ kèm thống kê trạng thái các hồ sơ."""
    init_db(db_path)
    canonical = resolve_module_code(code_or_id)
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM business_modules WHERE code = ? OR id = ?",
            (canonical, code_or_id),
        ).fetchone()
        if not row:
            return None

        mod = dict(row)
        code = mod["code"]

        # Thống kê theo status
        status_cur = conn.execute(
            "SELECT status, COUNT(*) as count FROM module_records WHERE module_code = ? GROUP BY status",
            (code,),
        ).fetchall()
        status_counts = {r["status"]: r["count"] for r in status_cur}
        total_records = sum(status_counts.values())

        mod["record_count"] = total_records
        mod["status_counts"] = status_counts
        mod["workflows"] = MODULE_WORKFLOWS.get(code, [
            {"id": "new", "label": "Mới tạo", "color": "blue"},
            {"id": "in_progress", "label": "Đang xử lý", "color": "purple"},
            {"id": "done", "label": "Hoàn tất", "color": "emerald"},
            {"id": "cancelled", "label": "Đã hủy", "color": "rose"},
        ])

        if not mod.get("is_connected"):
            mod["computed_status"] = "needs_config"
            mod["status_label"] = "Cần cấu hình"
        elif total_records > 0:
            mod["computed_status"] = "has_data"
            mod["status_label"] = f"Có dữ liệu ({total_records})"
        else:
            mod["computed_status"] = "connected"
            mod["status_label"] = "Đã kết nối"

        return mod


def list_records(
    module_code: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    owner_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db_path: Path | str | None = None,
) -> Dict[str, Any]:
    """Lấy danh sách hồ sơ của một phân hệ."""
    init_db(db_path)
    canonical = resolve_module_code(module_code)
    with get_connection(db_path) as conn:
        where_clauses = ["module_code = ?"]
        params: List[Any] = [canonical]

        if status:
            where_clauses.append("status = ?")
            params.append(status)
        if priority:
            where_clauses.append("priority = ?")
            params.append(priority)
        if owner_id:
            where_clauses.append("owner_id = ?")
            params.append(owner_id)
        if search:
            where_clauses.append("(title LIKE ? OR description LIKE ? OR payload_json LIKE ?)")
            s_param = f"%{search.strip()}%"
            params.extend([s_param, s_param, s_param])

        where_str = " AND ".join(where_clauses)
        count_cur = conn.execute(f"SELECT COUNT(*) as total FROM module_records WHERE {where_str}", params)
        total = count_cur.fetchone()["total"]

        query = f"SELECT * FROM module_records WHERE {where_str} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        exec_params = list(params) + [max(1, min(limit, 200)), max(0, offset)]

        rows = conn.execute(query, exec_params).fetchall()
        records: List[Dict[str, Any]] = []
        for r in rows:
            item = dict(r)
            try:
                item["payload"] = json.loads(item.get("payload_json") or "{}")
            except Exception:
                item["payload"] = {}
            records.append(item)

        return {
            "ok": True,
            "module_code": canonical,
            "total": total,
            "records": records,
        }


def get_record(record_id: str, db_path: Path | str | None = None) -> Optional[Dict[str, Any]]:
    """Lấy chi tiết một hồ sơ kèm toàn bộ timeline hoạt động, bình luận và file đính kèm."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM module_records WHERE id = ?", (record_id,)).fetchone()
        if not row:
            return None

        rec = dict(row)
        try:
            rec["payload"] = json.loads(rec.get("payload_json") or "{}")
        except Exception:
            rec["payload"] = {}

        # Lấy lịch sử hoạt động (Activity log)
        act_rows = conn.execute(
            "SELECT * FROM module_activities WHERE record_id = ? ORDER BY created_at DESC",
            (record_id,),
        ).fetchall()
        activities = []
        for a in act_rows:
            ad = dict(a)
            try:
                ad["before"] = json.loads(ad.get("before_json") or "{}")
            except Exception:
                ad["before"] = {}
            try:
                ad["after"] = json.loads(ad.get("after_json") or "{}")
            except Exception:
                ad["after"] = {}
            activities.append(ad)
        rec["activities"] = activities

        # Lấy bình luận (Comments)
        cmt_rows = conn.execute(
            "SELECT * FROM module_comments WHERE record_id = ? ORDER BY created_at ASC",
            (record_id,),
        ).fetchall()
        rec["comments"] = [dict(c) for c in cmt_rows]

        # Lấy file đính kèm (Attachments)
        att_rows = conn.execute(
            "SELECT * FROM module_attachments WHERE record_id = ? ORDER BY created_at DESC",
            (record_id,),
        ).fetchall()
        rec["attachments"] = [dict(att) for att in att_rows]

        return rec


def create_record(
    module_code: str,
    title: str,
    description: str = "",
    status: str = "new",
    priority: str = "normal",
    owner_id: str = "",
    source: str = "manual",
    payload: Optional[Dict[str, Any]] = None,
    due_at: Optional[str] = None,
    actor_id: str = "staff",
    db_path: Path | str | None = None,
) -> Dict[str, Any]:
    """Tạo hồ sơ mới trong phân hệ và tự động ghi activity log."""
    init_db(db_path)
    canonical = resolve_module_code(module_code)
    now = time.time()
    rec_id = f"rec_{uuid.uuid4().hex[:12]}"
    payload_dict = payload if isinstance(payload, dict) else {}
    payload_str = json.dumps(payload_dict, ensure_ascii=False)

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO module_records (
                id, module_code, title, description, status, priority, owner_id, source, payload_json, due_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rec_id,
                canonical,
                title.strip(),
                description.strip(),
                status.strip(),
                priority.strip(),
                owner_id.strip(),
                source.strip(),
                payload_str,
                due_at,
                now,
                now,
            ),
        )

        # Cập nhật updated_at của module
        conn.execute("UPDATE business_modules SET updated_at = ? WHERE code = ?", (now, canonical))

        # Ghi Activity Log
        act_id = f"act_{uuid.uuid4().hex[:12]}"
        after_snapshot = {
            "id": rec_id,
            "module_code": canonical,
            "title": title,
            "status": status,
            "priority": priority,
            "owner_id": owner_id,
            "payload": payload_dict,
        }
        conn.execute(
            """
            INSERT INTO module_activities (id, record_id, action, actor_id, before_json, after_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (act_id, rec_id, "created", actor_id, "{}", json.dumps(after_snapshot, ensure_ascii=False), now),
        )
        conn.commit()

    created = get_record(rec_id, db_path=db_path)
    return created or {}


def update_record(
    record_id: str,
    updates: Dict[str, Any],
    actor_id: str = "staff",
    db_path: Path | str | None = None,
) -> Optional[Dict[str, Any]]:
    """Cập nhật hồ sơ và ghi log vết thay đổi (diff) vào timeline."""
    existing = get_record(record_id, db_path=db_path)
    if not existing:
        return None

    now = time.time()
    set_clauses: List[str] = []
    params: List[Any] = []
    before_diff: Dict[str, Any] = {}
    after_diff: Dict[str, Any] = {}
    action_type = "updated"

    # Xử lý các trường cơ bản
    simple_fields = ["title", "description", "priority", "owner_id", "source", "due_at"]
    for f in simple_fields:
        if f in updates:
            new_val = updates[f]
            old_val = existing.get(f)
            if new_val != old_val:
                set_clauses.append(f"{f} = ?")
                params.append(new_val)
                before_diff[f] = old_val
                after_diff[f] = new_val

    # Xử lý chuyển đổi trạng thái (Status workflow transition)
    if "status" in updates:
        new_status = updates["status"]
        old_status = existing.get("status")
        if new_status != old_status:
            set_clauses.append("status = ?")
            params.append(new_status)
            before_diff["status"] = old_status
            after_diff["status"] = new_status
            action_type = "status_changed"

    # Xử lý payload bổ sung
    if "payload" in updates or "payload_json" in updates:
        new_payload = updates.get("payload")
        if new_payload is None and "payload_json" in updates:
            try:
                new_payload = json.loads(updates["payload_json"])
            except Exception:
                new_payload = {}
        if isinstance(new_payload, dict):
            old_payload = existing.get("payload") or {}
            # Merge payload
            merged_payload = {**old_payload, **new_payload}
            payload_str = json.dumps(merged_payload, ensure_ascii=False)
            set_clauses.append("payload_json = ?")
            params.append(payload_str)
            before_diff["payload"] = old_payload
            after_diff["payload"] = merged_payload

    if not set_clauses:
        return existing

    set_clauses.append("updated_at = ?")
    params.append(now)
    params.append(record_id)

    with get_connection(db_path) as conn:
        conn.execute(
            f"UPDATE module_records SET {', '.join(set_clauses)} WHERE id = ?",
            tuple(params),
        )

        # Ghi Activity Log
        act_id = f"act_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT INTO module_activities (id, record_id, action, actor_id, before_json, after_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                act_id,
                record_id,
                action_type,
                actor_id,
                json.dumps(before_diff, ensure_ascii=False),
                json.dumps(after_diff, ensure_ascii=False),
                now,
            ),
        )
        conn.commit()

    return get_record(record_id, db_path=db_path)


def delete_record(
    record_id: str,
    actor_id: str = "staff",
    db_path: Path | str | None = None,
) -> bool:
    """Xóa một hồ sơ và các bảng liên quan (ON DELETE CASCADE)."""
    existing = get_record(record_id, db_path=db_path)
    if not existing:
        return False

    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM module_records WHERE id = ?", (record_id,))
        conn.commit()
    return True


def add_comment(
    record_id: str,
    content: str,
    actor_id: str = "staff",
    db_path: Path | str | None = None,
) -> Optional[Dict[str, Any]]:
    """Thêm bình luận trao đổi nội bộ trên hồ sơ."""
    existing = get_record(record_id, db_path=db_path)
    if not existing or not content.strip():
        return None

    now = time.time()
    cmt_id = f"cmt_{uuid.uuid4().hex[:12]}"
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO module_comments (id, record_id, actor_id, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (cmt_id, record_id, actor_id, content.strip(), now),
        )

        # Ghi activity log
        act_id = f"act_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT INTO module_activities (id, record_id, action, actor_id, before_json, after_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                act_id,
                record_id,
                "comment_added",
                actor_id,
                "{}",
                json.dumps({"comment_id": cmt_id, "content": content.strip()}, ensure_ascii=False),
                now,
            ),
        )
        conn.commit()

    return {
        "id": cmt_id,
        "record_id": record_id,
        "actor_id": actor_id,
        "content": content.strip(),
        "created_at": now,
    }


def add_attachment(
    record_id: str,
    file_name: str,
    file_url: str,
    file_type: str = "",
    actor_id: str = "staff",
    db_path: Path | str | None = None,
) -> Optional[Dict[str, Any]]:
    """Đính kèm tệp hoặc liên kết tài liệu vào hồ sơ."""
    existing = get_record(record_id, db_path=db_path)
    if not existing or not file_name.strip() or not file_url.strip():
        return None

    now = time.time()
    att_id = f"att_{uuid.uuid4().hex[:12]}"
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO module_attachments (id, record_id, file_name, file_url, file_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (att_id, record_id, file_name.strip(), file_url.strip(), file_type.strip(), now),
        )

        # Ghi activity log
        act_id = f"act_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT INTO module_activities (id, record_id, action, actor_id, before_json, after_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                act_id,
                record_id,
                "attachment_added",
                actor_id,
                "{}",
                json.dumps({"attachment_id": att_id, "file_name": file_name, "file_url": file_url}, ensure_ascii=False),
                now,
            ),
        )
        conn.commit()

    return {
        "id": att_id,
        "record_id": record_id,
        "file_name": file_name.strip(),
        "file_url": file_url.strip(),
        "file_type": file_type.strip(),
        "created_at": now,
    }
