"""Test suite cho server/fanpage_care_policy.py."""
import pytest
from fanpage_care_policy import MODE_RANK, effective_mode, policy_allows


def test_mode_rank():
    assert MODE_RANK["suggest"] == 0
    assert MODE_RANK["auto"] == 1
    assert MODE_RANK["full"] == 2


def test_effective_mode():
    # Không có page override -> lấy global
    assert effective_mode("suggest") == "suggest"
    assert effective_mode("auto") == "auto"
    assert effective_mode("full") == "full"

    # Lấy mode chặt hơn (rank thấp hơn)
    assert effective_mode("full", "auto") == "auto"
    assert effective_mode("auto", "full") == "auto"
    assert effective_mode("auto", "suggest") == "suggest"
    assert effective_mode("suggest", "full") == "suggest"
    assert effective_mode("invalid", "auto") == "suggest"


def test_policy_kill_switch():
    ok, why = policy_allows("faq_reply", mode="full", class_name="faq", kill_switch=True)
    assert not ok
    assert why == "kill_switch_active"


def test_policy_rate_limit():
    ok, why = policy_allows("faq_reply", mode="full", class_name="faq", rate_exceeded=True)
    assert not ok
    assert why == "rate_limit_exceeded"


def test_policy_quiet_hours():
    ok, why = policy_allows("faq_reply", mode="full", class_name="faq", is_quiet=True)
    assert not ok
    assert why == "quiet_hours"


def test_policy_suggest_mode():
    # Mode suggest KHÔNG BAO GIỜ gửi Graph
    ok, why = policy_allows("faq_reply", mode="suggest", class_name="faq")
    assert not ok
    assert why == "mode_suggest_draft_only"

    ok, why = policy_allows("lead_thanks", mode="suggest", class_name="lead")
    assert not ok
    assert why == "mode_suggest_draft_only"

    # Draft luôn được phép
    ok, why = policy_allows("suggest_draft", mode="suggest", class_name="faq")
    assert ok


def test_policy_auto_mode():
    # FAQ template được gửi trong mode auto
    ok, why = policy_allows("faq_reply", mode="auto", class_name="faq")
    assert ok
    assert why == "allowed_faq_template"

    # Lead thanks được gửi trong mode auto
    ok, why = policy_allows("lead_thanks", mode="auto", class_name="lead")
    assert ok
    assert why == "allowed_lead_thanks"

    # Không cho hide spam trong auto nếu không có cờ đặc biệt
    ok, why = policy_allows("comment_hide", mode="auto", class_name="spam")
    assert not ok

    # Không cho llm_reply trong mode auto
    ok, why = policy_allows("llm_reply", mode="auto", class_name="ambiguous")
    assert not ok


def test_policy_full_mode():
    # FAQ, lead, khen, hide spam, delete spam, llm_reply trong full
    ok, _ = policy_allows("faq_reply", mode="full", class_name="faq")
    assert ok

    ok, _ = policy_allows("lead_thanks", mode="full", class_name="lead")
    assert ok

    ok, _ = policy_allows("comment_hide", mode="full", class_name="spam")
    assert ok

    ok, _ = policy_allows("comment_hide", mode="full", class_name="toxic")
    assert ok

    # Like khen chỉ được khi like_khen=True
    ok, _ = policy_allows("comment_like", mode="full", class_name="khen", like_khen=False)
    assert not ok
    ok, _ = policy_allows("comment_like", mode="full", class_name="khen", like_khen=True)
    assert ok

    # Delete spam chỉ được khi delete_spam=True
    ok, _ = policy_allows("comment_delete", mode="full", class_name="spam", delete_spam=False)
    assert not ok
    ok, _ = policy_allows("comment_delete", mode="full", class_name="spam", delete_spam=True)
    assert ok

    # LLM reply cho ky_thuat và ambiguous
    ok, _ = policy_allows("llm_reply", mode="full", class_name="ky_thuat")
    assert ok
    ok, _ = policy_allows("llm_reply", mode="full", class_name="ambiguous")
    assert ok
