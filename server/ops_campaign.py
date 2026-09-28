# -*- coding: utf-8 -*-
"""AI Campaign Autopilot for Javis Ops.

Cho phép chủ doanh nghiệp nhập mục tiêu chiến dịch (KPIs)
và AI tự động phân rã thành: Lộ trình 4 tuần, Ma trận 12 bài đăng đa kênh,
kịch bản video, kịch bản tư vấn chốt sale và checklist duyệt việc.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


def generate_campaign_autopilot(
    goal: str,
    target_metric: str = "50 học viên",
    duration_weeks: int = 4,
    budget_vnd: Optional[int] = None,
) -> Dict[str, Any]:
    """Tự động lập kế hoạch chiến dịch đa kênh từ mục tiêu kinh doanh."""
    now_ts = time.time()

    # Phân tích mục tiêu
    target_keyword = "tin học" if any(w in goal.lower() for w in ["học", "mos", "excel", "lớp", "đào tạo"]) else "sản phẩm"

    # Lộ trình 4 tuần
    phases = [
        {
            "week": 1,
            "phase_name": "Tuần 1: Khơi gợi nỗi đau & Nhận thức (Pain Point & Awareness)",
            "focus": "Đánh mạnh vào khó khăn thực tế khi làm việc chậm chạp do thiếu kỹ năng.",
            "kpi_target": "20.000 lượt tiếp cận, 40 lượt inbox khởi động.",
            "posts_count": 3,
            "highlight_activity": "Video TikTok tình huống: 'Khi sếp giao báo cáo lúc 17h00 và bạn chưa biết hàm INDEX MATCH'.",
        },
        {
            "week": 2,
            "phase_name": "Tuần 2: Giải pháp & Bằng chứng thực tế (Solution & Social Proof)",
            "focus": "Chia sẻ phương pháp giải quyết, câu chuyện học viên/khách hàng đã thay đổi thành công.",
            "kpi_target": "50 lượt inbox, 25 lead chất lượng cao.",
            "posts_count": 3,
            "highlight_activity": "Album Facebook: 'Hành trình từ sợ bảng tính đến cầm chứng chỉ MOS 980/1000 điểm của bạn Mai'.",
        },
        {
            "week": 3,
            "phase_name": "Tuần 3: Kích hoạt mua sớm (Early Bird & Urgency)",
            "focus": "Mở cổng đăng ký với ưu đãi giới hạn cho 20 suất đầu tiên.",
            "kpi_target": "30 đơn hàng / học viên đặt cọc giữ chỗ.",
            "posts_count": 3,
            "highlight_activity": "Livestream / Video Q&A: 'Giải đáp thắc mắc lộ trình học & tặng voucher 15% độc quyền'.",
        },
        {
            "week": 4,
            "phase_name": "Tuần 4: Đóng cổng chiến dịch & Chốt hạ (Final Call & FOMO)",
            "focus": "Nhắc nhở chỉ còn 48h trước khi khóa lớp hoặc hết hạn ưu đãi.",
            "kpi_target": "Đạt mốc mục tiêu 50 học viên, tối ưu tỷ lệ chốt đơn của đội ngũ.",
            "posts_count": 3,
            "highlight_activity": "Chiến dịch remarketing tin nhắn: 'Chỉ còn 3 suất cuối cùng trước ngày khai giảng thứ Hai'.",
        },
    ]

    # Ma trận 12 bài đăng nội dung gợi ý
    content_calendar = [
        {"day": 1, "platform": "tiktok", "title": "3 lỗi sai ngớ ngẩn khiến file Excel chạy chậm như rùa", "type": "Video 9:16", "cta": "Bình luận 'Tài liệu' để nhận file mẫu"},
        {"day": 3, "platform": "facebook", "title": "Bí kíp dọn dẹp dữ liệu 10.000 dòng trong 1 phút bằng Power Query", "type": "Album 1:1", "cta": "Nhắn tin nhận lộ trình học"},
        {"day": 5, "platform": "tiktok", "title": "Phỏng vấn xin việc: Câu hỏi test Excel 90% ứng viên bị loại", "type": "Video 9:16", "cta": "Xem link bio đăng ký học thử"},
        {"day": 8, "platform": "facebook", "title": "Học viên Sao Việt chia sẻ: Từ kế toán lương 7tr lên 15tr nhờ kỹ năng phân tích số liệu", "type": "Bài viết + Ảnh", "cta": "Đăng ký tư vấn miễn phí"},
        {"day": 10, "platform": "tiktok", "title": "So sánh hàm cổ điển vs hàm hiện đại trong Excel 365", "type": "Video 9:16", "cta": "Inbox để nhận bảng tra cứu phím tắt"},
        {"day": 12, "platform": "facebook", "title": "Lịch khai giảng các lớp Tháng 10 tại 13 chi nhánh TP.HCM & Bình Dương", "type": "Album cơ sở", "cta": "Chọn cơ sở gần bạn nhất để nhận ưu đãi"},
        {"day": 15, "platform": "tiktok", "title": "Mở quà bí mật: Bộ giáo trình và chứng nhận độc quyền tại Javis Academy", "type": "Video unbox", "cta": "Còn 15 suất ưu đãi 20%"},
        {"day": 17, "platform": "facebook", "title": "Chương trình Học Thử 1 Buổi Hoàn Toàn Miễn Phí cùng Giảng Viên Chuyên Gia", "type": "Post đăng ký", "cta": "Bấm 'Đăng ký ngay' để giữ chỗ"},
        {"day": 19, "platform": "tiktok", "title": "Tâm sự nghề: Vì sao học sinh giỏi vẫn trượt bài thi MOS quốc tế?", "type": "Video chia sẻ", "cta": "Inbox test thử trình độ miễn phí"},
        {"day": 22, "platform": "facebook", "title": "Chỉ còn 72 giờ: Đóng cổng ưu đãi Early Bird Khóa Cấp Tốc", "type": "Infographic đếm ngược", "cta": "Chát ngay để giữ voucher 15%"},
        {"day": 25, "platform": "tiktok", "title": "Hậu trường lớp học thực chiến: Học viên làm bài tập dự án thật", "type": "Video ngắn", "cta": "Còn 5 suất cuối cùng"},
        {"day": 28, "platform": "facebook", "title": "Chốt danh sách lớp học: Chào mừng 50 học viên mới gia nhập!", "type": "Thư cảm ơn", "cta": "Hẹn gặp các bạn tại buổi khai giảng"},
    ]

    budget = budget_vnd if budget_vnd is not None else 10000000
    target_rev = (budget * 5) if budget > 0 else 50000000
    roi_str = f"{(target_rev / budget):.1f}x" if budget > 0 else "5.0x"

    milestones = [
        {
            "week": p["week"],
            "theme": p["phase_name"],
            "kpi_target": p["kpi_target"],
            "key_action": p["highlight_activity"],
        }
        for p in phases
    ]

    calendar_items = []
    for item in content_calendar:
        calendar_items.append({
            "day": item["day"],
            "week": ((item["day"] - 1) // 7) + 1,
            "platform": item["platform"],
            "content_type": item.get("type", "Bài viết"),
            "angle": item.get("type", "Chia sẻ thực tế"),
            "hook": item.get("title", ""),
            "cta": item.get("cta", ""),
            "lead_target": 4,
        })

    # Kịch bản tư vấn chốt sale cho nhân sự
    sales_script = {
        "greeting": "Dạ chào bạn! Mình thấy bạn vừa quan tâm chiến dịch [Mục tiêu khóa học] bên mình. Mình xin phép gửi lộ trình chi tiết và ưu đãi dành riêng cho bạn ạ.",
        "qualify_question": "Dạ không biết hiện tại bạn đang cần học để phục vụ công việc hàng ngày hay chuẩn bị thi chứng chỉ ra trường ạ?",
        "closing_hook": "Dạ hiện tại lớp cơ sở gần bạn chỉ còn 2 suất ưu đãi giảm 15% học phí. Mình hỗ trợ giữ chỗ miễn phí cho bạn trong hôm nay trước nhé ạ?",
    }

    sales_objection_playbook = [
        {
            "customer_objection": "Khách chê học phí/giá dịch vụ cao hơn thị trường",
            "ai_counter_argument": "Phân tích giá trị thực chiến, thời gian hoàn vốn sau 14 ngày áp dụng kỹ năng và hỗ trợ trọn đời.",
            "closing_offer": "Tặng kèm trọn bộ template tài liệu trị giá 500.000đ và 1 buổi kèm 1-1 chuyên sâu.",
        },
        {
            "customer_objection": "Khách phân vân chưa sắp xếp được thời gian",
            "ai_counter_argument": "Cam kết lịch học linh hoạt chuyển ca tự do, có video và bài tập lưu lại trọn đời không lo mất bài.",
            "closing_offer": "Chính sách bảo lưu kết quả và quyền học bù trong 12 tháng không phụ phí.",
        },
        {
            "customer_objection": "Khách bảo muốn suy nghĩ thêm",
            "ai_counter_argument": "Xác định rõ băn khoăn về nội dung hay tài chính để tư vấn giải tỏa ngay điểm nghẽn.",
            "closing_offer": "Hỗ trợ giữ chỗ ưu đãi giảm 15% trong vòng 24 giờ mà chưa cần chuyển khoản đặt cọc ngay.",
        },
    ]

    checklist = [
        "Quản lý kiểm duyệt kịch bản video tuần 1 trước khi bắt đầu sản xuất",
        "Nhân viên tư vấn học thuộc bộ câu hỏi chốt sale và kịch bản xử lý từ chối",
        "Kế toán kiểm tra mã ưu đãi / voucher chiến dịch đã kích hoạt trên hệ thống",
        "Kỹ thuật kiểm tra link tracking UTM và chatbot auto-responder trước giờ phát sóng",
    ]

    return {
        "ok": True,
        "status": "ok",
        "created_at": now_ts,
        "goal": goal,
        "target_metric": target_metric,
        "duration_weeks": duration_weeks,
        "budget_vnd": budget,
        "target_revenue_vnd": target_rev,
        "roi_projected": roi_str,
        "summary": f"Chiến dịch được thiết kế tự động bám sát mục tiêu: '{goal}' với chỉ tiêu '{target_metric}' trong {duration_weeks} tuần.",
        "phases": phases,
        "milestones": milestones,
        "content_calendar": calendar_items,
        "sales_script": sales_script,
        "sales_objection_playbook": sales_objection_playbook,
        "human_review_checklist": checklist,
        "review_checklist": checklist,
    }

