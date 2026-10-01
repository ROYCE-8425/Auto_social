"""AI Sales Extraction Engine for Sèo Trum Ops Social Commerce.

Extracts structured order components from conversation threads:
- Customer name
- Phone number (VN standard)
- Delivery address (Street, ward, district, province)
- Products matched against real product catalog (no hallucinated products)
- Quantity, COD amount, customer notes
- Confidence score (0.0 to 1.0)
- Missing fields list (["phone", "address", "product"])
- Auto-generated follow-up questions for missing details
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import ops_order_store

# Regex chuẩn số điện thoại Việt Nam (10 chữ số)
VN_PHONE_RE = re.compile(r"(?:(?:\+84|84|0)[35789]\d{8})\b")

# Các từ khóa nhận diện địa chỉ giao hàng
ADDRESS_INDICATORS = [
    "số nhà", "ngõ", "ngách", "hẻm", "đường", "phố", "phường", "xã",
    "quận", "huyện", "thị xã", "thị trấn", "thành phố", "tỉnh",
    "ấp", "thôn", "xóm",
    "số nhà", "ngõ", "ngách", "hẻm", "đường", "phố", "phường", "xã",
    "quận", "huyện", "thị xã", "thị trấn", "thành phố", "tỉnh",
    "tp.", "q.", "h.", "p.", "x.", "ấp", "thôn", "xóm",
]

# Các từ khóa nhận diện ý định mua hàng
PURCHASE_INTENT_KEYWORDS = [
    "mua", "đặt", "lấy", "ship", "giao", "order", "gửi em", "cho mình",
    "cho anh", "cho chị", "chốt", "bán", "thanh toán", "cod", "lấy 1",
    "lấy 2", "cuốn", "cái", "bộ", "khóa học", "gói", "địa chỉ",
    "mua", "đặt", "lấy", "ship", "giao", "order", "gửi em", "cho mình",
    "cho anh", "cho chị", "chốt", "bán", "thanh toán", "cod", "lấy 1",
    "lấy 2", "cuốn", "cái", "bộ", "khoá học", "gói", "địa chỉ",
]


def extract_phone(text: str) -> Optional[str]:
    """Tìm số điện thoại hợp lệ đầu tiên trong văn bản."""
    if not text:
        return None
    # Xóa dấu chấm hoặc khoảng trắng xen giữa các chữ số: 0935.195.118 -> 0935195118
    normalized = re.sub(r"(\d)[\.\-\s](\d)", r"\1\2", text)
    match = VN_PHONE_RE.search(normalized)
    if match:
        p = match.group(0)
        if p.startswith("+84"):
            p = "0" + p[3:]
        elif p.startswith("84") and len(p) == 11:
            p = "0" + p[2:]
        return p
    return None


def extract_name(text: str, fallback_from_name: Optional[str] = None) -> Optional[str]:
    """Trích xuất tên người nhận từ nội dung tin nhắn hoặc dùng tên nick Facebook."""
    if not text:
        return fallback_from_name

    patterns = [
        r"(?:tên\s+(?:là|em là|mình là|của em là|anh là|chị là)|người\s+nhận:?|gửi\s+cho)\s+([A-ZÀ-Ỹa-zà-ỹ\s]{2,30})",
        r"(?:em\s+là|mình\s+là)\s+([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)*)",
    ]

    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            # Loại bỏ các từ thừa phổ biến
            candidate = re.sub(r"\b(nha|nhé|nhá|ạ|ơi|số|đt|sđt|địa|chỉ)\b.*", "", candidate, flags=re.IGNORECASE).strip()
            if len(candidate) >= 2 and len(candidate.split()) <= 5:
                return candidate.title()

    if fallback_from_name and fallback_from_name.strip():
        return fallback_from_name.strip()
    return None


def extract_address(text: str) -> Optional[str]:
    """Trích xuất địa chỉ nhận hàng từ tin nhắn nếu có chứa các chỉ dấu địa chỉ."""
    if not text:
        return None

    # 1. Tìm các mẫu câu trực tiếp: "giao về 123 Cầu Giấy...", "ship đến ...", "địa chỉ: ...", "về số 25..."
    direct_match = re.search(
        r"(?:giao\s+(?:về|đến|qua)|ship\s+(?:về|đến|qua)|địa\s+chỉ(?:\s+nhận|\s+là|:)?|gửi\s+(?:về|đến)|về\s+(?:số|địa\s+chỉ)?|đến\s+(?:số|địa\s+chỉ)?)\s*[:\s]*([^.\n;\?]+)",
        text,
        re.IGNORECASE,
    )
    if direct_match:
        candidate = direct_match.group(1).strip()
        clean_candidate = VN_PHONE_RE.sub("", candidate).strip()
        clean_candidate = re.sub(r"(?:sđt|sdt|đt|phone)\b.*", "", clean_candidate, flags=re.IGNORECASE).strip()
        clean_candidate = re.sub(r"\bnhé\s*(?:shop|em|bạn)?.*$", "", clean_candidate, flags=re.IGNORECASE).strip()
        clean_candidate = re.sub(r"^[-–,.:;\s]+|[-–,.:;\s]+$", "", clean_candidate)
        if len(clean_candidate) >= 8:
            return clean_candidate

    # 2. Tìm theo dòng chứa các từ khóa địa chỉ
    lines = text.split("\n")
    for line in lines:
        l_lower = line.lower()
        if any(ind in l_lower for ind in ADDRESS_INDICATORS):
            # Lọc bỏ phần số điện thoại nếu dính trong cùng dòng
            clean_line = VN_PHONE_RE.sub("", line).strip()
            clean_line = re.sub(r"(?:sđt|sdt|đt|phone):?\s*", "", clean_line, flags=re.IGNORECASE).strip()
            clean_line = re.sub(r"^[-–,.:;\s]+|[-–,.:;\s]+$", "", clean_line)
            if len(clean_line) >= 8:
                return clean_line

    # 3. Thử tìm theo cụm địa chỉ: bắt đầu từ số nhà hoặc đường
    pattern = r"((?:số\s+)?\d+[/0-9A-Za-z\-]*\s+(?:đường|phố|ngõ|ngách|hẻm|phường|xã|quận|huyện|tp|tỉnh)[^,\n\.]+(?:,[^,\n\.]+){1,4})"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        addr = match.group(1).strip()
        if len(addr) >= 10:
            return addr

    return None


def extract_quantity(text: str, default: int = 1) -> int:
    """Trích xuất số lượng hàng cần mua (ví dụ: '2 cái', '3 cuốn', 'sl: 2', 'x2')."""
    if not text:
        return default
    m = re.search(r"(?:x\s*|sl\s*:?\s*|số\s+lượng\s*:?\s*)(\d+)", text, re.IGNORECASE)
    if m:
        try:
            return max(1, int(m.group(1)))
        except ValueError:
            pass

    m2 = re.search(r"\b(\d+)\s*(?:cái|cuốn|bộ|gói|combo|chiếc|quyển|khoá)\b", text, re.IGNORECASE)
    if m2:
        try:
            return max(1, int(m2.group(1)))
        except ValueError:
            pass
    return default


def match_product_against_catalog(text: str, catalog: List[Dict[str, Any]]) -> tuple[Optional[Dict[str, Any]], bool]:
    """So khớp văn bản tin nhắn với danh mục sản phẩm thật (Catalog).
    Kiểm tra SKU, biến thể, Alias/từ khóa khách hay gọi, và tên sản phẩm.
    Tuyệt đối không bịa sản phẩm nếu không tìm thấy khớp trong catalog được cấp.
    Trả về (matched_item, is_matched).
    """
    if not text or not catalog:
        return None, False

    t_lower = text.lower()

    # 1. So khớp theo SKU sản phẩm chính xác
    for prod in catalog:
        sku = (prod.get("sku") or "").lower().strip()
        if sku and sku in t_lower:
            return prod, True

    # 2. So khớp theo SKU hoặc tên biến thể (Variants)
    for prod in catalog:
        for vr in prod.get("variants", []):
            v_sku = (vr.get("sku") or "").lower().strip()
            v_title = (vr.get("title") or "").lower().strip()
            if (v_sku and v_sku in t_lower) or (v_title and len(v_title) >= 3 and v_title in t_lower):
                matched = dict(prod)
                if vr.get("price") and vr["price"] > 0:
                    matched["price"] = vr["price"]
                matched["selected_variant"] = vr
                return matched, True

    # 3. So khớp theo Alias / Từ khóa khách hay gọi đã cấu hình
    for prod in catalog:
        aliases = prod.get("aliases") or []
        for al in aliases:
            al_clean = str(al).lower().strip()
            if al_clean and len(al_clean) >= 2 and al_clean in t_lower:
                return prod, True

    # 4. So khớp theo toàn bộ tên sản phẩm (substring match)
    for prod in catalog:
        p_name = (prod.get("name") or "").lower().strip()
        if p_name and len(p_name) >= 4 and p_name in t_lower:
            return prod, True

    # 5. So khớp theo từ khóa đặc trưng (quy tắc phổ biến)
    keyword_rules = [
        (["mos", "word", "excel văn phòng"], "SKU-MOS-01"),
        (["powerbi", "power bi", "dashboard", "dữ liệu"], "SKU-PBI-02"),
        (["sách", "giáo trình", "thủ thuật excel"], "SKU-BOOK-03"),
        (["bàn phím", "bàn phím cơ", "silent office"], "SKU-KEY-04"),
        (["chuột", "chuột không dây", "silent click", "chuột công thái học"], "SKU-MOU-05"),
    ]

    for kws, sku_target in keyword_rules:
        if any(kw in t_lower for kw in kws):
            target_prod = next((p for p in catalog if (p.get("sku") or "").upper() == sku_target), None)
            if target_prod:
                return target_prod, True

    # 6. So khớp một phần tên sản phẩm (độ tương đồng từ khóa >= 50%)
    for prod in catalog:
        name_words = [w for w in (prod.get("name") or "").lower().split() if len(w) > 3]
        matches = sum(1 for w in name_words if w in t_lower)
        if len(name_words) > 0 and (matches / len(name_words)) >= 0.5:
            return prod, True

    return None, False


def generate_followup_question(missing_fields: List[str], customer_name: Optional[str] = None) -> str:
    """Tự động sinh câu hỏi bổ sung lịch sự theo văn phong chăm sóc khách hàng Việt Nam."""
    greeting = f"Dạ {customer_name or 'anh/chị'}"

    has_phone = "phone" in missing_fields
    has_address = "address" in missing_fields
    has_product = "product" in missing_fields

    if has_phone and has_address:
        return f"{greeting} cho em xin số điện thoại và địa chỉ nhận hàng cụ thể để bên em lên đơn giao tận nơi cho mình nhé ạ!"
    elif has_phone:
        return f"{greeting} cho em xin số điện thoại liên hệ để bưu tá giao hàng gọi cho mình khi tới nơi nhé ạ!"
    elif has_address:
        return f"{greeting} cho em xin địa chỉ nhận hàng cụ thể (số nhà, tên đường, phường/xã, quận/huyện, tỉnh/thành) để bên em gửi đơn sớm nhất nhé ạ!"
    elif has_product:
        return f"{greeting} đang quan tâm đến sản phẩm hoặc gói khóa học nào để bên em báo giá ưu đãi và chuẩn bị hàng cho mình ạ?"
    else:
        return f"{greeting} ơi, bên em đã ghi nhận đủ thông tin đơn hàng. Em gửi đơn luôn cho mình nhé ạ!"


def extract_order_from_thread(
    messages: List[Dict[str, Any]],
    catalog: Optional[List[Dict[str, Any]]] = None,
    customer_name: Optional[str] = None,
    page_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    crm_id: Optional[str] = None,
    db_path: Optional[Any] = None,
) -> Dict[str, Any]:
    """Phân tích toàn bộ chuỗi hội thoại để trích xuất đơn hàng Social Commerce.

    Trả về:
    - customer_name, customer_phone, shipping_address
    - items (kèm SKU, giá thật từ catalog)
    - total_amount, cod_amount
    - ai_confidence (0.0 -> 1.0)
    - missing_fields (['phone', 'address', 'product'])
    - status ('ready_to_confirm' | 'needs_info' | 'draft')
    - followup_question
    """
    if catalog is None:
        catalog = ops_order_store.list_products(db_path=db_path, page_id=page_id, active_only=True, include_details=True)

    # Ghép văn bản từ các tin nhắn của khách hàng
    user_texts: list[str] = []
    full_thread_texts: list[str] = []
    for msg in messages:
        body = str(msg.get("body") or msg.get("text") or msg.get("message") or "").strip()
        if not body:
            continue
        full_thread_texts.append(body)
        sender = str(msg.get("sender") or msg.get("kind") or "").lower()
        if sender in ("user", "customer", "from_user", "echo_user"):
            user_texts.append(body)

    combined_user_text = "\n".join(user_texts)
    combined_all_text = "\n".join(full_thread_texts)

    # Nếu không phân tách được sender, dùng toàn bộ thread
    search_text = combined_user_text if user_texts else combined_all_text

    # 1. Trích xuất thông tin liên hệ & địa chỉ
    extracted_phone = extract_phone(search_text) or extract_phone(combined_all_text)
    extracted_name = extract_name(search_text, fallback_from_name=customer_name)
    extracted_address = extract_address(search_text) or extract_address(combined_all_text)

    # 2. Trích xuất sản phẩm & số lượng
    qty = extract_quantity(search_text, default=1)
    matched_prod, is_matched = match_product_against_catalog(search_text, catalog)
    if not is_matched:
        # Thử tìm trên toàn thread
        matched_prod, is_matched = match_product_against_catalog(combined_all_text, catalog)

    items = []
    total_amount = 0

    if is_matched and matched_prod:
        price = int(matched_prod.get("price") or 0)
        item_total = price * qty
        items.append({
            "product_id": matched_prod.get("id"),
            "sku": matched_prod.get("sku"),
            "name": matched_prod.get("name"),
            "quantity": qty,
            "price": price,
            "total": item_total,
        })
        total_amount = item_total
    else:
        # Kiểm tra xem khách có ý định mua sản phẩm nào nhưng không match catalog không
        has_buy_intent = any(kw in search_text.lower() for kw in PURCHASE_INTENT_KEYWORDS)
        if has_buy_intent:
            items.append({
                "product_id": None,
                "sku": "UNMATCHED",
                "name": "Sản phẩm khách yêu cầu (Cần nhân viên xác nhận)",
                "quantity": qty,
                "price": 0,
                "total": 0,
            })

    # 3. Tính toán Missing Fields & Confidence
    missing_fields: List[str] = []
    confidence = 1.0

    if not extracted_phone:
        missing_fields.append("phone")
        confidence -= 0.35

    if not extracted_address or len(extracted_address) < 8:
        missing_fields.append("address")
        confidence -= 0.35

    if not is_matched:
        missing_fields.append("product")
        confidence -= 0.25

    confidence = max(0.05, min(1.0, round(confidence, 2)))

    # 4. Xác định trạng thái đề xuất
    if missing_fields:
        status = "needs_info"
    elif not is_matched:
        status = "draft"  # Cần nhân viên duyệt SKU
    else:
        status = "ready_to_confirm"  # Đủ SĐT, địa chỉ và SKU hợp lệ

    # 5. Sinh câu hỏi bổ sung
    followup_q = generate_followup_question(missing_fields, customer_name=extracted_name)

    return {
        "ok": True,
        "crm_id": crm_id,
        "page_id": page_id,
        "thread_id": thread_id,
        "customer_name": extracted_name or "Khách hàng",
        "customer_phone": extracted_phone,
        "shipping_address": extracted_address,
        "items": items,
        "total_amount": total_amount,
        "cod_amount": total_amount,  # Tiêu chuẩn COD = tổng tiền hàng
        "shipping_fee": 0,
        "payment_method": "cod",
        "ai_confidence": confidence,
        "missing_fields": missing_fields,
        "status": status,
        "followup_question": followup_q,
        "is_product_matched": is_matched,
    }
