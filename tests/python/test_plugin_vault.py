"""Test: plugin phải thấy ĐÚNG brain, không âm thầm rơi về Brain Default. Chạy tay / CI:

    python tests/run.py plugin_vault

Bối cảnh bug: claude_sdk_engine._plugins_server gọi plugin_tools(mode, None) nên
PluginContext.vault_root (plugins_host.py:218) = None với MỌI plugin gọi từ Claude Code.
image-chatgpt truyền cctx.vault_root xuống image_gen._resolve_vault (image_gen.py:95-98),
hàm này thấy rỗng thì rơi về brains/Brain Default -> ảnh lưu SAI brain, im lặng.

Phủ:
- PluginContext giữ đúng vault_root được truyền.
- plugin_tools(mode, vault) dựng ctx có vault đó (không None).
- _resolve_vault: có vault hợp lệ thì KHÔNG rơi về Brain Default (khẳng định tiền đề của bug).
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-pvault-"))

import plugins_host  # noqa: E402
import image_gen     # noqa: E402

_fails = []


def check(name, cond):
    print(("ok  " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


_BRAIN = tempfile.mkdtemp(prefix="javis-brain-that-")

# ---- 1. Tiền đề của bug: _resolve_vault rơi về Brain Default khi vault rỗng ----
# Nếu assert này đỏ thì bug đã được sửa ở nơi khác và test cần viết lại.
fallback = str(image_gen._resolve_vault(None))
check("tiền đề: _resolve_vault(None) rơi về Brain Default",
      fallback.endswith("Brain Default"))
check("tiền đề: _resolve_vault(<vault thật>) tôn trọng vault",
      str(image_gen._resolve_vault(_BRAIN)) == _BRAIN)

# ---- 2. PluginContext giữ vault_root ----
# Chữ ký THẬT (plugins_host.py:214): __init__(self, slug, source, plugin_dir, vault_root)
ctx = plugins_host.PluginContext(slug="thu-nghiem", source="bundled",
                                 plugin_dir=Path(_BRAIN), vault_root=_BRAIN)
check("ctx: giữ đúng vault_root được truyền", ctx.vault_root == _BRAIN)
check("ctx: data_dir là property, không phải field gán tay", isinstance(ctx.data_dir, Path))

# ---- 3. _load_all dựng ctx THẤY vault (đây là chỗ bug sống) ----
# Assert vào ctx THẬT của plugin đã nạp, không assert kiểu trả về. LoadedPlugin giữ ctx
# (plugins_host.py:257 __slots__ có "ctx"), nên đọc thẳng được. Assert kiểu
# `isinstance(tools, list)` là TAUTOLOGY: luôn đúng kể cả khi ctx mù vault.
ent = plugins_host._load_all(_BRAIN)
loaded = ent["plugins"]
check("nạp: có ít nhất 1 plugin bundled để soi ctx", len(loaded) > 0)
check("ctx: MỌI plugin đã nạp thấy đúng brain (không None, không Brain Default)",
      all(lp.ctx.vault_root == _BRAIN for lp in loaded))

# Chứng minh bug: truyền None thì ctx mù -> đây chính là thứ đường SDK đang làm.
ent_none = plugins_host._load_all(None)
check("bug: _load_all(None) -> ctx.vault_root là None (tiền đề của lỗi lưu nhầm brain)",
      all(lp.ctx.vault_root is None for lp in ent_none["plugins"]))


# ---- 4. scope_vault=False: ctx VẪN thấy vault nhưng KHÔNG nạp plugin riêng-của-vault ----
import inspect  # noqa: E402
sig = inspect.signature(plugins_host.plugin_tools)
check("plugin_tools: có tham số scope_vault", "scope_vault" in sig.parameters)
check("plugin_tools: scope_vault mặc định True (giữ hành vi cũ cho hub)",
      sig.parameters["scope_vault"].default is True)

# ---- 5. HÀNH VI thật: engine SDK phải đưa ĐÚNG brain xuống plugin_tools, không suy từ cwd ----
# Bug gốc: _plugins_server cũ suy vault_root từ self.cwd, mà chat chạy với cwd = gốc project
# (CLAUDE_CWD, main.py:318) - không phải thư mục brain - nên vault_root luôn None ở đường chat.
# Test này monkeypatch plugin_tools để BẮT tham số vault_root nó thực sự nhận, thay vì đọc
# chuỗi trong source (giòn, không chứng minh hành vi).
import claude_sdk_engine  # noqa: E402

_seen = {}
_orig_plugin_tools = plugins_host.plugin_tools


def _spy_plugin_tools(mode, vault_root=None, *, scope_vault=True):
    _seen["mode"] = mode
    _seen["vault_root"] = vault_root
    _seen["scope_vault"] = scope_vault
    return [], {}   # danh sách tool rỗng -> _plugins_server dừng sớm, đủ để soi tham số


plugins_host.plugin_tools = _spy_plugin_tools
try:
    # Engine dựng với cwd = một thư mục KHÔNG phải brain (mô phỏng đúng CLAUDE_CWD của chat:
    # gốc project, không có Javis/ ở gốc) - đây chính là hiện trường của Critical.
    _cwd_khong_phai_brain = str(ROOT)   # gốc project, không có Javis/
    check("tiền đề: cwd mô phỏng KHÔNG phải một brain (không có Javis/ ở gốc)",
          not (Path(_cwd_khong_phai_brain) / "Javis").is_dir())

    eng = claude_sdk_engine.ClaudeSDK(cwd=_cwd_khong_phai_brain)
    eng.javis_vault = _BRAIN   # _apply_mcp (main.py) đặt tường minh - KHÔNG suy từ cwd
    eng._plugins_server()
    check("hành vi: plugin_tools nhận đúng brain đã đặt qua javis_vault (không None)",
          _seen.get("vault_root") == _BRAIN)

    # ---- Hồi quy CHÍNH cho Critical: cwd không phải brain + chưa đặt javis_vault ----
    # (vd engine mới dựng, _apply_mcp chưa chạy) -> vault_root PHẢI là None, không được suy
    # ngầm từ cwd ra bất kỳ giá trị nào khác - đúng hành vi "chưa biết brain" thay vì "đoán sai".
    eng2 = claude_sdk_engine.ClaudeSDK(cwd=_cwd_khong_phai_brain)
    _seen.clear()
    eng2._plugins_server()
    check("hồi quy: chưa đặt javis_vault -> vault_root None (không suy mù từ cwd)",
          _seen.get("vault_root") is None)

    check("hành vi: scope_vault vẫn False (không nạp plugin riêng-của-vault)",
          _seen.get("scope_vault") is False)
finally:
    plugins_host.plugin_tools = _orig_plugin_tools

# _brain_root suy-từ-cwd đã bị xoá khỏi engine (main._brain_root module-level mới là nguồn
# thật, main.py:1649) - đừng còn method trùng tên gây nhầm lẫn khi đọc code.
check("SDK: đã xoá helper _brain_root suy-từ-cwd (trùng tên, vô dụng)",
      not hasattr(claude_sdk_engine.ClaudeSDK, "_brain_root"))


if _fails:
    print(f"\nFAIL - test_plugin_vault: {len(_fails)} lỗi: {_fails}")
    sys.exit(1)
print("\nOK - test_plugin_vault: tất cả pass")
