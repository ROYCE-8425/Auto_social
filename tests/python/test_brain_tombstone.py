"""Test helpers giấy báo tử (tombstone) của git_brain. Chạy:
    python tests/run.py brain_tombstone
KHÔNG mạng."""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import os, sys, time, tempfile
from pathlib import Path
import git_brain as gb  # noqa: E402

_fails = []
def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond: _fails.append(name)

BR = Path(tempfile.mkdtemp(prefix="jv-tomb-")).resolve()

# write -> đọc lại đúng nội dung, file đúng tên
gb.write_tombstone(str(BR), "Ngọc Thu Phạm")
p = BR / gb.TOMBSTONE_DIR / "Ngọc Thu Phạm.json"
check("write_tombstone tạo đúng file", p.is_file())
ts = gb._read_tombstones(str(BR))
check("read_tombstones trả 1 mục", len(ts) == 1)
check("mục có name đúng (giữ dấu)", ts and ts[0]["name"] == "Ngọc Thu Phạm")
check("mục có deleted_at là số > 0", ts and isinstance(ts[0]["deleted_at"], int) and ts[0]["deleted_at"] > 0)

# clear -> hết
gb.clear_tombstone(str(BR), "Ngọc Thu Phạm")
check("clear_tombstone gỡ file", not p.exists())
check("read sau clear = rỗng", gb._read_tombstones(str(BR)) == [])
check("clear tên không tồn tại không ném", (gb.clear_tombstone(str(BR), "Không Có") or True))

# gc_tombstones: mục quá hạn bị xóa, mục mới giữ
gb.write_tombstone(str(BR), "Cu")
old = BR / gb.TOMBSTONE_DIR / "Cu.json"
import json
d = json.loads(old.read_text(encoding="utf-8")); d["deleted_at"] = int(time.time()) - (181 * 86400)
old.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
gb.write_tombstone(str(BR), "Moi")
n = gb.gc_tombstones(str(BR))
check("gc xóa đúng 1 mục quá hạn", n == 1)
names = {t["name"] for t in gb._read_tombstones(str(BR))}
check("gc giữ mục mới, bỏ mục cũ", names == {"Moi"})

print(); print("TẤT CẢ PASS" if not _fails else f"{len(_fails)} FAIL: {_fails}")
sys.exit(1 if _fails else 0)
