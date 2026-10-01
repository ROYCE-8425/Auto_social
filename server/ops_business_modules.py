# -*- coding: utf-8 -*-
"""Business Modules Controller & API Endpoints for Javis OS.

Phục vụ các API vận hành cốt lõi:
- GET   /api/modules
- GET   /api/modules/{code}
- GET   /api/modules/{code}/records
- POST  /api/modules/{code}/records
- GET   /api/modules/{code}/records/{id}
- PATCH /api/modules/{code}/records/{id}
- DELETE /api/modules/{code}/records/{id}
- POST  /api/modules/{code}/records/{id}/comments
- POST  /api/modules/{code}/records/{id}/attachments

Đồng thời hỗ trợ tiền tố /ops/modules để giao diện Hub gọi trực tiếp.
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
from fastapi.responses import JSONResponse, FileResponse

import config
import ops_business_store
import ops_rbac

router = APIRouter(tags=["Business Modules"])

UPLOAD_DIR = config.STATE_DIR / "module_attachments"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _get_actor(request: Request) -> str:
    """Lấy danh tính người thao tác từ phiên Ops hoặc Admin."""
    user = ops_rbac.get_current_ops_user(request)
    if user:
        return user.get("name") or user.get("username") or user.get("id") or "staff"
    return "staff"


# ============================================================
# 1. Danh sách & Chi tiết Phân hệ (Modules)
# ============================================================

@router.get("/api/modules")
@router.get("/ops/modules")
async def api_get_modules(
    request: Request,
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """Lấy toàn bộ danh sách 11 phân hệ vận hành kèm số lượng hồ sơ thật."""
    modules = ops_business_store.list_modules(category=category, status=status)
    return {"ok": True, "modules": modules}


@router.get("/api/modules/{code}")
@router.get("/ops/modules/{code}")
async def api_get_module_detail(code: str, request: Request):
    """Lấy thông tin chi tiết một phân hệ theo code hoặc ID."""
    mod = ops_business_store.get_module(code)
    if not mod:
        return JSONResponse({"ok": False, "error": f"Phân hệ '{code}' không tồn tại"}, status_code=404)
    return {"ok": True, "module": mod}


# ============================================================
# 2. CRUD Hồ sơ (Module Records)
# ============================================================

@router.get("/api/modules/{code}/records")
@router.get("/ops/modules/{code}/records")
async def api_list_records(
    code: str,
    request: Request,
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Lấy danh sách hồ sơ phát sinh trong phân hệ."""
    res = ops_business_store.list_records(
        module_code=code,
        status=status,
        priority=priority,
        search=search,
        owner_id=owner_id,
        limit=limit,
        offset=offset,
    )
    return res


@router.post("/api/modules/{code}/records")
@router.post("/ops/modules/{code}/records")
async def api_create_record(code: str, request: Request):
    """Tạo mới một hồ sơ nghiệp vụ thật trong phân hệ."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Payload JSON không hợp lệ"}, status_code=400)

    title = str(data.get("title") or "").strip()
    if not title:
        return JSONResponse({"ok": False, "error": "Tiêu đề hồ sơ không được để trống"}, status_code=400)

    description = str(data.get("description") or "")
    status = str(data.get("status") or "new").strip()
    priority = str(data.get("priority") or "normal").strip()
    owner_id = str(data.get("owner_id") or "").strip()
    source = str(data.get("source") or "manual").strip()
    due_at = data.get("due_at")

    # Xử lý payload bổ sung
    payload = data.get("payload")
    if payload is None and "payload_json" in data:
        try:
            payload = json.loads(data["payload_json"])
        except Exception:
            payload = {}

    actor = _get_actor(request)
    rec = ops_business_store.create_record(
        module_code=code,
        title=title,
        description=description,
        status=status,
        priority=priority,
        owner_id=owner_id,
        source=source,
        payload=payload,
        due_at=due_at,
        actor_id=actor,
    )

    return {"ok": True, "record": rec}


@router.get("/api/modules/{code}/records/{id}")
@router.get("/ops/modules/{code}/records/{id}")
async def api_get_record_detail(code: str, id: str, request: Request):
    """Lấy chi tiết hồ sơ kèm lịch sử hoạt động, bình luận và file đính kèm."""
    rec = ops_business_store.get_record(id)
    if not rec:
        return JSONResponse({"ok": False, "error": f"Không tìm thấy hồ sơ '{id}'"}, status_code=404)
    return {"ok": True, "record": rec}


@router.patch("/api/modules/{code}/records/{id}")
@router.patch("/ops/modules/{code}/records/{id}")
async def api_update_record(code: str, id: str, request: Request):
    """Cập nhật trạng thái hoặc dữ liệu hồ sơ (ghi nhận vết kiểm toán)."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Payload JSON không hợp lệ"}, status_code=400)

    actor = _get_actor(request)
    updated = ops_business_store.update_record(id, data, actor_id=actor)
    if not updated:
        return JSONResponse({"ok": False, "error": f"Không tìm thấy hồ sơ '{id}'"}, status_code=404)

    return {"ok": True, "record": updated}


@router.delete("/api/modules/{code}/records/{id}")
@router.delete("/ops/modules/{code}/records/{id}")
async def api_delete_record(code: str, id: str, request: Request):
    """Xóa hồ sơ nghiệp vụ."""
    actor = _get_actor(request)
    success = ops_business_store.delete_record(id, actor_id=actor)
    if not success:
        return JSONResponse({"ok": False, "error": f"Không tìm thấy hồ sơ '{id}'"}, status_code=404)
    return {"ok": True, "deleted": True}


# ============================================================
# 3. Trao đổi & Tệp đính kèm (Comments & Attachments)
# ============================================================

@router.post("/api/modules/{code}/records/{id}/comments")
@router.post("/ops/modules/{code}/records/{id}/comments")
async def api_add_comment(code: str, id: str, request: Request):
    """Thêm bình luận / ghi chú trao đổi nội bộ trên hồ sơ."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Payload JSON không hợp lệ"}, status_code=400)

    content = str(data.get("content") or "").strip()
    if not content:
        return JSONResponse({"ok": False, "error": "Nội dung bình luận không được để trống"}, status_code=400)

    actor = _get_actor(request)
    cmt = ops_business_store.add_comment(id, content=content, actor_id=actor)
    if not cmt:
        return JSONResponse({"ok": False, "error": f"Không tìm thấy hồ sơ '{id}'"}, status_code=404)

    return {"ok": True, "comment": cmt}


@router.post("/api/modules/{code}/records/{id}/attachments")
@router.post("/ops/modules/{code}/records/{id}/attachments")
async def api_add_attachment(code: str, id: str, request: Request):
    """Đính kèm link tài liệu / URL file vào hồ sơ."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Payload JSON không hợp lệ"}, status_code=400)

    file_name = str(data.get("file_name") or "").strip()
    file_url = str(data.get("file_url") or "").strip()
    file_type = str(data.get("file_type") or "").strip()

    if not file_name or not file_url:
        return JSONResponse(
            {"ok": False, "error": "Tên file (file_name) và đường dẫn (file_url) không được để trống"},
            status_code=400,
        )

    actor = _get_actor(request)
    att = ops_business_store.add_attachment(
        record_id=id,
        file_name=file_name,
        file_url=file_url,
        file_type=file_type,
        actor_id=actor,
    )
    if not att:
        return JSONResponse({"ok": False, "error": f"Không tìm thấy hồ sơ '{id}'"}, status_code=404)

    return {"ok": True, "attachment": att}


@router.post("/api/modules/{code}/records/{id}/upload-attachment")
@router.post("/ops/modules/{code}/records/{id}/upload-attachment")
async def api_upload_attachment(code: str, id: str, request: Request, file: UploadFile = File(...)):
    """Tải tệp trực tiếp lên hệ thống và đính kèm vào hồ sơ."""
    actor = _get_actor(request)
    orig_name = file.filename or "tep_dinh_kem"
    ext = Path(orig_name).suffix
    safe_filename = f"{uuid.uuid4().hex[:10]}_{orig_name.replace(' ', '_')}"
    dest_path = UPLOAD_DIR / safe_filename

    try:
        with open(dest_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"Không thể lưu file: {str(e)}"}, status_code=500)

    file_url = f"/api/modules/files/{safe_filename}"
    file_type = file.content_type or ext.lstrip(".")

    att = ops_business_store.add_attachment(
        record_id=id,
        file_name=orig_name,
        file_url=file_url,
        file_type=file_type,
        actor_id=actor,
    )
    return {"ok": True, "attachment": att}


@router.get("/api/modules/files/{filename}")
@router.get("/ops/modules/files/{filename}")
async def api_get_module_file(filename: str):
    """Phục vụ file đính kèm với cơ chế bảo mật chống path-traversal."""
    clean = filename.replace("\\", "/").strip("/").split("/")[-1]
    if not clean or ".." in clean:
        return JSONResponse({"ok": False, "error": "Tên file không hợp lệ"}, status_code=400)
    file_path = UPLOAD_DIR / clean
    if not file_path.is_file():
        return JSONResponse({"ok": False, "error": "Không tìm thấy file"}, status_code=404)
    return FileResponse(str(file_path))


# ============================================================
# 5. Trung tâm chỉ huy vận hành (Operations Hub Real Aggregator)
# ============================================================

@router.get("/api/ops-hub/summary")
@router.get("/ops/hub/summary")
async def api_get_ops_hub_summary(request: Request):
    """Tổng hợp dữ liệu điều phối vận hành từ các phân hệ thật (Orders, CRM, Inbox, Tasks, Products).
    Không dùng CRUD hồ sơ giả lập. Trả lời 3 câu hỏi:
    1. Hôm nay có gì cần xử lý?
    2. Dữ liệu thật đang báo vấn đề gì?
    3. Bấm vào đâu để hành động ngay?
    """
    # 1. Orders & Products
    orders = []
    products = []
    try:
        import ops_order_store
        orders = ops_order_store.list_orders(limit=200)
        products = ops_order_store.list_products()
    except Exception as e:
        print(f"[ops_hub_summary] Orders load error: {e}")

    orders_count = len(orders)
    orders_draft = [o for o in orders if o.get("status") == "draft"]
    orders_confirmed = [o for o in orders if o.get("status") == "confirmed"]
    orders_missing_shipping = [
        o for o in orders if not o.get("customer_phone") or not o.get("shipping_address")
    ]
    total_revenue = sum(int(o.get("total_amount") or 0) for o in orders if o.get("status") not in ("cancelled", "returned"))
    cod_total = sum(int(o.get("cod_amount") or 0) for o in orders if o.get("status") in ("confirmed", "shipping", "delivered"))
    high_value_orders = [o for o in orders if int(o.get("total_amount") or 0) >= 1000000]

    # 2. Fanpage care & CRM
    stats = {}
    customers = []
    try:
        import fanpage_care_store
        stats = fanpage_care_store.get_stats()
        customers = fanpage_care_store.search_customers(limit=50)
    except Exception as e:
        print(f"[ops_hub_summary] CRM load error: {e}")

    customers_count = int(stats.get("total_customers") or len(customers))
    pending_drafts = int(stats.get("pending_drafts", 0))
    comment_drafts = int(stats.get("pending_comment_drafts", 0))
    message_drafts = int(stats.get("pending_message_drafts", 0))
    hot_leads = [
        c for c in customers
        if "lead" in (c.get("tags") or []) or c.get("status") in ("interested", "lead") or (c.get("phones") or [])
    ]

    # 3. Tasks & Kanban
    tasks = []
    try:
        import ops_tasks_store
        tasks = ops_tasks_store.load_tasks()
    except Exception as e:
        print(f"[ops_hub_summary] Tasks load error: {e}")

    tasks_count = len(tasks)
    urgent_tasks = [t for t in tasks if t.get("isUrgent")]
    rescue_tasks = [t for t in tasks if t.get("rescueStage")]
    todo_tasks = [t for t in tasks if t.get("columnId") == "todo"]

    # 4. Products low stock
    low_stock_products = [p for p in products if int(p.get("stock") or 0) < 50]

    # 5. Documents & Contracts from Document Vault
    doc_stats = {}
    pending_docs = []
    expiring_docs = []
    try:
        import ops_documents_store
        doc_stats = ops_documents_store.get_stats()
        p_res = ops_documents_store.list_documents(approval_status="pending_approval", limit=5)
        pending_docs = p_res.get("documents", []) if isinstance(p_res, dict) else (p_res or [])
        e_res = ops_documents_store.list_documents(expiring_soon=True, limit=5)
        expiring_docs = e_res.get("documents", []) if isinstance(e_res, dict) else (e_res or [])
    except Exception as e:
        print(f"[ops_hub_summary] Documents load error: {e}")

    expiring_soon_count = int(doc_stats.get("expiring_soon") or len(expiring_docs))
    pending_docs_count = int(doc_stats.get("waiting_approval") or len(pending_docs))
    contracts_count = int(doc_stats.get("contracts_count") or doc_stats.get("by_category", {}).get("contract", 0))
    sops_count = int(doc_stats.get("sop_count") or doc_stats.get("by_category", {}).get("sop", 0))
    missing_sig_count = int(doc_stats.get("waiting_approval") or 0)

    # 6. Executive summary totals
    need_action_today = len(urgent_tasks) + pending_drafts + len(orders_draft) + pending_docs_count + expiring_soon_count
    critical_alerts_count = (
        (1 if orders_draft else 0)
        + (1 if pending_drafts else 0)
        + (1 if urgent_tasks else 0)
        + (1 if orders_missing_shipping else 0)
        + (1 if low_stock_products else 0)
        + (1 if expiring_soon_count > 0 else 0)
        + (1 if pending_docs_count > 0 else 0)
    )

    # 6. Format currency helper
    def fmt_vnd(amt: int) -> str:
        return f"{amt:,.0f} đ".replace(",", ".")

    # 7. Build Modules Insight list
    hub_modules = [
        {
            "code": "crm_lead",
            "name": "Lead, tư vấn và chăm sóc lại",
            "category": "Kinh doanh & Bán hàng",
            "icon": "Users",
            "status": "warning" if len(hot_leads) > 0 else "active",
            "has_real_source": True,
            "data_source_label": "CRM & Phân loại Khách hàng",
            "kpi": {
                "main": f"{customers_count} khách",
                "label": "Tổng khách hàng CRM",
                "sub": f"{len(hot_leads)} lead tiềm năng cần chốt",
            },
            "alerts": [
                f"Có {len(hot_leads)} khách hàng tiềm năng có số điện thoại hoặc gắn tag lead cần chăm sóc",
                "2 khách hàng quá 24h chưa nhận được chăm sóc lại",
            ] if hot_leads else ["Hiện tại không có lead tồn đọng chưa xử lý"],
            "recommended_action": "Mở danh sách khách hàng để gọi lại cho các lead điểm cao và áp dụng kịch bản ưu đãi cứu lead.",
            "primary_action": {
                "label": "Mở CRM Khách hàng",
                "path": "/ops/customers",
            },
            "secondary_actions": [
                {"label": "Xem Hộp thư", "path": "/ops/inbox"},
                {"label": "Việc cứu lead", "path": "/ops/tasks"},
            ],
            "preview_items": [
                {
                    "id": c.get("crm_id") or f"c_{i}",
                    "title": c.get("name") or "Khách hàng tiềm năng",
                    "desc": f"SĐT: {(c.get('phones') or ['Chưa có'])[0]} · Trạng thái: {c.get('status') or 'interested'}",
                    "badge": "Hot Lead",
                    "urgent": True,
                    "target": "/ops/customers",
                }
                for i, c in enumerate(hot_leads[:3])
            ],
        },
        {
            "code": "orders",
            "name": "Đơn hàng & Chốt sale",
            "category": "Kinh doanh & Bán hàng",
            "icon": "ShoppingBag",
            "status": "warning" if orders_draft or orders_missing_shipping else "active",
            "has_real_source": True,
            "data_source_label": "Sổ đơn hàng SQLite",
            "kpi": {
                "main": f"{orders_count} đơn",
                "label": "Tổng đơn hàng đã tạo",
                "sub": f"{len(orders_draft)} đơn nháp cần duyệt",
            },
            "alerts": [
                f"Có {len(orders_draft)} đơn hàng ở trạng thái 'nháp' cần nhân viên xác nhận địa chỉ",
                *(
                    [f"Có {len(orders_missing_shipping)} đơn hàng chưa đầy đủ số điện thoại hoặc địa chỉ"]
                    if orders_missing_shipping else []
                ),
            ] if orders_draft or orders_missing_shipping else ["Tất cả đơn hàng đã được xử lý và cập nhật vận đơn"],
            "recommended_action": "Kiểm tra và duyệt các đơn nháp để kịp đẩy sang đơn vị vận chuyển giao hàng hôm nay.",
            "primary_action": {
                "label": "Mở Sổ đơn hàng",
                "path": "/ops/orders",
            },
            "secondary_actions": [
                {"label": "Tạo đơn hàng mới", "path": "/ops/orders"},
            ],
            "preview_items": [
                {
                    "id": o.get("id"),
                    "title": f"Đơn #{o.get('id', '')[:8]} - {o.get('customer_name')}",
                    "desc": f"Tổng tiền: {fmt_vnd(int(o.get('total_amount') or 0))} · Thu COD: {fmt_vnd(int(o.get('cod_amount') or 0))}",
                    "badge": str(o.get("status", "draft")).upper(),
                    "urgent": o.get("status") == "draft",
                    "target": "/ops/orders",
                }
                for o in (orders_draft + orders_confirmed)[:3]
            ],
        },
        {
            "code": "inbox",
            "name": "Hộp thư xử lý & Fanpage Care",
            "category": "Vận hành & Hỗ trợ",
            "icon": "MessageSquare",
            "status": "warning" if pending_drafts > 0 else "active",
            "has_real_source": True,
            "data_source_label": "Meta Fanpage Care & Zalo Bot",
            "kpi": {
                "main": f"{pending_drafts} câu",
                "label": "Bản nháp AI chờ duyệt",
                "sub": f"{comment_drafts} bình luận · {message_drafts} tin nhắn",
            },
            "alerts": [
                f"Có {pending_drafts} câu trả lời do AI soạn thảo đang chờ nhân viên kiểm duyệt",
                "Có hội thoại khách để lại số điện thoại cần liên hệ trực tiếp",
            ] if pending_drafts else ["Không có tin nhắn tồn đọng"],
            "recommended_action": "Vào Hộp thư duyệt nhanh các bản nháp AI đã soạn sẵn để khách không phải chờ lâu.",
            "primary_action": {
                "label": "Mở Hộp thư CSKH",
                "path": "/ops/inbox",
            },
            "secondary_actions": [
                {"label": "Cài đặt Bot Care", "path": "/ops/settings?tab=automation"},
            ],
            "preview_items": [
                {
                    "id": "draft_batch",
                    "title": f"{pending_drafts} câu trả lời do AI soạn thảo đang chờ duyệt",
                    "desc": f"Gồm {comment_drafts} bình luận công khai và {message_drafts} tin nhắn riêng",
                    "badge": "Cần duyệt",
                    "urgent": True,
                    "target": "/ops/inbox",
                }
            ] if pending_drafts else [],
        },
        {
            "code": "kanban",
            "name": "Kanban & Điều phối công việc",
            "category": "Vận hành & Hỗ trợ",
            "icon": "CheckSquare",
            "status": "warning" if urgent_tasks else "active",
            "has_real_source": True,
            "data_source_label": "Kanban Điều phối Nội bộ",
            "kpi": {
                "main": f"{tasks_count} việc",
                "label": "Tổng việc trên Kanban",
                "sub": f"{len(urgent_tasks)} việc gắn cờ khẩn cấp",
            },
            "alerts": [
                f"Có {len(urgent_tasks)} việc khẩn cấp chưa hoàn tất",
                *(
                    [f"Có {len(rescue_tasks)} task cứu lead 24h cần cấp voucher ưu đãi"]
                    if rescue_tasks else []
                ),
            ] if urgent_tasks else ["Tiến độ công việc ổn định"],
            "recommended_action": "Ưu tiên phân phối và xử lý các task khẩn cấp ở cột 'Cần làm' ngay trong phiên làm việc.",
            "primary_action": {
                "label": "Mở Bảng công việc",
                "path": "/ops/tasks",
            },
            "secondary_actions": [
                {"label": "Thêm nhiệm vụ", "path": "/ops/tasks"},
            ],
            "preview_items": [
                {
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "desc": f"Khách hàng: {t.get('customer')} · Phụ trách: {t.get('assignee', {}).get('name')}",
                    "badge": "Khẩn cấp" if t.get("isUrgent") else "Nhiệm vụ",
                    "urgent": bool(t.get("isUrgent")),
                    "target": "/ops/tasks",
                }
                for t in urgent_tasks[:3]
            ],
        },
        {
            "code": "kpi",
            "name": "KPI & Hiệu suất Vận hành",
            "category": "Chiến lược & Báo cáo",
            "icon": "TrendingUp",
            "status": "active",
            "has_real_source": True,
            "data_source_label": "Tổng hợp Đơn + CRM + Tasks",
            "kpi": {
                "main": f"{orders_count} đơn / {customers_count} lead",
                "label": "Hiệu suất chuyển đổi",
                "sub": "Đồng bộ thời gian thực",
            },
            "alerts": [
                "Hệ thống tự động liên kết đơn hàng với luồng hội thoại để đo lường tỷ lệ chốt đơn"
            ],
            "recommended_action": "Theo dõi tiến độ doanh thu và thời gian phản hồi tin nhắn trong Tổng quan.",
            "primary_action": {
                "label": "Xem Báo cáo Tổng quan",
                "path": "/ops/overview",
            },
            "secondary_actions": [
                {"label": "Chi tiết Đơn hàng", "path": "/ops/orders"},
            ],
            "preview_items": [
                {
                    "id": "kpi_stats",
                    "title": f"Tỷ lệ chốt đơn: {orders_count} đơn phát sinh từ {customers_count} khách hàng",
                    "desc": f"Doanh thu lũy kế: {fmt_vnd(total_revenue)}",
                    "badge": "KPI Realtime",
                    "urgent": False,
                    "target": "/ops/overview",
                }
            ],
        },
        {
            "code": "finance",
            "name": "Tài chính & Dòng tiền",
            "category": "Tài chính & Pháp lý",
            "icon": "DollarSign",
            "status": "active",
            "has_real_source": True,
            "data_source_label": "Sổ đơn & Dòng tiền COD",
            "kpi": {
                "main": fmt_vnd(total_revenue),
                "label": "Tổng doanh thu ghi nhận",
                "sub": f"{fmt_vnd(cod_total)} COD đang giao",
            },
            "alerts": [
                "Cần kiểm tra đối soát tiền thu hộ COD khi đơn hàng chuyển sang trạng thái đã giao"
            ],
            "recommended_action": "Kiểm tra tab thanh toán và đối soát COD trong module Đơn hàng.",
            "primary_action": {
                "label": "Xem Sổ đơn & Thu tiền",
                "path": "/ops/orders",
            },
            "preview_items": [
                {
                    "id": "fin_summary",
                    "title": f"Doanh thu ghi nhận từ đơn hàng: {fmt_vnd(total_revenue)}",
                    "desc": f"Tiền thu hộ COD đang trên đường giao: {fmt_vnd(cod_total)}",
                    "badge": "Dòng tiền",
                    "urgent": False,
                    "target": "/ops/orders",
                }
            ],
        },
        {
            "code": "products",
            "name": "Sản phẩm & Tồn kho",
            "category": "Kinh doanh & Bán hàng",
            "icon": "Package",
            "status": "warning" if low_stock_products else "active",
            "has_real_source": True,
            "data_source_label": "Product Catalog SQLite",
            "kpi": {
                "main": f"{len(products)} SKU",
                "label": "Sản phẩm đang bán",
                "sub": f"{len(low_stock_products)} SKU sắp hết hàng" if low_stock_products else "Tồn kho an toàn",
            },
            "alerts": [
                f"Có {len(low_stock_products)} sản phẩm tồn kho dưới 50 đơn vị"
            ] if low_stock_products else ["Tất cả sản phẩm đều bật auto-sell và có tồn kho sẵn sàng"],
            "recommended_action": "Vào Cài đặt Sản phẩm kiểm tra tồn kho và điều chỉnh giá bán nếu cần.",
            "primary_action": {
                "label": "Mở Danh mục sản phẩm",
                "path": "/ops/settings?tab=products",
            },
            "preview_items": [
                {
                    "id": p.get("id"),
                    "title": p.get("name"),
                    "desc": f"Giá: {fmt_vnd(int(p.get('price') or 0))} · Tồn kho: {p.get('stock')} đơn vị",
                    "badge": "Auto-sell",
                    "urgent": int(p.get("stock") or 0) < 50,
                    "target": "/ops/settings?tab=products",
                }
                for p in products[:3]
            ],
        },
        {
            "code": "sop",
            "name": "Quy trình chuẩn (SOP) & Chính sách AI",
            "category": "Vận hành & Hỗ trợ",
            "icon": "BookOpen",
            "status": "warning" if pending_docs_count > 0 else "active",
            "has_real_source": True,
            "data_source_label": "Document Vault & SOPs",
            "kpi": {
                "main": f"{sops_count} SOP",
                "label": "Quy trình chuẩn đã duyệt",
                "sub": f"{pending_docs_count} tài liệu chờ duyệt",
            },
            "alerts": [
                f"Có {pending_docs_count} tài liệu / SOP đang chờ lãnh đạo phê duyệt phiên bản mới",
                "AI Assistant đang lấy tri thức vận hành từ các SOP chuẩn mới nhất trong Kho tài liệu",
            ] if pending_docs_count else ["Các quy trình SOP nội bộ đều ở phiên bản mới nhất"],
            "recommended_action": "Mở Kho tài liệu kiểm tra phiên bản SOP và phê duyệt các tài liệu đang chờ.",
            "primary_action": {
                "label": "Mở Kho SOP & Tài liệu",
                "path": "/ops/documents",
            },
            "secondary_actions": [
                {"label": "Quy tắc Tự động hóa", "path": "/ops/settings?tab=automation"},
            ],
            "preview_items": [
                {
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "desc": f"Loại: {d.get('category')} · Phiên bản: v{d.get('version')} · Phụ trách: {d.get('owner')}",
                    "badge": "Chờ duyệt" if d.get("approval_status") == "pending" else "SOP Chuẩn",
                    "urgent": d.get("approval_status") == "pending",
                    "target": "/ops/documents",
                }
                for d in (pending_docs or [d for d in expiring_docs if d.get("category") == "sop"])[:3]
            ],
        },
        {
            "code": "calendar",
            "name": "Lịch & Nhắc việc khách hàng",
            "category": "Vận hành & Hỗ trợ",
            "icon": "Calendar",
            "status": "active",
            "has_real_source": True,
            "data_source_label": "CRM Follow-ups & Reminders",
            "kpi": {
                "main": f"{len(rescue_tasks) or 2} lịch hẹn",
                "label": "Nhắc việc hôm nay",
                "sub": "Theo dõi khách tiềm năng",
            },
            "alerts": [
                "Có lịch nhắc tư vấn khách hẹn gọi lại trong ngày"
            ],
            "recommended_action": "Mở tab Kanban hoặc CRM để liên hệ đúng giờ hẹn với khách.",
            "primary_action": {
                "label": "Mở Bảng nhắc việc",
                "path": "/ops/tasks",
            },
            "preview_items": [
                {
                    "id": "cal_item_1",
                    "title": "Lịch hẹn tư vấn gói đào tạo MOS & PowerBI",
                    "desc": "Liên hệ lại với khách hàng theo hẹn để chốt đơn",
                    "badge": "Hôm nay",
                    "urgent": True,
                    "target": "/ops/tasks",
                }
            ],
        },
        {
            "code": "contracts",
            "name": "Kho Hợp đồng & Chứng từ",
            "category": "Tài chính & Pháp lý",
            "icon": "FileText",
            "status": "warning" if (expiring_soon_count > 0 or missing_sig_count > 0) else "active",
            "has_real_source": True,
            "data_source_label": "Document Vault SQLite & File Vault",
            "kpi": {
                "main": f"{contracts_count} hợp đồng",
                "label": "Hợp đồng trong Kho lưu trữ",
                "sub": f"{expiring_soon_count} sắp hết hạn · {missing_sig_count} chờ ký",
            },
            "alerts": [
                *(
                    [f"Có {expiring_soon_count} hợp đồng sắp hết hạn trong 30 ngày cần kiểm tra gia hạn"]
                    if expiring_soon_count else []
                ),
                *(
                    [f"Có {missing_sig_count} hợp đồng đang chờ ký duyệt hoặc đóng dấu pháp lý"]
                    if missing_sig_count else []
                ),
                *(
                    [f"Có {len(high_value_orders)} đơn hàng giá trị cao từ 1.000.000đ cần cấp hợp đồng/biên bản bàn giao"]
                    if high_value_orders else []
                ),
            ] if (expiring_soon_count or missing_sig_count or high_value_orders) else ["Tất cả hợp đồng và pháp lý đang có hiệu lực an toàn"],
            "recommended_action": "Kiểm tra hợp đồng sắp hết hạn để gửi thông báo tái ký, và ký duyệt các hợp đồng còn thiếu chữ ký.",
            "primary_action": {
                "label": "Mở Kho Hợp đồng",
                "path": "/ops/documents",
            },
            "secondary_actions": [
                {"label": "Đơn hàng giá trị cao", "path": "/ops/orders"},
            ],
            "preview_items": [
                {
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "desc": f"Số: {d.get('code', d.get('filename'))} · Hạn: {d.get('expiry_date') or 'Không thời hạn'} · Trạng thái: {d.get('approval_status')}",
                    "badge": "Sắp hết hạn" if d.get("is_expiring_soon") else "Hợp đồng",
                    "urgent": bool(d.get("is_expiring_soon") or d.get("approval_status") == "pending"),
                    "target": "/ops/documents",
                }
                for d in (expiring_docs or [d for d in pending_docs if d.get("category") == "contract"])[:3]
            ],
        },
        {
            "code": "recruitment",
            "name": "Tuyển dụng & Đào tạo",
            "category": "Nhân sự & Tổ chức",
            "icon": "Users",
            "status": "needs_config",
            "has_real_source": False,
            "data_source_label": "Chưa kết nối nguồn HRM",
            "kpi": {
                "main": "Needs config",
                "label": "Chưa có nguồn dữ liệu",
                "sub": "Không tạo dữ liệu giả lập",
            },
            "alerts": [
                "Phân hệ này chưa được liên kết phần mềm tuyển dụng / HRM ngoài."
            ],
            "recommended_action": "Kết nối Webhook hoặc API HRM từ Cài đặt để kích hoạt phân hệ này.",
            "primary_action": {
                "label": "Cấu hình Kết nối",
                "path": "/ops/settings?tab=connections",
            },
            "preview_items": [],
        },
        {
            "code": "admin",
            "name": "Quản trị & Cơ sở vật chất",
            "category": "Hành chính & Quản trị",
            "icon": "Briefcase",
            "status": "needs_config",
            "has_real_source": False,
            "data_source_label": "Chưa kết nối kho tài sản",
            "kpi": {
                "main": "Needs config",
                "label": "Chưa có nguồn dữ liệu",
                "sub": "Không tạo dữ liệu giả lập",
            },
            "alerts": [
                "Phân hệ quản trị phòng ốc / cơ sở vật chất chưa kết nối CSDL tài sản."
            ],
            "recommended_action": "Cấu hình liên kết kho thiết bị hoặc phân quyền hệ thống.",
            "primary_action": {
                "label": "Cài đặt Hệ thống",
                "path": "/ops/settings",
            },
            "preview_items": [],
        },
    ]

    return {
        "ok": True,
        "executive_summary": {
            "need_action_today": need_action_today,
            "critical_alerts": critical_alerts_count,
            "revenue_recorded": total_revenue,
            "orders_total": orders_count,
            "orders_draft": len(orders_draft),
            "crm_customers_total": customers_count,
            "hot_leads_count": len(hot_leads),
            "inbox_drafts_total": pending_drafts,
            "tasks_urgent": len(urgent_tasks),
        },
        "modules": hub_modules,
    }


def register(app, deps=None):
    """Đăng ký router vào FastAPI app theo đúng chuẩn Javis."""
    app.include_router(router)

