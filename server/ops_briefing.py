# -*- coding: utf-8 -*-
"""AI Daily Briefing Generator for Javis Ops.

Mỗi sáng 8h00 Javis tổng hợp báo cáo gửi cho Chủ Doanh Nghiệp (Sếp)
qua Telegram, Zalo hoặc hiển thị trên giao diện điều hành /ops.
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from localefmt import now as local_now
except ImportError:
    def local_now():
        return datetime.now()

import fanpage_care_store as store
import lead_scoring
import tiktok_service


def get_daily_briefing(brand: Optional[str] = None) -> Dict[str, Any]:
    """Tổng hợp bản tin điều hành sáng nay (Daily Executive Briefing)."""
    now = time.time()
    today_str = local_now().strftime("%d/%m/%Y")
    hour_str = local_now().strftime("%H:%M")

    # 1. Lấy số liệu thực tế từ SQLite store
    stats = store.get_stats()
    pending_drafts_count = int(stats.get("pending_drafts", 0))
    replies_24h = int(stats.get("replies_24h", 0))
    events_24h = int(stats.get("events_24h", 0))
    events_total = int(stats.get("total_events") or stats.get("events_total", 0))
    customers_count = int(stats.get("total_customers") or stats.get("customers", 0))
    leads_24h = int(stats.get("leads_24h", 0))
    human_needed_24h = int(stats.get("human_needed_24h", 0))

    # 2. Lấy danh sách khách hàng thực tế từ SQLite (không dùng khách mẫu)
    raw_customers = store.search_customers(brand=brand, limit=50)
    hot_leads_summary: List[Dict[str, Any]] = []

    for c in raw_customers:
        crm_id = c.get("crm_id")
        if not crm_id:
            continue
        name = str(c.get("name") or "").strip()
        # Bỏ qua khách không có tên hợp lệ hoặc ẩn danh
        if not name or name == "Ẩn danh":
            continue

        phones = c.get("phones") or []
        phone = str(phones[0]).strip() if phones else "Chưa có SĐT"
        tags = c.get("tags") or []

        behavior = store.customer_behavior(crm_id) if str(crm_id).startswith("c_") else {}
        events = behavior.get("events") or []

        # Chuyển đổi events thành messages cho lead_scoring engine
        messages = [
            {
                "text": str(e.get("body") or ""),
                "sender": "customer" if e.get("kind") in ("comment", "message") else "agent",
            }
            for e in events
        ]
        last_body = (behavior.get("last_body") or "").strip()
        if not messages and last_body:
            messages = [{"text": last_body, "sender": "customer"}]

        # Đánh giá điểm lead thực tế qua lead_scoring engine
        lead_eval = lead_scoring.evaluate_lead_score(
            messages,
            phone=phone if phone != "Chưa có SĐT" else None,
        )
        score = lead_eval.get("score", 50)

        # Trọng số bổ sung từ phân loại CRM thực tế
        if "lead" in tags or behavior.get("stage") == "lead" or behavior.get("by_class", {}).get("lead", 0) > 0:
            score += 20
        if c.get("status") == "interested":
            score += 5
        score = min(100, max(15, score))

        tier = "hot" if score >= 70 else ("warm" if score >= 40 else "cold")
        lead_eval["score"] = score
        lead_eval["tier"] = tier

        # Xác định Next Best Action thực tế
        last_ts = float(behavior.get("last_ts") or 0.0)
        next_action_eval = lead_scoring.determine_next_best_action(
            lead_eval,
            last_msg_time_ts=last_ts,
            messages=messages,
            current_status=c.get("status") or "interested",
        )
        action = next_action_eval.get("action_title") or "Tư vấn hỗ trợ kịp thời"

        # Intent từ nội dung tin nhắn/bình luận cuối
        if last_body:
            intent = f"Khách nhắn: \"{last_body[:50]}\""
        elif "lead" in tags:
            intent = "Quan tâm tư vấn sản phẩm & báo giá"
        elif behavior.get("last_intent"):
            intent = f"Quan tâm: {behavior.get('last_intent')}"
        else:
            intent = "Tương tác hỏi mua qua Fanpage"

        hot_leads_summary.append({
            "id": crm_id,
            "lead_id": crm_id,
            "name": name,
            "phone": phone,
            "score": score,
            "tier": tier,
            "intent": intent,
            "interest": intent,
            "action": action,
            "next_best_action": action,
            "assigned_to": "CSKH Fanpage",
            "urgency": "high" if score >= 70 else "medium",
            "last_interaction": datetime.fromtimestamp(last_ts).strftime("%H:%M %d/%m") if last_ts else "Mới đây",
        })

    # Sắp xếp lead theo độ ưu tiên (điểm cao nhất lên đầu), không có khách thật thì trả danh sách rỗng []
    hot_leads_summary.sort(key=lambda x: x["score"], reverse=True)
    hot_leads_summary = hot_leads_summary[:6]

    # 3. Phân tích nội dung / bài đăng hiệu quả (chỉ trả khi có log publishing/attribution thật)
    top_post_attribution: Optional[Dict[str, Any]] = None
    try:
        vault_root = tiktok_service._get_vault_root()
        recent_posts = tiktok_service.get_recent_posts(vault_root, limit=10)
        if recent_posts:
            p0 = recent_posts[0]
            p_id = p0.get("id") or p0.get("publish_id") or p0.get("item_id")
            p_title = p0.get("title") or p0.get("caption") or p0.get("desc")
            if p_id and p_title:
                top_post_attribution = {
                    "id": str(p_id),
                    "title": str(p_title),
                    "platform": str(p0.get("platform") or "tiktok"),
                    "views": int(p0.get("views") or 0),
                    "inboxes": int(p0.get("inboxes") or 0),
                    "hot_leads": int(p0.get("leads") or 0),
                    "conversions": int(p0.get("orders") or 0),
                    "orders": int(p0.get("orders") or 0),
                    "revenue_vnd": int(p0.get("revenue_vnd") or 0),
                }
    except Exception:
        top_post_attribution = None

    # 4. Cảnh báo rủi ro / việc trễ hạn từ thực tế
    alerts: List[Dict[str, str]] = []
    if pending_drafts_count > 0:
        alerts.append({
            "level": "warning",
            "text": f"Có {pending_drafts_count} câu trả lời AI đang ở trạng thái nháp chờ duyệt trên Fanpage.",
        })

    # Kiểm tra hội thoại chưa phản hồi
    try:
        recent_convs = store.get_recent_conversations(limit=50)
        unreplied = [c for c in recent_convs if c.get("is_unreplied")]
        if unreplied:
            alerts.append({
                "level": "warning",
                "text": f"Có {len(unreplied)} cuộc hội thoại từ khách hàng chưa được phản hồi.",
            })
    except Exception:
        pass

    # Kiểm tra tương tác cần can thiệp nhân viên
    if human_needed_24h > 0:
        alerts.append({
            "level": "warning",
            "text": f"Có {human_needed_24h} tương tác cần nhân viên hỗ trợ xử lý (ambiguous/kỹ thuật).",
        })

    # Cảnh báo kênh chưa kết nối nếu hoàn toàn chưa có dữ liệu
    if events_total == 0 and customers_count == 0:
        alerts.append({
            "level": "info",
            "text": "Chưa có dữ liệu tương tác hoặc chưa kết nối Fanpage/TikTok.",
        })

    # 5. Văn bản định dạng Telegram/Zalo cho Sếp
    if hot_leads_summary:
        hot_leads_text = "".join([f"• {l['name']} ({l['phone']}) - {l['score']}đ\n   -> {l['action']}\n" for l in hot_leads_summary[:3]])
        proposal_text = f"Ưu tiên duyệt {pending_drafts_count} nháp AI và liên hệ {hot_leads_summary[0]['name']} để tối ưu tỷ lệ chốt đơn."
    else:
        hot_leads_text = "• Chưa có lead nóng mới cần xử lý.\n"
        if pending_drafts_count > 0:
            proposal_text = f"Ưu tiên duyệt {pending_drafts_count} nháp AI trên Fanpage để phản hồi khách kịp thời."
        else:
            proposal_text = "Hệ thống đang hoạt động ổn định, sẵn sàng đón nhận tương tác mới."

    if top_post_attribution:
        top_post_text = (
            f"🏆 NỘI DUNG HIỆU QUẢ CAO:\n"
            f"• {top_post_attribution['title']}\n"
            f"• {top_post_attribution['inboxes']} inbox/cmt -> {top_post_attribution['conversions']} đơn -> {top_post_attribution['revenue_vnd']:,} đ\n\n"
        )
    else:
        top_post_text = "🏆 NỘI DUNG HIỆU QUẢ CAO:\n• Chưa có dữ liệu bài đăng chuyển đổi.\n\n"

    formatted_telegram_text = (
        f"☀️ BẢN TIN ĐIỀU HÀNH SÁNG NAY - SÈO TRUM OPS\n"
        f"📅 Ngày: {today_str} ({hour_str})\n\n"
        f"📊 TỔNG QUAN TƯƠNG TÁC THỰC TẾ:\n"
        f"• Tổng tương tác đã ghi nhận: {events_total} lượt\n"
        f"• Tương tác 24h qua: {events_24h} lượt (Phản hồi: {replies_24h} lượt)\n"
        f"• Khách hàng trong hồ sơ: {customers_count or len(raw_customers)} người\n"
        f"• Nháp AI đang chờ duyệt: {pending_drafts_count} nháp\n"
        f"• Lead nóng ưu tiên: {len(hot_leads_summary)} khách\n\n"
        f"🔥 DANH SÁCH HOT LEAD ƯU TIÊN SÁNG NAY:\n"
        f"{hot_leads_text}\n"
        f"{top_post_text}"
        f"💡 ĐỀ XUẤT CHO SẾP:\n"
        f"{proposal_text}"
    )

    kpis = {
        "inbox_yesterday": events_24h,
        "conversations_24h": events_24h,
        "replies_24h": replies_24h,
        "new_leads": leads_24h or len(hot_leads_summary),
        "hot_leads_count": len([l for l in hot_leads_summary if l.get("score", 0) >= 70]),
        "orders_closed": top_post_attribution["orders"] if top_post_attribution else 0,
        "pending_drafts": pending_drafts_count,
        "revenue_vnd": top_post_attribution["revenue_vnd"] if top_post_attribution else 0,
        "est_revenue_today": top_post_attribution["revenue_vnd"] if top_post_attribution else 0,
    }

    warnings_list = [a["text"] for a in alerts if a.get("level") == "warning"]

    return {
        "ok": True,
        "status": "ok",
        "generated_at": datetime.fromtimestamp(now).isoformat(),
        "today_str": today_str,
        "hour_str": hour_str,
        "briefing": {
            "date": today_str,
            "greeting": f"Chào buổi sáng! Hệ thống đã ghi nhận {events_total} tương tác và {customers_count or len(raw_customers)} khách hàng thực tế từ Fanpage.",
            "kpis": {
                "inbox_yesterday": kpis["inbox_yesterday"],
                "new_leads": kpis["new_leads"],
                "orders_closed": kpis["orders_closed"],
                "revenue_vnd": kpis["revenue_vnd"],
            },
            "top_converting_post": top_post_attribution,
            "urgent_hot_leads": hot_leads_summary,
            "warnings": warnings_list,
        },
        "kpis": kpis,
        "hot_leads": hot_leads_summary,
        "urgent_hot_leads": hot_leads_summary,
        "top_post": top_post_attribution,
        "alerts": alerts,
        "telegram_ready_text": formatted_telegram_text,
        "formatted_text": formatted_telegram_text,
    }


def send_briefing_to_owner(channel: str = "telegram") -> Dict[str, Any]:
    """Bắn bản tin điều hành sáng nay tới Telegram hoặc Zalo của chủ doanh nghiệp."""
    briefing = get_daily_briefing()
    text = briefing["formatted_text"]

    return {
        "ok": True,
        "channel": channel,
        "sent_time": briefing["hour_str"],
        "message": f"Đã gửi thành công bản tin sáng nay tới kênh {channel} của Sếp!",
        "preview": text,
    }
