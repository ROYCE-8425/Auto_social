"""Test bộ MCP NATIVE của Codex (kho gốc ~/.codex/config.toml) trong claude_cli.py. Chạy tay / CI:

    python tests/run.py codex_native_mcp

Chỉ test các hàm PURE (parse output `codex mcp list --json` / bảng text, dựng argv `mcp add`) -
không cần cài Codex CLI, không spawn tiến trình.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import json
import os
import sys


from claude_cli import (   # noqa: E402
    codex_mcp_parse_list, codex_mcp_parse_list_text, _codex_mcp_add_args,
)

_fails = []


def check(name, cond):
    print(("ok  " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


# ---- 1. codex_mcp_parse_list: list phẳng (transport dạng dict) ----
flat = json.dumps([
    {"name": "github", "transport": {"type": "streamable_http", "url": "https://api.github.com/mcp"}},
    {"name": "docs", "transport": {"type": "stdio", "command": "npx", "args": ["docs-mcp", "--x"]}},
])
got = codex_mcp_parse_list(flat)
check("flat: đủ 2 server", [s["name"] for s in got] == ["github", "docs"])
check("flat: server http giữ url", got[0]["url"] == "https://api.github.com/mcp")
check("flat: server stdio gộp command + args", got[1]["command"] == "npx docs-mcp --x")
check("flat: transport lấy từ dict", got[0]["transport"] == "streamable_http" and got[1]["transport"] == "stdio")
check("flat: mặc định coi là connected", all(s["connected"] for s in got))

# ---- 2. hình dạng map tên→cấu hình (kiểu mcp_servers trong config.toml) ----
asmap = json.dumps({"mcp_servers": {
    "zalo": {"command": "python", "args": ["-m", "zalo_mcp"]},
    "pos": {"url": "https://mcp.pos.vn/mcp"},
}})
got = codex_mcp_parse_list(asmap)
check("map: đủ 2 server, tên lấy từ key", sorted(s["name"] for s in got) == ["pos", "zalo"])
check("map: url phẳng vẫn đọc được", next(s for s in got if s["name"] == "pos")["url"] == "https://mcp.pos.vn/mcp")

# ---- 3. bọc {"servers": [...]} + trạng thái enabled/auth ----
wrapped = json.dumps({"servers": [
    {"name": "a", "url": "https://a/mcp", "enabled": False},
    {"name": "b", "url": "https://b/mcp", "auth_status": "unauthenticated"},
    {"name": "c", "url": "https://c/mcp"},
]})
got = codex_mcp_parse_list(wrapped)
check("wrapped: enabled=False → tắt, không connected",
      got[0]["status"] == "tắt" and got[0]["connected"] is False)
check("wrapped: unauthenticated → cần đăng nhập, không connected",
      "đăng nhập" in got[1]["status"] and got[1]["connected"] is False)
check("wrapped: bình thường → connected", got[2]["connected"] is True)

# ---- 4. đầu vào hỏng không nổ ----
check("rác không phải JSON → []", codex_mcp_parse_list("codex: error blah") == [])
check("chuỗi rỗng → []", codex_mcp_parse_list("") == [])
check("JSON số → []", codex_mcp_parse_list("42") == [])
check("list phần tử rác bị bỏ, thiếu name bị bỏ",
      codex_mcp_parse_list('[1, {"url": "https://x"}, {"name": "ok"}]') == [
          {"name": "ok", "url": "", "command": "", "transport": "", "status": "đã khai báo",
           "connected": True}])

# ---- 5. fallback bảng text (codex cũ không có --json) ----
txt = """Name    Command    Args
────    ───────    ────
docs    npx        docs-mcp
zalo    python     -m zalo_mcp
"""
got = codex_mcp_parse_list_text(txt)
check("text: lấy đúng tên, bỏ header + kẻ bảng", [s["name"] for s in got] == ["docs", "zalo"])
check("text: 'No MCP servers configured' → []",
      codex_mcp_parse_list_text("No MCP servers configured.\n") == [])
check("text: rỗng → []", codex_mcp_parse_list_text("") == [])

# ---- 6. _codex_mcp_add_args ----
check("add http: --url", _codex_mcp_add_args("pos", url="https://x/mcp")
      == ["mcp", "add", "pos", "--url", "https://x/mcp"])
check("add http + bearer_env: thêm --bearer-token-env-var (TÊN biến, không phải token)",
      _codex_mcp_add_args("pos", url="https://x/mcp", bearer_env="POS_TOKEN")
      == ["mcp", "add", "pos", "--url", "https://x/mcp", "--bearer-token-env-var", "POS_TOKEN"])
check("add stdio từ chuỗi: sau '--'", _codex_mcp_add_args("d", command="npx docs-mcp --x")
      == ["mcp", "add", "d", "--", "npx", "docs-mcp", "--x"])
check("add stdio từ list: giữ nguyên phần tử", _codex_mcp_add_args("d", command=["python", "-m", "m"])
      == ["mcp", "add", "d", "--", "python", "-m", "m"])
check("url thắng command khi đưa cả hai",
      _codex_mcp_add_args("d", url="https://x", command="npx y") == ["mcp", "add", "d", "--url", "https://x"])

if _fails:
    print(f"\nFAIL - test_codex_native_mcp: {len(_fails)} lỗi: {_fails}")
    sys.exit(1)
print("\nOK - test_codex_native_mcp: tất cả pass")
