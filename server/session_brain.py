"""Bản đồ phiên -> brain: cho trang Token gọi đúng TÊN DỰ ÁN.

Vì sao cần: mọi engine Claude đều chạy với cwd = gốc project (CLAUDE_CWD), không phải
thư mục brain - cả chat lẫn Telegram. Log thô của Claude Code chỉ ghi `cwd`, nên trang
Token gộp hết mọi phiên vào MỘT dự án ("Javis-OS" khi chạy ở máy, "app" khi chạy trong
Docker) dù thật ra mỗi phiên làm việc trên một brain khác nhau.

Đổi cwd sang thư mục brain thì sửa được nhãn nhưng phá chỗ khác (dò .claude/skills,
vault_root của plugin - xem chú thích ở main.py `_apply_mcp`), nên thay vào đó ta ghi
riêng ra đây: phiên nào thuộc brain nào. Engine gọi `record()` ngay khi biết session_id,
usage_index đọc `mapping()` lúc index log.

Chỉ có tác dụng cho phiên chạy TỪ LÚC bản này trở đi - phiên cũ không có gì để tra nên
vẫn mang nhãn theo cwd như trước.
"""
import os
import sqlite3
import threading

from config import STATE_DIR

DB_PATH = STATE_DIR / "session_brain.db"
_LOCK = threading.Lock()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=5)
    conn.execute("CREATE TABLE IF NOT EXISTS session_brain("
                 "session_id TEXT PRIMARY KEY, brain TEXT)")
    return conn


def record(session_id: str, brain: str) -> None:
    """Ghi nhớ phiên này chạy trên brain nào. Lỗi thì im lặng bỏ qua - đây chỉ là
    nhãn thống kê, không được phép làm hỏng một lượt chat."""
    if not session_id or not brain:
        return
    try:
        with _LOCK:
            conn = _connect()
            try:
                conn.execute(
                    "INSERT INTO session_brain(session_id, brain) VALUES(?,?) "
                    "ON CONFLICT(session_id) DO UPDATE SET brain=excluded.brain",
                    (str(session_id), str(brain)))
                conn.commit()
            finally:
                conn.close()
    except Exception:
        pass


def mapping() -> dict:
    """{session_id: duong_dan_brain}. Thiếu file / lỗi -> {} (không chặn index)."""
    out = {}
    try:
        if not os.path.exists(DB_PATH):
            return out
        conn = sqlite3.connect("file:%s?mode=ro" % DB_PATH, uri=True, timeout=5)
        try:
            for sid, brain in conn.execute("SELECT session_id, brain FROM session_brain"):
                if sid and brain:
                    out[sid] = brain
        finally:
            conn.close()
    except Exception:
        pass
    return out
