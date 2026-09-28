# -*- coding: utf-8 -*-
"""Lead Scoring Engine & Next Best Action for Javis Ops.

Phân tích hội thoại khách hàng, tính toán điểm độ nóng (Hot/Warm/Cold),
xác định Hành động tiếp theo tối ưu (Next Best Action) và phân loại
cấp độ an toàn (Human Approval Risk Level).
"""
from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional, Tuple


# ==========================================
# 1. SCORING WEIGHTS & CRITERIA
# ==========================================
INTENT_WEIGHTS = {
    "price_enquiry": 20,       # Hỏi giá, học phí, chi phí
    "phone_provided": 35,      # Để lại số điện thoại liên hệ
    "warranty_policy": 15,     # Hỏi cam kết đầu ra, bảo hành, đổi trả
    "address_schedule": 15,    # Hỏi địa chỉ cơ sở, lịch học, lịch khai giảng
    "payment_method": 25,      # Hỏi số tài khoản, chuyển khoản, đặt cọc
    "deep_engagement": 10,     # Tương tác sâu (trên 3 lượt tin nhắn)
}

# Regex nhận diện số điện thoại Việt Nam
PHONE_REGEX = re.compile(r"(?:0|\+84)(?:3|5|7|8|9)\d{8}\b")

# Từ khóa nhận diện ý định mua hàng
PRICE_KEYWORDS = ["giá", "học phí", "chi phí", "bao nhiêu", "nhiêu tiền", "giá sao", "báo giá", "cost", "price"]
WARRANTY_KEYWORDS = ["bảo hành", "cam kết", "đổi trả", "uy tín", "chứng chỉ", "đầu ra", "bằng cấp", "hỗ trợ sau"]
SCHEDULE_KEYWORDS = ["địa chỉ", "ở đâu", "cơ sở", "lịch học", "khai giảng", "mấy giờ", "chi nhánh", "quận", "hà nội", "hồ chí minh"]
PAYMENT_KEYWORDS = ["chuyển khoản", "stk", "tài khoản", "thanh toán", "đặt cọc", "momo", "ngân hàng", "banking", "ck"]


def evaluate_lead_score(messages: List[Dict[str, Any]], phone: Optional[str] = None) -> Dict[str, Any]:
    """Tính toán điểm số Lead (0 - 100) và phân loại Hot/Warm/Cold."""
    score = 0
    signals: List[str] = []

    # 1. Kiểm tra SĐT
    has_phone = bool(phone and PHONE_REGEX.search(phone.replace(" ", "")))
    all_text = " ".join(str(m.get("text") or "") for m in messages).lower()

    if not has_phone and PHONE_REGEX.search(all_text):
        has_phone = True

    if has_phone:
        score += INTENT_WEIGHTS["phone_provided"]
        signals.append("Đã để lại số điện thoại liên hệ")

    # 2. Kiểm tra hỏi giá
    if any(kw in all_text for kw in PRICE_KEYWORDS):
        score += INTENT_WEIGHTS["price_enquiry"]
        signals.append("Đã hỏi thông tin giá / học phí")

    # 3. Kiểm tra hỏi bảo hành / cam kết
    if any(kw in all_text for kw in WARRANTY_KEYWORDS):
        score += INTENT_WEIGHTS["warranty_policy"]
        signals.append("Quan tâm chính sách bảo hành & cam kết")

    # 4. Kiểm tra hỏi địa chỉ / lịch
    if any(kw in all_text for kw in SCHEDULE_KEYWORDS):
        score += INTENT_WEIGHTS["address_schedule"]
        signals.append("Đã hỏi địa chỉ cơ sở & lịch học")

    # 5. Kiểm tra hỏi thanh toán
    if any(kw in all_text for kw in PAYMENT_KEYWORDS):
        score += INTENT_WEIGHTS["payment_method"]
        signals.append("Hỏi thông tin thanh toán / đặt cọc")

    # 6. Kiểm tra độ sâu tương tác
    customer_msgs = [m for m in messages if m.get("sender") == "customer"]
    if len(customer_msgs) >= 3:
        score += INTENT_WEIGHTS["deep_engagement"]
        signals.append(f"Tương tác sâu ({len(customer_msgs)} lượt phản hồi)")

    # Giới hạn trần 100 điểm
    score = min(100, max(15, score))

    if score >= 70:
        tier = "hot"
        label = "Hot Lead"
        color = "red"
    elif score >= 40:
        tier = "warm"
        label = "Warm Lead"
        color = "amber"
    else:
        tier = "cold"
        label = "Cold Lead"
        color = "blue"

    return {
        "score": score,
        "tier": tier,
        "label": label,
        "color": color,
        "signals": signals,
    }


def determine_next_best_action(
    lead_info: Dict[str, Any],
    last_msg_time_ts: float,
    messages: List[Dict[str, Any]],
    current_status: str = "interested",
) -> Dict[str, Any]:
    """Xác định Hành động tiếp theo tốt nhất (Next Best Action) cho nhân viên."""
    now = time.time()
    silence_hours = max(0.0, (now - last_msg_time_ts) / 3600.0) if last_msg_time_ts else 0.0
    tier = lead_info.get("tier", "warm")
    last_msg = messages[-1].get("text", "").lower() if messages else ""

    # Kịch bản 1: Khách phàn nàn / khiếu nại
    if any(w in last_msg for w in ["chậm", "kém", "lỗi", "không hài lòng", "tệ", "thất vọng", "khiếu nại"]):
        return {
            "type": "escalate_manager",
            "action_title": "Chuyển Quản lý xử lý khiếu nại",
            "rationale": "Phát hiện cảm xúc tiêu cực hoặc phản hồi không hài lòng từ khách.",
            "recommended_channel": "call",
            "cta_text": "Chuyển Quản lý ca trực",
            "risk_level": "high",
            "draft_text": "Dạ Javis rất tiếc về trải nghiệm chưa trọn vẹn của bạn ạ. Bên mình đã báo trực tiếp Quản lý cơ sở để liên hệ hỗ trợ giải quyết ngay cho bạn trong 15 phút tới ạ!",
        }

    # Kịch bản 2: Hot Lead im lặng > 2 giờ -> Gọi điện chốt ưu đãi
    if tier == "hot" and silence_hours >= 2.0 and current_status != "purchased":
        return {
            "type": "call_hot_lead",
            "action_title": "Gọi điện chốt ưu đãi suất học thử",
            "rationale": f"Khách có điểm tiềm năng cao ({lead_info.get('score')}đ) nhưng chưa phản hồi trong {int(silence_hours)} giờ.",
            "recommended_channel": "call",
            "cta_text": "Bấm gọi chốt đơn",
            "risk_level": "medium",
            "draft_text": "Dạ chào bạn, Javis thấy bạn đang quan tâm khóa học. Hôm nay bên mình đang có suất ưu đãi trải nghiệm 1 buổi miễn phí, mình giữ chỗ cho bạn nhé ạ?",
        }

    # Kịch bản 3: Khách đã hỏi giá nhưng chưa chốt > 6 giờ -> Gửi voucher có thời hạn
    if "Đã hỏi thông tin giá / học phí" in lead_info.get("signals", []) and silence_hours >= 6.0 and current_status != "purchased":
        return {
            "type": "send_voucher",
            "action_title": "Gửi Voucher giảm 10% có hạn 2h",
            "rationale": "Khách đã biết giá nhưng đang cân nhắc, cần thêm động lực kích hoạt mua ngay.",
            "recommended_channel": "chat",
            "cta_text": "Gửi Voucher ưu đãi",
            "risk_level": "medium",
            "draft_text": "Dạ chào bạn, để hỗ trợ bạn bắt đầu lộ trình học sớm nhất, Javis xin gửi bạn mã ưu đãi [JAVIS10] giảm thêm 10% học phí nếu đăng ký trong hôm nay ạ!",
        }

    # Kịch bản 4: Khách đã mua -> Mời vào nhóm hỗ trợ VIP & hướng dẫn onboarding
    if current_status == "purchased":
        return {
            "type": "onboarding_care",
            "action_title": "Gửi thư chào mừng & link nhóm Zalo VIP",
            "rationale": "Khách đã hoàn tất đơn hàng, cần chăm sóc chu đáo sau bán.",
            "recommended_channel": "chat",
            "cta_text": "Gửi link nhóm VIP",
            "risk_level": "low",
            "draft_text": "Javis chúc mừng bạn đã chính thức tham gia khóa học! Bạn bấm vào link sau để vào nhóm Zalo lớp mình nhận tài liệu và lịch học chi tiết nhé: https://zalo.me/g/javis-vip",
        }

    # Mặc định: Tư vấn hỗ trợ kịp thời
    return {
        "type": "consult_support",
        "action_title": "Gợi ý mẫu câu tư vấn chi tiết",
        "rationale": "Khách đang trao đổi tích cực, AI đã chuẩn bị câu trả lời phù hợp nhất theo Brand Kit.",
        "recommended_channel": "chat",
        "cta_text": "Dùng câu trả lời gợi ý",
        "risk_level": "low",
        "draft_text": "Dạ Javis rất vui được đồng hành cùng bạn! Bạn đang cần tư vấn thêm về thời gian học hay nội dung chi tiết của từng buổi ạ?",
    }


def classify_approval_risk(action_type: str, text: str = "") -> Tuple[str, str]:
    """Phân loại mức độ kiểm soát rủi ro của AI (Human Approval Risk Matrix).
    
    Returns:
        (risk_level, risk_label): ('low' | 'medium' | 'high', human_readable_label)
    """
    text_lower = text.lower()

    # Cấp độ 3: Rủi ro cao -> Bắt buộc Quản lý phê duyệt
    if (
        "hoàn tiền" in text_lower
        or "trả tiền" in text_lower
        or "bồi thường" in text_lower
        or "giảm 25%" in text_lower
        or "giảm 30%" in text_lower
        or "giảm 50%" in text_lower
        or "chuyển quản lý" in text_lower
        or action_type in ["refund", "escalate_manager", "deep_discount"]
    ):
        return ("high", "Cần Quản lý duyệt (High Risk)")

    # Cấp độ 2: Rủi ro trung bình -> AI soạn, Nhân viên ca trực bấm duyệt
    if (
        "voucher" in text_lower
        or "giảm giá" in text_lower
        or "học phí" in text_lower
        or "ưu đãi" in text_lower
        or "tài khoản" in text_lower
        or action_type in ["send_voucher", "quote_price", "call_hot_lead"]
    ):
        return ("medium", "Cần Nhân viên duyệt (Medium Risk)")

    # Cấp độ 1: Rủi ro thấp -> AI tự động gửi hoặc nháp thông thường
    return ("low", "Tự động an toàn (Low Risk)")
