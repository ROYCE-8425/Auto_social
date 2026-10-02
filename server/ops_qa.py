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

try:
    import ops_order_store
except Exception:
    ops_order_store = None

try:
    import ops_documents_store
except Exception:
    ops_documents_store = None

try:
    import ops_tasks_store
except Exception:
    ops_tasks_store = None


def _fmt_price(num: Any) -> str:
    try:
        val = float(num)
        return f"{val:,.0f} đ".replace(",", ".")
    except Exception:
        return str(num)


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
                    "Tôi là trợ lý ca CSKH Sèo Trum Ops và không có quyền can thiệp hệ thống, lấy token, "
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

    if scope_str in ("saoviet", "tin-hoc", "tinhoc", "royce", "royceshop"):
        filtered = [p for p in eligible_pages if p["brand"] in ("saoviet", "royce", "royceshop")]
        return (filtered or eligible_pages), "Royce Shop"

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
        clean_q = re.sub(r"(hỏi|tìm|xem|khách|check ib|cho mình hỏi|là ai|thế nào|\?|:)", " ", msg_low).strip()
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

    # 7. Tra cứu Sản phẩm & Bảng giá (ops_order_store)
    price_asked = any(w in msg_low for w in ("giá", "gia", "học phí", "hoc phi", "chi phí", "chi phi", "bao nhiêu tiền", "bao nhieu tien", "báo giá", "bao gia"))
    prod_asked = price_asked or any(w in msg_low for w in ("khóa học", "khoa hoc", "sản phẩm", "san pham", "mặt hàng", "mat hang", "sku", "bàn phím", "chuột", "sách", "game"))
    found_products = []
    if prod_asked and ops_order_store:
        try:
            clean_prod_q = re.sub(r"(hỏi|tìm|xem|báo giá|bao gia|giá|học phí|hoc phi|chi phí|chi phi|bao nhiêu|bao nhieu|tiền|tien|khoá học|khoa hoc|sản phẩm|san pham|mặt hàng|mat hang|cho mình|với ạ|\?|:)", " ", msg_low).strip()
            if clean_prod_q and len(clean_prod_q) >= 2:
                found_products = ops_order_store.search_products(clean_prod_q)
            if not found_products:
                all_prods = ops_order_store.list_products(active_only=True)
                # Lọc nhẹ nếu có từ khóa
                if clean_prod_q:
                    words = [w for w in clean_prod_q.split() if len(w) >= 2]
                    found_products = [p for p in all_prods if any(w in p["name"].lower() or w in p["sku"].lower() for w in words)]
                if not found_products and (price_asked or "bảng giá" in msg_low or "danh mục" in msg_low):
                    found_products = all_prods[:6]
        except Exception:
            found_products = []

    # 8. Tra cứu Kho văn bản, Hợp đồng & SOP (ops_documents_store)
    doc_asked = any(w in msg_low for w in ("văn bản", "van ban", "hợp đồng", "hop dong", "sop", "tài liệu", "tai lieu", "hết hạn", "het han", "chờ duyệt", "cho duyet", "quy trình", "quy trinh", "biểu mẫu", "bieu mau", "template", "nda"))
    doc_stats = {}
    found_docs = []
    if doc_asked and ops_documents_store:
        try:
            doc_stats = ops_documents_store.get_stats()
            # Lọc tài liệu theo ý định
            cat_filter = None
            if "hợp đồng" in msg_low or "hop dong" in msg_low:
                cat_filter = "contract"
            elif "sop" in msg_low or "quy trình" in msg_low:
                cat_filter = "sop"
            elif "biểu mẫu" in msg_low or "template" in msg_low:
                cat_filter = "template"

            status_filter = "pending" if ("chờ duyệt" in msg_low or "chưa duyệt" in msg_low) else None
            res_docs = ops_documents_store.list_documents(category=cat_filter, approval_status=status_filter, limit=10)
            all_list = res_docs.get("documents", []) if isinstance(res_docs, dict) else []
            if "hết hạn" in msg_low:
                now_ts = time.time()
                found_docs = [d for d in all_list if d.get("expires_at") and float(d["expires_at"]) <= now_ts + 30 * 86400]
            else:
                found_docs = all_list[:5]
        except Exception:
            doc_stats = {}
            found_docs = []

    # 9. Tra cứu Đơn hàng & Vận đơn GHN (ops_order_store)
    order_asked = any(w in msg_low for w in ("đơn", "don", "vận đơn", "van don", "ghn", "tracking", "giao hàng", "giao hang", "ship", "ord_")) or "ghnmock" in msg_low
    found_shipment = None
    found_orders = []
    if order_asked and ops_order_store:
        try:
            m_ghn = re.search(r"(GHNMOCK-[A-Za-z0-9-]+|[A-Z0-9]{8,15})", message)
            m_ord = re.search(r"(ord_[a-z0-9]+)", message, re.I)
            if m_ghn:
                t_code = m_ghn.group(1).strip()
                found_shipment = ops_order_store.get_shipment_by_tracking(t_code)
                if found_shipment and found_shipment.get("order_id"):
                    ord_obj = ops_order_store.get_order(found_shipment["order_id"])
                    if ord_obj:
                        found_orders.append(ord_obj)
            elif m_ord:
                ord_obj = ops_order_store.get_order(m_ord.group(1).strip())
                if ord_obj:
                    found_orders.append(ord_obj)
            else:
                clean_ord_q = re.sub(r"(hỏi|tìm|xem|đơn hàng|don hang|vận đơn|van don|ghn|ship|trạng thái|trang thai|\?|:)", " ", msg_low).strip()
                if clean_ord_q and len(clean_ord_q) >= 2:
                    found_orders = ops_order_store.list_orders(search=clean_ord_q, limit=3)
                else:
                    found_orders = ops_order_store.list_orders(limit=3)
        except Exception:
            found_shipment = None
            found_orders = []

    # 10. Tra cứu Việc ca trực & Cứu lead Kanban (ops_tasks_store)
    task_asked = any(w in msg_low for w in ("việc", "viec", "nhiệm vụ", "nhiem vu", "task", "kanban", "cần làm", "can lam", "gấp", "gap", "cứu lead", "cuu lead"))
    found_tasks = []
    if task_asked and ops_tasks_store:
        try:
            all_tasks = ops_tasks_store.load_tasks()
            found_tasks = [t for t in all_tasks if (t.get("isUrgent") or "rescue" in str(t.get("id", ""))) and t.get("columnId") != "done"]
            if not found_tasks:
                found_tasks = all_tasks[:5]
        except Exception:
            found_tasks = []

    # 11. Hướng dẫn vận hành (Takeover, Duyệt nháp, Tổng quan)
    takeover_asked = any(w in msg_low for w in ("takeover", "nhận lại", "tranh lời", "tiếp quản", "can thiệp", "dừng ai", "dừng bot", "nhường lời", "ai trực"))
    drafts_asked = any(w in msg_low for w in ("nháp", "nhap", "hôm nay", "thống kê", "tình hình", "briefing", "tổng hợp", "tong hop", "báo cáo", "bao cao", "tổng quan", "tong quan"))


    citations = []
    if pages:
        citations.append(pages[0]["kit_file"])
    if takeover_asked:
        citations.append("docs/28-cham-soc-fanpage.md")
    if found_products:
        citations.append("facts/ops_business_catalog.md")
    if doc_asked or found_docs:
        citations.append("facts/ops_documents_vault.md")
    if order_asked or found_shipment or found_orders:
        citations.append("facts/ops_shipping_and_operations.md")

    # Xây dựng System Prompt cho LLM
    system_prompt = (
        f"Bạn là trợ lý ca CSKH Sèo Trum Ops Hub. Nhiệm vụ của bạn là hỗ trợ nhân viên trực ca tra cứu thông tin nhanh.\n"
        f"Phạm vi thương hiệu đang chọn: {scope_label}.\n\n"
        "QUY TẮC BẮT BUỘC:\n"
        "1. CHỈ dùng số liệu và thông tin có trong Context bên dưới. CẤM BỊA SỐ LIỆU, SỐ ĐIỆN THOẠI HOẶC GIÁ TIỀN.\n"
        "2. Nếu hỏi giá/sản phẩm: Báo giá niêm yết chính xác từ bảng giá trong Context. Nếu mặt hàng không có trong Context và Brand Kit, "
        f"từ chối bịa giá và dặn nhân viên hướng dẫn khách inbox hoặc liên hệ Hotline {primary_hotline}.\n"
        "3. Nếu tra cứu đơn hàng / vận đơn GHN: Báo rõ mã vận đơn, trạng thái giao hàng, tiền COD và kiện hàng.\n"
        "4. Nếu hỏi về kho văn bản: Báo số lượng văn bản, các tài liệu cần phê duyệt hoặc sắp hết hạn.\n"
        "5. Nếu hỏi về ca trực / việc cần làm: Báo các việc gấp và khách dừng tương tác cần cứu lead.\n"
        "6. Tuyệt đối không gửi tin nhắn Facebook hộ; hướng dẫn nhân viên bấm nút 'Gửi' trên Hộp thư.\n"
        "7. Tuyệt đối không cung cấp token, mật khẩu hoặc hướng dẫn vào buồng lái /app.\n"
        "8. Định dạng đầu ra BẮT BUỘC là 1 JSON object duy nhất:\n"
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

    if found_products:
        context_lines.append("=== BẢNG GIÁ & SẢN PHẨM NIÊM YẾT (DATABASE OPS HUB) ===")
        for p in found_products[:8]:
            context_lines.append(f"- [{p.get('sku')}] {p.get('name')}: {_fmt_price(p.get('price', 0))} (Danh mục: {p.get('category')}, Tồn kho: {p.get('stock')})")
        context_lines.append("")

    if doc_stats:
        context_lines.append("=== KHO VĂN BẢN & PHÁP LÝ (OPS HUB) ===")
        context_lines.append(f"- Tổng số văn bản: {doc_stats.get('total', 0)}")
        context_lines.append(f"- Cần phê duyệt: {doc_stats.get('pending_approval', 0)}")
        context_lines.append(f"- Sắp hết hạn trong 30 ngày: {doc_stats.get('expiring_soon', 0)}")
        context_lines.append(f"- Hợp đồng cần ký: {doc_stats.get('missing_signature', 0)}")
        if found_docs:
            for d in found_docs:
                context_lines.append(f"  • [{d.get('id')}] {d.get('title')} ({d.get('category')}) - Trạng thái: {d.get('approval_status')}")
        context_lines.append("")

    if found_shipment or found_orders:
        context_lines.append("=== THÔNG TIN ĐƠN HÀNG & GIAO VẬN GHN ===")
        if found_shipment:
            context_lines.append(
                f"- Vận đơn GHN: {found_shipment.get('tracking_code')} | Trạng thái: {found_shipment.get('status')} | "
                f"Phí ship: {_fmt_price(found_shipment.get('fee', 0))} | COD: {_fmt_price(found_shipment.get('cod_amount', 0))}"
            )
        for o in found_orders:
            cname = o.get("customer_name") or "Khách"
            cphone = mask_phone(o.get("customer_phone") or "")
            tot = _fmt_price(o.get("total_amount", 0))
            items_str = ", ".join(f"{it.get('name')} x{it.get('quantity')}" for it in (o.get("items") or []))
            context_lines.append(f"- Đơn {o.get('id')}: Khách {cname} ({cphone}) - {tot} - Trạng thái: {o.get('status')} - Món: {items_str or 'N/A'}")
        context_lines.append("")

    if found_tasks:
        context_lines.append("=== VIỆC CA TRỰC KANBAN ===")
        for t in found_tasks[:5]:
            context_lines.append(f"- [{t.get('id')}] {t.get('title')} (Khách: {t.get('customer')}, Gấp: {t.get('isUrgent')})")
        context_lines.append("")

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

    # 12. Gọi aux_engine.complete_json (với timeout 20s, tools=[])
    used_stats = drafts_asked or "hôm nay" in msg_low or doc_asked or order_asked or task_asked or prod_asked
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

    # 13. Deterministic Rules-First Fallback khi không có LLM / timeout / offline
    # 13. Deterministic Rules-First Fallback khi không có LLM / timeout / offline
    reply = ""
    # Ưu tiên 1: Tra cứu vận đơn GHN / Đơn hàng cụ thể
    if found_shipment or (order_asked and found_orders and not found_products):
        s_lines = ["Thông tin đơn hàng & vận chuyển GHN:"]
        if found_shipment:
            s_lines.append(f"• Mã vận đơn: {found_shipment.get('tracking_code')} (Đơn vị: GHN)")
            s_lines.append(f"• Trạng thái: {found_shipment.get('status')} | Phí ship: {_fmt_price(found_shipment.get('fee', 0))} | COD: {_fmt_price(found_shipment.get('cod_amount', 0))}")
        for o in found_orders[:2]:
            cname = o.get("customer_name") or "Khách"
            cphone = mask_phone(o.get("customer_phone") or "")
            s_lines.append(f"• Đơn [{o.get('id')}]: Khách {cname} ({cphone}) - Tổng: {_fmt_price(o.get('total_amount', 0))} - Trạng thái: {o.get('status')}")
        reply = "\n".join(s_lines)
    # Ưu tiên 2: Cơ chế Human Takeover (Tiếp quản ca trực)
    elif takeover_asked:
        reply = (
            "Takeover là cơ chế tạm dừng AI khi nhân viên can thiệp chat thủ công với khách: Khi bạn hoặc nhân sự nhắn tin trên Messenger/Inbox, "
            "Javis sẽ tự động lùi lại và tạm dừng phản hồi tự động trong 24 giờ để tránh tranh lời nhân viên.\n\n"
            "Khi bạn tư vấn xong và muốn AI trực tiếp tục, hãy vào tab **Hộp thư & Nháp** trên /ops và bấm nút **'Javis nhận lại'** (Release Takeover)."
        )
    # Ưu tiên 3: Kho văn bản, Hợp đồng & Quy trình SOP
    elif doc_asked and (doc_stats or found_docs):
        d_lines = [f"Tình hình Kho văn bản & Pháp lý ({scope_label}):"]
        if doc_stats:
            d_lines.append(f"• Tổng số văn bản: {doc_stats.get('total', 0)} | Chờ phê duyệt: {doc_stats.get('pending_approval', 0)} | Sắp hết hạn trong 30 ngày: {doc_stats.get('expiring_soon', 0)} | Hợp đồng cần ký: {doc_stats.get('missing_signature', 0)}")
        if found_docs:
            d_lines.append("\nTài liệu liên quan trong kho:")
            for d in found_docs[:3]:
                d_lines.append(f"• [{d.get('id')}] {d.get('title')} ({d.get('category')} - Trạng thái: {d.get('approval_status')})")
        d_lines.append("\nVui lòng vào tab **Kho văn bản** trên /ops để xem chi tiết hoặc ký duyệt.")
        reply = "\n".join(d_lines)
    # Ưu tiên 4: Sản phẩm & Bảng giá
    elif found_products:
        p_lines = [f"Bảng giá niêm yết trong hệ thống Ops Hub ({scope_label}):"]
        for p in found_products[:5]:
            p_lines.append(f"• [{p.get('sku')}] {p.get('name')}: {_fmt_price(p.get('price', 0))} (Tồn kho: {p.get('stock')})")
        p_lines.append(f"\nNếu cần tư vấn cấu hình hoặc chính sách ưu đãi riêng, xin liên hệ Hotline/Zalo {primary_hotline}.")
        reply = "\n".join(p_lines)
    elif price_asked and not has_any_price_info:
        reply = (
            f"Trong tài liệu Brand Kit của {scope_label} hiện tại không có bảng giá hoặc mức học phí cụ thể cho mặt hàng này. "
            f"Bạn vui lòng hướng dẫn khách nhắn tin inbox hoặc liên hệ Hotline/Zalo {primary_hotline} để được tư vấn chính xác, "
            f"tránh tự báo giá sai nhé."
        )
    # Ưu tiên 5: Việc ca trực & Cứu lead
    elif task_asked and found_tasks:
        t_lines = [f"Nhiệm vụ ca trực Kanban cần chú ý ({len(found_tasks)} việc):"]
        for t in found_tasks[:5]:
            t_lines.append(f"• [{t.get('id')}] {t.get('title')} (Khách: {t.get('customer')}, Gấp: {'Có' if t.get('isUrgent') else 'Không'})")
        t_lines.append("Bạn hãy kiểm tra tab **Việc ca trực** trên /ops để xử lý nhé.")
        reply = "\n".join(t_lines)
    # Ưu tiên 6: Báo cáo tổng hợp điều hành ca trực hôm nay
    elif drafts_asked:
        sum_lines = [
            f"Tình hình ca trực {scope_label} hôm nay:",
            f"• Hộp thư CSKH: {total_pending} nháp chờ duyệt ({pending_cmt_count} bình luận, {pending_msg_count} tin nhắn).",
            f"• Tương tác 24h: {care_stats.get('events_24h', 0)} lượt | Khách mới (Leads): {care_stats.get('leads_24h', 0)}.",
        ]
        if ops_order_store:
            try:
                orders = ops_order_store.list_orders(limit=20)
                shipping_cnt = sum(1 for o in orders if o.get("status") == "shipping")
                delivered_cnt = sum(1 for o in orders if o.get("status") == "delivered")
                sum_lines.append(f"• Đơn hàng & GHN: {len(orders)} đơn ({shipping_cnt} đang giao, {delivered_cnt} đã giao).")
            except Exception:
                pass
        if ops_documents_store:
            try:
                ds = ops_documents_store.get_stats()
                sum_lines.append(f"• Kho văn bản: {ds.get('pending_approval', 0)} cần duyệt | {ds.get('expiring_soon', 0)} sắp hết hạn 30 ngày.")
            except Exception:
                pass
        if ops_tasks_store:
            try:
                tasks = ops_tasks_store.load_tasks()
                urg_cnt = sum(1 for t in tasks if t.get("isUrgent") and t.get("columnId") != "done")
                sum_lines.append(f"• Việc ca trực: {urg_cnt} việc gấp cần xử lý.")
            except Exception:
                pass
        sum_lines.append(f"• Hotline kit: {primary_hotline}.")
        sum_lines.append("Bạn hãy mở các tab tương ứng trên /ops để kiểm tra và xử lý nhé!")
        reply = "\n".join(sum_lines)
    elif customer_matches:
        c_info = []
        for cm in customer_matches:
            c_info.append(f"• {cm['name']} — SĐT: {', '.join(cm['phones'])} (Tags: {', '.join(cm['tags']) or 'Chưa gắn'})")
        reply = f"Tìm thấy thông tin khách hàng trong hệ thống:\n" + "\n".join(c_info)
    else:
        reply = (
            f"Chào bạn, tôi là trợ lý ca CSKH Sèo Trum Ops ({scope_label}). "
            f"Hiện tại có {total_pending} nháp chờ duyệt trên Hộp thư. "
            f"Hotline hỗ trợ của kit là {primary_hotline}. Bạn cần kiểm tra bảng giá, vận đơn GHN, kho văn bản hay nhiệm vụ ca trực?"
        )


    return {
        "ok": True,
        "reply": reply,
        "citations": citations,
        "used_stats": used_stats,
    }

