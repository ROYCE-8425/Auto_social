# -*- coding: utf-8 -*-
"""Company Document Vault Controller & API Endpoints for Javis Ops.

Endpoints phục vụ kho tài liệu & SOP doanh nghiệp:
- GET   /ops/documents              Liệt kê, tìm kiếm tài liệu theo bộ lọc
- GET   /ops/documents/stats        Thống kê tổng hợp (chờ duyệt, sắp hết hạn, hợp đồng)
- GET   /ops/documents/templates    Biểu mẫu chuẩn dùng để tạo hợp đồng/báo giá
- POST  /ops/documents/upload       Upload tài liệu thực tế + metadata + liên kết
- GET   /ops/documents/{id}         Chi tiết tài liệu + lịch sử phiên bản + nhật ký
- GET   /ops/documents/{id}/file    Tải về hoặc xem trực tiếp file thực tế
- PATCH /ops/documents/{id}         Cập nhật metadata
- DELETE /ops/documents/{id}        Xóa tài liệu
- POST  /ops/documents/{id}/approve Phê duyệt hoặc từ chối
- POST  /ops/documents/{id}/sign    Ký duyệt tài liệu / hợp đồng
- POST  /ops/documents/{id}/versions Upload phiên bản mới cho tài liệu
"""
from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

import config
import ops_documents_store
import ops_rbac

router = APIRouter(tags=["Company Documents Vault"])


def _get_actor(request: Request) -> str:
    """Lấy danh tính người thao tác từ phiên Ops hoặc Admin."""
    user = ops_rbac.get_current_ops_user(request)
    if user:
        return user.get("name") or user.get("username") or user.get("id") or "staff"
    return "staff"


@router.get("/api/documents")
@router.get("/ops/documents")
async def api_list_documents(
    request: Request,
    category: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    approval_status: Optional[str] = Query(None),
    is_template: Optional[bool] = Query(None),
    expiring_soon: bool = Query(False),
    search: Optional[str] = Query(None),
    linked_entity_type: Optional[str] = Query(None),
    linked_entity_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Tìm kiếm và liệt kê tài liệu trong kho."""
    res = ops_documents_store.list_documents(
        category=category,
        department=department,
        approval_status=approval_status,
        is_template=is_template,
        expiring_soon=expiring_soon,
        search=search,
        linked_entity_type=linked_entity_type,
        linked_entity_id=linked_entity_id,
        limit=limit,
        offset=offset,
    )
    return res


@router.get("/api/documents/stats")
@router.get("/ops/documents/stats")
async def api_get_document_stats(request: Request):
    """Lấy chỉ số thống kê kho tài liệu."""
    stats = ops_documents_store.get_stats()
    return {"ok": True, "stats": stats}


@router.get("/api/documents/templates")
@router.get("/ops/documents/templates")
async def api_get_document_templates(request: Request):
    """Lấy danh sách các biểu mẫu chuẩn của công ty."""
    res = ops_documents_store.list_documents(is_template=True, limit=50)
    return {"ok": True, "templates": res.get("documents", [])}


@router.post("/api/documents/upload")
@router.post("/ops/documents/upload")
async def api_upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form(...),
    department: str = Form("van_hanh"),
    owner_id: str = Form("admin"),
    version: str = Form("v1.0"),
    approval_status: str = Form("approved"),
    expires_at: Optional[str] = Form(None),
    permission_level: str = Form("public_internal"),
    linked_entity_type: str = Form("none"),
    linked_entity_id: Optional[str] = Form(None),
    linked_entity_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    is_template: bool = Form(False),
    tags: Optional[str] = Form("[]"),
):
    """Tải lên file tài liệu thực tế và lưu trữ metadata vào CSDL."""
    actor = _get_actor(request)
    orig_name = file.filename or "tai_lieu"
    ext = Path(orig_name).suffix.lower()

    # Tạo thư mục theo năm và category: e.g. storage/documents/2026/contracts/
    year = time.strftime("%Y")
    clean_cat = "".join(c for c in category.lower() if c.isalnum() or c in ("_", "-")) or "general"
    storage_sub_dir = Path(year) / clean_cat
    abs_storage_dir = ops_documents_store.get_base_storage_dir() / storage_sub_dir
    abs_storage_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex[:10]}_{orig_name.replace(' ', '_')}"
    abs_file_path = abs_storage_dir / safe_name
    rel_file_path = str(storage_sub_dir / safe_name).replace("\\", "/")

    # Lưu file vật lý
    try:
        with open(abs_file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"Không thể lưu file: {str(e)}"}, status_code=500)

    file_size = abs_file_path.stat().st_size

    # Phân tích tags
    parsed_tags = []
    if tags:
        try:
            parsed_tags = json.loads(tags)
        except Exception:
            parsed_tags = [t.strip() for t in tags.split(",") if t.strip()]

    # Phân tích hạn dùng
    parsed_expires_at = None
    if expires_at and expires_at.strip():
        try:
            # Hỗ trợ ISO string hoặc timestamp
            if expires_at.replace(".", "").isdigit():
                parsed_expires_at = float(expires_at)
            else:
                import datetime
                dt = datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                parsed_expires_at = dt.timestamp()
        except Exception:
            pass

    doc = ops_documents_store.create_document(
        title=title.strip(),
        file_name=orig_name,
        file_path=rel_file_path,
        file_size=file_size,
        category=clean_cat,
        department=department,
        owner_id=owner_id or actor,
        version=version or "v1.0",
        approval_status=approval_status or "approved",
        expires_at=parsed_expires_at,
        permission_level=permission_level,
        linked_entity_type=linked_entity_type or "none",
        linked_entity_id=linked_entity_id,
        linked_entity_name=linked_entity_name,
        description=description,
        is_template=bool(is_template),
        tags=parsed_tags,
        actor_id=actor,
    )

    return {"ok": True, "document": doc}


@router.get("/api/documents/{doc_id}")
@router.get("/ops/documents/{doc_id}")
async def api_get_document_detail(doc_id: str, request: Request):
    """Lấy chi tiết một tài liệu kèm danh sách phiên bản và nhật ký hoạt động."""
    doc = ops_documents_store.get_document(doc_id)
    if not doc:
        return JSONResponse({"ok": False, "error": f"Tài liệu '{doc_id}' không tồn tại"}, status_code=404)
    return {"ok": True, "document": doc}


@router.get("/api/documents/{doc_id}/file")
@router.get("/ops/documents/{doc_id}/file")
async def api_download_document_file(doc_id: str, download: bool = Query(False)):
    """Tải về hoặc xem trực tiếp file tài liệu thật từ ổ đĩa."""
    doc = ops_documents_store.get_document(doc_id)
    if not doc:
        return JSONResponse({"ok": False, "error": "Không tìm thấy hồ sơ tài liệu"}, status_code=404)

    rel_path = doc.get("file_path", "").replace("\\", "/").strip("/")
    abs_path = ops_documents_store.get_base_storage_dir() / rel_path

    if not abs_path.is_file():
        return JSONResponse({"ok": False, "error": f"File vật lý không tồn tại trên máy chủ: {rel_path}"}, status_code=404)

    file_name = doc.get("file_name") or abs_path.name
    media_type = doc.get("file_type") or "application/octet-stream"

    # Header inline cho PDF để trình duyệt mở xem trước
    headers = {}
    if not download and file_name.lower().endswith(".pdf"):
        headers["Content-Disposition"] = f'inline; filename="{file_name}"'
    else:
        headers["Content-Disposition"] = f'attachment; filename="{file_name}"'

    return FileResponse(str(abs_path), media_type=media_type, headers=headers)


@router.patch("/api/documents/{doc_id}")
@router.patch("/ops/documents/{doc_id}")
@router.put("/api/documents/{doc_id}")
@router.put("/ops/documents/{doc_id}")
async def api_update_document(doc_id: str, request: Request):
    """Cập nhật thông tin metadata của tài liệu."""
    actor = _get_actor(request)
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Payload JSON không hợp lệ"}, status_code=400)

    doc = ops_documents_store.update_document(doc_id, data, actor_id=actor)
    if not doc:
        return JSONResponse({"ok": False, "error": "Tài liệu không tồn tại"}, status_code=404)
    return {"ok": True, "document": doc}


@router.delete("/api/documents/{doc_id}")
@router.delete("/ops/documents/{doc_id}")
async def api_delete_document(doc_id: str, request: Request):
    """Xóa tài liệu khỏi kho."""
    actor = _get_actor(request)
    ops_documents_store.delete_document(doc_id, actor_id=actor)
    return {"ok": True, "deleted": True}


@router.post("/api/documents/{doc_id}/approve")
@router.post("/ops/documents/{doc_id}/approve")
async def api_approve_document(doc_id: str, request: Request):
    """Phê duyệt hoặc từ chối tài liệu."""
    actor = _get_actor(request)
    try:
        data = await request.json()
    except Exception:
        data = {}

    approved = bool(data.get("approved", True))
    note = str(data.get("note") or "")

    doc = ops_documents_store.approve_document(doc_id, approved=approved, note=note, actor_id=actor)
    if not doc:
        return JSONResponse({"ok": False, "error": "Tài liệu không tồn tại"}, status_code=404)
    return {"ok": True, "document": doc}


@router.post("/api/documents/{doc_id}/sign")
@router.post("/ops/documents/{doc_id}/sign")
async def api_sign_document(doc_id: str, request: Request):
    """Đánh dấu tài liệu / hợp đồng đã hoàn tất ký kết."""
    actor = _get_actor(request)
    try:
        data = await request.json()
    except Exception:
        data = {}

    note = str(data.get("note") or "Đã ký số / ký tươi hoàn tất")
    doc = ops_documents_store.sign_document(doc_id, note=note, actor_id=actor)
    if not doc:
        return JSONResponse({"ok": False, "error": "Tài liệu không tồn tại"}, status_code=404)
    return {"ok": True, "document": doc}


@router.post("/api/documents/{doc_id}/versions")
@router.post("/ops/documents/{doc_id}/versions")
async def api_add_document_version(
    doc_id: str,
    request: Request,
    file: UploadFile = File(...),
    version: str = Form(...),
    change_note: str = Form("Cập nhật phiên bản mới"),
):
    """Tải lên phiên bản mới cho một tài liệu."""
    actor = _get_actor(request)
    doc = ops_documents_store.get_document(doc_id)
    if not doc:
        return JSONResponse({"ok": False, "error": "Tài liệu không tồn tại"}, status_code=404)

    orig_name = file.filename or "tai_lieu"
    year = time.strftime("%Y")
    clean_cat = doc.get("category", "general")
    storage_sub_dir = Path(year) / clean_cat
    abs_storage_dir = ops_documents_store.get_base_storage_dir() / storage_sub_dir
    abs_storage_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex[:10]}_{orig_name.replace(' ', '_')}"
    abs_file_path = abs_storage_dir / safe_name
    rel_file_path = str(storage_sub_dir / safe_name).replace("\\", "/")

    try:
        with open(abs_file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"Không thể lưu file: {str(e)}"}, status_code=500)

    file_size = abs_file_path.stat().st_size

    updated_doc = ops_documents_store.add_version(
        doc_id=doc_id,
        new_version=version,
        file_name=orig_name,
        file_path=rel_file_path,
        file_size=file_size,
        change_note=change_note,
        actor_id=actor,
    )

    return {"ok": True, "document": updated_doc}


def register(app, deps=None):
    """Đăng ký router vào FastAPI app theo đúng chuẩn Javis."""
    app.include_router(router)
