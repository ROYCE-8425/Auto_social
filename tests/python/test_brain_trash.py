"""Test helpers thùng rác + _dir_newer_than của git_brain. Chạy:
    python tests/run.py brain_trash"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import os, sys, time, tempfile
from pathlib import Path
import git_brain as gb  # noqa: E402

_fails = []
def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond: _fails.append(name)

TMP = Path(tempfile.mkdtemp(prefix="jv-trash-")).resolve()
BR = TMP / "brains"; TRASH = TMP / "trash"
brain = BR / "Foo"; (brain / "sub").mkdir(parents=True)
(brain / "note.md").write_text("hi", encoding="utf-8")

# move_to_trash: nguồn biến mất, đích xuất hiện trong thùng rác
dest = gb.move_to_trash(str(brain), str(TRASH), "Foo")
check("move_to_trash trả path đích", bool(dest))
check("nguồn đã biến khỏi brains", not brain.exists())
check("đích nằm trong thùng rác + còn note", dest and Path(dest, "note.md").read_text(encoding="utf-8") == "hi")
check("move nguồn không tồn tại -> None", gb.move_to_trash(str(BR / "KhongCo"), str(TRASH), "KhongCo") is None)

# _dir_newer_than
d2 = BR / "Bar"; d2.mkdir(parents=True)
f = d2 / "x.md"; f.write_text("x", encoding="utf-8")
past = int(time.time()) - 1000; future = int(time.time()) + 1000
check("_dir_newer_than: có file mới hơn mốc quá khứ", gb._dir_newer_than(str(d2), past) is True)
check("_dir_newer_than: không file nào mới hơn mốc tương lai", gb._dir_newer_than(str(d2), future) is False)
check("_dir_newer_than: ts<=0 -> False", gb._dir_newer_than(str(d2), 0) is False)

# gc_trash: mục quá 30 ngày bị dọn, mục mới giữ
oldt = TRASH / "Old__20200101-000000"; oldt.mkdir(parents=True)
os.utime(oldt, (time.time() - 40 * 86400, time.time() - 40 * 86400))
newt = TRASH / "New__20990101-000000"; newt.mkdir(parents=True)
n = gb.gc_trash(str(TRASH), 30)
check("gc_trash dọn mục >30 ngày", not oldt.exists() and n >= 1)
check("gc_trash giữ mục mới", newt.exists())

print(); print("TẤT CẢ PASS" if not _fails else f"{len(_fails)} FAIL: {_fails}")
sys.exit(1 if _fails else 0)
