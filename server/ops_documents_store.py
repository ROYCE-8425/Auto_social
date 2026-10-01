# -*- coding: utf-8 -*-
"""Company Document Vault Database & File Storage for Javis Ops.

Quản lý lưu trữ tài liệu thực tế của doanh nghiệp:
- Physical File Storage: STATE_DIR / "storage" / "documents" / {year} / {category} / {safe_filename}
- SQLite Metadata Database: STATE_DIR / "ops_documents.sqlite3"
- Tables:
  * ops_documents: Lưu metadata, phòng ban, version, hạn dùng, trạng thái duyệt, liên kết entity.
  * ops_document_versions: Lưu lịch sử từng phiên bản file.
  * ops_document_activities: Nhật ký thao tác (upload, duyệt, ký, tải về).
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import config

DEFAULT_DB_PATH = config.STATE_DIR / "ops_documents.sqlite3"

def get_base_storage_dir() -> Path:
    p = Path(config.STATE_DIR) / "storage" / "documents"
    p.mkdir(parents=True, exist_ok=True)
    return p

# Backward compatibility module-level attribute
DOCUMENTS_STORAGE_DIR = get_base_storage_dir()


def get_connection(db_path: Path | str | None = None) -> Generator[sqlite3.Connection, None, None]:
    p = Path(db_path or DEFAULT_DB_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: Path | str | None = None, seed_demo: bool = True) -> None:
    """Khởi tạo toàn bộ cấu trúc CSDL Kho tài liệu doanh nghiệp."""
    for conn in get_connection(db_path):
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS ops_documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            file_type TEXT DEFAULT 'application/pdf',
            category TEXT NOT NULL,
            tags_json TEXT DEFAULT '[]',
            department TEXT NOT NULL DEFAULT 'van_hanh',
            owner_id TEXT DEFAULT 'admin',
            version TEXT DEFAULT 'v1.0',
            approval_status TEXT DEFAULT 'approved',
            approved_by TEXT,
            approved_at REAL,
            signed_at REAL,
            expires_at REAL,
            permission_level TEXT DEFAULT 'public_internal',
            linked_entity_type TEXT DEFAULT 'none',
            linked_entity_id TEXT,
            linked_entity_name TEXT,
            description TEXT,
            is_template INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ops_document_versions (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            version TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            change_note TEXT,
            uploaded_by TEXT,
            created_at REAL NOT NULL,
            FOREIGN KEY (document_id) REFERENCES ops_documents(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ops_document_activities (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            action TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            note TEXT,
            created_at REAL NOT NULL,
            FOREIGN KEY (document_id) REFERENCES ops_documents(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_docs_category ON ops_documents(category);
        CREATE INDEX IF NOT EXISTS idx_docs_department ON ops_documents(department);
        CREATE INDEX IF NOT EXISTS idx_docs_approval ON ops_documents(approval_status);
        CREATE INDEX IF NOT EXISTS idx_docs_expires ON ops_documents(expires_at);
        CREATE INDEX IF NOT EXISTS idx_docs_linked ON ops_documents(linked_entity_type, linked_entity_id);
        """)

        # Kiểm tra nếu chưa có tài liệu nào, seed bộ tài liệu và biểu mẫu mẫu của công ty
        cur = conn.execute("SELECT COUNT(*) as cnt FROM ops_documents")
        row = cur.fetchone()
        if seed_demo and row and row["cnt"] == 0:
            _seed_initial_documents(conn)


def _seed_initial_documents(conn: sqlite3.Connection) -> None:
    """Tạo bộ tài liệu, hợp đồng, SOP và biểu mẫu thực tế kèm file thật trên ổ đĩa."""
    now = time.time()
    day_secs = 86400

    sample_docs = [
        {
            "id": "doc_hd_01",
            "title": "Hợp đồng Dịch vụ Đào tạo Tin học Doanh nghiệp - Công ty CP Sao Việt",
            "file_name": "HD-DT-2026-001.pdf",
            "rel_path": "2026/contracts/HD-DT-2026-001.pdf",
            "category": "contract",
            "department": "kinh_doanh",
            "owner_id": "ql_tuan",
            "version": "v1.0",
            "approval_status": "signed",
            "approved_by": "ql_tuan",
            "approved_at": now - day_secs * 5,
            "signed_at": now - day_secs * 4,
            "expires_at": now + day_secs * 25,  # Sắp hết hạn trong 25 ngày
            "permission_level": "department_only",
            "linked_entity_type": "customer",
            "linked_entity_id": "c_tuan_01",
            "linked_entity_name": "Hoàng Anh Tuấn",
            "description": "Hợp đồng trọn gói đào tạo 30 nhân sự kỹ năng Excel Dashboard & PowerBI thực chiến.",
            "is_template": 0,
            "tags": ["hợp đồng", "khách hàng", "đào tạo", "doanh nghiệp"],
        },
        {
            "id": "doc_sop_01",
            "title": "SOP Chuẩn: Quy trình Phân loại Lead & Kịch bản Cứu khách dừng tương tác 24h",
            "file_name": "SOP-CSKH-LEAD-2026.pdf",
            "rel_path": "2026/sop/SOP-CSKH-LEAD-2026.pdf",
            "category": "sop",
            "department": "van_hanh",
            "owner_id": "nv_thao",
            "version": "v2.1",
            "approval_status": "approved",
            "approved_by": "admin",
            "approved_at": now - day_secs * 15,
            "signed_at": None,
            "expires_at": None,
            "permission_level": "public_internal",
            "linked_entity_type": "none",
            "linked_entity_id": None,
            "linked_entity_name": None,
            "description": "Tài liệu quy chuẩn hướng dẫn tư vấn viên xử lý tin nhắn, duyệt nháp AI và tặng mã cứu lead 24h.",
            "is_template": 0,
            "tags": ["sop", "cskh", "quy trình", "cứu lead"],
        },
        {
            "id": "doc_policy_01",
            "title": "Chính sách Thưởng Doanh số & Hoa hồng Đại lý Bán lẻ Khóa học",
            "file_name": "CHINH-SACH-HOA-HONG-2026.pdf",
            "rel_path": "2026/policy/CHINH-SACH-HOA-HONG-2026.pdf",
            "category": "policy",
            "department": "kinh_doanh",
            "owner_id": "admin",
            "version": "v1.2",
            "approval_status": "approved",
            "approved_by": "admin",
            "approved_at": now - day_secs * 30,
            "signed_at": None,
            "expires_at": None,
            "permission_level": "public_internal",
            "linked_entity_type": "none",
            "linked_entity_id": None,
            "linked_entity_name": None,
            "description": "Khung tỷ lệ hoa hồng cho nhân viên tư vấn và đại lý phân phối khóa học thực chiến.",
            "is_template": 0,
            "tags": ["chính sách", "hoa hồng", "thưởng", "kinh doanh"],
        },
        {
            "id": "doc_tpl_01",
            "title": "Mẫu Biểu Báo giá Tiêu chuẩn Giải pháp Tự động hóa & Khóa học",
            "file_name": "MAU-BAO-GIA-TIÊU-CHUAN-2026.xlsx",
            "rel_path": "2026/templates/MAU-BAO-GIA-TIÊU-CHUAN-2026.xlsx",
            "category": "template",
            "department": "kinh_doanh",
            "owner_id": "ql_tuan",
            "version": "v1.0",
            "approval_status": "approved",
            "approved_by": "ql_tuan",
            "approved_at": now - day_secs * 10,
            "signed_at": None,
            "expires_at": None,
            "permission_level": "public_internal",
            "linked_entity_type": "none",
            "linked_entity_id": None,
            "linked_entity_name": None,
            "description": "File mẫu Excel tính tự động đơn giá, chiết khấu và thuế VAT cho báo giá gửi khách hàng.",
            "is_template": 1,
            "tags": ["mẫu biểu", "báo giá", "excel", "template"],
        },
        {
            "id": "doc_tpl_02",
            "title": "Mẫu Biên bản Bàn giao & Nghiệm thu Dịch vụ Đào tạo Kỹ thuật",
            "file_name": "MAU-BIEN-BAN-BAN-GIAO.docx",
            "rel_path": "2026/templates/MAU-BIEN-BAN-BAN-GIAO.docx",
            "category": "template",
            "department": "van_hanh",
            "owner_id": "nv_an",
            "version": "v1.1",
            "approval_status": "approved",
            "approved_by": "ql_tuan",
            "approved_at": now - day_secs * 8,
            "signed_at": None,
            "expires_at": None,
            "permission_level": "public_internal",
            "linked_entity_type": "none",
            "linked_entity_id": None,
            "linked_entity_name": None,
            "description": "Biểu mẫu Word chuẩn dùng để ký nghiệm thu khi hoàn thành bàn giao tài liệu và cấp chứng nhận.",
            "is_template": 1,
            "tags": ["mẫu biểu", "nghiệm thu", "bàn giao"],
        },
        {
            "id": "doc_hr_01",
            "title": "Hợp đồng Thử việc & Tiếp nhận Nhân sự Chuyên viên Tư vấn",
            "file_name": "HDTV-NV-TRAN-MAI-2026.pdf",
            "rel_path": "2026/hr/HDTV-NV-TRAN-MAI-2026.pdf",
            "category": "hr",
            "department": "nhan_su",
            "owner_id": "admin",
            "version": "v1.0",
            "approval_status": "pending_approval",  # Chờ duyệt
            "approved_by": None,
            "approved_at": None,
            "signed_at": None,
            "expires_at": now + day_secs * 60,
            "permission_level": "manager_only",
            "linked_entity_type": "staff",
            "linked_entity_id": "nv_thao",
            "linked_entity_name": "Lê Thảo",
            "description": "Hồ sơ hợp đồng thử việc 2 tháng phòng Chăm sóc khách hàng và bán hàng online.",
            "is_template": 0,
            "tags": ["nhân sự", "thử việc", "hợp đồng"],
        },
        {
            "id": "doc_legal_01",
            "title": "Thỏa thuận Bảo mật Thông tin Doanh nghiệp & Quyền Sở hữu Trí tuệ (NDA)",
            "file_name": "THOA-THUAN-NDA-2026.pdf",
            "rel_path": "2026/legal/THOA-THUAN-NDA-2026.pdf",
            "category": "legal",
            "department": "phap_ly",
            "owner_id": "admin",
            "version": "v2.0",
            "approval_status": "approved",
            "approved_by": "admin",
            "approved_at": now - day_secs * 40,
            "signed_at": None,
            "expires_at": None,
            "permission_level": "public_internal",
            "linked_entity_type": "none",
            "linked_entity_id": None,
            "linked_entity_name": None,
            "description": "Văn bản thỏa thuận bảo vệ dữ liệu khách hàng, mã nguồn phần mềm và bí mật kinh doanh.",
            "is_template": 1,
            "tags": ["pháp lý", "nda", "bảo mật"],
        },
    ]

    for d in sample_docs:
        # 1. Tạo file vật lý mẫu trên ổ đĩa
        full_file_path = get_base_storage_dir() / d["rel_path"]
        full_file_path.parent.mkdir(parents=True, exist_ok=True)
        if not full_file_path.exists():
            content = f"""TÀI LIỆU NỘI BỘ DOANH NGHIỆP - SÈO TRUM OPS
===================================================
Mã hồ sơ: {d['id']}
Tiêu đề: {d['title']}
Loại: {d['category'].upper()}
Phòng ban: {d['department']}
Người phụ trách: {d['owner_id']}
Phiên bản: {d['version']}
Trạng thái: {d['approval_status']}
Mô tả: {d['description']}
Thời gian khởi tạo: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))}
===================================================
File được lưu trữ thực tế tại hệ thống Company Document Vault.
"""
            full_file_path.write_text(content, encoding="utf-8")

        file_size = full_file_path.stat().st_size

        # 2. Insert metadata vào DB
        conn.execute("""
        INSERT OR REPLACE INTO ops_documents (
            id, title, file_name, file_path, file_size, file_type,
            category, tags_json, department, owner_id, version,
            approval_status, approved_by, approved_at, signed_at, expires_at,
            permission_level, linked_entity_type, linked_entity_id, linked_entity_name,
            description, is_template, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            d["id"],
            d["title"],
            d["file_name"],
            d["rel_path"],
            file_size,
            "application/pdf" if d["file_name"].endswith(".pdf") else "application/octet-stream",
            d["category"],
            json.dumps(d["tags"], ensure_ascii=False),
            d["department"],
            d["owner_id"],
            d["version"],
            d["approval_status"],
            d["approved_by"],
            d["approved_at"],
            d["signed_at"],
            d["expires_at"],
            d["permission_level"],
            d["linked_entity_type"],
            d["linked_entity_id"],
            d["linked_entity_name"],
            d["description"],
            d["is_template"],
            now - day_secs * 2,
            now,
        ))

        # 3. Tạo version ban đầu
        v_id = f"ver_{uuid.uuid4().hex[:8]}"
        conn.execute("""
        INSERT OR REPLACE INTO ops_document_versions (
            id, document_id, version, file_name, file_path, file_size, change_note, uploaded_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            v_id,
            d["id"],
            d["version"],
            d["file_name"],
            d["rel_path"],
            file_size,
            "Khởi tạo tài liệu bản chuẩn",
            d["owner_id"],
            now - day_secs * 2,
        ))

        # 4. Tạo nhật ký activity
        act_id = f"act_{uuid.uuid4().hex[:8]}"
        conn.execute("""
        INSERT OR REPLACE INTO ops_document_activities (
            id, document_id, action, actor_id, note, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            act_id,
            d["id"],
            "uploaded",
            d["owner_id"],
            "Tải lên phiên bản đầu tiên",
            now - day_secs * 2,
        ))

    conn.commit()


def seed_demo_documents(db_path: Path | str | None = None) -> None:
    """Tạo bộ tài liệu mẫu và file thực tế nếu chưa có."""
    init_db(db_path, seed_demo=True)


# ============================================================
# CRUD & Query Operations
# ============================================================

def list_documents(
    category: Optional[str] = None,
    department: Optional[str] = None,
    approval_status: Optional[str] = None,
    is_template: Optional[bool] = None,
    expiring_soon: bool = False,
    search: Optional[str] = None,
    linked_entity_type: Optional[str] = None,
    linked_entity_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db_path: Path | str | None = None,
) -> Dict[str, Any]:
    """Tìm kiếm và liệt kê danh sách tài liệu từ CSDL."""
    init_db(db_path)
    for conn in get_connection(db_path):
        query = "SELECT * FROM ops_documents WHERE 1=1"
        params: List[Any] = []

        if category and category != "all":
            query += " AND category = ?"
            params.append(category)

        if department and department != "all":
            query += " AND department = ?"
            params.append(department)

        if approval_status and approval_status != "all":
            query += " AND approval_status = ?"
            params.append(approval_status)

        if is_template is not None:
            query += " AND is_template = ?"
            params.append(1 if is_template else 0)

        if expiring_soon:
            # Hết hạn trong vòng 30 ngày tới
            now = time.time()
            query += " AND expires_at IS NOT NULL AND expires_at > ? AND expires_at <= ?"
            params.extend([now - 86400, now + 30 * 86400])

        if linked_entity_type and linked_entity_type != "all":
            query += " AND linked_entity_type = ?"
            params.append(linked_entity_type)

        if linked_entity_id:
            query += " AND linked_entity_id = ?"
            params.append(linked_entity_id)

        if search:
            s = f"%{search.strip()}%"
            query += " AND (title LIKE ? OR file_name LIKE ? OR description LIKE ? OR tags_json LIKE ? OR linked_entity_name LIKE ?)"
            params.extend([s, s, s, s, s])

        count_query = query.replace("SELECT *", "SELECT COUNT(*) as total", 1)
        cur = conn.execute(count_query, params)
        total = cur.fetchone()["total"]

        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = conn.execute(query, params)
        rows = cur.fetchall()

        docs = []
        for r in rows:
            d = dict(r)
            try:
                d["tags"] = json.loads(d.get("tags_json") or "[]")
            except Exception:
                d["tags"] = []
            docs.append(d)

        return {
            "ok": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "documents": docs,
        }


def get_document(doc_id: str, db_path: Path | str | None = None) -> Optional[Dict[str, Any]]:
    """Lấy chi tiết một tài liệu kèm danh sách version và activity log."""
    init_db(db_path)
    for conn in get_connection(db_path):
        cur = conn.execute("SELECT * FROM ops_documents WHERE id = ?", (doc_id,))
        row = cur.fetchone()
        if not row:
            return None

        doc = dict(row)
        try:
            doc["tags"] = json.loads(doc.get("tags_json") or "[]")
        except Exception:
            doc["tags"] = []

        # Lấy versions
        cur_v = conn.execute("SELECT * FROM ops_document_versions WHERE document_id = ? ORDER BY created_at DESC", (doc_id,))
        doc["versions"] = [dict(v) for v in cur_v.fetchall()]

        # Lấy activities
        cur_a = conn.execute("SELECT * FROM ops_document_activities WHERE document_id = ? ORDER BY created_at DESC LIMIT 30", (doc_id,))
        doc["activities"] = [dict(a) for a in cur_a.fetchall()]

        return doc


def get_document_file_path(doc_id: str, db_path: Path | str | None = None) -> Optional[Path]:
    """Lấy đường dẫn tệp tin thực tế trên ổ cứng."""
    doc = get_document(doc_id, db_path)
    if not doc:
        return None
    base = Path(config.STATE_DIR) / "storage" / "documents"
    fp = Path(doc["file_path"])
    if fp.is_absolute():
        return fp
    return base / fp


def create_document(
    title: str,
    file_name: str,
    file_path: str,
    file_size: int,
    category: str,
    department: str = "van_hanh",
    owner_id: str = "admin",
    version: str = "v1.0",
    approval_status: str = "approved",
    expires_at: Optional[float] = None,
    permission_level: str = "public_internal",
    linked_entity_type: str = "none",
    linked_entity_id: Optional[str] = None,
    linked_entity_name: Optional[str] = None,
    description: Optional[str] = None,
    is_template: bool = False,
    tags: Optional[List[str]] = None,
    actor_id: str = "admin",
    db_path: Path | str | None = None,
) -> Dict[str, Any]:
    """Tạo mới một tài liệu trong kho."""
    init_db(db_path)
    doc_id = f"doc_{uuid.uuid4().hex[:10]}"
    now = time.time()
    tags_json = json.dumps(tags or [], ensure_ascii=False)
    file_type = "application/pdf" if file_name.endswith(".pdf") else "application/octet-stream"

    for conn in get_connection(db_path):
        conn.execute("""
        INSERT INTO ops_documents (
            id, title, file_name, file_path, file_size, file_type,
            category, tags_json, department, owner_id, version,
            approval_status, approved_by, approved_at, signed_at, expires_at,
            permission_level, linked_entity_type, linked_entity_id, linked_entity_name,
            description, is_template, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id, title, file_name, file_path, file_size, file_type,
            category, tags_json, department, owner_id, version,
            approval_status,
            actor_id if approval_status == "approved" else None,
            now if approval_status == "approved" else None,
            now if approval_status == "signed" else None,
            expires_at,
            permission_level, linked_entity_type, linked_entity_id, linked_entity_name,
            description, 1 if is_template else 0, now, now
        ))

        # Lưu version 1.0
        v_id = f"ver_{uuid.uuid4().hex[:8]}"
        conn.execute("""
        INSERT INTO ops_document_versions (
            id, document_id, version, file_name, file_path, file_size, change_note, uploaded_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (v_id, doc_id, version, file_name, file_path, file_size, "Tải lên bản đầu tiên", actor_id, now))

        # Ghi log activity
        act_id = f"act_{uuid.uuid4().hex[:8]}"
        conn.execute("""
        INSERT INTO ops_document_activities (
            id, document_id, action, actor_id, note, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """, (act_id, doc_id, "uploaded", actor_id, f"Khởi tạo tài liệu {title}", now))

        conn.commit()

    return get_document(doc_id, db_path) or {}


def update_document(
    doc_id: str,
    data: Dict[str, Any],
    actor_id: str = "admin",
    db_path: Path | str | None = None,
) -> Optional[Dict[str, Any]]:
    """Cập nhật metadata của tài liệu."""
    init_db(db_path)
    allowed_fields = [
        "title", "category", "department", "owner_id", "version",
        "approval_status", "expires_at", "permission_level",
        "linked_entity_type", "linked_entity_id", "linked_entity_name",
        "description", "is_template"
    ]
    updates = []
    params = []
    for k in allowed_fields:
        if k in data:
            updates.append(f"{k} = ?")
            params.append(data[k])

    if "tags" in data and isinstance(data["tags"], list):
        updates.append("tags_json = ?")
        params.append(json.dumps(data["tags"], ensure_ascii=False))

    if not updates:
        return get_document(doc_id, db_path)

    now = time.time()
    updates.append("updated_at = ?")
    params.append(now)
    params.append(doc_id)

    for conn in get_connection(db_path):
        conn.execute(f"UPDATE ops_documents SET {', '.join(updates)} WHERE id = ?", params)

        act_id = f"act_{uuid.uuid4().hex[:8]}"
        conn.execute("""
        INSERT INTO ops_document_activities (id, document_id, action, actor_id, note, created_at)
        VALUES (?, ?, 'updated', ?, 'Cập nhật thông tin hồ sơ tài liệu', ?)
        """, (act_id, doc_id, actor_id, now))
        conn.commit()

    return get_document(doc_id, db_path)


def delete_document(doc_id: str, actor_id: str = "admin", db_path: Path | str | None = None) -> bool:
    """Xóa tài liệu và các phiên bản liên quan."""
    init_db(db_path)
    for conn in get_connection(db_path):
        conn.execute("DELETE FROM ops_documents WHERE id = ?", (doc_id,))
        conn.commit()
    return True


def add_version(
    doc_id: str,
    new_version: str,
    file_name: str,
    file_path: str,
    file_size: int,
    change_note: str,
    actor_id: str = "admin",
    db_path: Path | str | None = None,
) -> Optional[Dict[str, Any]]:
    """Tải lên phiên bản mới cho tài liệu hiện có."""
    init_db(db_path)
    now = time.time()
    v_id = f"ver_{uuid.uuid4().hex[:8]}"

    for conn in get_connection(db_path):
        # 1. Thêm vào bảng versions
        conn.execute("""
        INSERT INTO ops_document_versions (
            id, document_id, version, file_name, file_path, file_size, change_note, uploaded_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (v_id, doc_id, new_version, file_name, file_path, file_size, change_note, actor_id, now))

        # 2. Cập nhật con trỏ version hiện tại của document
        conn.execute("""
        UPDATE ops_documents
        SET version = ?, file_name = ?, file_path = ?, file_size = ?, updated_at = ?
        WHERE id = ?
        """, (new_version, file_name, file_path, file_size, now, doc_id))

        # 3. Ghi activity
        act_id = f"act_{uuid.uuid4().hex[:8]}"
        conn.execute("""
        INSERT INTO ops_document_activities (id, document_id, action, actor_id, note, created_at)
        VALUES (?, ?, 'version_bumped', ?, ?, ?)
        """, (act_id, doc_id, actor_id, f"Nâng cấp lên phiên bản {new_version}: {change_note}", now))

        conn.commit()

    return get_document(doc_id, db_path)


def approve_document(
    doc_id: str,
    approved: bool,
    note: str = "",
    actor_id: str = "admin",
    db_path: Path | str | None = None,
) -> Optional[Dict[str, Any]]:
    """Phê duyệt hoặc từ chối tài liệu."""
    init_db(db_path)
    now = time.time()
    status = "approved" if approved else "rejected"

    for conn in get_connection(db_path):
        conn.execute("""
        UPDATE ops_documents
        SET approval_status = ?, approved_by = ?, approved_at = ?, updated_at = ?
        WHERE id = ?
        """, (status, actor_id, now, now, doc_id))

        act_id = f"act_{uuid.uuid4().hex[:8]}"
        action = "approved" if approved else "rejected"
        conn.execute("""
        INSERT INTO ops_document_activities (id, document_id, action, actor_id, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (act_id, doc_id, action, actor_id, note or ("Đã phê duyệt" if approved else "Bị từ chối"), now))

        conn.commit()

    return get_document(doc_id, db_path)


def sign_document(
    doc_id: str,
    note: str = "Đã ký số / ký tươi",
    actor_id: str = "admin",
    db_path: Path | str | None = None,
) -> Optional[Dict[str, Any]]:
    """Đánh dấu tài liệu / hợp đồng đã được ký duyệt."""
    init_db(db_path)
    now = time.time()

    for conn in get_connection(db_path):
        conn.execute("""
        UPDATE ops_documents
        SET approval_status = 'signed', signed_at = ?, updated_at = ?
        WHERE id = ?
        """, (now, now, doc_id))

        act_id = f"act_{uuid.uuid4().hex[:8]}"
        conn.execute("""
        INSERT INTO ops_document_activities (id, document_id, action, actor_id, note, created_at)
        VALUES (?, ?, 'signed', ?, ?, ?)
        """, (act_id, doc_id, actor_id, note, now))

        conn.commit()

    return get_document(doc_id, db_path)


def get_stats(db_path: Path | str | None = None) -> Dict[str, Any]:
    """Tổng hợp chỉ số phục vụ Executive Command Center và Dashboard."""
    init_db(db_path)
    now = time.time()
    day_secs = 86400

    for conn in get_connection(db_path):
        total_docs = conn.execute("SELECT COUNT(*) as cnt FROM ops_documents").fetchone()["cnt"]
        waiting_approval = conn.execute("SELECT COUNT(*) as cnt FROM ops_documents WHERE approval_status = 'pending_approval'").fetchone()["cnt"]
        
        # Sắp hết hạn trong 30 ngày
        expiring_soon = conn.execute("""
        SELECT COUNT(*) as cnt FROM ops_documents
        WHERE expires_at IS NOT NULL AND expires_at > ? AND expires_at <= ?
        """, (now - day_secs, now + 30 * day_secs)).fetchone()["cnt"]

        # Số hợp đồng
        contracts_count = conn.execute("SELECT COUNT(*) as cnt FROM ops_documents WHERE category = 'contract'").fetchone()["cnt"]
        
        # Số SOP
        sop_count = conn.execute("SELECT COUNT(*) as cnt FROM ops_documents WHERE category = 'sop'").fetchone()["cnt"]

        # Số templates
        templates_count = conn.execute("SELECT COUNT(*) as cnt FROM ops_documents WHERE is_template = 1").fetchone()["cnt"]

        # Thống kê theo category
        cat_cur = conn.execute("SELECT category, COUNT(*) as cnt FROM ops_documents GROUP BY category")
        by_category = {row["category"]: row["cnt"] for row in cat_cur.fetchall()}

        # Thống kê theo phòng ban
        dept_cur = conn.execute("SELECT department, COUNT(*) as cnt FROM ops_documents GROUP BY department")
        by_department = {row["department"]: row["cnt"] for row in dept_cur.fetchall()}

        return {
            "total_documents": total_docs,
            "waiting_approval": waiting_approval,
            "expiring_soon": expiring_soon,
            "contracts_count": contracts_count,
            "sop_count": sop_count,
            "templates_count": templates_count,
            "by_category": by_category,
            "by_department": by_department,
        }
