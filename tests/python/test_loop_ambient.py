"""Test cờ opt-in `ambient_mcp` của loop (khôi phục connector claude.ai cho loop nền).
Chạy tay / CI:

    python tests/run.py loop_ambient

KHÔNG cần Claude CLI/SDK/đăng nhập - chỉ test logic thuần:
- _norm_loop parse ambient_mcp (True / "true" / absent / False).
- save_loop round-trip: BẬT → ghi 'ambient_mcp: true' + đọc lại True; TẮT → KHÔNG ghi dòng, đọc lại False.
- _make_cli chọn nhánh đúng: ambient_mcp=true (suggest/auto) → KHÔNG gated (allowed_tools=None) +
  chặn cứng Bash/Web/Task + apply_mcp đúng mode; loop thường → gated (allowed_tools có giá trị);
  for_verify → LUÔN gated dù ambient_mcp (bước kiểm chứng phải an toàn).
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-looptest-"))

import self_improve

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


# ── stub deps (không đụng mạng / CLI) ──
_BRAIN_ROOT = tempfile.mkdtemp(prefix="javis-loopbrain-")
_applied = []   # ghi lại mode mỗi lần apply_mcp được gọi


def _atomic_write(path, text):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _apply_mcp(cli, mode="full", brain=None):
    # brain=None trong chữ ký: khớp _apply_mcp thật (main.py) sau khi self_improve._make_cli
    # được vá truyền brain=brain tường minh (Nợ 1, final-fix-gd2) - stub cũ thiếu tham số này
    # sẽ TypeError ở call site thật, rơi vào nhánh except TypeError và làm rớt luôn 'mode'.
    _applied.append(mode)
    cli.mcp_config = "STUB_HUB"
    return cli


deps = self_improve.LoopDeps(
    build_system_prompt=lambda brain: "SYS",
    brain_root=lambda brain: _BRAIN_ROOT,
    aux_model=lambda: None,
    atomic_write_text=_atomic_write,
    project_root=Path("."),
    state_dir=Path(os.environ["JAVIS_STATE_DIR"]),
    safe_tools=["Read", "Write", "Edit", "Glob", "Grep"],
    readonly_tools=["Read", "Glob", "Grep", "LS"],
    apply_mcp=_apply_mcp,
    mcp_allow_patterns=lambda: ["mcp__javis"],
)
feat = self_improve.LoopFeature(deps)


# ── 1. _norm_loop parse ambient_mcp ──
check("norm: ambient_mcp True → True",
      feat._norm_loop({"name": "L", "ambient_mcp": True}, "b", "l")["ambient_mcp"] is True)
check("norm: ambient_mcp 'true' → True",
      feat._norm_loop({"name": "L", "ambient_mcp": "true"}, "b", "l")["ambient_mcp"] is True)
check("norm: absent → False",
      feat._norm_loop({"name": "L"}, "b", "l")["ambient_mcp"] is False)
check("norm: False → False",
      feat._norm_loop({"name": "L", "ambient_mcp": False}, "b", "l")["ambient_mcp"] is False)


# ── 2. save_loop round-trip ──
feat.save_loop("brain", {"name": "Loop Ambient", "slug": "loop-ambient", "mode": "suggest",
                         "ambient_mcp": True, "body": "đọc gmail mỗi vòng"})
got = feat.get_loop("brain", "loop-ambient")
check("save: BẬT → đọc lại True", bool(got) and got["ambient_mcp"] is True)
raw_amb = (Path(_BRAIN_ROOT) / "Javis" / "loops" / "loop-ambient.md").read_text(encoding="utf-8")
check("save: file BẬT có dòng ambient_mcp: true", "ambient_mcp: true" in raw_amb)

feat.save_loop("brain", {"name": "Loop Thuong", "slug": "loop-thuong", "mode": "suggest",
                         "body": "việc thường"})
got2 = feat.get_loop("brain", "loop-thuong")
check("save: mặc định → đọc lại False", bool(got2) and got2["ambient_mcp"] is False)
raw_thuong = (Path(_BRAIN_ROOT) / "Javis" / "loops" / "loop-thuong.md").read_text(encoding="utf-8")
check("save: file mặc định KHÔNG có dòng ambient_mcp", "ambient_mcp" not in raw_thuong)


# ── 3. _make_cli chọn nhánh theo ambient_mcp ──
def _mk(over, for_verify=False):
    _applied.clear()
    base = {"mode": "suggest", "tools_profile": "vault-safe", "ambient_mcp": False, "goal": "business"}
    base.update(over)
    return feat._make_cli(base, cwd=_BRAIN_ROOT, sysprompt="SYS", for_verify=for_verify)


c_norm = _mk({"mode": "suggest"})
check("make: loop thường → gated (allowed_tools not None)", c_norm.allowed_tools is not None)

c_amb = _mk({"mode": "suggest", "ambient_mcp": True})
check("make: ambient suggest → allowed_tools None (non-gated)", c_amb.allowed_tools is None)
check("make: ambient suggest → chặn cứng Bash/Web/Task",
      {"Bash", "WebFetch", "WebSearch", "Task"}.issubset(set(c_amb.disallowed_tools or [])))
check("make: ambient suggest → apply_mcp mode='suggest'", _applied == ["suggest"])

c_amb_auto = _mk({"mode": "auto", "ambient_mcp": True})
check("make: ambient auto → allowed_tools None", c_amb_auto.allowed_tools is None)
check("make: ambient auto → apply_mcp mode='auto'", _applied == ["auto"])

c_verify = _mk({"mode": "auto", "ambient_mcp": True}, for_verify=True)
check("make: ambient + for_verify → vẫn gated (an toàn)", c_verify.allowed_tools is not None)


if _fails:
    print(f"\nFAIL - test_loop_ambient: {len(_fails)} lỗi: {_fails}")
    sys.exit(1)
print("\nOK - test_loop_ambient: tất cả pass")
