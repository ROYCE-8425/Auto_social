"""MCP stdio phải đọc được response tools/list LỚN (một dòng NDJSON > 64KB).

    python tests/run.py stdio_big_line

Không cần pytest, không chạm mạng (tiến trình con là python -c ngay tại chỗ).

Bối cảnh: asyncio.create_subprocess_exec mặc định giới hạn StreamReader 64KB MỖI DÒNG.
tools/list của workspace-mcp (connector Google Workspace) là MỘT dòng JSON ~vài trăm KB
(hàng chục tool, docstring dài) nên readline() nổ "Separator is found, but chunk is longer
than limit" (LimitOverrunError đội lốt ValueError). Nút Kết nối chỉ hiện "Không kết nối
được (ValueError)" - không lần ra manh mối. Test này giữ cho trần dòng luôn đủ rộng.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import asyncio
import json
import os
import sys

import mcp_client

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


# Server MCP giả: trả lời initialize bình thường, tools/list là MỘT dòng ~200KB.
BIG = 200_000
CHILD = r"""
import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    msg = json.loads(line)
    m = msg.get("method")
    if msg.get("id") is None:
        continue
    if m == "initialize":
        res = {"capabilities": {}, "protocolVersion": "2025-06-18",
               "serverInfo": {"name": "fake", "version": "1"}}
    elif m == "tools/list":
        res = {"tools": [{"name": "big_tool", "description": "x" * %d,
                          "inputSchema": {"type": "object"}}]}
    else:
        res = {}
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": res}) + "\n")
    sys.stdout.flush()
""" % BIG

spec = {
    "key": "test-big-line",
    "transport": "stdio",
    "command": sys.executable,
    "args": ["-c", CHILD],
    "env": {},
    "label": "fake-big",
}


async def main():
    try:
        tools = await mcp_client.pool.list_tools(spec)
    finally:
        await mcp_client.pool.close_all()
    return tools


# CANARY: kịch bản phải THẬT SỰ vượt trần 64KB mặc định của asyncio.
line_len = len(json.dumps({"jsonrpc": "2.0", "id": 2, "result": {"tools": [
    {"name": "big_tool", "description": "x" * BIG, "inputSchema": {"type": "object"}}]}}) + "\n")
check(f"CANARY: dòng tools/list giả ({line_len} byte) vượt trần 64KB mặc định", line_len > 65536)

try:
    tools = asyncio.run(main())
    check("đọc được tools/list một dòng lớn (không nổ LimitOverrun/ValueError)", True)
    check("bóc đúng 1 tool", len(tools) == 1 and tools[0].get("name") == "big_tool")
    check("mô tả tool về đủ, không mất đuôi", len(tools[0].get("description") or "") == BIG)
except Exception as e:
    check(f"đọc được tools/list một dòng lớn (không nổ {type(e).__name__}: {str(e)[:80]})", False)

if _fails:
    print(f"\nFAIL - test_stdio_big_line: {len(_fails)} lỗi: {_fails}")
    sys.exit(1)
print("\nOK - test_stdio_big_line: tất cả pass")
