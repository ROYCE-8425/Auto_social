"""Test endpoint /brains/delete + /brains/new (tombstone). Chạy:
    python tests/run.py brain_delete_endpoint"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import os, sys, asyncio, tempfile
from pathlib import Path
os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="jv-del-state-"))
import main  # noqa: E402
import git_brain as gb  # noqa: E402

_fails = []
def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond: _fails.append(name)

BR = Path(tempfile.mkdtemp(prefix="jv-del-brains-")).resolve()
main.BRAINS_DIR = str(BR)
(BR / "Brain Default").mkdir(parents=True)         # não mặc định (không xóa được)
foo = BR / "Foo"; foo.mkdir(parents=True); (foo / "n.md").write_text("hi", encoding="utf-8")

# Xóa Foo hợp lệ (confirm khớp) -> vào thùng rác + tombstone, không còn trong brains
r = asyncio.run(main.delete_brain(name="Foo", confirm="Foo"))
check("xóa Foo trả ok", isinstance(r, dict) and r.get("ok"))
check("Foo biến khỏi brains", not foo.exists())
check("tombstone Foo được ghi", (BR / gb.TOMBSTONE_DIR / "Foo.json").exists())
import config as cfgmod
trash = Path(cfgmod.STATE_DIR) / "brain-trash"
check("Foo nằm trong thùng rác", trash.is_dir() and len(list(trash.glob("Foo__*"))) == 1)

# Chặn xóa não mặc định
r2 = asyncio.run(main.delete_brain(name="Brain Default", confirm="Brain Default"))
check("chặn xóa não mặc định", hasattr(r2, "status_code") and r2.status_code == 400)

# confirm sai -> chặn
bar = BR / "Bar"; bar.mkdir(parents=True)
r3 = asyncio.run(main.delete_brain(name="Bar", confirm="sai"))
check("confirm sai -> chặn, Bar còn nguyên", hasattr(r3, "status_code") and bar.exists())

# Nguyên tử: write_tombstone lỗi SAU KHI move_to_trash thành công -> phải HOÀN TÁC move (đưa não
# trở lại brains), không được để lại trạng thái "mất mà không tombstone" (dễ bị hồi sinh oan).
roll = BR / "Roll"; roll.mkdir(parents=True); (roll / "n.md").write_text("hi", encoding="utf-8")
_orig_write_tombstone = gb.write_tombstone
def _boom(*a, **kw):
    raise RuntimeError("boom giả lập lỗi ghi tombstone")
gb.write_tombstone = _boom
try:
    r5 = asyncio.run(main.delete_brain(name="Roll", confirm="Roll"))
finally:
    gb.write_tombstone = _orig_write_tombstone
check("tombstone lỗi -> trả lỗi 500", hasattr(r5, "status_code") and r5.status_code == 500)
check("tombstone lỗi -> Roll được hoàn tác, còn nguyên trong brains", roll.is_dir())
check("tombstone lỗi -> không để lại tombstone cho Roll", not (BR / gb.TOMBSTONE_DIR / "Roll.json").exists())

# /brains/new gỡ tombstone cùng tên (dựng lại Foo)
gb.write_tombstone(str(BR), "Foo")
r4 = asyncio.run(main.new_brain(name="Foo"))
check("tạo lại Foo -> gỡ tombstone Foo", not (BR / gb.TOMBSTONE_DIR / "Foo.json").exists())

print(); print("TẤT CẢ PASS" if not _fails else f"{len(_fails)} FAIL: {_fails}")
sys.exit(1 if _fails else 0)
