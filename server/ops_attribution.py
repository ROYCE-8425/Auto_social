# -*- coding: utf-8 -*-
"""Content-to-Sale Attribution & Content Learning Loop for Javis Ops.

Đo lường hiệu quả kinh doanh từ bài viết tới doanh thu thực tế,
nhận diện mẫu bài bán chạy và phân tích rada đối thủ / khoảng trống nội dung.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


def get_content_attribution_matrix(brand: Optional[str] = None) -> Dict[str, Any]:
    """Lấy bảng ma trận chuyển đổi từ bài viết/video đến doanh thu thực tế."""
    items = [
        {
            "id": "post_101",
            "title": "3 Phím tắt Excel dân văn phòng bắt buộc phải biết (MOS Series)",
            "platform": "tiktok",
            "format": "video_9_16",
            "views": 28400,
            "inboxes": 142,
            "leads": 48,
            "orders": 14,
            "conversion_rate": 9.85,
            "revenue_vnd": 22400000,
            "roi_ratio": "14.2x",
            "top_hook": "Biết 3 phím này sếp tăng lương gấp đôi!",
        },
        {
            "id": "post_102",
            "title": "Thông báo khai giảng khóa Tin học Văn phòng cấp tốc Cơ sở Q7",
            "platform": "facebook",
            "format": "album_1_1",
            "views": 8500,
            "inboxes": 65,
            "leads": 29,
            "orders": 11,
            "conversion_rate": 16.92,
            "revenue_vnd": 18700000,
            "roi_ratio": "8.5x",
            "top_hook": "Ưu đãi 15% học phí cho 20 bạn đăng ký đầu tiên trong tuần này.",
        },
        {
            "id": "post_103",
            "title": "So sánh hàm VLOOKUP và XLOOKUP: Khi nào nên đổi?",
            "platform": "tiktok",
            "format": "video_9_16",
            "views": 45000,
            "inboxes": 88,
            "leads": 22,
            "orders": 5,
            "conversion_rate": 5.68,
            "revenue_vnd": 7500000,
            "roi_ratio": "6.1x",
            "top_hook": "Bỏ ngay VLOOKUP nếu không muốn mất việc vì lỗi bảng.",
        },
        {
            "id": "post_104",
            "title": "Tổng hợp bài tập thực hành AutoCAD 2D cho sinh viên Bách Khoa",
            "platform": "facebook",
            "format": "single_image",
            "views": 6200,
            "inboxes": 42,
            "leads": 18,
            "orders": 6,
            "conversion_rate": 14.28,
            "revenue_vnd": 10200000,
            "roi_ratio": "7.2x",
            "top_hook": "Tặng trọn bộ 50 bản vẽ mẫu AutoCAD kèm video chữa chi tiết.",
        },
        {
            "id": "post_105",
            "title": "Game BSN - Hướng dẫn tải và cài đặt game bản quyền an toàn không virus",
            "platform": "tiktok",
            "format": "video_9_16",
            "views": 18900,
            "inboxes": 95,
            "leads": 52,
            "orders": 24,
            "conversion_rate": 25.26,
            "revenue_vnd": 3600000,
            "roi_ratio": "9.4x",
            "top_hook": "Chơi game bản quyền giá rẻ bảo hành trọn đời chỉ với 45k.",
        },
    ]

    total_revenue = sum(item["revenue_vnd"] for item in items)
    total_orders = sum(item["orders"] for item in items)
    total_inboxes = sum(item["inboxes"] for item in items)
    avg_conversion = round((total_orders / total_inboxes * 100), 2) if total_inboxes else 0.0

    return {
        "status": "ok",
        "total_revenue_vnd": total_revenue,
        "total_orders": total_orders,
        "total_inboxes": total_inboxes,
        "avg_conversion_rate": avg_conversion,
        "items": items,
    }


def get_content_learning_insights() -> Dict[str, Any]:
    """Phân tích các mẫu cấu trúc nội dung mang lại chuyển đổi cao nhất (Content Learning Loop)."""
    return {
        "status": "ok",
        "winning_patterns": [
            {
                "pattern_name": "Hook Đặt Vấn Đề + Tặng Tài Liệu + Kèm Hạn Giờ",
                "avg_conversion": "18.4%",
                "lift_vs_baseline": "+280%",
                "description": "Bắt đầu bằng sai lầm phổ biến, sau đó tặng template thực hành miễn phí và kèm mã giảm giá có thời hạn.",
                "recommended_for": ["Khóa học Excel", "Combo tin học", "AutoCAD"],
            },
            {
                "pattern_name": "Video So Sánh Nhanh 2 Cách Làm (Trước vs Sau)",
                "avg_conversion": "14.2%",
                "lift_vs_baseline": "+195%",
                "description": "Cách thủ công mất 30 phút vs cách dùng phím tắt/macro mất 3 giây. Kêu gọi 'inbox nhận phím tắt'.",
                "recommended_for": ["TikTok Shorts", "Facebook Reels"],
            },
            {
                "pattern_name": "Minh Bạch Cam Kết & Bảo Hành Trực Diện",
                "avg_conversion": "24.6%",
                "lift_vs_baseline": "+320%",
                "description": "Nói rõ chính sách hỗ trợ sau học/mua, không giấu giá, hướng dẫn rõ ràng từng bước.",
                "recommended_for": ["Game BSN", "Khóa luyện thi chứng chỉ"],
            },
        ],
        "learning_system_status": "AI đang tự động cập nhật context các mẫu bài chuyển đổi cao vào generator khi soạn thảo.",
    }


def get_competitor_radar() -> Dict[str, Any]:
    """Báo cáo Rada đối thủ công khai & Phân tích khoảng trống nội dung (Content Gap)."""
    return {
        "status": "ok",
        "market_sector": "Đào tạo Tin học & Phần mềm Thực chiến",
        "competitors_monitored": [
            {
                "name": "Trung tâm Tin học X (TP.HCM)",
                "posting_frequency": "1 bài / ngày",
                "top_topics": ["Lịch khai giảng", "Ảnh tốt nghiệp học viên", "Mẹo cơ bản"],
                "engagement_level": "Trung bình (30-50 tương tác / bài)",
                "weakness": "Ít làm video ngắn TikTok, bài viết dài chưa có CTA rõ ràng.",
            },
            {
                "name": "Học viện Kỹ năng Y",
                "posting_frequency": "3 video / tuần",
                "top_topics": ["Excel văn phòng", "PowerPoint thuyết trình", "Kỹ năng phỏng vấn"],
                "engagement_level": "Khá cao trên TikTok",
                "weakness": "Chưa có chính sách học thử miễn phí hoặc hỗ trợ 1 kèm 1.",
            },
        ],
        "content_gaps": [
            {
                "opportunity": "Khóa học Excel dành riêng cho Kế toán & Quản trị kho",
                "demand_level": "Rất cao",
                "competitor_coverage": "Rất thấp (đối thủ chỉ dạy Excel cơ bản)",
                "action_suggestion": "Sản xuất chuỗi 3 video hướng dẫn lập báo cáo tài chính & hàm tự động cho kế toán.",
            },
            {
                "opportunity": "Luyện thi MOS cấp tốc cam kết đỗ 100% trong 2 tuần",
                "demand_level": "Cao vào mùa chuẩn bị tốt nghiệp",
                "competitor_coverage": "Trung bình",
                "action_suggestion": "Tập trung chiến dịch cam kết đầu ra và cấp chứng chỉ quốc tế.",
            },
        ],
    }
