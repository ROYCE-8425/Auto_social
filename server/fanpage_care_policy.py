"""Policy cho Fanpage Care: suggest / auto / full.

Đặc tả:
- MODE_RANK = {"suggest": 0, "auto": 1, "full": 2}
- effective_mode: lấy mode chặt hơn (rank nhỏ hơn) giữa toàn cục và per-page
- policy_allows: kiểm tra quyền thực thi action dựa trên (mode x class x quiet x rate x kill)
"""
from __future__ import annotations

from typing import Any

MODE_RANK = {"suggest": 0, "auto": 1, "full": 2}


def effective_mode(global_mode: str, page_mode: str | None = None) -> str:
    """Xác định mode hiệu lực: lấy mode chặt hơn (rank thấp hơn)."""
    gm = str(global_mode or "suggest").lower().strip()
    if gm not in MODE_RANK:
        gm = "suggest"

    if not page_mode:
        return gm

    pm = str(page_mode).lower().strip()
    if pm not in MODE_RANK:
        return gm

    # Chọn rank nhỏ hơn
    return gm if MODE_RANK[gm] <= MODE_RANK[pm] else pm


def policy_allows(
    action: str,
    *,
    mode: str,
    class_name: str,
    is_quiet: bool = False,
    rate_exceeded: bool = False,
    kill_switch: bool = False,
    delete_spam: bool = False,
    like_khen: bool = False,
) -> tuple[bool, str]:
    """Kiểm tra xem hành động action có được phép thực hiện tự động hay không.

    Trả (allowed: bool, reason: str).
    """
    m = str(mode or "suggest").lower().strip()
    if m not in MODE_RANK:
        m = "suggest"

    # 1. Kill switch: lập tức dừng mọi hành động ghi Graph
    if kill_switch:
        return False, "kill_switch_active"

    # 2. Vượt hạn mức giờ (max 8 replies/page/hour)
    if rate_exceeded:
        return False, "rate_limit_exceeded"

    # 3. Giờ im lặng (21h - 7h)
    if is_quiet:
        return False, "quiet_hours"

    act = action.lower().strip()

    if act == "suggest_draft":
        return True, "draft_always_allowed"

    # 4. Mode suggest: KHÔNG BAO GIỜ gửi Graph, chỉ tạo draft
    if m == "suggest":
        return False, "mode_suggest_draft_only"

    # 5. Các hành động cụ thể trong mode auto / full

    if act == "faq_reply":
        if class_name == "faq":
            return True, "allowed_faq_template"
        return False, f"class_{class_name}_not_faq"

    if act == "lead_thanks":
        if class_name == "lead":
            return True, "allowed_lead_thanks"
        return False, f"class_{class_name}_not_lead"

    if act == "comment_like":
        if class_name == "khen" and like_khen:
            return True, "allowed_like_khen"
        return False, "like_khen_disabled_or_not_khen"

    if act == "comment_hide":
        # Chỉ ở mode=full và class là spam hoặc toxic
        if m == "full" and class_name in ("spam", "toxic"):
            return True, "allowed_hide_spam"
        return False, "hide_only_in_full_mode_for_spam"

    if act == "comment_delete":
        # Chỉ ở mode=full, class là spam và bật delete_spam=True
        if m == "full" and class_name == "spam" and delete_spam:
            return True, "allowed_delete_spam"
        return False, "delete_spam_requires_full_mode_and_flag"

    if act == "llm_reply":
        # Chỉ ở mode=full và class là ky_thuat hoặc ambiguous
        if m == "full" and class_name in ("ky_thuat", "ambiguous"):
            return True, "allowed_llm_reply"
        return False, "llm_reply_only_in_full_mode"

    if act == "messenger_reply":
        if m == "full":
            return True, "allowed_messenger_reply"
        return False, "messenger_reply_only_in_full_mode"

    if act == "suggest_draft":
        return True, "draft_always_allowed"

    return False, f"unknown_action_{act}"
