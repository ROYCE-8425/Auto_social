# -*- coding: utf-8 -*-
"""AI Campaign Autopilot for Javis Ops.

Cho phép chủ doanh nghiệp nhập mục tiêu chiến dịch (KPIs)
và AI tự động phân rã thành: Lộ trình tuần, Ma trận bài đăng đa kênh,
kịch bản video, kịch bản tư vấn chốt sale và checklist duyệt việc.

Tích hợp tự động lưu trữ trạng thái bền vững (SQLite) và phân công việc Kanban.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import config
import ops_campaign_store
import task_store
import tasks


def generate_campaign_autopilot(
    goal: str,
    target_metric: str = "50 học viên",
    duration_weeks: int = 4,
    budget_vnd: Optional[int] = None,
    platforms: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Tự động lập kế hoạch chiến dịch đa kênh từ mục tiêu kinh doanh."""
    now_ts = time.time()
    valid_platforms = [str(p).strip().lower() for p in (platforms or ["tiktok", "facebook"]) if str(p).strip()]
    if not valid_platforms:
        valid_platforms = ["tiktok", "facebook"]

    # Phân tích mục tiêu
    target_keyword = "tin học" if any(w in goal.lower() for w in ["học", "mos", "excel", "lớp", "đào tạo"]) else "sản phẩm"

    # Lộ trình theo số tuần
    weeks_count = max(1, min(12, int(duration_weeks or 4)))
    phases = []
    phase_templates = [
        ("Khơi gợi nỗi đau & Nhận thức (Pain Point & Awareness)", "Đánh mạnh vào khó khăn thực tế khi làm việc chậm chạp do thiếu kỹ năng/công cụ.", "Video ngắn tình huống khó khăn thường gặp trong thực tế.", 20000, 40),
        ("Giải pháp & Bằng chứng thực tế (Solution & Social Proof)", "Chia sẻ phương pháp giải quyết, câu chuyện khách hàng đã thay đổi thành công.", "Bài viết chia sẻ hành trình thay đổi và giải pháp thực chiến.", 35000, 50),
        ("Kích hoạt mua sớm (Early Bird & Urgency)", "Mở cổng đăng ký với ưu đãi có hạn cho các suất đầu tiên.", "Livestream/Video Q&A tư vấn trực tiếp và ưu đãi đặc quyền.", 45000, 30),
        ("Đóng cổng chiến dịch & Chốt hạ (Final Call & FOMO)", "Nhắc nhở chỉ còn 48h trước khi hết hạn ưu đãi hoặc đóng cổng.", "Chiến dịch remarketing tin nhắn nhắc nhở thời hạn chót.", 50000, 20),
    ]

    for w in range(1, weeks_count + 1):
        tpl_idx = min(w - 1, len(phase_templates) - 1)
        name_sub, focus_sub, highlight_sub, reach_kpi, inbox_kpi = phase_templates[tpl_idx]
        phases.append({
            "week": w,
            "phase_name": f"Tuần {w}: {name_sub}",
            "focus": focus_sub,
            "kpi_target": f"{reach_kpi:,} lượt tiếp cận, {inbox_kpi} lượt inbox quan tâm.",
            "posts_count": 3,
            "highlight_activity": f"{highlight_sub} Cho mục tiêu: '{goal}'.",
        })

    # Ma trận bài đăng theo ngày và tuần (3 bài / tuần)
    calendar_templates = [
        {"day": 1, "title": f"3 lỗi sai ngớ ngẩn khi xử lý {target_keyword} khiến bạn mất hàng giờ", "type": "Video ngắn 9:16", "cta": "Bình luận 'Tài liệu' để nhận cẩm nang miễn phí"},
        {"day": 3, "title": f"Bí kíp giải quyết công việc 10.000 dữ liệu trong 1 phút", "type": "Album ảnh hướng dẫn", "cta": "Nhắn tin nhận lộ trình chi tiết"},
        {"day": 5, "title": f"Câu hỏi tình huống 90% người ứng tuyển bị lúng túng", "type": "Video ngắn 9:16", "cta": "Xem link bio để nhận tư vấn"},
        {"day": 8, "title": f"Khách hàng chia sẻ: Từ loay hoay bế tắc đến làm chủ kỹ năng chỉ sau 2 tuần", "type": "Bài viết + Ảnh thực tế", "cta": "Đăng ký tư vấn miễn phí ngay hôm nay"},
        {"day": 10, "title": f"So sánh cách làm truyền thống vs tự động hóa thời 4.0", "type": "Video so sánh trực quan", "cta": "Inbox để nhận bảng phân tích miễn phí"},
        {"day": 12, "title": f"Lịch phục vụ và các cơ sở sẵn sàng hỗ trợ khách hàng", "type": "Album cơ sở / Dịch vụ", "cta": "Chọn địa điểm gần bạn nhất để nhận ưu đãi"},
        {"day": 15, "title": f"Mở hộp trải nghiệm: Bộ tài liệu và quy trình chuẩn độc quyền", "type": "Video unbox / review", "cta": "Còn 15 suất ưu đãi 20%"},
        {"day": 17, "title": f"Chương trình Trải nghiệm Thử 1 Buổi Hoàn Toàn Miễn Phí cùng Chuyên Gia", "type": "Bài đăng đăng ký", "cta": "Bấm 'Đăng ký ngay' để giữ chỗ"},
        {"day": 19, "title": f"Tâm sự trong ngành: Vì sao học nhiều mà vẫn không áp dụng được vào công việc?", "type": "Video chia sẻ chân thực", "cta": "Inbox test thử trình độ miễn phí"},
        {"day": 22, "title": f"Chỉ còn 72 giờ: Đóng cổng ưu đãi Early Bird chiến dịch", "type": "Infographic đếm ngược", "cta": "Chat ngay để giữ voucher ưu đãi"},
        {"day": 25, "title": f"Hậu trường quy trình thực chiến: Đội ngũ triển khai dự án thật", "type": "Video ngắn hậu trường", "cta": "Còn 5 suất cuối cùng"},
        {"day": 28, "title": f"Chốt danh sách chiến dịch: Chào mừng các thành viên mới gia nhập!", "type": "Thư cảm ơn khách hàng", "cta": "Hẹn gặp các bạn tại đợt triển khai tới"},
    ]

    total_posts = weeks_count * 3
    calendar_items = []
    for idx in range(total_posts):
        tpl = calendar_templates[idx % len(calendar_templates)]
        day = (idx // 3) * 7 + ((idx % 3) * 2 + 1)
        plat = valid_platforms[idx % len(valid_platforms)]
        calendar_items.append({
            "day": day,
            "week": ((day - 1) // 7) + 1,
            "platform": plat,
            "content_type": tpl.get("type", "Bài viết"),
            "angle": tpl.get("type", "Chia sẻ thực tế"),
            "hook": tpl.get("title", ""),
            "cta": tpl.get("cta", ""),
            "lead_target": 4,
        })

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

    # Kịch bản tư vấn chốt sale cho nhân sự
    sales_script = {
        "greeting": f"Dạ chào bạn! Mình thấy bạn vừa quan tâm chiến dịch '{goal}' bên mình. Mình xin phép gửi thông tin chi tiết và ưu đãi dành riêng cho bạn ạ.",
        "qualify_question": "Dạ không biết hiện tại bạn đang cần phục vụ công việc hàng ngày hay chuẩn bị cho kế hoạch sắp tới ạ?",
        "closing_hook": "Dạ hiện tại bên mình chỉ còn 2 suất ưu đãi giảm 15% trong đợt này. Mình hỗ trợ giữ chỗ miễn phí cho bạn trong hôm nay trước nhé ạ?",
    }

    sales_objection_playbook = [
        {
            "customer_objection": "Khách chê chi phí/giá dịch vụ cao hơn mặt bằng",
            "ai_counter_argument": "Phân tích giá trị thực tế, thời gian hoàn vốn nhanh chóng sau khi áp dụng và cam kết hỗ trợ trọn đời.",
            "closing_offer": "Tặng kèm trọn bộ template tài liệu trị giá 500.000đ và 1 buổi tư vấn 1-1 chuyên sâu.",
        },
        {
            "customer_objection": "Khách phân vân chưa sắp xếp được thời gian",
            "ai_counter_argument": "Cam kết lịch trình linh hoạt, tài liệu và video lưu trữ đầy đủ không lo bị mất bài.",
            "closing_offer": "Chính sách bảo lưu kết quả và quyền tham gia bù trong 12 tháng không phụ phí.",
        },
        {
            "customer_objection": "Khách bảo muốn suy nghĩ thêm",
            "ai_counter_argument": "Xác định rõ băn khoăn về nội dung hay tài chính để tư vấn giải tỏa ngay điểm nghẽn.",
            "closing_offer": "Hỗ trợ giữ chỗ ưu đãi giảm 15% trong vòng 24 giờ mà chưa cần thanh toán ngay.",
        },
    ]

    checklist = [
        f"Quản lý kiểm duyệt kế hoạch và ma trận bài đăng chiến dịch '{goal}'",
        "Nhân viên tư vấn học thuộc bộ câu hỏi chốt sale và kịch bản xử lý từ chối",
        "Kế toán kiểm tra mã ưu đãi / voucher chiến dịch đã kích hoạt trên hệ thống",
        f"Kỹ thuật kiểm tra link tracking UTM và chatbot auto-responder trên các kênh ({', '.join(valid_platforms)})",
    ]

    return {
        "ok": True,
        "status": "ok",
        "created_at": now_ts,
        "goal": goal,
        "target_metric": target_metric,
        "duration_weeks": weeks_count,
        "budget_vnd": budget,
        "target_revenue_vnd": target_rev,
        "roi_projected": roi_str,
        "platforms": valid_platforms,
        "summary": f"Chiến dịch được thiết kế tự động bám sát mục tiêu: '{goal}' với chỉ tiêu '{target_metric}' trong {weeks_count} tuần trên các kênh {', '.join(valid_platforms)}.",
        "phases": phases,
        "milestones": milestones,
        "content_calendar": calendar_items,
        "sales_script": sales_script,
        "sales_objection_playbook": sales_objection_playbook,
        "human_review_checklist": checklist,
        "review_checklist": checklist,
    }


def enqueue_campaign_kanban_tasks(
    campaign_id: str,
    goal: str,
    budget_vnd: int,
    platforms: List[str],
    brain_root: Optional[str] = None,
) -> List[str]:
    """Enqueue 4 nhiệm vụ Kanban chuẩn cho một chiến dịch mới:

    1. [Review] Phê duyệt kế hoạch & ngân sách
    2. [Content] Sản xuất nội dung các bài đăng
    3. [Publishing] Chuẩn bị lịch xuất bản đa kênh
    4. [Follow-up] Triển khai kịch bản tư vấn & chốt sale

    Nếu Kanban enqueue fail, raise Exception để caller xử lý và trả lỗi rõ ràng.
    """
    feature = tasks.current()
    plat_str = ", ".join(platforms) if platforms else "đa kênh"
    budget_str = f"{budget_vnd:,.0f} đ" if budget_vnd else "tự chủ"

    task_specs = [
        {
            "title": f"[Review Campaign] Kiểm duyệt kế hoạch chiến dịch: {goal[:60]}",
            "intent": f"Kiểm duyệt mục tiêu '{goal}', ngân sách {budget_str} và checklist phê duyệt của chiến dịch {campaign_id}.",
            "priority": 1,
            "needs_approval": True,
        },
        {
            "title": f"[Content Production] Sản xuất nội dung đa kênh: {goal[:60]}",
            "intent": f"Soạn thảo nội dung và kịch bản video trên các nền tảng ({plat_str}) cho chiến dịch {campaign_id}.",
            "priority": 2,
            "needs_approval": False,
        },
        {
            "title": f"[Publishing Schedule] Chuẩn bị lịch xuất bản: {goal[:60]}",
            "intent": f"Cấu hình lịch đăng và kênh xuất bản ({plat_str}) cho chiến dịch {campaign_id}. Không tự ý đăng khi chưa có lệnh duyệt.",
            "priority": 2,
            "needs_approval": False,
        },
        {
            "title": f"[Sales Follow-up] Triển khai kịch bản tư vấn: {goal[:60]}",
            "intent": f"Học kịch bản tư vấn, xử lý từ chối và quy trình chuyển đổi khách hàng từ chiến dịch {campaign_id}.",
            "priority": 2,
            "needs_approval": False,
        },
    ]

    task_ids: List[str] = []
    # Sử dụng TaskStore với STATE_DIR hiện hành
    kanban_db_path = config.STATE_DIR / "kanban.sqlite3"
    t_store = task_store.TaskStore(kanban_db_path)

    # Xác định brain root thích hợp
    root = brain_root
    if not root:
        if feature:
            roots = feature._brain_roots()
            root = roots[0] if roots else str(config.STATE_DIR)
        else:
            root = str(config.STATE_DIR)

    for spec in task_specs:
        try:
            tid = t_store.enqueue(
                brain_root=root,
                title=spec["title"],
                intent=spec["intent"],
                route="auto",
                priority=spec["priority"],
                needs_approval=spec["needs_approval"],
                created_by="campaign_autopilot",
                idempotency_key=f"camp:{campaign_id}:{spec['title'][:30]}",
            )
            task_ids.append(tid)
            if feature:
                feature.wake()
        except Exception as exc:
            raise RuntimeError(f"Lỗi khi enqueue Kanban task '{spec['title']}': {exc}") from exc

    return task_ids


def create_autopilot_campaign(
    goal: str,
    target_metric: str = "50 học viên",
    duration_weeks: int = 4,
    budget_vnd: Optional[int] = None,
    platforms: Optional[List[str]] = None,
    db_path: Path | str | None = None,
) -> Dict[str, Any]:
    """Quy trình tổng thể: Validate -> Generate plan -> Persist SQLite -> Enqueue Kanban -> Return."""
    # 1. Validation nghiêm ngặt
    goal_clean = str(goal or "").strip()
    if not goal_clean or len(goal_clean) < 3:
        raise ValueError("Mục tiêu chiến dịch (goal) là bắt buộc và phải có ít nhất 3 ký tự.")

    if budget_vnd is not None:
        try:
            budget_val = int(budget_vnd)
            if budget_val < 0:
                raise ValueError("Ngân sách chiến dịch (budget_vnd) phải là số không âm.")
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Ngân sách chiến dịch (budget_vnd) không hợp lệ: {exc}")
    else:
        budget_val = 10000000

    try:
        duration_val = int(duration_weeks or 4)
        if duration_val < 1 or duration_val > 52:
            raise ValueError("Thời gian chiến dịch (duration_weeks) phải từ 1 đến 52 tuần.")
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Thời gian chiến dịch (duration_weeks) không hợp lệ: {exc}")

    if platforms is not None:
        if not isinstance(platforms, list) or len(platforms) == 0:
            raise ValueError("Danh sách nền tảng (platforms) phải là danh sách hợp lệ ít nhất một nền tảng.")
        valid_platforms = [str(p).strip().lower() for p in platforms if str(p).strip()]
        if not valid_platforms:
            raise ValueError("Danh sách nền tảng (platforms) không chứa nền tảng hợp lệ.")
    else:
        valid_platforms = ["tiktok", "facebook"]

    # 2. Sinh kế hoạch
    plan = generate_campaign_autopilot(
        goal=goal_clean,
        target_metric=target_metric or "50 học viên",
        duration_weeks=duration_val,
        budget_vnd=budget_val,
        platforms=valid_platforms,
    )

    calendar_items = plan.get("content_calendar") or []

    # 3. Lưu chiến dịch vào SQLite
    campaign = ops_campaign_store.create_campaign(
        goal=goal_clean,
        target_metric=str(target_metric or "50 học viên").strip(),
        duration_weeks=duration_val,
        budget_vnd=budget_val,
        target_revenue_vnd=int(plan.get("target_revenue_vnd") or 50000000),
        roi_projected=str(plan.get("roi_projected") or "5.0x"),
        platforms=valid_platforms,
        plan=plan,
        items=calendar_items,
        db_path=db_path,
    )
    cid = campaign["id"]

    # 4. Enqueue Kanban Tasks (Nếu fail phải xóa record vừa tạo và raise lỗi rõ ràng)
    try:
        task_ids = enqueue_campaign_kanban_tasks(
            campaign_id=cid,
            goal=goal_clean,
            budget_vnd=budget_val,
            platforms=valid_platforms,
        )
    except Exception as exc:
        # Rollback: Xóa chiến dịch vừa lưu để không để lại trạng thái rác
        ops_campaign_store.delete_campaign(cid, db_path=db_path)
        raise RuntimeError(f"Khởi tạo Kanban tasks thất bại: {exc}") from exc

    # 5. Cập nhật task_ids vào database
    ops_campaign_store.update_campaign_task_ids(cid, task_ids, db_path=db_path)
    campaign["task_ids"] = task_ids

    return {
        "ok": True,
        "campaign_id": cid,
        "task_ids": task_ids,
        "status": "active",
        "campaign_plan": plan,
        "items": campaign.get("items") or [],
        **plan,
    }
