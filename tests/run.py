"""Chạy toàn bộ test của Javis (Python + JS). Chạy từ ĐÂU cũng được.

    python tests/run.py                  # tất cả
    python tests/run.py zalo             # chỉ file có 'zalo' trong tên
    python tests/run.py --js             # chỉ test JS
    python tests/run.py --py             # chỉ test Python
    python tests/run.py -v               # in cả output của test đỏ

Vì sao có file này: CI quét thư mục bằng vòng lặp shell, nhưng trên máy Windows thì gõ lại
vòng lặp đó mỗi lần rất phiền, và dễ chạy nhầm bằng python hệ thống (thiếu thư viện) thay vì
.venv. Script này tự tìm .venv và tự chọn đúng trình thông dịch.
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY_DIR = ROOT / "tests" / "python"
JS_DIR = ROOT / "tests" / "js"


def trinh_thong_dich() -> str:
    """Ưu tiên .venv của dự án - python hệ thống thường thiếu fastapi/yaml."""
    for p in (ROOT / ".venv" / "Scripts" / "python.exe", ROOT / ".venv" / "bin" / "python"):
        if p.is_file():
            return str(p)
    return sys.executable


def main() -> int:
    args = [a for a in sys.argv[1:]]
    ver = "-v" in args
    chi_js = "--js" in args
    chi_py = "--py" in args
    loc = [a for a in args if not a.startswith("-")]

    py = trinh_thong_dich()
    node = shutil.which("node")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")

    viec = []
    if not chi_js:
        viec += [([py, str(f)], f.name) for f in sorted(PY_DIR.glob("test_*.py"))]
    if not chi_py:
        if node:
            viec += [([node, str(f)], f.name)
                     for f in sorted(list(JS_DIR.glob("test_*.js")) + list(JS_DIR.glob("test_*.mjs")))]
        else:
            print("BỎ QUA test JS: không tìm thấy node trong PATH")
    if loc:
        viec = [(c, n) for c, n in viec if any(k.lower() in n.lower() for k in loc)]

    if not viec:
        print("Không có test nào khớp.")
        return 1

    # flush=True ở MỌI dòng: Python đệm stdout khi không gắn terminal, nên chạy nền hay qua
    # pipe thì log im ru tới lúc kết thúc - đúng lúc cần theo dõi tiến độ nhất thì không thấy gì.
    def ra(s=""):
        print(s, flush=True)

    ra(f"Chạy {len(viec)} test bằng {py}\n")
    do, t0 = [], time.perf_counter()
    for i, (cmd, ten) in enumerate(viec, 1):
        t = time.perf_counter()
        r = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        giay = time.perf_counter() - t
        cham = f"  ({giay:.0f}s)" if giay >= 5 else ""
        if r.returncode == 0:
            ra(f"  [{i:>2}/{len(viec)}] ok   {ten}{cham}")
        else:
            ra(f"  [{i:>2}/{len(viec)}] ĐỎ   {ten}{cham}")
            do.append(ten)
            if ver:
                for ln in (r.stdout or "").split("\n")[-25:]:
                    ra("       " + ln)
                for ln in (r.stderr or "").split("\n")[-15:]:
                    ra("       " + ln)

    giay = time.perf_counter() - t0
    ra(f"\n{len(viec) - len(do)}/{len(viec)} xanh trong {giay:.0f} giây")
    if do:
        ra("ĐỎ: " + ", ".join(do))
        ra("Chạy lại một cái để xem chi tiết:  python tests/run.py <tên> -v")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
