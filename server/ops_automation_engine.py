"""Automation Case Engine for Sèo Trum Ops (Javis Social Commerce).

Processes incoming social messages/inbox threads and executes rule-based automation:
1. Detects customer intent (price, stock, faq, purchase, missing info).
2. Matches products strictly against the current page's catalog.
3. Evaluates 4 automation levels (0: Observe, 1: Draft, 2: Safe reply, 3: Full auto-order & GHN).
4. Handles safety constraints: Global Kill Switch, cooldowns, max COD limits, staff approval.
5. Queues all outbound messages into ops_outbox_messages.
6. Records complete audit trails in ops_automation_runs.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import config
import ops_order_store
import ops_orders
import ops_sales_extraction
import ops_shipping_store


# Key-value file or setting for Global Automation Kill Switch
KILL_SWITCH_FILE = config.STATE_DIR / "ops_automation_kill_switch.json"


def get_kill_switch(db_path: Optional[Any] = None) -> bool:
    """Kiểm tra xem Global Kill Switch có đang bật không.
    Nếu bật, mọi hành động gửi tin nhắn hoặc tạo vận đơn tự động đều bị dừng ngay lập tức.
    """
    # 1. Kiểm tra file riêng
    if KILL_SWITCH_FILE.exists():
        try:
            data = json.loads(KILL_SWITCH_FILE.read_text(encoding="utf-8"))
            if data.get("kill_switch") is not None:
                return bool(data.get("kill_switch"))
        except Exception:
            pass

    # 2. Kiểm tra trong shipping settings (nếu có)
    try:
        settings = ops_shipping_store.load_shipping_settings()
        if settings.get("automation", {}).get("kill_switch"):
            return True
    except Exception:
        pass

    return False


def set_kill_switch(enabled: bool, db_path: Optional[Any] = None) -> bool:
    """Bật / tắt Global Kill Switch."""
    KILL_SWITCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    KILL_SWITCH_FILE.write_text(json.dumps({"kill_switch": bool(enabled), "updated_at": time.time()}), encoding="utf-8")
    
    # Đồng bộ sang shipping settings
    try:
        settings = ops_shipping_store.load_shipping_settings()
        if "automation" not in settings:
            settings["automation"] = {}
        settings["automation"]["kill_switch"] = bool(enabled)
        ops_shipping_store.save_shipping_settings(settings)
    except Exception:
        pass

    return bool(enabled)


# ============================================================
# Intent Detection
# ============================================================

PRICE_KEYWORDS = [
    "giá", "nhiêu", "bao nhiêu", "bao tiền", "chi phí", "giá cả",
    "báo giá", "mấy đồng", "xin giá", "giá sao",
    "giá", "nhiêu", "bao nhiêu", "bn", "bao tiền", "chi phí", "giá cả",
    "báo giá", "cost", "price", "mấy đồng", "xin giá", "giá sao",
]

STOCK_KEYWORDS = [
    "còn hàng", "hết hàng", "còn không", "còn k", "còn ko", "có sẵn",
    "còn màu", "còn size", "hết chưa", "còn mẫu",
    "còn hàng", "hết hàng", "còn không", "còn k", "còn ko", "có sẵn",
    "còn màu", "còn size", "hết chưa", "còn mẫu",
]

FAQ_KEYWORDS = [
    "bảo hành", "ở đâu", "địa chỉ shop", "ship bao lâu", "phí ship",
    "đổi trả", "hướng dẫn", "thời gian nhận", "giao trong ngày",
    "bảo hành", "ở đâu", "địa chỉ shop", "ship bao lâu", "phí ship",
    "đổi trả", "hướng dẫn", "thời gian nhận", "giao trong ngày",
]


def detect_intent(text: str) -> str:
    """Nhận diện ý định chính của khách hàng từ tin nhắn."""
    if not text:
        return "general"
    t = text.lower()

    # Kiểm tra ý định mua hàng / đặt hàng trước
    if any(kw in t for kw in ops_sales_extraction.PURCHASE_INTENT_KEYWORDS):
        return "purchase_intent"

    # Kiểm tra hỏi giá
    if any(kw in t for kw in PRICE_KEYWORDS):
        return "price_inquiry"

    # Kiểm tra hỏi tồn kho
    if any(kw in t for kw in STOCK_KEYWORDS):
        return "stock_inquiry"

    # Kiểm tra FAQ
    if any(kw in t for kw in FAQ_KEYWORDS):
        return "faq_inquiry"

    return "general"


def _looks_mojibake(text: str) -> bool:
    return any(marker in text for marker in ("Ã", "Ä", "Æ", "áº", "á»"))


def _repair_mojibake(text: str) -> str:
    if not _looks_mojibake(text):
        return text
    try:
        return text.encode("latin1").decode("utf-8")
    except Exception:
        return text


def _template_value(value: Any, repair_mode: bool) -> str:
    text = str(value) if value is not None else ""
    if not repair_mode:
        return text
    try:
        return text.encode("utf-8").decode("latin1")
    except Exception:
        return text


def format_template(template: str, context: Dict[str, Any]) -> str:
    """Thay thế các biến động trong message_template an toàn."""
    repair_mode = _looks_mojibake(template)
    res = template
    for k, v in context.items():
        placeholder = "{" + k + "}"
        if placeholder in res:
            res = res.replace(placeholder, _template_value(v, repair_mode))
    res = res.strip()
    return _repair_mojibake(res) if repair_mode else res


def check_cooldown(thread_id: str, case_type: str, cooldown_seconds: int, db_path: Optional[Any] = None) -> bool:
    """Kiểm tra xem case này đã vừa chạy cho thread_id trong khoảng cooldown_seconds chưa.
    Trả về True nếu còn trong thời gian cooldown (nên bỏ qua).
    """
    if cooldown_seconds <= 0 or not thread_id:
        return False
    runs = ops_order_store.list_automation_runs(thread_id=thread_id, limit=5, db_path=db_path)
    now = time.time()
    for r in runs:
        if r.get("case_type") == case_type and r.get("status") in ("sent", "success", "executed"):
            if now - r.get("created_at", 0) < cooldown_seconds:
                return True
    return False


# ============================================================
# Core Pipeline Execution
# ============================================================

def evaluate_and_run(
    thread_id: str,
    page_id: str,
    messages: List[Dict[str, Any]],
    channel: str = "*",
    customer_info: Optional[Dict[str, Any]] = None,
    db_path: Optional[Any] = None,
    actor: str = "javis_automation",
) -> Dict[str, Any]:
    """Quy trình tự động hóa toàn diện từ lúc nhận tin nhắn đến chốt đơn / tạo vận đơn."""
    init_res: Dict[str, Any] = {
        "ok": True,
        "thread_id": thread_id,
        "page_id": page_id,
        "channel": channel,
        "cases_evaluated": [],
        "cases_executed": [],
        "outbox_messages": [],
        "order": None,
        "decision": "completed",
        "kill_switch_active": False,
    }

    # 1. Kiểm tra Global Kill Switch
    if get_kill_switch(db_path=db_path):
        init_res["kill_switch_active"] = True
        init_res["decision"] = "skipped_kill_switch"
        init_res["status"] = "skipped"
        init_res["reason"] = "kill_switch_active"
        init_res["case"] = "global_kill_switch"
        ops_order_store.record_automation_run(
            case_type="global_kill_switch",
            decision_reason="Global Automation Kill Switch is ON. All outbound actions aborted.",
            status="skipped",
            thread_id=thread_id,
            page_id=page_id,
            db_path=db_path,
        )
        return init_res

    # Ghép chuỗi văn bản của khách hàng
    user_texts: list[str] = []
    full_texts: list[str] = []
    for m in messages:
        body = str(m.get("body") or m.get("text") or "").strip()
        if not body:
            continue
        full_texts.append(body)
        sender = str(m.get("sender") or m.get("kind") or "").lower()
        if sender in ("user", "customer", "from_user", "echo_user"):
            user_texts.append(body)

    combined_text = "\n".join(user_texts) if user_texts else "\n".join(full_texts)
    if not combined_text:
        return init_res

    latest_text = user_texts[-1] if user_texts else full_texts[-1]
    detected_intent = detect_intent(latest_text)

    # 2. Nạp danh mục sản phẩm gắn CHẶT với page_id hiện tại
    page_catalog = ops_order_store.list_products(
        db_path=db_path,
        page_id=page_id,
        channel=channel,
        active_only=True,
        include_details=True,
    )

    # Trích xuất dữ liệu bán hàng
    extracted = ops_sales_extraction.extract_order_from_thread(
        messages=messages,
        catalog=page_catalog,
        customer_name=(customer_info.get("name") if customer_info else None),
        page_id=page_id,
        thread_id=thread_id,
        crm_id=(customer_info.get("crm_id") if customer_info else None),
        db_path=db_path,
    )

    is_product_matched = bool(extracted.get("is_product_matched"))
    matched_item = extracted["items"][0] if (extracted.get("items") and is_product_matched) else None
    customer_name = extracted.get("customer_name") or (customer_info.get("name") if customer_info else "anh/chị")
    phone = extracted.get("customer_phone")
    address = extracted.get("shipping_address")
    confidence = float(extracted.get("ai_confidence") or 0.0)
    missing_fields = extracted.get("missing_fields") or []

    # Helper tạo ngữ cảnh tin nhắn
    context = {
        "customer_name": customer_name,
        "product_name": matched_item["name"] if matched_item else "sản phẩm",
        "price": f"{matched_item['price']:,}đ" if matched_item else "liên hệ",
        "phone": phone or "",
        "address": address or "",
        "order_id": "",
        "tracking_code": "",
        "carrier": "GHN",
    }

    # ============================================================
    # CASE 1: BÁO GIÁ SẢN PHẨM (price_reply)
    # ============================================================
    rule_price = ops_order_store.get_automation_rule("price_reply", page_id=page_id, channel=channel, db_path=db_path)
    if rule_price and rule_price.get("enabled"):
        init_res["cases_evaluated"].append("price_reply")
        # Kiểm tra xem có hỏi giá không
        is_asking_price = detected_intent == "price_inquiry" or any(kw in latest_text.lower() for kw in PRICE_KEYWORDS)
        if is_asking_price:
            if rule_price.get("require_product_match") and not is_product_matched:
                ops_order_store.record_automation_run(
                    case_type="price_reply",
                    decision_reason="Customer asked price but product is not matched in page catalog.",
                    status="requires_review",
                    thread_id=thread_id,
                    page_id=page_id,
                    db_path=db_path,
                )
            elif check_cooldown(thread_id, "price_reply", rule_price.get("cooldown_seconds", 30), db_path=db_path):
                ops_order_store.record_automation_run(
                    case_type="price_reply",
                    decision_reason="Price reply in cooldown period.",
                    status="skipped",
                    thread_id=thread_id,
                    page_id=page_id,
                    db_path=db_path,
                )
            elif rule_price.get("level", 2) >= 2:
                tpl = rule_price.get("message_template") or (
                    "Dạ {customer_name}, sản phẩm {product_name} bên em đang có giá ưu đãi là {price} ạ. "
                    "Mình cho em xin số điện thoại và địa chỉ để em hỗ trợ giao tận nơi cho mình nhé!"
                )
                body = format_template(tpl, context)
                msg = ops_order_store.queue_outbox_message(
                    body=body,
                    thread_id=thread_id,
                    page_id=page_id,
                    channel=channel,
                    recipient_id=customer_info.get("from_id") if customer_info else None,
                    db_path=db_path,
                )
                init_res["outbox_messages"].append(msg)
                init_res["cases_executed"].append("price_reply")
                ops_order_store.record_automation_run(
                    case_type="price_reply",
                    decision_reason=f"Auto replied price for product '{matched_item['name'] if matched_item else 'unmatched'}'.",
                    status="sent",
                    thread_id=thread_id,
                    page_id=page_id,
                    payload={"message_id": msg["id"], "price": matched_item.get("price") if matched_item else None},
                    db_path=db_path,
                )

    # ============================================================
    # CASE 2: HỎI TỒN KHO (stock_reply)
    # ============================================================
    rule_stock = ops_order_store.get_automation_rule("stock_reply", page_id=page_id, channel=channel, db_path=db_path)
    if rule_stock and rule_stock.get("enabled"):
        init_res["cases_evaluated"].append("stock_reply")
        if detected_intent == "stock_inquiry" or any(kw in latest_text.lower() for kw in STOCK_KEYWORDS):
            if is_product_matched and matched_item:
                prod_data = ops_order_store.get_product(matched_item.get("product_id") or "", db_path=db_path)
                stock_cnt = prod_data.get("stock", 0) if prod_data else 0
                if stock_cnt > 0:
                    tpl = rule_stock.get("message_template") or (
                        "Dạ {customer_name}, sản phẩm {product_name} hiện bên em ĐANG CÒN HÀNG sẵn trong kho ạ. "
                        "Anh/chị muốn đặt hàng luôn hôm nay bên em gửi bưu tá giao sớm nhé!"
                    )
                else:
                    tpl = "Dạ {customer_name}, sản phẩm {product_name} hiện đang tạm hết hàng ạ. Nhân viên bên em sẽ liên hệ lại báo khi hàng về nhé ạ!"
                body = format_template(tpl, context)
                msg = ops_order_store.queue_outbox_message(
                    body=body,
                    thread_id=thread_id,
                    page_id=page_id,
                    channel=channel,
                    db_path=db_path,
                )
                init_res["outbox_messages"].append(msg)
                init_res["cases_executed"].append("stock_reply")
                ops_order_store.record_automation_run(
                    case_type="stock_reply",
                    decision_reason=f"Replied stock status (stock={stock_cnt}) for {matched_item['name']}.",
                    status="sent",
                    thread_id=thread_id,
                    page_id=page_id,
                    db_path=db_path,
                )

    # ============================================================
    # CASE 3: HỎI THÔNG TIN CÒN THIẾU (ask_missing_phone / ask_missing_address)
    # ============================================================
    has_buy_intent = (
        detected_intent == "purchase_intent"
        or any(kw in latest_text.lower() for kw in ops_sales_extraction.PURCHASE_INTENT_KEYWORDS)
        or any(kw in combined_text.lower() for kw in ("đặt", "mua", "ship", "gửi cho", "chốt đơn", "lấy"))
    )

    if has_buy_intent and not is_product_matched:
        init_res["decision"] = "requires_review"
        init_res["cases_evaluated"].append("unmatched_product")
        ops_order_store.record_automation_run(
            case_type="unmatched_product",
            decision_reason="Customer expressed buy intent but product is UNMATCHED in page catalog. Handoff to staff.",
            status="requires_review",
            thread_id=thread_id,
            page_id=page_id,
            db_path=db_path,
        )

    if has_buy_intent and is_product_matched:
        # Nếu thiếu SĐT
        if "phone" in missing_fields:
            rule_phone = ops_order_store.get_automation_rule("ask_missing_phone", page_id=page_id, channel=channel, db_path=db_path)
            if rule_phone and rule_phone.get("enabled") and rule_phone.get("level", 2) >= 2:
                init_res["cases_evaluated"].append("ask_missing_phone")
                if not check_cooldown(thread_id, "ask_missing_phone", rule_phone.get("cooldown_seconds", 30), db_path=db_path):
                    tpl = rule_phone.get("message_template") or (
                        "Dạ {customer_name} cho em xin số điện thoại để bên em lưu thông tin tạo đơn giao hàng tận nơi cho mình nhé ạ!"
                    )
                    body = format_template(tpl, context)
                    msg = ops_order_store.queue_outbox_message(body=body, thread_id=thread_id, page_id=page_id, channel=channel, db_path=db_path)
                    init_res["outbox_messages"].append(msg)
                    init_res["cases_executed"].append("ask_missing_phone")
                    ops_order_store.record_automation_run(
                        case_type="ask_missing_phone",
                        decision_reason="Customer expressed buy intent but phone is missing. Asked for phone.",
                        status="sent",
                        thread_id=thread_id,
                        page_id=page_id,
                        db_path=db_path,
                    )

        # Nếu có SĐT nhưng thiếu địa chỉ
        elif "address" in missing_fields:
            rule_addr = ops_order_store.get_automation_rule("ask_missing_address", page_id=page_id, channel=channel, db_path=db_path)
            if rule_addr and rule_addr.get("enabled") and rule_addr.get("level", 2) >= 2:
                init_res["cases_evaluated"].append("ask_missing_address")
                if not check_cooldown(thread_id, "ask_missing_address", rule_addr.get("cooldown_seconds", 30), db_path=db_path):
                    tpl = rule_addr.get("message_template") or (
                        "Dạ {customer_name} cho em xin địa chỉ nhận hàng cụ thể (số nhà, tên đường, phường/xã, quận/huyện, tỉnh/thành) để bên em gửi bưu tá GHN giao sớm nhất cho mình nhé ạ!"
                    )
                    body = format_template(tpl, context)
                    msg = ops_order_store.queue_outbox_message(body=body, thread_id=thread_id, page_id=page_id, channel=channel, db_path=db_path)
                    init_res["outbox_messages"].append(msg)
                    init_res["cases_executed"].append("ask_missing_address")
                    ops_order_store.record_automation_run(
                        case_type="ask_missing_address",
                        decision_reason="Customer provided phone but address is missing. Asked for address.",
                        status="sent",
                        thread_id=thread_id,
                        page_id=page_id,
                        db_path=db_path,
                    )

    # ============================================================
    # CASE 4: TẠO ĐƠN HÀNG (create_order_draft)
    # ============================================================
    rule_draft = ops_order_store.get_automation_rule("create_order_draft", page_id=page_id, channel=channel, db_path=db_path)
    created_order = None

    if has_buy_intent and rule_draft and rule_draft.get("enabled") and rule_draft.get("level", 1) >= 1:
        init_res["cases_evaluated"].append("create_order_draft")

        # AN TOÀN TUYỆT ĐỐI: Không tạo đơn nếu sản phẩm chưa khớp danh mục
        if not is_product_matched:
            init_res["decision"] = "requires_review"
            init_res["cases_evaluated"].append("unmatched_product")
            ops_order_store.record_automation_run(
                case_type="create_order_draft",
                decision_reason="Cannot create auto order: Product is UNMATCHED in catalog for this page.",
                status="requires_review",
                thread_id=thread_id,
                page_id=page_id,
                db_path=db_path,
            )
        else:
            # Tạo đơn nháp hoặc đơn ready_to_confirm
            created_order = ops_order_store.create_order(
                crm_id=extracted.get("crm_id"),
                customer_name=customer_name,
                customer_phone=phone,
                shipping_address=address,
                page_id=page_id,
                thread_id=thread_id,
                items=extracted.get("items"),
                cod_amount=extracted.get("cod_amount"),
                shipping_fee=0,
                ai_confidence=confidence,
                missing_fields=missing_fields,
                status=extracted.get("status", "draft"),
                source="inbox_auto_engine",
                actor=actor,
                db_path=db_path,
            )
            init_res["order"] = created_order
            init_res["cases_executed"].append("create_order_draft")
            ops_order_store.record_automation_run(
                case_type="create_order_draft",
                decision_reason=f"Created order #{created_order['id']} with status '{created_order['status']}'.",
                status="success",
                order_id=created_order["id"],
                thread_id=thread_id,
                page_id=page_id,
                payload={"order_id": created_order["id"], "total": created_order["total_amount"]},
                db_path=db_path,
            )

    # ============================================================
    # CASE 5: TỰ ĐỘNG XÁC NHẬN ĐƠN (auto_confirm_order)
    # ============================================================
    rule_confirm = ops_order_store.get_automation_rule("auto_confirm_order", page_id=page_id, channel=channel, db_path=db_path)
    if (
        created_order
        and created_order["status"] == "ready_to_confirm"
        and rule_confirm
        and rule_confirm.get("enabled")
        and rule_confirm.get("level", 3) >= 3
    ):
        init_res["cases_evaluated"].append("auto_confirm_order")
        min_conf = float(rule_confirm.get("min_confidence", 0.9))
        max_cod = int(rule_confirm.get("max_cod_amount", 3000000))
        req_staff = bool(rule_confirm.get("require_staff_approval", False))

        if confidence < min_conf:
            ops_order_store.record_automation_run(
                case_type="auto_confirm_order",
                decision_reason=f"Confidence {confidence} < min {min_conf}. Requires staff review.",
                status="requires_review",
                order_id=created_order["id"],
                thread_id=thread_id,
                page_id=page_id,
                db_path=db_path,
            )
        elif created_order["total_amount"] > max_cod:
            ops_order_store.record_automation_run(
                case_type="auto_confirm_order",
                decision_reason=f"Order amount {created_order['total_amount']} > max COD {max_cod}. Requires staff review.",
                status="requires_review",
                order_id=created_order["id"],
                thread_id=thread_id,
                page_id=page_id,
                db_path=db_path,
            )
        elif req_staff:
            ops_order_store.record_automation_run(
                case_type="auto_confirm_order",
                decision_reason="Rule requires staff approval. Order kept in ready_to_confirm.",
                status="requires_review",
                order_id=created_order["id"],
                thread_id=thread_id,
                page_id=page_id,
                db_path=db_path,
            )
        else:
            # Xác nhận đơn thành công
            ops_order_store.update_order(created_order["id"], {"status": "confirmed"}, actor="auto_confirm_engine", db_path=db_path)
            created_order["status"] = "confirmed"
            init_res["cases_executed"].append("auto_confirm_order")
            ops_order_store.record_automation_run(
                case_type="auto_confirm_order",
                decision_reason=f"Order #{created_order['id']} auto confirmed.",
                status="success",
                order_id=created_order["id"],
                thread_id=thread_id,
                page_id=page_id,
                db_path=db_path,
            )

    # ============================================================
    # CASE 6: TỰ ĐỘNG TẠO VẬN ĐƠN GHN (auto_create_shipment)
    # ============================================================
    rule_ship = ops_order_store.get_automation_rule("auto_create_shipment", page_id=page_id, channel=channel, db_path=db_path)
    shipment_created_info = None

    if (
        created_order
        and created_order["status"] == "confirmed"
        and rule_ship
        and rule_ship.get("enabled")
        and rule_ship.get("level", 3) >= 3
    ):
        init_res["cases_evaluated"].append("auto_create_shipment")
        settings = ops_shipping_store.load_shipping_settings()
        ghn_cfg = settings.get("providers", {}).get("ghn", {})

        # Phải cấu hình GHN mới tạo vận đơn
        if not ghn_cfg.get("token") or not ghn_cfg.get("shop_id"):
            ops_order_store.record_automation_run(
                case_type="auto_create_shipment",
                decision_reason="GHN provider is not configured. Skipped shipment creation.",
                status="skipped",
                order_id=created_order["id"],
                thread_id=thread_id,
                page_id=page_id,
                db_path=db_path,
            )
        else:
            try:
                ship_res = ops_orders.create_shipment_for_order(
                    order_id=created_order["id"],
                    provider_id="ghn",
                    actor="auto_shipment_engine",
                    db_path=db_path,
                )
                if ship_res.get("ok"):
                    shipment_created_info = ship_res.get("shipment")
                    init_res["cases_executed"].append("auto_create_shipment")
                    ops_order_store.record_automation_run(
                        case_type="auto_create_shipment",
                        decision_reason=f"Auto created GHN shipment #{shipment_created_info.get('id')} tracking: {shipment_created_info.get('tracking_code')}.",
                        status="success",
                        order_id=created_order["id"],
                        thread_id=thread_id,
                        page_id=page_id,
                        payload=shipment_created_info,
                        db_path=db_path,
                    )
                else:
                    ops_order_store.record_automation_run(
                        case_type="auto_create_shipment",
                        decision_reason=f"Failed to create shipment: {ship_res.get('error')}",
                        status="failed",
                        order_id=created_order["id"],
                        thread_id=thread_id,
                        page_id=page_id,
                        db_path=db_path,
                    )
            except Exception as exc:
                ops_order_store.record_automation_run(
                    case_type="auto_create_shipment",
                    decision_reason=f"Exception creating shipment: {exc}",
                    status="failed",
                    order_id=created_order["id"],
                    thread_id=thread_id,
                    page_id=page_id,
                    db_path=db_path,
                )

    # ============================================================
    # CASE 7: GỬI MÃ VẬN ĐƠN CHO KHÁCH (send_tracking_code)
    # ============================================================
    rule_tracking = ops_order_store.get_automation_rule("send_tracking_code", page_id=page_id, channel=channel, db_path=db_path)
    if (
        shipment_created_info
        and shipment_created_info.get("tracking_code")
        and rule_tracking
        and rule_tracking.get("enabled")
        and rule_tracking.get("level", 3) >= 3
    ):
        init_res["cases_evaluated"].append("send_tracking_code")
        context["order_id"] = created_order["id"] if created_order else ""
        context["tracking_code"] = shipment_created_info.get("tracking_code")
        context["carrier"] = shipment_created_info.get("provider", "GHN").upper()

        tpl = rule_tracking.get("message_template") or (
            "Dạ {customer_name}, đơn hàng #{order_id} của mình đã được tạo vận đơn thành công qua {carrier} "
            "với mã vận đơn: {tracking_code}. Bưu tá sẽ liên hệ giao hàng sớm cho mình nhé ạ!"
        )
        body = format_template(tpl, context)
        msg = ops_order_store.queue_outbox_message(body=body, thread_id=thread_id, page_id=page_id, channel=channel, db_path=db_path)
        init_res["outbox_messages"].append(msg)
        init_res["cases_executed"].append("send_tracking_code")
        ops_order_store.record_automation_run(
            case_type="send_tracking_code",
            decision_reason=f"Sent tracking code {context['tracking_code']} to customer.",
            status="sent",
            order_id=created_order["id"] if created_order else None,
            thread_id=thread_id,
            page_id=page_id,
            db_path=db_path,
        )

    # Cập nhật kết quả đơn hàng mới nhất
    if created_order:
        init_res["order"] = ops_order_store.get_order(created_order["id"], db_path=db_path)
        init_res["order_id"] = created_order["id"]

    if shipment_created_info and shipment_created_info.get("tracking_code"):
        init_res["tracking_code"] = shipment_created_info["tracking_code"]

    primary_case = (
        init_res["cases_executed"][-1]
        if init_res["cases_executed"]
        else (init_res["cases_evaluated"][-1] if init_res["cases_evaluated"] else "none")
    )
    init_res["case"] = primary_case
    init_res["status"] = (
        "success"
        if init_res["cases_executed"]
        else ("requires_review" if init_res.get("decision") == "requires_review" else "none")
    )
    first_outbox = init_res["outbox_messages"][0] if init_res["outbox_messages"] else None
    init_res["reply_text"] = (first_outbox.get("body") or first_outbox.get("message_text") or "") if first_outbox else ""
    init_res["product_sku"] = matched_item.get("sku") if matched_item else None

    return init_res
