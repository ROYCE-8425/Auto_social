"""Cổng gọi Graph an toàn cho Fanpage Care (fanpage_care_graph.call).

Mọi thao tác gọi Meta Graph từ Fanpage Care BẮT BUỘC đi qua module này:
1. Kiểm tra enabled / kill_switch
2. Kiểm tra kết nối facebook-pages & mức quyền perm
3. Kiểm tra catalog.allowed + policy
4. Gọi tool qua plugins_host
5. Ghi đồng thời mcp_audit.jsonl (với actor) và fanpage_care_audit.jsonl
6. Đảm bảo plain text caption, không bao giờ qua _publish hay _caption_kit_err
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import config
from config import STATE_DIR
import mcp_catalog
import mcp_store
import plugins_host
from fanpage_care_policy import policy_allows

_MCP_AUDIT_PATH = STATE_DIR / "mcp_audit.jsonl"
_CARE_AUDIT_PATH = STATE_DIR / "fanpage_care_audit.jsonl"

_DANGER_TOOLS = {
    "fb_page_post", "fb_page_photo", "fb_page_album", "fb_page_video",
    "fb_page_edit", "fb_page_reply", "fb_page_delete",
    "fb_page_comment_hide", "fb_page_comment_like", "fb_page_comment_delete",
    "fb_message_send", "fb_private_reply",
}


def _append_audit(path: Path, rec: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    except Exception as e:
        print(f"[fanpage_care_graph] Ghi audit {path.name} lỗi: {e}", file=sys.stderr)


async def call(
    tool: str,
    args: dict[str, Any] | None = None,
    *,
    actor: str = "care-worker",
    vault_root: str | None = None,
    policy_context: dict[str, Any] | None = None,
) -> str:
    """Gọi một tool của Meta Pages Graph an toàn.
    
    Trả kết quả dạng string (thường là JSON) hoặc 'ERROR: ...'.
    """
    t0 = time.time()
    args = args or {}
    tool_name = str(tool).strip()

    settings = config.read_settings()
    care_cfg = settings.get("fanpage_care", {})
    enabled = bool(care_cfg.get("enabled", False))
    kill_switch = bool(care_cfg.get("kill_switch", False))

    is_write = tool_name in _DANGER_TOOLS

    # 1. enabled=false -> từ chối mọi thứ
    if not enabled:
        err = "ERROR: fanpage_care_disabled (Tính năng Chăm sóc Fanpage đang tắt)"
        _append_audit(_CARE_AUDIT_PATH, {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "actor": actor, "tool": tool_name, "ok": False,
            "err": "fanpage_care_disabled", "ms": 0,
        })
        return err

    # 1b. kill_switch -> từ chối các hành động ghi
    if kill_switch and is_write:
        err = "ERROR: kill_switch_active (Kill switch đang bật, mọi hành động ghi Graph bị chặn)"
        _append_audit(_CARE_AUDIT_PATH, {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "actor": actor, "tool": tool_name, "ok": False,
            "err": "kill_switch_active", "ms": 0,
        })
        return err

    # 2. Tìm kết nối facebook-pages trong mcp_store
    connector_id = "facebook-pages"
    raw_conns = mcp_store._load().get("connections", [])
    conn = next((c for c in raw_conns if c.get("connector_id") == connector_id), None)
    connector = mcp_catalog.get(connector_id)

    # Nếu không có connection cấu hình trong store nhưng có manual tokens / plugin có thể chạy
    # Ta vẫn tạo một connection stub danh nghĩa để kiểm catalog
    if not conn:
        conn = {
            "id": "facebook-pages-auto",
            "connector_id": connector_id,
            "label": "Facebook Pages",
            "perm": "readonly",  # Mặc định an toàn
        }

    conn_perm = conn.get("perm", "full")

    # 3. Phân loại và kiểm tra quyền qua mcp_catalog
    mode_for_catalog = "full" if is_write else "suggest"
    cls = mcp_catalog.classify(connector, tool_name, args)
    cat_ok, cat_why = mcp_catalog.allowed(connector, conn_perm, mode_for_catalog, tool_name, args)

    if not cat_ok:
        err = f"ERROR: {cat_why}"
        rec = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "conn_id": conn.get("id"), "connector": connector_id,
            "label": conn.get("label"), "tool": tool_name,
            "mode": mode_for_catalog, "cls": cls, "ok": False, "ms": 0,
            "err": cat_why[:200], "actor": actor,
        }
        _append_audit(_MCP_AUDIT_PATH, rec)
        _append_audit(_CARE_AUDIT_PATH, rec)
        return err

    # 5. if write and conn.perm != "full": refuse
    if is_write and conn_perm != "full":
        err = f"ERROR: connection_perm_not_full (Kết nối Facebook chỉ có quyền '{conn_perm}', cần 'full')"
        _append_audit(_CARE_AUDIT_PATH, {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "actor": actor, "tool": tool_name, "ok": False,
            "err": "connection_perm_not_full", "ms": 0,
        })
        return err

    # 6. Policy check nếu được cung cấp
    if is_write and policy_context:
        action = policy_context.get("action", "faq_reply")
        mode = policy_context.get("mode", care_cfg.get("mode", "suggest"))
        class_name = policy_context.get("class_name", "ambiguous")
        pol_ok, pol_why = policy_allows(
            action,
            mode=mode,
            class_name=class_name,
            is_quiet=policy_context.get("is_quiet", False),
            rate_exceeded=policy_context.get("rate_exceeded", False),
            kill_switch=kill_switch,
            delete_spam=bool(care_cfg.get("delete_spam", False)),
            like_khen=bool(care_cfg.get("like_khen", False)),
        )
        if not pol_ok:
            err = f"ERROR: policy_denied ({pol_why})"
            _append_audit(_CARE_AUDIT_PATH, {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "actor": actor, "tool": tool_name, "ok": False,
                "err": pol_why, "ms": 0,
            })
            return err

    # 7. Gọi tool qua plugins_host
    _, route = plugins_host.plugin_tools(mode="full", vault_root=vault_root)
    if tool_name not in route:
        err = f"ERROR: tool '{tool_name}' không tồn tại trong plugin"
        return err

    res = await route[tool_name]["call"](args)
    ms = int((time.time() - t0) * 1000)
    is_ok = not str(res).startswith("ERROR:")

    # 8. Append audit cả 2 nơi
    rec = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "conn_id": conn.get("id"),
        "connector": connector_id,
        "label": conn.get("label"),
        "tool": tool_name,
        "mode": "full",
        "cls": cls,
        "ok": is_ok,
        "ms": ms,
        "err": str(res)[:200] if not is_ok else "",
        "actor": actor,
        "args_keys": sorted((args or {}).keys()),
    }
    _append_audit(_MCP_AUDIT_PATH, rec)
    _append_audit(_CARE_AUDIT_PATH, rec)

    return res
