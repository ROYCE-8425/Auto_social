"""usage_index: nhớ đệm bảng giá không đổi kết quả, và sqlite chịu được đọc-ghi song song.

    python tests/run.py usage_hotpath     (KHÔNG mạng)

Bối cảnh 0.9.238:
- estimate_cost quét tuyến tính CẢ bảng giá cho MỖI dòng. Đo trên dữ liệu thật: 53.496 lần
  gọi, 321.009 lần startswith cho 3 vòng summary+insights, trong khi chỉ có 11 model phân
  biệt và 6 khoá giá. Nay nhớ đệm model -> khoá giá.
- summary/insights chuyển sang chạy trong asyncio.to_thread, nên chúng đọc SONG SONG với
  refresh() đang ghi. Không có WAL thì người đọc và người ghi khoá nhau -> "database is
  locked" đúng lúc user mở trang Mức dùng.

Rủi ro của nhớ đệm là im lặng trả sai TIỀN, nên test đối chiếu từng dòng với thuật toán gốc.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import os
import sqlite3
import sys
import tempfile
import threading
import time
from pathlib import Path

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-usagehot-"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import usage_index as u      # noqa: E402
import usage_parsers as up   # noqa: E402

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


def cost_goc(ev, prices):
    """Thuật toán NGUYÊN BẢN trước khi nhớ đệm - dùng làm chuẩn đối chiếu."""
    model = ev.get("model") or ""
    best = ""
    for k in prices:
        if model.startswith(k) and len(k) > len(best):
            best = k
    if not best:
        return 0.0
    q = prices[best]
    c = (int(ev.get("input") or 0) * float(q.get("in") or 0)
         + int(ev.get("output") or 0) * float(q.get("out") or 0)
         + int(ev.get("cache_read") or 0) * float(q.get("cache_read") or 0)
         + int(ev.get("cache_create") or 0) * float(q.get("cache_write") or 0))
    return c / 1_000_000.0


prices = up.load_prices()
check(f"đọc được bảng giá ({len(prices)} khoá)", len(prices) > 0)

# ---- 1. Đối chiếu trên mọi tổ hợp model đáng ngờ ----
MODELS = sorted(prices) + [
    "", "khong-ton-tai", "claude", "claude-opus-5", "claude-opus-5-20260101",
    "gpt", "gpt-5-codex", "gpt-5-codex-high", "x" * 200,
    # tiền tố lồng nhau: phải chọn khoá DÀI NHẤT, đây là chỗ nhớ đệm dễ sai nhất
] + [k + "-hau-to" for k in prices] + [k[:-1] for k in prices if len(k) > 1]

lech = []
for m in MODELS:
    for tok in ((0, 0, 0, 0), (1000, 500, 0, 0), (0, 0, 12345, 6789), (10**9, 10**9, 10**9, 10**9)):
        ev = {"model": m, "input": tok[0], "output": tok[1],
              "cache_read": tok[2], "cache_create": tok[3]}
        if up.estimate_cost(ev, prices) != cost_goc(ev, prices):
            lech.append(m)
check(f"đối chiếu {len(MODELS)} model x 4 mức token: khớp tuyệt đối"
      + (f" (LỆCH: {lech[:4]})" if lech else ""), not lech)

# ---- 2. Đổi bảng giá thì nhớ đệm phải reset, không được dùng khoá cũ ----
gia_a = {"claude-": {"in": 3.0, "out": 15.0}}
gia_b = {"claude-": {"in": 999.0, "out": 999.0}}
ev = {"model": "claude-opus-5", "input": 1_000_000, "output": 0}
ca = up.estimate_cost(ev, gia_a)
cb = up.estimate_cost(ev, gia_b)
check("đổi bảng giá thì tính lại theo bảng MỚI", ca == 3.0 and cb == 999.0)
check("quay lại bảng cũ vẫn ra giá cũ", up.estimate_cost(ev, gia_a) == 3.0)

# ---- 3. Bảng giá RỖNG -> chi phí 0, không nổ ----
check("bảng giá rỗng thì chi phí = 0", up.estimate_cost(ev, {}) == 0.0)

# ---- 4. Nhớ đệm thật sự cắt được vòng quét ----
dem = {"n": 0}


class DemDict(dict):
    def __iter__(self):
        dem["n"] += 1
        return dict.__iter__(self)


gia_dem = DemDict({"claude-": {"in": 3.0, "out": 15.0}, "gpt-": {"in": 1.0, "out": 2.0}})
dem["n"] = 0
for _ in range(500):
    up.estimate_cost({"model": "claude-opus-5", "input": 1, "output": 1}, gia_dem)
check(f"500 lần tính cùng model chỉ quét bảng giá 1 lần (đếm {dem['n']})", dem["n"] == 1)

dem["n"] = 0
for i in range(500):
    up.estimate_cost({"model": f"model-{i % 7}", "input": 1, "output": 1}, gia_dem)
check(f"7 model phân biệt chỉ quét 7 lần dù gọi 500 lần (đếm {dem['n']})", dem["n"] == 7)

# ---- 5. sqlite: đọc trong lúc đang ghi (mô phỏng to_thread song song refresh) ----
u.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
c = u._connect()
mode = c.execute("PRAGMA journal_mode").fetchone()[0]
c.close()
check(f"kho usage bật WAL (đang là {mode})", str(mode).lower() == "wal")

loi = []


def ghi_lien_tuc():
    try:
        w = u._connect()
        for i in range(200):
            w.execute("INSERT INTO file_daily(path,day,provider,source,activity,model,project,"
                      "input,output,cache_read,cache_create) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                      (f"/p/{i}", "2026-07-28", "claude", "javis", "chat",
                       "claude-opus-5", "prj", 10, 5, 0, 0))
            w.commit()
        w.close()
    except Exception as e:
        loi.append(f"ghi: {type(e).__name__}: {e}")


t = threading.Thread(target=ghi_lien_tuc)
t.start()
try:
    for _ in range(60):
        r = u._connect()
        r.execute("SELECT count(*) FROM file_daily").fetchone()
        r.close()
        time.sleep(0.001)
except Exception as e:
    loi.append(f"đọc: {type(e).__name__}: {e}")
t.join()
check("đọc song song lúc đang ghi: không 'database is locked'"
      + (f" ({loi[:2]})" if loi else ""), not loi)

print()
if _fails:
    print(f"FAIL {len(_fails)} test: " + ", ".join(_fails))
    sys.exit(1)
print("TẤT CẢ PASS")
