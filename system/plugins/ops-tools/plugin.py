"""Plugin bundled: Bộ công cụ Điều hành Ops Hub (ops-tools).

Kết nối Javis và các engine AI (Claude, Codex, Gemini, Grok, OpenRouter)
với toàn bộ cơ sở dữ liệu vận hành Social Commerce Ops Hub:
- Bảng giá, SKU & Danh mục sản phẩm (ops_products)
- Kho văn bản, Hợp đồng, SOP & Biểu mẫu (ops_documents)
- Tra cứu đơn hàng & Vận đơn GHN (ops_orders & ops_shipments)
- Tổng hợp tình hình điều hành ca trực hôm nay (executive overview)
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Đảm bảo server module có trong sys.path
_SERVER_DIR = Path(__file__).resolve().parents[2] / "server"
if str(_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVER_DIR))

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

try:
    import fanpage_care_store as care_store
except Exception:
    care_store = None


def _mask_phone(phone: str) -> str:
    """Che số điện thoại hiển thị (vd: 0912***456)."""
    if not phone:
        return ""
    clean = re.sub(r"\D", "", str(phone))
    if len(clean) >= 9:
        return clean[:4] + "***" + clean[-3:]
    if len(clean) >= 6:
        return clean[:3] + "***" + clean[-2:]
    return "***"


def _fmt_price(num: Any) -> str:
    try:
        val = float(num)
        return f"{val:,.0f} đ".replace(",", ".")
    except Exception:
        return str(num)


def _fmt_time(ts: Any) -> str:
    if not ts:
        return "N/A"
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%d/%m/%Y")
    except Exception:
        return str(ts)


# ============================================================
# Handlers
# ============================================================

def _handle_catalog_query(args: dict, ctx: Any) -> str:
    """Tra cứu danh mục sản phẩm, khóa học, bảng giá niêm yết và tồn kho."""
    if not ops_order_store:
        return "ERROR: Module ops_order_store chưa sẵn sàng trên máy chủ."

    keyword = str((args or {}).get("keyword") or "").strip()
    category = str((args or {}).get("category") or "").strip().lower()
    page_id = str((args or {}).get("page_id") or "").strip() or None

    try:
        if keyword:
            items = ops_order_store.search_products(keyword, page_id=page_id)
        else:
            items = ops_order_store.list_products(page_id=page_id, active_only=True)
    except Exception as e:
        return f"ERROR: Không thể tra cứu sản phẩm ({type(e).__name__}: {e})"

    if category:
        items = [i for i in items if str(i.get("category") or "").lower() == category]

    if not items:
        msg = f"Không tìm thấy sản phẩm nào trong Ops Hub khớp với từ khóa '{keyword}'" if keyword else "Danh mục sản phẩm hiện đang trống."
        return msg + " (Liên hệ Hotline/CSKH nếu cần thêm mã mới)."

    lines = [f"📦 KẾT QUẢ TRA CỨU SẢN PHẨM & BẢNG GIÁ ({len(items)} mặt hàng):"]
    for idx, p in enumerate(items[:15], 1):
        sku = p.get("sku") or "N/A"
        name = p.get("name") or "Sản phẩm"
        price = _fmt_price(p.get("price", 0))
        cat = p.get("category") or "chung"
        stock = p.get("stock", 0)
        aliases = p.get("aliases") or []
        alias_str = f" [Từ đồng nghĩa: {', '.join(aliases[:3])}]" if aliases else ""

        lines.append(f"{idx}. [{sku}] {name}")
        lines.append(f"   • Giá niêm yết: {price} | Danh mục: {cat} | Tồn kho: {stock}{alias_str}")

    if len(items) > 15:
        lines.append(f"   ... còn {len(items) - 15} sản phẩm khác trong hệ thống.")

    return "\n".join(lines)


def _handle_document_query(args: dict, ctx: Any) -> str:
    """Tra cứu kho văn bản, hợp đồng, SOP, biểu mẫu và cảnh báo hết hạn."""
    if not ops_documents_store:
        return "ERROR: Module ops_documents_store chưa sẵn sàng trên máy chủ."

    action = str((args or {}).get("action") or "stats").strip().lower()
    category = str((args or {}).get("category") or "").strip().lower() or None
    query = str((args or {}).get("query") or "").strip() or None

    try:
        if action == "stats":
            stats = ops_documents_store.get_stats()
            by_cat = stats.get("by_category") or {}
            cat_breakdown = ", ".join(f"{k}: {v}" for k, v in by_cat.items()) if by_cat else "Chưa có"

            return (
                "📑 THỐNG KÊ KHO VĂN BẢN & HỢP ĐỒNG OPS HUB:\n"
                f"• Tổng số văn bản: {stats.get('total', 0)}\n"
                f"• Hợp đồng: {stats.get('contracts_count', 0)} (Cần ký: {stats.get('missing_signature', 0)})\n"
                f"• Quy trình vận hành (SOP): {stats.get('sop_count', 0)}\n"
                f"• Biểu mẫu chuẩn (Templates): {stats.get('templates_count', 0)}\n"
                f"• Văn bản chờ phê duyệt: {stats.get('pending_approval', 0)}\n"
                f"• Văn bản sắp hết hạn trong 30 ngày: {stats.get('expiring_soon', 0)}\n"
                f"• Văn bản đã hết hạn: {stats.get('expired', 0)}\n"
                f"• Phân loại chi tiết: {cat_breakdown}"
            )

        # Liệt kê hoặc tìm kiếm
        status_filter = None
        if action == "pending_approval":
            status_filter = "pending"

        res = ops_documents_store.list_documents(
            category=category,
            approval_status=status_filter,
            search=query,
            limit=20,
        )
        docs = res.get("documents", []) if isinstance(res, dict) else []

        if action == "expiring":
            now = time.time()
            thirty_days = 30 * 86400
            docs = [d for d in docs if d.get("expires_at") and float(d["expires_at"]) >= now and float(d["expires_at"]) <= now + thirty_days]

        if not docs:
            return f"Không tìm thấy văn bản nào phù hợp với yêu cầu (action={action}, category={category or 'tất cả'})."

        lines = [f"📂 DANH SÁCH VĂN BẢN TÌM THẤY ({len(docs)} tài liệu):"]
        for idx, d in enumerate(docs[:15], 1):
            doc_id = d.get("id") or "N/A"
            title = d.get("title") or "Văn bản"
            cat = d.get("category") or "khác"
            status = d.get("approval_status") or "draft"
            exp = _fmt_time(d.get("expires_at"))
            dept = d.get("department") or "toàn công ty"

            lines.append(f"{idx}. [{doc_id}] {title}")
            lines.append(f"   • Loại: {cat} | Trạng thái: {status} | Phòng ban: {dept} | Hết hạn: {exp}")

        return "\n".join(lines)
    except Exception as e:
        return f"ERROR: Tra cứu kho văn bản thất bại ({type(e).__name__}: {e})"


def _handle_order_tracking(args: dict, ctx: Any) -> str:
    """Tra cứu đơn hàng và trạng thái vận chuyển GHN."""
    if not ops_order_store:
        return "ERROR: Module ops_order_store chưa sẵn sàng trên máy chủ."

    tracking_code = str((args or {}).get("tracking_code") or "").strip()
    order_id = str((args or {}).get("order_id") or "").strip()
    query = str((args or {}).get("query") or "").strip()

    try:
        # 1. Tra theo mã vận đơn GHN
        if tracking_code:
            shipment = ops_order_store.get_shipment_by_tracking(tracking_code)
            if not shipment:
                return f"Không tìm thấy vận đơn GHN với mã '{tracking_code}' trên hệ thống Ops Hub."

            oid = shipment.get("order_id")
            order = ops_order_store.get_order(oid) if oid else None

            carrier = str(shipment.get("provider") or "GHN").upper()
            status = shipment.get("status") or "unknown"
            fee = _fmt_price(shipment.get("fee", 0))
            cod = _fmt_price(shipment.get("cod_amount", 0))

            lines = [
                f"🚚 THÔNG TIN VẬN ĐƠN {carrier} - {tracking_code}:",
                f"• Trạng thái vận chuyển: {status}",
                f"• Phí vận chuyển: {fee}",
                f"• Tiền thu hộ COD: {cod}",
                f"• Mã đơn hàng liên kết: {oid or 'N/A'}",
            ]
            if order:
                cname = order.get("customer_name") or "Khách hàng"
                cphone = _mask_phone(order.get("customer_phone") or "")
                lines.append(f"• Người nhận: {cname} (SĐT: {cphone})")
                lines.append(f"• Địa chỉ: {order.get('customer_address') or 'Theo vận đơn'}")
                items = order.get("items") or []
                if items:
                    item_strs = [f"{it.get('name', 'Mặt hàng')} x{it.get('quantity', 1)}" for it in items]
                    lines.append(f"• Kiện hàng gồm: {', '.join(item_strs)}")

            return "\n".join(lines)

        # 2. Tra theo mã đơn hàng
        if order_id:
            order = ops_order_store.get_order(order_id)
            if not order:
                return f"Không tìm thấy đơn hàng với mã '{order_id}'."

            cname = order.get("customer_name") or "Khách hàng"
            cphone = _mask_phone(order.get("customer_phone") or "")
            total_amt = _fmt_price(order.get("total_amount", 0))
            status = order.get("status") or "pending"

            shipment = order.get("shipment")
            ship_info = "Chưa tạo vận đơn"
            if shipment:
                ship_info = f"GHN ({shipment.get('tracking_code', 'N/A')}) - Trạng thái: {shipment.get('status', 'unknown')}"

            items = order.get("items") or []
            item_strs = [f"{it.get('name', 'Mặt hàng')} x{it.get('quantity', 1)} ({_fmt_price(it.get('price', 0))})" for it in items]

            return (
                f"📋 THÔNG TIN ĐƠN HÀNG {order_id}:\n"
                f"• Khách hàng: {cname} (SĐT: {cphone})\n"
                f"• Trạng thái đơn: {status}\n"
                f"• Tổng thanh toán: {total_amt}\n"
                f"• Vận chuyển: {ship_info}\n"
                f"• Sản phẩm: {', '.join(item_strs) if item_strs else 'Không có món hàng'}"
            )

        # 3. Tìm kiếm theo tên khách hoặc SĐT
        if query:
            orders = ops_order_store.list_orders(search=query, limit=5)
            if not orders:
                return f"Không tìm thấy đơn hàng nào khớp với tìm kiếm '{query}'."

            lines = [f"📋 KẾT QUẢ TÌM KIẾM ĐƠN HÀNG ({len(orders)} đơn):"]
            for o in orders:
                oid = o.get("id") or "N/A"
                cname = o.get("customer_name") or "Khách"
                cphone = _mask_phone(o.get("customer_phone") or "")
                amt = _fmt_price(o.get("total_amount", 0))
                st = o.get("status") or "pending"
                lines.append(f"• [{oid}] {cname} ({cphone}) - {amt} - Trạng thái: {st}")
            return "\n".join(lines)

        return "Vui lòng cung cấp mã vận đơn GHN (tracking_code), mã đơn hàng (order_id), hoặc tên/SĐT khách (query)."
    except Exception as e:
        return f"ERROR: Tra cứu đơn hàng / vận đơn thất bại ({type(e).__name__}: {e})"


def _handle_today_summary(args: dict, ctx: Any) -> str:
    """Tổng hợp toàn diện bức tranh điều hành Ops Hub hôm nay."""
    lines = ["🌅 BÁO CÁO TỔNG QUAN ĐIỀU HÀNH OPS HUB HÔM NAY:"]

    # 1. CSKH & Fanpage Care
    if care_store:
        try:
            cs = care_store.get_stats()
            lines.append("1. CSKH & TIN NHẮN / BÌNH LUẬN:")
            lines.append(f"   • Nháp chờ duyệt: {cs.get('pending_drafts', 0)} ({cs.get('pending_comment_drafts', 0)} bình luận, {cs.get('pending_message_drafts', 0)} tin nhắn)")
            lines.append(f"   • Tương tác 24h qua: {cs.get('events_24h', 0)} | Khách tiềm năng (Leads) mới: {cs.get('leads_24h', 0)}")
        except Exception:
            pass

    # 2. Đơn hàng & Vận chuyển GHN
    if ops_order_store:
        try:
            orders = ops_order_store.list_orders(limit=50)
            pending_orders = sum(1 for o in orders if o.get("status") == "pending")
            shipping_orders = sum(1 for o in orders if o.get("status") == "shipping")
            delivered_orders = sum(1 for o in orders if o.get("status") == "delivered")
            lines.append("2. ĐƠN HÀNG & GIAO VẬN GHN:")
            lines.append(f"   • Đơn mới chờ xử lý: {pending_orders} | Đang giao hàng: {shipping_orders} | Giao thành công: {delivered_orders} (Tổng {len(orders)} đơn)")
        except Exception:
            pass

    # 3. Kho văn bản & Hợp đồng
    if ops_documents_store:
        try:
            ds = ops_documents_store.get_stats()
            lines.append("3. KHO VĂN BẢN & PHÁP LÝ:")
            lines.append(f"   • Cần phê duyệt: {ds.get('pending_approval', 0)} | Sắp hết hạn trong 30 ngày: {ds.get('expiring_soon', 0)} | Hợp đồng cần ký: {ds.get('missing_signature', 0)}")
        except Exception:
            pass

    # 4. Việc ca trực & Cứu lead
    if ops_tasks_store:
        try:
            tasks = ops_tasks_store.load_tasks()
            urgent_tasks = sum(1 for t in tasks if t.get("isUrgent") and t.get("columnId") != "done")
            rescue_tasks = sum(1 for t in tasks if "rescue" in str(t.get("id", "")) and t.get("columnId") != "done")
            lines.append("4. NHIỆM VỤ CA TRỰC KANBAN:")
            lines.append(f"   • Việc gấp cần xử lý: {urgent_tasks} | Khách dừng tương tác cần cứu lead: {rescue_tasks} (Tổng {len(tasks)} nhiệm vụ)")
        except Exception:
            pass

    lines.append("\n👉 Thao tác chi tiết xin mời truy cập các tab tương ứng trên buồng điều hành /ops.")
    return "\n".join(lines)


# ============================================================
# Plugin Registration
# ============================================================

def register(ctx: Any) -> None:
    """Đăng ký các tools Ops Hub vào MCP Hub của Javis."""

    ctx.register_tool(
        "ops_catalog_query",
        "Tra cứu danh mục sản phẩm, khóa học, bảng giá niêm yết, tồn kho, và SKU từ cơ sở dữ liệu Social Commerce Ops Hub. "
        "Dùng khi khách hoặc nhân viên hỏi giá sản phẩm, học phí khóa học, mã SKU, tình trạng còn hàng.",
        _handle_catalog_query,
        schema={
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Tên sản phẩm, khóa học, SKU, hoặc từ khóa tìm kiếm"},
                "category": {"type": "string", "description": "Lọc theo danh mục: education, games, books, hardware"},
                "page_id": {"type": "string", "description": "ID Fanpage nếu muốn tra giá ưu đãi theo page cụ thể"},
            },
        },
        min_mode="readonly",
        emoji="📦",
    )

    ctx.register_tool(
        "ops_document_query",
        "Tra cứu kho văn bản, tài liệu pháp lý, hợp đồng, SOP quy trình và biểu mẫu trên Ops Hub. "
        "Xem thống kê văn bản sắp hết hạn trong 30 ngày, hợp đồng thiếu chữ ký, hoặc danh sách tài liệu theo phân loại.",
        _handle_document_query,
        schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["stats", "list", "expiring", "pending_approval"],
                    "description": "Hành động: stats (thống kê tổng), list (danh sách), expiring (sắp hết hạn 30 ngày), pending_approval (chờ duyệt)",
                },
                "category": {
                    "type": "string",
                    "description": "Lọc phân loại: contract, sop, policy, template, hr, legal",
                },
                "query": {"type": "string", "description": "Từ khóa tìm kiếm tiêu đề tài liệu"},
            },
        },
        min_mode="readonly",
        emoji="📑",
    )

    ctx.register_tool(
        "ops_order_tracking",
        "Tra cứu thông tin đơn hàng và tình trạng vận chuyển GHN (Giao Hàng Nhanh) từ Ops Hub. "
        "Tra theo mã đơn (ord_...), mã vận đơn GHN (GHNMOCK-...), hoặc tên/SĐT khách hàng.",
        _handle_order_tracking,
        schema={
            "type": "object",
            "properties": {
                "tracking_code": {"type": "string", "description": "Mã vận đơn GHN, ví dụ GHNMOCK-HCM-001"},
                "order_id": {"type": "string", "description": "Mã đơn hàng, ví dụ ord_6455269a10"},
                "query": {"type": "string", "description": "Tên khách hàng hoặc số điện thoại"},
            },
        },
        min_mode="readonly",
        emoji="🚚",
    )

    ctx.register_tool(
        "ops_today_summary",
        "Tổng hợp toàn diện bức tranh điều hành hôm nay của Ops Hub: số nháp CSKH chờ duyệt, đơn hàng mới, tình hình giao vận GHN, văn bản cần duyệt hoặc sắp hết hạn, và các nhiệm vụ ca trực Kanban.",
        _handle_today_summary,
        schema={
            "type": "object",
            "properties": {
                "brand": {"type": "string", "description": "Lọc theo thương hiệu nếu cần (bsn hoặc saoviet)"},
            },
        },
        min_mode="readonly",
        emoji="🌅",
    )
