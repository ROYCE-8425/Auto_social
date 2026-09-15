"""Test hạ khối điều khiển xuống chữ cho kênh không phải web (v0.9.61). Chạy tay / CI:

    python tests/run.py channel_ask

KHÔNG mạng. Phủ: JAVIS_ASK xuống danh sách đánh số, JAVIS_METRICS biến mất sạch
(hồi quy cho lỗi rò sang Telegram), JSON hỏng không nuốt câu trả lời.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import os
import sys
import tempfile

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-asktest-"))

import channel_context  # noqa: E402

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


strip = channel_context.strip_control_blocks

# ---- 1. JAVIS_ASK xuống danh sách đánh số ----
ask = ('Doanh thu hôm nay 250k.\n\n<!-- JAVIS_ASK: {"question":"Xem kỳ nào?",'
       '"options":[{"label":"Tuần này","desc":"7 ngày"},{"label":"Tháng này"}]} -->')
out = strip(ask)
check("ask: giữ câu trả lời", "Doanh thu hôm nay 250k." in out)
check("ask: có câu hỏi", "Xem kỳ nào?" in out)
check("ask: đánh số 1", "1. Tuần này" in out)
check("ask: đánh số 2", "2. Tháng này" in out)
check("ask: không lộ khối thô", "JAVIS_ASK" not in out and "<!--" not in out)

# ---- 2. JAVIS_METRICS biến mất sạch (hồi quy lỗi rò sang Telegram) ----
met = 'Báo cáo xong.\n\n<!-- JAVIS_METRICS: [{"label":"Doanh thu","value":"250k"}] -->'
out = strip(met)
check("metrics: biến mất sạch", "JAVIS_METRICS" not in out and "<!--" not in out)
check("metrics: giữ câu trả lời", out.strip() == "Báo cáo xong.")

# ---- 3. Cả hai khối cùng lúc ----
both = ('Báo cáo.\n<!-- JAVIS_METRICS: [{"label":"A","value":"1"}] -->\n'
        '<!-- JAVIS_ASK: {"question":"Chọn?","options":[{"label":"a"}]} -->')
out = strip(both)
check("cả hai: metrics mất, ask thành danh sách", "JAVIS_METRICS" not in out
      and "1. a" in out and "Chọn?" in out)

# ---- 4. JSON hỏng: bỏ khối rác nhưng KHÔNG nuốt câu trả lời ----
bad = 'Câu trả lời thật.\n<!-- JAVIS_ASK: {"question": hỏng rồi -->'
out = strip(bad)
check("json hỏng: giữ câu trả lời", out.strip() == "Câu trả lời thật.")
check("json hỏng: không lộ khối thô", "JAVIS_ASK" not in out)

# ---- 5. Thừa lựa chọn cắt còn 4 ----
many = ('<!-- JAVIS_ASK: {"question":"Chọn?","options":[{"label":"a"},{"label":"b"},'
        '{"label":"c"},{"label":"d"},{"label":"e"}]} -->')
out = strip(many)
check("thừa lựa chọn: cắt còn 4", "4. d" in out and "5. e" not in out)

# ---- 6. Không có khối: trả nguyên văn ----
check("không khối: giữ nguyên", strip("Chỉ là câu trả lời.") == "Chỉ là câu trả lời.")
check("text rỗng: không nổ", strip("") == "")
check("None: không nổ", strip(None) == "")

if _fails:
    print(f"\nFAIL - {len(_fails)} test: {_fails}")
    sys.exit(1)
print("\nOK - test_channel_ask: tất cả pass")
