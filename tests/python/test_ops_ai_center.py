# -*- coding: utf-8 -*-
"""Test suite cho AI Operations Center (Briefing, Lead Scoring, Attribution, Campaign Autopilot)."""
from _paths import ROOT, SERVER  # noqa: E402,F401
import pytest
import lead_scoring
import ops_briefing
import ops_attribution
import ops_campaign


def test_lead_scoring_hot_tier():
    messages = [
        {"sender": "customer", "text": "Khóa MOS giá bao nhiêu ạ?"},
        {"sender": "staff", "text": "Dạ học phí 1.200.000đ ạ"},
        {"sender": "customer", "text": "Có bảo hành đầu ra không bạn? Số điện thoại mình là 0967123456, cho mình stk chuyển khoản luôn nhé"},
    ]
    res = lead_scoring.evaluate_lead_score(messages, phone="0967123456")
    assert res["score"] >= 70, f"Expected hot score >= 70, got {res['score']}"
    assert res["tier"] == "hot"
    assert "Đã để lại số điện thoại liên hệ" in res["signals"]
    assert "Đã hỏi thông tin giá / học phí" in res["signals"]


def test_lead_scoring_cold_tier():
    messages = [
        {"sender": "customer", "text": "Chào shop"},
    ]
    res = lead_scoring.evaluate_lead_score(messages)
    assert res["tier"] == "cold"
    assert res["score"] < 40


def test_next_best_action_escalate_complaint():
    lead_info = {"tier": "warm", "score": 50, "signals": []}
    messages = [
        {"sender": "customer", "text": "Bên bạn làm ăn chậm và kém quá, tôi rất không hài lòng và thất vọng!"}
    ]
    action = lead_scoring.determine_next_best_action(lead_info, 0, messages)
    assert action["type"] == "escalate_manager"
    assert action["risk_level"] == "high"


def test_next_best_action_hot_silence():
    lead_info = {"tier": "hot", "score": 85, "signals": ["Đã hỏi thông tin giá / học phí"]}
    messages = [
        {"sender": "customer", "text": "Cho mình xin giá khóa học"}
    ]
    # Im lặng 3 tiếng trước
    import time
    last_ts = time.time() - 3600 * 3
    action = lead_scoring.determine_next_best_action(lead_info, last_ts, messages, current_status="interested")
    assert action["type"] == "call_hot_lead"
    assert "chốt" in action["action_title"].lower() or "gọi" in action["action_title"].lower()


def test_classify_approval_risk():
    lvl_high, _ = lead_scoring.classify_approval_risk("refund", "yêu cầu hoàn tiền 100%")
    assert lvl_high == "high"

    lvl_med, _ = lead_scoring.classify_approval_risk("send_voucher", "gửi voucher giảm 10%")
    assert lvl_med == "medium"

    lvl_low, _ = lead_scoring.classify_approval_risk("consult_support", "chào bạn, bạn cần hỗ trợ gì ạ")
    assert lvl_low == "low"


def test_ops_briefing_generation():
    briefing = ops_briefing.get_daily_briefing()
    assert briefing["status"] == "ok"
    assert "kpis" in briefing
    assert len(briefing["hot_leads"]) > 0
    assert "top_post" in briefing
    assert "BẢN TIN ĐIỀU HÀNH SÁNG NAY" in briefing["formatted_text"]


def test_ops_attribution_matrix():
    matrix = ops_attribution.get_content_attribution_matrix()
    assert matrix["status"] == "ok"
    assert matrix["total_revenue_vnd"] > 0
    assert matrix["total_orders"] > 0
    assert len(matrix["items"]) >= 5


def test_ops_attribution_insights():
    insights = ops_attribution.get_content_learning_insights()
    assert insights["status"] == "ok"
    assert len(insights["winning_patterns"]) >= 3


def test_ops_competitor_radar():
    radar = ops_attribution.get_competitor_radar()
    assert radar["status"] == "ok"
    assert len(radar["competitors_monitored"]) >= 2
    assert len(radar["content_gaps"]) >= 2


def test_ops_campaign_autopilot():
    plan = ops_campaign.generate_campaign_autopilot(goal="Tuyển 50 học viên MOS Tháng 10", target_metric="50 học viên")
    assert plan["status"] == "ok"
    assert len(plan["phases"]) == 4
    assert len(plan["content_calendar"]) == 12
    assert "sales_script" in plan


def main():
    test_lead_scoring_hot_tier()
    test_lead_scoring_cold_tier()
    test_next_best_action_escalate_complaint()
    test_next_best_action_hot_silence()
    test_classify_approval_risk()
    test_ops_briefing_generation()
    test_ops_attribution_matrix()
    test_ops_attribution_insights()
    test_ops_competitor_radar()
    test_ops_campaign_autopilot()
    print("OK - test_ops_ai_center: tất cả pass")


if __name__ == "__main__":
    main()
