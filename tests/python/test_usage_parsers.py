"""Test usage_parsers (parse thuan, khong I/O ngoai path duoc truyen). Chay tay:

    python tests/run.py usage_parsers

Khong pytest, khong cham mang. Exit code != 0 neu fail. Tu co lap temp dir cho phan
co doc file (Codex).
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import json
import os
import sys
import tempfile
from pathlib import Path

import usage_parsers as up  # noqa: E402

_fails = []


def check(name, cond):
    print(("OK   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


# ============================================================
# Task 1: parse_claude_line
# ============================================================
# Dong that dang assistant, entrypoint sdk-cli, co cache. Timestamp 18:30 UTC =
# 01:30 (+7) NGAY HOM SAU (30) - de bat loi doi mui gio.
line_bg = {
    "type": "assistant", "entrypoint": "sdk-cli", "isSidechain": False,
    "sessionId": "sess-bg", "cwd": "D:\\Project\\Javis-OS",
    "timestamp": "2026-06-29T18:30:00.000Z",
    "message": {"model": "claude-opus-4-8", "usage": {
        "input_tokens": 10, "output_tokens": 300,
        "cache_read_input_tokens": 14447, "cache_creation_input_tokens": 18184}},
}
ev = up.parse_claude_line(line_bg, set())
check("claude: provider=claude", bool(ev) and ev["provider"] == "claude")
check("claude: source=javis (sdk)", ev["source"] == "javis")
check("claude: activity=background (session ngoai chat set)", ev["activity"] == "background")
check("claude: giu du input+cache", ev["input"] == 10 and ev["cache_read"] == 14447 and ev["cache_create"] == 18184)
check("claude: output", ev["output"] == 300)
check("claude: day doi sang UTC+7 (hom sau)", ev["day"] == "2026-06-30")
check("claude: project = basename cwd", ev["project"] == "Javis-OS")
check("claude: model giu nguyen", ev["model"] == "claude-opus-4-8")

ev_chat = up.parse_claude_line(line_bg, {"sess-bg"})
check("claude: activity=chat khi session thuoc chat set", ev_chat["activity"] == "chat")

ev_sc = up.parse_claude_line({**line_bg, "isSidechain": True}, {"sess-bg"})
check("claude: activity=subagent khi isSidechain (uu tien)", ev_sc["activity"] == "subagent")

ev_man = up.parse_claude_line({**line_bg, "entrypoint": "claude-desktop"}, set())
check("claude: entrypoint desktop -> source=manual", ev_man["source"] == "manual")
check("claude: manual -> activity=manual", ev_man["activity"] == "manual")

check("claude: synthetic -> None",
      up.parse_claude_line({**line_bg, "message": {"model": "<synthetic>", "usage": {"input_tokens": 5}}}, set()) is None)
check("claude: non-assistant -> None", up.parse_claude_line({"type": "user"}, set()) is None)
check("claude: khong co usage -> None",
      up.parse_claude_line({"type": "assistant", "message": {"model": "claude-opus-4-8"}}, set()) is None)
check("claude: 0 token -> None",
      up.parse_claude_line({"type": "assistant", "entrypoint": "sdk-cli", "timestamp": "2026-06-29T18:30:00.000Z",
                            "message": {"model": "claude-opus-4-8", "usage": {"input_tokens": 0, "output_tokens": 0}}}, set()) is None)


# ============================================================
# Task 2: parse_codex_file
# ============================================================
_CODEX_LINES = [
    {"timestamp": "2026-07-05T02:00:00.000Z", "type": "session_meta",
     "payload": {"id": "abc", "cwd": "D:\\Project\\Demo", "model_provider": "openai"}},
    {"timestamp": "2026-07-05T02:00:05.000Z", "type": "turn_context", "payload": {"model": "gpt-5.5"}},
    # token_count CONG DON (cumulative) - lay dong CUOI lam tong phien, KHONG cong het.
    {"timestamp": "2026-07-05T02:01:00.000Z", "type": "event_msg", "payload": {"type": "token_count",
     "info": {"total_token_usage": {"input_tokens": 1000, "cached_input_tokens": 200, "output_tokens": 50, "total_tokens": 1050}}}},
    {"timestamp": "2026-07-05T18:30:00.000Z", "type": "event_msg", "payload": {"type": "token_count",
     "info": {"total_token_usage": {"input_tokens": 3000, "cached_input_tokens": 800, "output_tokens": 150, "total_tokens": 3150}}}},
]
_tmp = Path(tempfile.mkdtemp(prefix="javis-codextest-"))
_rollout = _tmp / "rollout-2026-07-05T02-00-00-abc.jsonl"
_rollout.write_text("\n".join(json.dumps(x) for x in _CODEX_LINES), encoding="utf-8")

cev = up.parse_codex_file(str(_rollout))
check("codex: provider=codex", bool(cev) and cev["provider"] == "codex")
check("codex: lay tong phien = dong cuoi (khong cong don)", cev["output"] == 150)
check("codex: input moi = input - cached", cev["input"] == 2200)
check("codex: cache_read = cached", cev["cache_read"] == 800)
check("codex: cache_create = 0", cev["cache_create"] == 0)
check("codex: model tu payload", cev["model"] == "gpt-5.5")
check("codex: project tu session_meta cwd", cev["project"] == "Demo")
check("codex: day UTC+7 (18:30Z -> hom sau)", cev["day"] == "2026-07-06")
check("codex: source=javis", cev["source"] == "javis")

_no = _tmp / "rollout-empty.jsonl"
_no.write_text(json.dumps({"type": "session_meta", "payload": {"id": "x"}}), encoding="utf-8")
check("codex: khong co token_count -> None", up.parse_codex_file(str(_no)) is None)


# ============================================================
# Task 3: estimate_cost + load_prices
# ============================================================
_prices = {"claude-opus": {"in": 15.0, "out": 75.0, "cache_read": 1.5, "cache_write": 18.75}}
_ev_1m = {"model": "claude-opus-4-8", "input": 1_000_000, "output": 1_000_000,
          "cache_read": 1_000_000, "cache_create": 1_000_000}
check("cost: 1M moi loai opus = 15+75+1.5+18.75", abs(up.estimate_cost(_ev_1m, _prices) - 110.25) < 1e-6)
check("cost: model khong khop -> 0",
      up.estimate_cost({"model": "weird-model", "input": 1000, "output": 1000, "cache_read": 0, "cache_create": 0}, _prices) == 0)

_prices2 = {"gpt": {"in": 1.0, "out": 0, "cache_read": 0, "cache_write": 0},
            "gpt-5": {"in": 2.0, "out": 0, "cache_read": 0, "cache_write": 0}}
_ev_g = {"model": "gpt-5.5", "input": 1_000_000, "output": 0, "cache_read": 0, "cache_create": 0}
check("cost: khop tien to DAI NHAT (gpt-5 chu khong gpt)", abs(up.estimate_cost(_ev_g, _prices2) - 2.0) < 1e-6)

_loaded = up.load_prices()
check("cost: load_prices doc duoc usage_pricing.json", isinstance(_loaded, dict) and "claude-opus" in _loaded)


if _fails:
    print("\n%d FAIL" % len(_fails))
    sys.exit(1)
print("\nALL PASS")
