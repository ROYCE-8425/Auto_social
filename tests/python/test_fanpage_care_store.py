"""Test SQLite Store & Markdown CRM (PR 3).

Kiểm tra:
- Khởi tạo SQLite WAL, bảng events, customers, identities, drafts, actions, cursors, rate_buckets, messaging_windows
- Dedup event qua UNIQUE(kind, object_id)
- Gộp danh tính mạnh qua SĐT: 2 comment ở 2 page khác nhau, cùng SĐT -> gộp về 1 crm_id
- Ghi và bảo toàn timeline trong crm/customers/<crm_id>.md
- Sinh bảng crm/index.md
- Xóa khách PDPD (xóa identities, customers, ẩn SĐT trong events)
- Không rò rỉ token / secret trong markdown
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "server"))

import fanpage_care_store as store
import fanpage_care_crm as crm

_fails = []


def check(name: str, cond: bool, extra: str = ""):
    if cond:
        print(f"ok  {name}")
    else:
        print(f"FAIL {name} {extra}".rstrip())
        _fails.append(name)


def main():
    tmp_dir = Path(tempfile.mkdtemp(prefix="care-test-"))
    db_path = tmp_dir / "test_care.sqlite3"
    vault_root = tmp_dir / "vault"
    vault_root.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Khởi tạo DB
        store.init_db(db_path)
        check("db: tạo file sqlite3 thành công", db_path.is_file())

        # 2. Dedup event
        ev1 = {
            "kind": "comment",
            "page_id": "P1",
            "object_id": "P1_10_c1",
            "from_id": "U1",
            "from_name": "Nguyen Van A",
            "body": "hoc phi bao nhieu 0935195118",
            "class": "lead",
        }
        id1, is_new1 = store.record_event(ev1, db_path)
        check("event: ghi mới thành công", is_new1 is True and id1 > 0)

        id2, is_new2 = store.record_event(ev1, db_path)
        check("event: dedup cùng (kind, object_id) trả is_new=False", is_new2 is False and id2 == id1)

        # 3. Gộp danh tính qua SĐT
        # Khách comment trên Page P1
        cust1, is_new_cust1 = store.get_or_create_customer(
            name="Nguyen Van A",
            phones=["0935195118"],
            page_id="P1",
            from_id="U1",
            course_interest="tin-hoc",
            campus="Quan 7",
            db_path=db_path,
        )
        check("crm: tạo khách mới cust1", is_new_cust1 is True and cust1["crm_id"].startswith("c_"))

        # Cùng khách đó comment trên Page P2 với cùng SĐT nhưng tên chưa rõ
        cust2, is_new_cust2 = store.get_or_create_customer(
            name="Ẩn danh",
            phones=["0935195118"],
            page_id="P2",
            from_id="U2_different",
            course_interest="ke-toan",
            db_path=db_path,
        )
        check("crm: cùng SĐT gộp về cùng crm_id", is_new_cust2 is False and cust2["crm_id"] == cust1["crm_id"])
        check("crm: page_ids chứa cả P1 và P2", "P1" in cust2["page_ids"] and "P2" in cust2["page_ids"])

        # 4. Search khách hàng LIKE
        res_phone = store.search_customers("0935195118", db_path=db_path)
        check("search: tìm theo SĐT", len(res_phone) == 1 and res_phone[0]["crm_id"] == cust1["crm_id"])

        res_name = store.search_customers("Nguyen Van", db_path=db_path)
        check("search: tìm theo tên", len(res_name) == 1 and res_name[0]["crm_id"] == cust1["crm_id"])

        # 5. Ghi Markdown CRM
        md_file = crm.write_customer_markdown(
            vault_root,
            cust2,
            timeline_entry="comment P1_10_c1: 'hoc phi bao nhieu 0935195118' class=lead",
            identities=["fb_comment_from:P1:U1", "fb_comment_from:P2:U2_different"],
        )
        check("markdown: tạo file khách hàng", md_file.is_file())

        content1 = md_file.read_text(encoding="utf-8")
        check("markdown: có crm_id trong frontmatter", f"crm_id: {cust1['crm_id']}" in content1)
        check("markdown: có timeline entry 1", "P1_10_c1" in content1)
        check("markdown: KHÔNG lộ access_token", "access_token" not in content1.lower() and "eaa" not in content1.lower())

        # Ghi thêm timeline entry thứ 2 -> bảo toàn timeline cũ
        crm.write_customer_markdown(
            vault_root,
            cust2,
            timeline_entry="reply R1: 'Da em nhan thong tin roi ạ'",
        )
        content2 = md_file.read_text(encoding="utf-8")
        check("markdown: bảo toàn entry 1 khi ghi entry 2", "P1_10_c1" in content2 and "reply R1" in content2)

        # 6. Rebuild index.md
        crm.rebuild_crm_index(vault_root, db_path=db_path)
        index_file = vault_root / "crm" / "index.md"
        check("index.md: tồn tại", index_file.is_file())
        idx_content = index_file.read_text(encoding="utf-8")
        check("index.md: có dòng bảng chứa khách", cust1["crm_id"] in idx_content and "0935 195 118" in idx_content)

        # 7. Xóa khách theo PDPD
        del_ok = store.delete_customer(cust1["crm_id"], db_path=db_path)
        check("delete: xóa khách thành công", del_ok is True)

        cust_after = store.get_customer(cust1["crm_id"], db_path=db_path)
        check("delete: get_customer trả None", cust_after is None)

        with store.get_connection(db_path) as conn:
            ev_row = conn.execute("SELECT body FROM events WHERE id = ?", (id1,)).fetchone()
            check("delete: SĐT trong events đã được ẩn [redacted]", "[redacted]" in ev_row["body"])

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    if _fails:
        print(f"\nFAIL - {len(_fails)} test: {_fails}")
        sys.exit(1)
    print("\nOK - test_fanpage_care_store: tất cả pass")


if __name__ == "__main__":
    main()
