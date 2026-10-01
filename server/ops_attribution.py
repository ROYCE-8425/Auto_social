# -*- coding: utf-8 -*-
"""Content-to-Sale Attribution & Content Learning Loop for Javis Ops.

Đo lường hiệu quả kinh doanh từ bài viết tới doanh thu thực tế,
nhận diện mẫu bài bán chạy và phân tích rada đối thủ / khoảng trống nội dung.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import fanpage_care_store as store
import tiktok_service


def get_content_attribution_matrix(brand: Optional[str] = None) -> Dict[str, Any]:
    """Lấy bảng ma trận chuyển đổi từ bài viết/video đến doanh thu thực tế."""
    vault_root = tiktok_service._get_vault_root()
    recent_posts = tiktok_service.get_recent_posts(vault_root, limit=50)

    # Đọc thêm bài viết / tương tác theo post_id từ SQLite events nếu có
    store_posts: Dict[str, Dict[str, Any]] = {}
    try:
        with store.get_connection() as conn:
            rows = conn.execute(
                "SELECT post_id, COUNT(*) as inboxes, "
                "SUM(CASE WHEN class = 'lead' THEN 1 ELSE 0 END) as leads "
                "FROM events "
                "WHERE post_id IS NOT NULL AND post_id != '' "
                "GROUP BY post_id ORDER BY inboxes DESC LIMIT 50"
            ).fetchall()
            for r in rows:
                pid = str(r["post_id"])
                store_posts[pid] = {
                    "post_id": pid,
                    "inboxes": int(r["inboxes"] or 0),
                    "leads": int(r["leads"] or 0),
                }
    except Exception:
        pass

    items: List[Dict[str, Any]] = []

    # Ghép từ các bài đăng gần nhất
    for idx, p in enumerate(recent_posts):
        pid = str(p.get("id") or p.get("publish_id") or p.get("item_id") or f"post_{idx+1}")
        title = str(p.get("title") or p.get("caption") or p.get("desc") or f"Bài đăng {pid}").strip()
        platform = str(p.get("platform") or "tiktok").lower()
        format_type = "video_9_16" if platform == "tiktok" else "single_image"
        views = int(p.get("views") or 0)

        # Thống kê từ store nếu có post_id trùng
        sp = store_posts.pop(pid, {})
        inboxes = int(p.get("inboxes") or sp.get("inboxes") or 0)
        leads = int(p.get("leads") or sp.get("leads") or 0)
        orders = int(p.get("orders") or 0)
        revenue_vnd = int(p.get("revenue_vnd") or 0)
        conversion_rate = round((orders / inboxes * 100), 2) if inboxes > 0 else 0.0

        items.append({
            "id": pid,
            "post_id": pid,
            "title": title,
            "platform": platform,
            "format": format_type,
            "views": views,
            "inboxes": inboxes,
            "leads": leads,
            "orders": orders,
            "conversion_rate": conversion_rate,
            "revenue_vnd": revenue_vnd,
            "roi_ratio": f"{round(revenue_vnd / 500000, 1)}x" if revenue_vnd > 0 else "0.0x",
            "top_hook": title[:60],
            "posted_at": p.get("posted_at") or p.get("created_at") or "",
            "status": "winning" if conversion_rate >= 10 else "active",
        })

    # Thêm các bài từ store_posts chưa có trong recent_posts
    for pid, sp in store_posts.items():
        inboxes = sp["inboxes"]
        leads = sp["leads"]
        items.append({
            "id": pid,
            "post_id": pid,
            "title": f"Bài đăng Fanpage ({pid})",
            "platform": "facebook",
            "format": "single_image",
            "views": 0,
            "inboxes": inboxes,
            "leads": leads,
            "orders": 0,
            "conversion_rate": 0.0,
            "revenue_vnd": 0,
            "roi_ratio": "0.0x",
            "top_hook": f"Tương tác Fanpage: {inboxes} inboxes, {leads} leads",
            "posted_at": "",
            "status": "active",
        })

    total_revenue = sum(item["revenue_vnd"] for item in items)
    total_orders = sum(item["orders"] for item in items)
    total_inboxes = sum(item["inboxes"] for item in items)
    total_views = sum(item["views"] for item in items)
    total_leads = sum(item["leads"] for item in items)
    avg_conversion = round((total_orders / total_inboxes * 100), 2) if total_inboxes else 0.0

    # Xác định data_source: real | empty | partial
    if not items:
        data_source = "empty"
    elif total_orders > 0 and total_revenue > 0:
        data_source = "real"
    else:
        data_source = "partial"

    top_platform = "Chưa có"
    if items:
        platforms = [it["platform"] for it in items]
        top_platform = max(set(platforms), key=platforms.count).capitalize()

    return {
        "status": "ok",
        "data_source": data_source,
        "total_revenue_vnd": total_revenue,
        "total_orders": total_orders,
        "total_inboxes": total_inboxes,
        "avg_conversion_rate": avg_conversion,
        "items": items,
        "summary": {
            "total_views": total_views,
            "total_inboxes": total_inboxes,
            "total_leads": total_leads,
            "total_orders": total_orders,
            "total_revenue_vnd": total_revenue,
            "top_converting_platform": top_platform,
        },
    }


def get_content_learning_insights() -> Dict[str, Any]:
    """Phân tích các mẫu cấu trúc nội dung mang lại chuyển đổi cao nhất (Content Learning Loop)."""
    attr = get_content_attribution_matrix()
    items = [it for it in attr.get("items", []) if (it.get("orders", 0) > 0 or it.get("conversion_rate", 0) > 0)]

    if not items:
        return {
            "status": "ok",
            "data_source": "empty",
            "winning_patterns": [],
            "timing_recommendation": None,
            "content_to_replicate": [],
            "learning_system_status": "Chưa có dữ liệu bài đăng và chuyển đổi thực tế để trích xuất quy luật.",
        }

    winning_patterns = []
    for item in sorted(items, key=lambda x: x.get("conversion_rate", 0), reverse=True)[:5]:
        winning_patterns.append({
            "hook_type": f"Định dạng {item.get('format', 'bài đăng')} ({item.get('platform', 'mạng xã hội')})",
            "avg_conversion_rate": item.get("conversion_rate", 0.0),
            "avg_revenue_vnd": item.get("revenue_vnd", 0),
            "recommendation": f"Tái sử dụng cấu trúc từ bài '{item.get('title', item.get('id'))}'.",
        })

    return {
        "status": "ok",
        "data_source": "real",
        "winning_patterns": winning_patterns,
        "timing_recommendation": None,
        "content_to_replicate": [it.get("title", "") for it in items[:3] if it.get("title")],
        "learning_system_status": f"Đang học hỏi từ {len(items)} bài đăng có chuyển đổi thực tế.",
    }



def get_competitor_radar() -> Dict[str, Any]:
    """Báo cáo Rada đối thủ công khai & Phân tích khoảng trống nội dung (Competitor Radar)."""
    return {
        "status": "not_configured",
        "status_code": "disconnected",
        "message": "Chưa kích hoạt hoặc cấu hình crawler đối thủ tự động.",
        "market_sector": None,
        "competitors_monitored": [],
        "competitors": [],
        "content_gaps": [],
        "content_gap_analysis": [],
        "actionable_counter_hooks": [],
    }
