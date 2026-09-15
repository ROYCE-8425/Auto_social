"""Test endpoint /path/exists (dùng cho dropdown chọn não dọn folder ngoài đã xoá). Chạy:

    python tests/run.py path_exists

KHÔNG mạng: gọi thẳng hàm endpoint. Phủ: thư mục thật → is_dir True; path đã xoá → is_dir
False + exists False; file (không phải thư mục) → exists True nhưng is_dir False; path rỗng.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import asyncio
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-pathtest-"))

import main  # noqa: E402

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


_TMP = Path(tempfile.mkdtemp(prefix="javis-pathexists-")).resolve()
_DIR = _TMP / "brain-that"
_DIR.mkdir()
_FILE = _TMP / "la-file.md"
_FILE.write_text("hi", encoding="utf-8")
_GONE = _TMP / "da-xoa"   # chưa từng tạo

try:
    r = asyncio.run(main.path_exists(path=str(_DIR)))
    check("thư mục thật → exists=True, is_dir=True", r["exists"] is True and r["is_dir"] is True)

    r = asyncio.run(main.path_exists(path=str(_GONE)))
    check("path đã xoá → exists=False, is_dir=False", r["exists"] is False and r["is_dir"] is False)

    r = asyncio.run(main.path_exists(path=str(_FILE)))
    check("là FILE → exists=True nhưng is_dir=False (dropdown sẽ loại)",
          r["exists"] is True and r["is_dir"] is False)

    r = asyncio.run(main.path_exists(path=""))
    check("path rỗng → exists=False", r["exists"] is False and r["is_dir"] is False)
finally:
    import shutil
    shutil.rmtree(_TMP, ignore_errors=True)

print()
if _fails:
    print(f"{len(_fails)} FAIL: {_fails}")
    sys.exit(1)
print("TẤT CẢ PASS")
