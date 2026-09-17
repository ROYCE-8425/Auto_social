"""Module Trợ lý Hỏi đáp Ca làm việc trên /ops (Ops Q&A Assistant).
docs/dev/2026-09-17-ops-hoi-dap-javis.md

Tôn chỉ:
1. Nhân viên không cầm buồng lái: Không terminal, không MCP, không lấy token, không gửi Graph từ chat.
2. Grounding chặt chẽ: Dựa vào Brand Kit trong scope, Care stats 24h, danh sách nháp, CRM (SĐT che cho staff), docs vận hành.
3. Không bịa giá: Nếu kit không có giá/học phí cụ thể -> cấm bịa, hướng dẫn xin inbox/hotline.
4. Rate limit: 20 câu / 10 phút / user.
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Optional

import aux_engine
import config as cfgmod
from brand_kit import detect_brand_from_kit, parse_brand_kit_channels, load_all_brand_kits
import fanpage_care_store as store
from fanpage_care_ground import address_short, sanitize_kit

_RATE_LIMITS: dict[str, list[float]] = {}
_RATE_LIMIT_WINDOW = 600.0  # 10 phút (600 giây)
_RATE_LIMIT_MAX = 20        # Tối đa 20 câu


def check_rate_limit(user_id: str) -> bool:
    """Kiểm tra giới hạn tần suất gọi 20 câu / 10 phút / user."""
    now = time.time()
    uid = str(user_id or "anonymous").strip()
    timestamps = _RATE_LIMITS.get(uid, [])
    # Lọc bỏ các timestamp ngoài cửa sổ 10 phút
    timestamps = [t for t in timestamps if now - t < _RATE_LIMIT_WINDOW]
    if len(timestamps) >= _RATE_LIMIT_MAX:
        _RATE_LIMITS[uid] = timestamps
        return False
    timestamps.append(now)
    _RATE_LIMITS[uid] = timestamps
    return True


def mask_phone(phone: str) -> str:
    """Che số điện thoại hiển thị cho nhân viên (vd: 0912***456)."""
    if not phone:
        return ""
    clean = re.sub(r"\D", "", str(phone))
    if len(clean) >= 9:
        return clean[:4] + "***" + clean[-3:]
    if len(clean) >= 6:
        return clean[:3] + "***" + clean[-2:]
    return "***"


def _check_prohibited_intent(message: str) -> Optional[dict[str, Any]]:
    """Phát hiện và chặn các câu hỏi / hành vi ngoài thẩm quyền của nhân viên."""
    msg_lower = message.lower().strip()

    # 1. Các hành vi can thiệp hệ thống / buồng lái / token
    sys_patterns = [
        "xóa page", "xoá page", "xoa page", "delete page",
        "lấy token", "lay token", "đổi token", "doi token", "access_token", "access token",
        "app_secret", "app secret", "postpeer key", "postpeer_key",
        "claude.md", "agents.md", "mở mcp", "mo mcp", "open mcp",
        "terminal", "shell", "bash", "cmd.exe", "powershell", "run command", "chạy lệnh",
        "vào buồng lái", "buồng lái", "buong lai", "cầm buồng lái",
    ]
    for pat in sys_patterns:
        if pat in msg_lower:
            return {
                "ok": True,
                "reply": (
                    "Tôi là trợ lý ca CSKH Javis Ops và không có quyền can thiệp hệ thống, lấy token, "
                    "chạy lệnh terminal hoặc xóa Fanpage. Mọi thao tác buồng lái xin vui lòng liên hệ trực tiếp Chủ máy."
                ),
                "citations": [],
                "used_stats": False,
            }

    # 2. Yêu cầu gửi tin nhắn / bình luận Facebook trực tiếp từ chat
    fb_send_patterns = [
        "gửi tin facebook", "gui tin facebook", "gửi tin fb", "gui tin fb",
        "gửi tin nhắn hộ", "gui tin nhan ho", "nhắn tin cho khách hộ", "nhan tin cho khach ho",
        "reply comment hộ", "reply comment ho", "trả lời bình luận hộ", "tra loi binh luan ho",
        "gửi graph", "gui graph", "bấm gửi hộ", "bam gui ho", "gửi tin nhắn này đi",
    ]
    for pat in fb_send_patterns:
        if pat in msg_lower:
            return {
                "ok": True,
                "reply": (
                    "Tôi không có quyền gửi tin nhắn hoặc bình luận trực tiếp từ khung chat này để đảm bảo an toàn. "
                    "Để gửi tin cho khách hàng, bạn vui lòng chuyển sang tab **Hộp thư & Nháp** trên /ops "
                    "và bấm nút **Gửi** tại dòng nháp tương ứng."
                ),
                "citations": ["docs/28-cham-soc-fanpage.md"],
                "used_stats": False,
            }

    return None


def _resolve_scope_pages(
    scope_raw: Any, vault_root: Path
) -> tuple[list[dict[str, Any]], str]:
    """Phân giải phạm vi trang theo scope từ frontend hoặc filter.
    Trả về (danh sách trang hợp lệ, nhãn scope hiển thị).
    """
    all_kits = load_all_brand_kits(vault_root)
    eligible_pages = []
    for k in all_kits:
        if k.facebook.enabled and k.facebook.ids.get("page_id"):
            eligible_pages.append({
                "page_id": k.facebook.ids["page_id"],
                "name": k.name or k.filename,
                "brand": k.brand,
                "kit_file": k.filename,
                "raw_content": k.raw_content,
            })

    scope_str = ""
    if isinstance(scope_raw, str):
        scope_str = scope_raw.strip().lower()
    elif isinstance(scope_raw, dict):
        scope_str = str(scope_raw.get("scope_brand") or scope_raw.get("scope_page_id") or scope_raw.get("scope") or "").strip().lower()

    if not scope_str or scope_str == "all":
        return eligible_pages, "Tất cả thương hiệu"

    if scope_str in ("bsn", "game"):
        filtered = [p for p in eligible_pages if p["brand"] == "bsn"]
        return (filtered or eligible_pages), "Game Giá Rẻ BSN"

    if scope_str in ("saoviet", "tin-hoc", "tinhoc"):
        filtered = [p for p in eligible_pages if p["brand"] == "saoviet"]
        return (filtered or eligible_pages), "Tin Học Sao Việt"

    # Match theo page_id cụ thể
    filtered = [p for p in eligible_pages if p["page_id"] == scope_str]
    if filtered:
        return filtered, filtered[0]["name"]

    return eligible_pages, "Tất cả thương hiệu"


async def answer_ops_qa(
    message: str,
    scope: Any,
    user: dict[str, Any],
    vault_root: Optional[Path | str] = None,
) -> dict[str, Any]:
    """Xử lý câu hỏi của nhân viên trực ca trên /ops."""
    v_root = Path(vault_root) if vault_root else (Path(cfgmod.STATE_DIR).parent / "brains" / "Brain Default")
    if not v_root.exists():
        v_root = Path(__file__).resolve().parents[1] / "brains" / "Brain Default"

    user_id = str(user.get("id") or user.get("username") or "staff")
    user_role = str(user.get("role") or "staff")

    # 1. Rate limit
    if not check_rate_limit(user_id):
        return {
            "ok": False,
            "error": "Bạn đã hỏi quá 20 câu trong 10 phút. Vui lòng nghỉ tay một lát rồi tiếp tục nhé!",
            "reply": "Bạn đã vượt quá giới hạn 20 câu hỏi / 10 phút. Vui lòng thử lại sau.",
            "citations": [],
            "used_stats": False,
        }

    # 2. Check prohibited intent
    banned_res = _check_prohibited_intent(message)
    if banned_res:
        return banned_res

    # 3. Resolve scope
    pages, scope_label = _resolve_scope_pages(scope, v_root)
    target_pids = [p["page_id"] for p in pages if p.get("page_id")]

    # 4. Gather Care Snapshot (Stats & Drafts)
    care_stats = {}
    try:
        care_stats = store.get_stats(page_ids=target_pids if target_pids else None)
    except Exception:
        care_stats = {"pending_drafts": 0, "events_24h": 0, "replies_24h": 0, "leads_24h": 0}

    pending_drafts = []
    try:
        pending_drafts = store.list_drafts(page_ids=target_pids if target_pids else None, status="pending", limit=5)
    except Exception:
        pending_drafts = []

    pending_cmt_count = care_stats.get("pending_comment_drafts", 0)
    pending_msg_count = care_stats.get("pending_message_drafts", 0)
    total_pending = care_stats.get("pending_drafts", pending_cmt_count + pending_msg_count)

    # 5. Gather Kit Details
    kit_summaries = []
    has_any_price_info = False
    hotlines_in_scope = []
    for p in pages:
        raw_md = p.get("raw_content") or ""
        m_hotline = re.search(r"(?:Hotline / Zalo|Hotline riêng|Hotline):\s*([^\n]+)", raw_md, re.I)
        hotline = m_hotline.group(1).strip() if m_hotline else ""
        if hotline and hotline not in hotlines_in_scope:
            hotlines_in_scope.append(hotline)

        m_addr = re.search(r"(?:Cơ sở / địa chỉ|Địa chỉ):\s*([^\n]+)", raw_md, re.I)
        addr = m_addr.group(1).strip() if m_addr else ""

        # Kiểm tra xem kit có liệt kê giá cụ thể không
        if "giá:" in raw_md.lower() or "học phí:" in raw_md.lower():
            has_any_price_info = True

        kit_summaries.append(
            f"Thương hiệu: {p['name']} (Kit: {p['kit_file']})\n"
            f"- Hotline/Zalo: {hotline or 'Xem trên trang'}\n"
            f"- Địa chỉ/Hình thức: {addr or 'Online / Các chi nhánh niêm yết'}\n"
        )
    primary_hotline = hotlines_in_scope[0] if hotlines_in_scope else "trên trang"

    # 6. Customer lookup nếu tin nhắn có dấu hiệu tìm khách
    customer_matches = []
    msg_low = message.lower()
    is_cust_search = any(k in msg_low for k in ("khách", "check ib", "khach", "sđt", "sdt", "sdt:", "tìm khách")) or bool(re.search(r"\d{7,11}", message))
    if is_cust_search:
        clean_q = re.sub(r"(hỏi|tìm|xem|khách|check ib|cho em hỏi|là ai|thế nào|\?|:)", " ", msg_low).strip()
        try:
            found_custs = store.search_customers(query=clean_q if len(clean_q) >= 2 else None, limit=3)
            for c in found_custs:
                phones = c.get("phones") or []
                masked_phones = [mask_phone(ph) for ph in phones]
                customer_matches.append({
                    "name": c.get("name") or "Khách hàng",
                    "phones": masked_phones,
                    "tags": c.get("tags") or [],
                    "course_interest": c.get("course_interest") or "",
                })
        except Exception:
            pass

    # 7. Check if price was asked
    price_asked = any(w in msg_low for w in ("giá", "gia", "học phí", "hoc phi", "chi phí", "chi phi", "bao nhiêu tiền", "bao nhieu tien"))

    # 8. Hướng dẫn vận hành (Takeover, Duyệt nháp)
    takeover_asked = "takeover" in msg_low or "nhận lại" in msg_low or "tranh lời" in msg_low
    drafts_asked = "nháp" in msg_low or "nhap" in msg_low or "hôm nay" in msg_low or "thống kê" in msg_low or "tình hình" in msg_low

    citations = []
    if pages:
        citations.append(pages[0]["kit_file"])
    if takeover_asked:
        citations.append("docs/28-cham-soc-fanpage.md")

    # Xây dựng System Prompt cho LLM
    system_prompt = (
        f"Bạn là trợ lý ca CSKH Javis Ops. Nhiệm vụ của bạn là hỗ trợ nhân viên trực ca tra cứu thông tin nhanh.\n"
        f"Phạm vi thương hiệu đang chọn: {scope_label}.\n\n"
        "QUY TẮC BẮT BUỘC:\n"
        "1. CHỈ dùng số liệu và thông tin có trong Context bên dưới. CẤM BỊA SỐ LIỆU, SỐ ĐIỆN THOẠI HOẶC GIÁ TIỀN.\n"
        "2. Nếu nhân viên hỏi giá / học phí mà trong Brand Kit không có con số cụ thể cho mặt hàng/khoá học đó, "
        f"bạn BẮT BUỘC từ chối bịa giá và dặn nhân viên hướng dẫn khách inbox hoặc liên hệ Hotline {primary_hotline}.\n"
        "3. Tuyệt đối không gửi tin nhắn Facebook hộ; hướng dẫn nhân viên bấm nút 'Gửi' trên Hộp thư.\n"
        "4. Tuyệt đối không cung cấp token, mật khẩu hoặc hướng dẫn vào buồng lái /app.\n"
        "5. Định dạng đầu ra BẮT BUỘC là 1 JSON object duy nhất:\n"
        '{\n  "reply": "Nội dung trả lời nhân viên ngắn gọn, lịch sự, đúng trọng tâm",\n  "citations": ["tên_file.md"],\n  "used_stats": true/false\n}'
    )

    context_lines = [
        f"=== THỐNG KÊ CA TRỰC ({scope_label}) ===",
        f"- Nháp bình luận chờ duyệt: {pending_cmt_count}",
        f"- Nháp tin nhắn Messenger chờ duyệt: {pending_msg_count}",
        f"- Tổng số nháp đang chờ: {total_pending}",
        f"- Tương tác 24h qua: {care_stats.get('events_24h', 0)}",
        f"- Khách tiềm năng (Leads) 24h: {care_stats.get('leads_24h', 0)}",
        "",
        "=== BRAND KIT TRONG PHẠM VI ===",
        "\n".join(kit_summaries),
    ]

    if customer_matches:
        context_lines.append("=== THÔNG TIN KHÁCH HÀNG TÌM THẤY ===")
        for cm in customer_matches:
            context_lines.append(f"- Tên: {cm['name']}, SĐT: {', '.join(cm['phones'])}, Nhãn: {', '.join(cm['tags'])}")
        context_lines.append("")

    if takeover_asked:
        context_lines.append(
            "=== TÀI LIỆU VẬN HÀNH: HUMAN TAKEOVER ===\n"
            "- Takeover là cơ chế tạm dừng AI khi nhân viên can thiệp thủ công: Khi nhân viên vào trả lời tin nhắn của khách trên Messenger/Inbox, "
            "Javis tự động lùi lại và tạm dừng trả lời tự động trong 24 giờ để tránh tranh lời nhân viên.\n"
            "- Nút bấm: Sau khi nhân viên tư vấn xong hoặc muốn bàn giao lại cho AI trực, nhân viên mở tab Hộp thư & Nháp -> "
            "bấm nút 'Javis nhận lại' (Release Takeover) để AI tiếp tục chăm sóc hội thoại đó."
        )

    user_prompt = f"--- CONTEXT ---\n" + "\n".join(context_lines) + f"\n\nCâu hỏi của nhân viên trực ca: {message}"

    # 9. Gọi aux_engine.complete_json (với timeout 20s, tools=[])
    used_stats = drafts_asked or "hôm nay" in msg_low
    try:
        llm_res = await aux_engine.complete_json(system_prompt, user_prompt, timeout_s=20)
        if isinstance(llm_res, dict) and not llm_res.get("refuse") and llm_res.get("reply"):
            rep = str(llm_res.get("reply") or "").strip()
            cites = llm_res.get("cite_files") or citations
            return {
                "ok": True,
                "reply": rep,
                "citations": cites,
                "used_stats": bool(llm_res.get("used_stats", used_stats)),
            }
    except Exception:
        pass

    # 10. Deterministic Rules-First Fallback khi không có LLM / timeout / offline
    reply = ""
    if price_asked and not has_any_price_info:
        reply = (
            f"Trong tài liệu Brand Kit của {scope_label} hiện tại không có bảng giá hoặc mức học phí cụ thể. "
            f"Bạn vui lòng hướng dẫn khách nhắn tin inbox hoặc liên hệ Hotline/Zalo {primary_hotline} để được tư vấn chính xác, "
            f"tránh tự báo giá sai nhé."
        )
    elif takeover_asked:
        reply = (
            "Takeover là cơ chế tạm dừng AI: Khi bạn hoặc nhân sự can thiệp chat thủ công với khách trên Messenger, "
            "Javis sẽ tự động ngưng trả lời trong 24h để không tranh lời nhân viên. "
            "Khi bạn xử lý xong và muốn AI trực tiếp tục, hãy vào tab **Hộp thư & Nháp** và bấm nút **'Javis nhận lại'** (Release Takeover)."
        )
    elif drafts_asked:
        reply = (
            f"Tình hình ca trực {scope_label} hôm nay: Hiện có {total_pending} nháp đang chờ duyệt "
            f"({pending_cmt_count} nháp bình luận, {pending_msg_count} nháp tin nhắn Messenger). "
            f"Trong 24h qua có {care_stats.get('events_24h', 0)} lượt tương tác và {care_stats.get('leads_24h', 0)} khách để lại thông tin. "
            f"Bạn hãy mở tab **Hộp thư & Nháp** để kiểm tra và bấm nút **Gửi** nhé!"
        )
    elif customer_matches:
        c_info = []
        for cm in customer_matches:
            c_info.append(f"• {cm['name']} — SĐT: {', '.join(cm['phones'])} (Tags: {', '.join(cm['tags']) or 'Chưa gắn'})")
        reply = f"Tìm thấy thông tin khách hàng trong hệ thống:\n" + "\n".join(c_info)
    else:
        reply = (
            f"Chào bạn, tôi là trợ lý ca CSKH Javis Ops ({scope_label}). "
            f"Hiện tại có {total_pending} nháp chờ duyệt trên Hộp thư. "
            f"Hotline hỗ trợ của kit là {primary_hotline}. Bạn cần kiểm tra số liệu nháp, thông tin khách hàng hay hướng dẫn ca làm việc nào?"
        )

    return {
        "ok": True,
        "reply": reply,
        "citations": citations,
        "used_stats": used_stats,
    }
