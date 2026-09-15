"""Test: trang Token gọi ĐÚNG tên dự án, và bảng thẻ số liệu đã gỡ sạch. Chạy tay / CI:

    python tests/run.py session_brain

Bối cảnh:
- Nhãn dự án: mọi engine Claude chạy với cwd = gốc project chứ không phải thư mục brain,
  mà log thô của Claude Code chỉ ghi cwd - nên chat Telegram, việc nền và job dashboard bị
  gộp hết vào một dự án ("Javis-OS" ở máy, "app" trong Docker). Nay engine ghi riêng phiên
  nào thuộc brain nào (session_brain.py) để index lấy tên brain làm nhãn.
- Gỡ bảng số liệu: bảng thẻ ở cột trái đã bỏ khỏi giao diện từ trước, nhưng máy móc phía sau
  (/metrics + job spawn agent kèm MCP) vẫn chạy để nuôi một stub ẩn - đo trên log VPS là
  402/502 phiên của dự án "app". Bản này gỡ hẳn; test dưới chốt để không ai vô tình dựng lại.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import os
import sys
import tempfile
from pathlib import Path

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-sbrain-")

import session_brain       # noqa: E402
import usage_parsers as up  # noqa: E402

fails = []


def check(name, cond):
    print(("  OK   " if cond else "  FAIL ") + name)
    if not cond:
        fails.append(name)


# ---- 1. session_brain: ghi/đọc bản đồ phiên -> brain ----
session_brain.record("sid-abc", r"D:\Project\Javis-OS\brains\My Bullet Journal")
check("ghi/doc duoc", session_brain.mapping().get("sid-abc", "").endswith("My Bullet Journal"))

session_brain.record("sid-abc", r"D:\Project\Javis-OS\brains\Brain Default")
check("ghi de cung session_id (khong nhan doi)", len(session_brain.mapping()) == 1)
check("ghi de lay gia tri moi",
      session_brain.mapping()["sid-abc"].endswith("Brain Default"))

session_brain.record("", "x")
session_brain.record("sid-x", "")
check("bo qua doi so rong", len(session_brain.mapping()) == 1)


# ---- 2. Nhãn dự án trong index token ----
def _line(sid, cwd):
    return {"type": "assistant", "sessionId": sid, "cwd": cwd,
            "entrypoint": "sdk-py", "timestamp": "2026-07-25T10:00:00Z",
            "message": {"model": "claude-sonnet-5",
                        "usage": {"input_tokens": 10, "output_tokens": 5,
                                  "cache_read_input_tokens": 100,
                                  "cache_creation_input_tokens": 0}}}


brains = {"sid-1": "/data/brains/My Bullet Journal"}

ev = up.parse_claude_line(_line("sid-1", "/app"), set(), brains)
check("tra duoc brain -> nhan la ten brain", ev and ev["project"] == "My Bullet Journal")

ev2 = up.parse_claude_line(_line("sid-2", "/app"), set(), brains)
check("khong tra duoc brain -> giu nhan theo cwd", ev2 and ev2["project"] == "app")

ev3 = up.parse_claude_line(_line("sid-1", "/app"), set())
check("khong truyen map -> giu nhan theo cwd (tuong thich nguoc)",
      ev3 and ev3["project"] == "app")

check("nhan brain khong lam hong so token",
      ev and ev["input"] == 10 and ev["output"] == 5 and ev["cache_read"] == 100)


# ---- 3. Bảng thẻ số liệu đã gỡ sạch (chốt chặn hồi quy) ----
root = ROOT
main_src = (root / "server" / "main.py").read_text(encoding="utf-8")
app_src = (root / "dashboard" / "app.js").read_text(encoding="utf-8")
html_src = (root / "dashboard" / "index.html").read_text(encoding="utf-8")
css_src = (root / "dashboard" / "style.css").read_text(encoding="utf-8")
claude_md = (root / "CLAUDE.md").read_text(encoding="utf-8")

check("server: khong con endpoint /metrics", '@app.get("/metrics")' not in main_src)
check("server: khong con cache metrics", "_METRICS_CACHE" not in main_src)
check("dashboard: app.js sach", not any(
    k in app_src for k in ("loadMetrics", "renderMetrics", "metricCards",
                           "savedMetrics", "JAVIS_METRICS")))
check("dashboard: index.html khong con stub", "metricsStub" not in html_src)
check("dashboard: style.css khong con .metric-", ".metric-" not in css_src)
check("system prompt: khong con bat nhung JAVIS_METRICS", "JAVIS_METRICS" not in claude_md)

# Khối điều khiển JAVIS_* vẫn phải bị bóc trước khi ra kênh chữ thuần: ký ức cũ trong brain
# còn nhắc JAVIS_METRICS nên model vẫn có thể lỡ nhúng - không được lọt nguyên xi ra Telegram.
import channel_context  # noqa: E402
out = channel_context.strip_control_blocks(
    'Báo cáo xong.\n\n<!-- JAVIS_METRICS: [{"label":"Doanh thu","value":"250k"}] -->')
check("khoi la van bi boc khoi kenh chu thuan",
      "JAVIS_METRICS" not in out and "<!--" not in out and "Báo cáo xong." in out)

print()
if fails:
    print(f"FAILED {len(fails)}: " + "; ".join(fails))
    sys.exit(1)
print("PASS - tat ca")
