"""
Cầu nối Botcake (transport "internal" trong catalog) - Botcake KHÔNG có MCP chính chủ,
Javis tự bọc Public API v1 thành bộ tool MCP-tương-đương.
Đã verify 2026-07-04: base https://botcake.io/api/public_api/v1, auth header
"access-token: <page token>" (Botcake > Cấu hình > Tích hợp > Public API).
spec["secrets"] = {"api_key": <token>, "page_id": <id trang>} (mcp_store.resolved cấp).
"""
import json

import httpx

BASE = "https://botcake.io/api/public_api/v1"


def _clip(text, max_chars=8000):
    text = str(text)
    if len(text) <= max_chars:
        return text
    head = int(max_chars * 0.6)
    tail = max_chars - head
    return (text[:head] + f"\n… [KẾT QUẢ BỊ CẮT - bỏ {len(text) - head - tail:,} ký tự giữa] …\n"
            + text[-tail:])


def _t(name, description, props=None, required=None):
    return {"name": name, "description": description,
            "inputSchema": {"type": "object", "properties": props or {}, "required": required or []}}


TOOLS = [
    _t("botcake_customers", "Danh sách khách hàng (subscriber) của page Botcake, phân trang.",
       {"page": {"type": "integer", "description": "trang, mặc định 1"}}),
    _t("botcake_customer", "Lịch sử thao tác / chi tiết 1 khách theo PSID.",
       {"psid": {"type": "string"}}, ["psid"]),
    _t("botcake_customer_fields_get", "Đọc custom field của 1 khách theo PSID.",
       {"psid": {"type": "string"}}, ["psid"]),
    _t("botcake_customer_fields_set", "Ghi 1 custom field cho khách (thao tác GHI).",
       {"psid": {"type": "string"}, "field_name": {"type": "string"}, "value": {"type": "string"}},
       ["psid", "field_name", "value"]),
    _t("botcake_custom_fields", "Danh sách custom field của page."),
    _t("botcake_tags", "Danh sách tag của page."),
    _t("botcake_tag_statistic", "Thống kê số khách theo tag."),
    _t("botcake_flows", "Danh sách flow (kịch bản chatbot) của page."),
    _t("botcake_flow_statistics", "Thống kê 1 flow theo flow_id.",
       {"flow_id": {"type": "string"}}, ["flow_id"]),
    _t("botcake_send_flow", "GỬI 1 flow THẬT tới khách (PSID) - tin nhắn sẽ đến người thật, "
       "CHỈ dùng khi user yêu cầu rõ ràng. (Body API chưa verify 100% - nếu lỗi hãy báo lại.)",
       {"psid": {"type": "string"}, "flow_id": {"type": "string"}}, ["psid", "flow_id"]),
    _t("botcake_keywords", "Danh sách keyword tự động trả lời của page."),
    _t("botcake_sequences", "Danh sách sequence (chuỗi tin nhắn định kỳ) của page."),
    _t("botcake_message_templates", "Danh sách message template của page."),
]

# tool -> (method, path template có {page_id}/{psid}/{flow_id}, query builder?)
_ROUTES = {
    "botcake_customers": ("GET", "/pages/{page_id}/customer"),
    "botcake_customer": ("GET", "/pages/{page_id}/customer/{psid}"),
    "botcake_customer_fields_get": ("GET", "/pages/{page_id}/customer/{psid}/customer_fields"),
    "botcake_customer_fields_set": ("POST", "/pages/{page_id}/customer/{psid}/customer_fields"),
    "botcake_custom_fields": ("GET", "/pages/{page_id}/custom_fields"),
    "botcake_tags": ("GET", "/pages/{page_id}/get_list_tag"),
    "botcake_tag_statistic": ("GET", "/pages/{page_id}/get_tag_statistic"),
    "botcake_flows": ("GET", "/pages/{page_id}/flows"),
    "botcake_flow_statistics": ("GET", "/pages/{page_id}/flows/{flow_id}/statistics"),
    "botcake_send_flow": ("POST", "/pages/{page_id}/flows/send_flow"),
    "botcake_keywords": ("GET", "/pages/{page_id}/keywords"),
    "botcake_sequences": ("GET", "/pages/{page_id}/sequences/"),
    "botcake_message_templates": ("GET", "/pages/{page_id}/message_templates"),
}


async def list_tools(spec):
    return TOOLS


async def call(tool, arguments, spec):
    secrets = (spec or {}).get("secrets") or {}
    token = secrets.get("api_key", "")
    page_id = str(secrets.get("page_id", "")).strip()
    if not token or not page_id:
        return "ERROR: kết nối Botcake thiếu page_id/API key - sửa lại ở trang Kết nối"
    ent = _ROUTES.get(tool)
    if not ent:
        return f"ERROR: tool '{tool}' không tồn tại trong cầu nối Botcake"
    method, path = ent
    args = arguments or {}
    try:
        path = path.format(page_id=page_id, psid=str(args.get("psid", "")).strip(),
                           flow_id=str(args.get("flow_id", "")).strip())
    except KeyError:
        pass
    params, body = {}, None
    if tool == "botcake_customers":
        params["page"] = int(args.get("page") or 1)
    elif tool == "botcake_customer_fields_set":
        body = {"field_name": args.get("field_name"), "value": args.get("value")}
    elif tool == "botcake_send_flow":
        body = {"psid": args.get("psid"), "flow_id": args.get("flow_id")}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.request(method, BASE + path, params=params or None, json=body,
                                     headers={"access-token": token})
        if r.status_code >= 400:
            return f"ERROR: Botcake {r.status_code}: {(r.text or '')[:300]}"
        try:
            return _clip(json.dumps(r.json(), ensure_ascii=False))
        except ValueError:
            return _clip(r.text or "(rỗng)")
    except Exception as e:
        return f"ERROR: Botcake không phản hồi: {type(e).__name__}: {e}"
