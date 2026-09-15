"""Đường khởi động phải nhẹ: thư viện của tính năng tuỳ chọn KHÔNG được nạp lúc import main.

    python tests/run.py khoi_dong_nhe     (KHÔNG mạng)

Bối cảnh 0.9.238: `import edge_tts` nằm ở đầu main.py dù TTS là tính năng tuỳ chọn mà đa số
phiên không đụng tới. Đo bằng `python -X importtime`: 944ms trong tổng 2.263ms nạp main (41%),
cộng kéo cả chuỗi aiohttp 212ms vào đường khởi động. Trên VPS, khởi động chậm ăn thẳng vào
cửa sổ healthcheck lúc deploy.

Test này tồn tại vì lỗi kiểu đó rất dễ tái phát: ai đó thêm `import <thư viện nặng>` lên đầu
file cho tiện, không ai nhận ra, và app chậm dần từng chút một mà không có tín hiệu nào.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-khoidong-"))
HERE = str(SERVER)
sys.path.insert(0, HERE)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


# Thư viện chỉ phục vụ tính năng TUỲ CHỌN -> phải nạp lười.
# Thêm vào đây khi phát hiện thư viện nặng mới, đừng chờ ai đó tự nhận ra.
NANG_PHAI_LUOI = {
    "edge_tts": "TTS (giọng đọc) - 944ms, kéo theo cả aiohttp",
    "aiohttp": "chỉ đi kèm edge_tts, không code nào của Javis dùng trực tiếp",
}

import main  # noqa: E402,F401

for mod, ly_do in NANG_PHAI_LUOI.items():
    check(f"'{mod}' KHÔNG nạp lúc import main ({ly_do})", mod not in sys.modules)

# ---- Nạp lười phải thật sự nạp được, không phải chỉ hoãn lỗi sang lúc user bấm nói ----
# CỐ TÌNH không gọi main.tts_voices(): hàm đó đi mạng tới dịch vụ giọng đọc của Microsoft,
# mà test này phải chạy được offline. Chỉ kiểm hai điều tách bạch: (a) thư viện nạp được
# khi cần, (b) hai chỗ dùng đều có lệnh import cục bộ nên sẽ nạp được lúc chạy.
try:
    import edge_tts  # noqa: E402,F401
    nap_duoc = True
except Exception as e:
    nap_duoc = False
    print(f"     (nạp edge_tts lỗi: {type(e).__name__}: {e})")
check("edge_tts vẫn nạp được khi cần (không phải chỉ hoãn lỗi sang lúc dùng)", nap_duoc)

import inspect  # noqa: E402

for ten in ("_tts_edge", "tts_voices"):
    fn = getattr(main, ten, None)
    src = inspect.getsource(fn) if fn else ""
    check(f"{ten}() có lệnh import edge_tts cục bộ", "import edge_tts" in src)

# ---- Trần chi phí nạp, đo bằng TỈ LỆ chứ không phải mili giây ----
# Bản đầu dùng trần tuyệt đối 3000ms và nó ĐÃ báo oan: trên máy đang bị quét virus, chỉ
# riêng `import fastapi` đã 2,9-6,3 giây và interpreter trống mất 500ms, nên `import main`
# vọt lên 7,6 giây mà không có dòng code nào đổi. Trần theo mili giây đo tốc độ MÁY, không
# đo thứ ta quan tâm.
#
# Tỉ lệ so với `import fastapi` thì miễn nhiễm với tốc độ máy, vì cả tử lẫn mẫu cùng chậm
# đi. Đo thực tế: hiện tại 1,93; nếu ai đó thêm lại edge_tts vào đầu file là 3,66. Ngưỡng
# 3,0 tách sạch hai trường hợp và còn dư biên cả hai phía.
TRAN_TI_LE = 3.0


def do_nap(code, n=3):
    import time
    ts = []
    for _ in range(n):
        t = time.perf_counter()
        subprocess.run([sys.executable, "-c", code], cwd=HERE, capture_output=True)
        ts.append((time.perf_counter() - t) * 1000)
    return min(ts)      # min: nhiễu chỉ cộng thêm, không bao giờ trừ bớt


base = do_nap("pass")
chi_fastapi = do_nap("import fastapi") - base
chi_main = do_nap("import main") - base
ti_le = chi_main / chi_fastapi if chi_fastapi > 0 else 0
print(f"     (interpreter trần {base:.0f} ms | fastapi {chi_fastapi:.0f} ms | "
      f"main {chi_main:.0f} ms | tỉ lệ {ti_le:.2f})")
check(f"nạp main không quá {TRAN_TI_LE} lần chi phí nạp fastapi (đang {ti_le:.2f} lần)",
      0 < ti_le < TRAN_TI_LE)

# ---- Không ai lén thêm lại import ở mức module ----
src = Path(HERE, "main.py").read_text(encoding="utf-8", errors="replace")
for mod in NANG_PHAI_LUOI:
    o_cot_0 = [ln for ln in src.split("\n")
               if ln.startswith(f"import {mod}") or ln.startswith(f"from {mod} ")]
    check(f"main.py không có 'import {mod}' ở mức module", not o_cot_0)

print()
if _fails:
    print(f"FAIL {len(_fails)} test: " + ", ".join(_fails))
    sys.exit(1)
print("TẤT CẢ PASS")
