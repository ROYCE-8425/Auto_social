"""Order Core & Shipping Controller for Sèo Trum Ops Social Commerce.

Handles business logic for:
- Manual & AI order creation
- Extraction from conversation threads
- Order confirmation & state transitions
- Shipment creation via Shipping Gateway (GHN)
- Order & shipment cancellation
- Carrier webhook ingestion
- Carrier settings & automation rules
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import ops_order_store
import ops_sales_extraction
import ops_shipping
import ops_shipping_store


def get_orders_list(
    status: Optional[str] = None,
    crm_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    page_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db_path: Optional[Any] = None,
) -> Dict[str, Any]:
    orders = ops_order_store.list_orders(
        status=status,
        crm_id=crm_id,
        thread_id=thread_id,
        page_id=page_id,
        limit=limit,
        offset=offset,
        db_path=db_path,
    )
    return {
        "ok": True,
        "orders": orders,
        "total": len(orders),
    }


def get_order_detail(order_id: str, db_path: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    order = ops_order_store.get_order(order_id, db_path=db_path)
    if not order:
        return None
    return {
        "ok": True,
        "order": order,
    }


def create_new_order(payload: Dict[str, Any], actor: str = "staff", db_path: Optional[Any] = None) -> Dict[str, Any]:
    crm_id = payload.get("crm_id")
    customer_name = payload.get("customer_name")
    customer_phone = payload.get("customer_phone")
    page_id = payload.get("page_id")
    thread_id = payload.get("thread_id")
    items = payload.get("items") or []
    shipping_address = payload.get("shipping_address")
    cod_amount = payload.get("cod_amount")
    shipping_fee = int(payload.get("shipping_fee") or 0)
    payment_method = payload.get("payment_method") or "cod"
    customer_notes = payload.get("customer_notes")
    internal_notes = payload.get("internal_notes")
    ai_confidence = float(payload.get("ai_confidence") or 1.0)
    missing_fields = payload.get("missing_fields") or []
    status = payload.get("status") or "draft"

    order = ops_order_store.create_order(
        crm_id=crm_id,
        customer_name=customer_name,
        customer_phone=customer_phone,
        page_id=page_id,
        thread_id=thread_id,
        items=items,
        shipping_address=shipping_address,
        cod_amount=cod_amount,
        shipping_fee=shipping_fee,
        payment_method=payment_method,
        customer_notes=customer_notes,
        internal_notes=internal_notes,
        ai_confidence=ai_confidence,
        missing_fields=missing_fields,
        status=status,
        actor=actor,
        db_path=db_path,
    )

    return {
        "ok": True,
        "order": order,
    }


def update_order_info(order_id: str, updates: Dict[str, Any], actor: str = "staff", db_path: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    updated = ops_order_store.update_order(order_id, updates, actor=actor, db_path=db_path)
    if not updated:
        return None
    return {
        "ok": True,
        "order": updated,
    }


def extract_order_from_messages(
    messages: List[Dict[str, Any]],
    customer_name: Optional[str] = None,
    page_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    crm_id: Optional[str] = None,
    auto_save: bool = False,
    actor: str = "ai",
    db_path: Optional[Any] = None,
) -> Dict[str, Any]:
    """Phân tích hội thoại bằng AI Sales Extraction và trả về dữ liệu đơn hàng cấu trúc."""
    extracted = ops_sales_extraction.extract_order_from_thread(
        messages=messages,
        customer_name=customer_name,
        page_id=page_id,
        thread_id=thread_id,
        crm_id=crm_id,
        db_path=db_path,
    )

    if auto_save:
        # Tự động lưu bản ghi đơn nháp vào SQLite
        order = ops_order_store.create_order(
            crm_id=crm_id,
            customer_name=extracted.get("customer_name"),
            customer_phone=extracted.get("customer_phone"),
            page_id=page_id,
            thread_id=thread_id,
            items=extracted.get("items"),
            shipping_address=extracted.get("shipping_address"),
            cod_amount=extracted.get("cod_amount"),
            shipping_fee=0,
            ai_confidence=extracted.get("ai_confidence", 0.0),
            missing_fields=extracted.get("missing_fields", []),
            status=extracted.get("status", "draft"),
            source="inbox_ai_extracted",
            actor=actor,
            db_path=db_path,
        )
        extracted["saved_order"] = order

    return extracted


def confirm_order(order_id: str, actor: str = "staff", db_path: Optional[Any] = None) -> Dict[str, Any]:
    """Chuyển trạng thái đơn thành 'confirmed'. Nếu bật rule tự động tạo vận đơn thì tạo shipment."""
    order = ops_order_store.get_order(order_id, db_path=db_path)
    if not order:
        raise ValueError(f"Không tìm thấy đơn hàng #{order_id}")

    if order["status"] in ("cancelled", "delivered", "shipping"):
        raise ValueError(f"Không thể xác nhận đơn hàng đang ở trạng thái '{order['status']}'")

    updated = ops_order_store.update_order(
        order_id,
        {"status": "confirmed"},
        actor=actor,
        db_path=db_path,
    )

    ops_order_store.record_audit_log(
        order_id=order_id,
        action="confirmed",
        actor=actor,
        details={"previous_status": order["status"], "new_status": "confirmed"},
        db_path=db_path,
    )

    # Kiểm tra Automation Rules xem có được auto tạo vận đơn hay không
    settings = ops_shipping_store.load_shipping_settings()
    automation = settings.get("automation") or {}
    auto_shipment = bool(automation.get("auto_create_shipment", False))
    min_conf = float(automation.get("min_confidence", 0.85))
    kill_switch = bool(automation.get("kill_switch", False))

    auto_result = None
    if auto_shipment and not kill_switch:
        curr_conf = float(updated.get("ai_confidence") or 1.0)
        missing = updated.get("missing_fields") or []
        has_phone = bool(updated.get("customer_phone"))
        has_addr = bool(updated.get("shipping_address"))
        if curr_conf >= min_conf and not missing and has_phone and has_addr:
            try:
                auto_result = create_shipment_for_order(order_id, actor="automation_rule", db_path=db_path)
            except Exception as exc:
                auto_result = {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "order": ops_order_store.get_order(order_id, db_path=db_path),
        "auto_shipment": auto_result,
    }


def create_shipment_for_order(
    order_id: str,
    provider_id: Optional[str] = None,
    actor: str = "staff",
    db_path: Optional[Any] = None,
) -> Dict[str, Any]:
    """Tạo vận đơn thật qua Shipping Gateway (mặc định GHN)."""
    order = ops_order_store.get_order(order_id, db_path=db_path)
    if not order:
        raise ValueError(f"Không tìm thấy đơn hàng #{order_id}")

    if order.get("status") != "confirmed":
        raise ValueError("Chỉ đơn hàng đã xác nhận mới được tạo vận đơn.")

    if not order.get("customer_phone"):
        raise ValueError("Đơn hàng chưa có số điện thoại người nhận. Không thể tạo vận đơn.")
    if not order.get("shipping_address"):
        raise ValueError("Đơn hàng chưa có địa chỉ nhận hàng. Không thể tạo vận đơn.")

    settings = ops_shipping_store.load_shipping_settings()
    prov_key = provider_id or settings.get("default_provider") or "ghn"
    provider = ops_shipping.get_shipping_provider(prov_key)

    prov_config = settings.get("providers", {}).get(prov_key, {})
    if not provider.is_configured(prov_config):
        return {
            "ok": False,
            "status": "not_configured",
            "error": f"Đơn vị vận chuyển {provider.name} chưa được cấu hình API Token / Shop ID.",
        }

    # Gọi provider abstraction
    res = provider.create_shipment(order, prov_config)
    if not res.get("ok"):
        ops_order_store.record_audit_log(
            order_id=order_id,
            action="shipment_failed",
            actor=actor,
            details={"error": res.get("error"), "provider": prov_key},
            db_path=db_path,
        )
        return {
            "ok": False,
            "status": "error",
            "error": res.get("error") or "Không thể tạo vận đơn từ hãng",
        }

    tracking_code = res.get("tracking_code")
    fee = int(res.get("fee") or 0)
    cod_amount = int(res.get("cod_amount") or order.get("cod_amount") or 0)
    expected_time = res.get("expected_delivery_time")

    shipment = ops_order_store.create_shipment(
        order_id=order_id,
        provider=prov_key,
        tracking_code=tracking_code,
        external_order_code=tracking_code,
        status="ready_to_pick",
        fee=fee,
        cod_amount=cod_amount,
        expected_delivery_time=expected_time,
        provider_response=res.get("raw_response"),
        actor=actor,
        db_path=db_path,
    )

    return {
        "ok": True,
        "shipment": shipment,
        "order": ops_order_store.get_order(order_id, db_path=db_path),
    }


def cancel_order_and_shipment(
    order_id: str,
    reason: Optional[str] = None,
    actor: str = "staff",
    db_path: Optional[Any] = None,
) -> Dict[str, Any]:
    """Hủy đơn hàng và vận đơn liên quan nếu đã xuất đơn."""
    order = ops_order_store.get_order(order_id, db_path=db_path)
    if not order:
        raise ValueError(f"Không tìm thấy đơn hàng #{order_id}")

    shipment = order.get("shipment")
    cancel_shipment_res = None

    if shipment and shipment.get("tracking_code"):
        prov_key = shipment.get("provider") or "ghn"
        provider = ops_shipping.get_shipping_provider(prov_key)
        settings = ops_shipping_store.load_shipping_settings()
        prov_config = settings.get("providers", {}).get(prov_key, {})
        cancel_shipment_res = provider.cancel_shipment(shipment["tracking_code"], prov_config)

        if shipment.get("id"):
            ops_order_store.update_shipment_status(
                shipment_id=shipment["id"],
                new_status="cancelled",
                description=f"Hủy đơn hàng: {reason or 'Yêu cầu từ nhân viên/khách'}",
                actor=actor,
                db_path=db_path,
            )

    updated_order = ops_order_store.update_order(
        order_id,
        {"status": "cancelled", "internal_notes": f"Lý do hủy: {reason or 'Không có'}"},
        actor=actor,
        db_path=db_path,
    )

    ops_order_store.record_audit_log(
        order_id=order_id,
        action="cancelled",
        actor=actor,
        details={"reason": reason, "shipment_cancelled": bool(cancel_shipment_res and cancel_shipment_res.get("ok"))},
        db_path=db_path,
    )

    return {
        "ok": True,
        "order": updated_order,
        "shipment_cancelled": cancel_shipment_res,
    }


def sync_shipment_status(
    order_id: str,
    actor: str = "staff",
    db_path: Optional[Any] = None,
) -> Dict[str, Any]:
    """Chủ động kiểm tra trạng thái vận đơn từ provider và ghi lại vào lịch sử."""
    order = ops_order_store.get_order(order_id, db_path=db_path)
    if not order:
        raise ValueError(f"Không tìm thấy đơn hàng #{order_id}")

    shipment = order.get("shipment")
    if not shipment or not shipment.get("tracking_code"):
        raise ValueError("Đơn hàng chưa có mã vận đơn để kiểm tra trạng thái.")

    prov_key = shipment.get("provider") or "ghn"
    provider = ops_shipping.get_shipping_provider(prov_key)
    if not hasattr(provider, "check_tracking_status"):
        return {
            "ok": False,
            "status": "unsupported_provider",
            "error": f"Đơn vị vận chuyển {provider.name} chưa hỗ trợ kiểm tra trạng thái chủ động.",
        }

    settings = ops_shipping_store.load_shipping_settings()
    prov_config = settings.get("providers", {}).get(prov_key, {})
    tracking_res = provider.check_tracking_status(shipment["tracking_code"], prov_config)
    if not tracking_res.get("ok"):
        ops_order_store.record_audit_log(
            order_id=order_id,
            action="shipment_sync_failed",
            actor=actor,
            details={
                "provider": prov_key,
                "tracking_code": shipment.get("tracking_code"),
                "error": tracking_res.get("error"),
                "status": tracking_res.get("status"),
            },
            db_path=db_path,
        )
        return tracking_res

    updated_shipment = ops_order_store.update_shipment_status(
        shipment_id=shipment["id"],
        new_status=tracking_res["status"],
        description=tracking_res.get("description"),
        location=tracking_res.get("location"),
        raw_payload=tracking_res.get("raw_response") or tracking_res,
        actor=actor,
        db_path=db_path,
    )

    return {
        "ok": True,
        "tracking": tracking_res,
        "shipment": updated_shipment,
        "order": ops_order_store.get_order(order_id, db_path=db_path),
    }


def handle_ghn_webhook_payload(payload: Dict[str, Any], db_path: Optional[Any] = None) -> Dict[str, Any]:
    """Xử lý webhook callback từ GHN để đồng bộ trạng thái vận đơn & đơn hàng tức thì."""
    provider = ops_shipping.get_shipping_provider("ghn")
    norm = provider.parse_webhook(payload)
    tracking_code = norm.get("tracking_code")

    if not tracking_code:
        return {"ok": False, "error": "Thiếu mã OrderCode / tracking_code trong webhook GHN"}

    shipment = ops_order_store.get_shipment_by_tracking(tracking_code, db_path=db_path)
    if not shipment:
        return {"ok": False, "error": f"Không tìm thấy vận đơn với mã {tracking_code}"}

    updated_shipment = ops_order_store.update_shipment_status(
        shipment_id=shipment["id"],
        new_status=norm["status"],
        description=norm.get("description"),
        location=norm.get("location"),
        raw_payload=payload,
        actor="ghn_webhook",
        db_path=db_path,
    )

    return {
        "ok": True,
        "tracking_code": tracking_code,
        "status": norm["status"],
        "shipment": updated_shipment,
    }
