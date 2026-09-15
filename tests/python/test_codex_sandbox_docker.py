"""Việc nền chạy bằng ChatGPT phải đọc/ghi được file trong Docker.

    python tests/run.py codex_sandbox_docker      (KHÔNG mạng, không spawn codex)

Chủ repo báo 2026-08-07 kèm ảnh Telegram: loop "[CK] Tin Hot Chứng Khoán" chạy bằng ChatGPT,
mọi lệnh đọc/ghi file đều trả `bwrap: Failed to make / slave: Permission denied`, và bản báo
cáo gửi về là một bài dài model tự kể lại nỗi bối rối của nó.

Nguyên nhân nằm NGOÀI Javis. Codex bọc mọi lệnh đọc/ghi file của nó bằng bubblewrap, mà
bubblewrap cần tạo được user namespace + đổi propagation của `/`. Container Javis chạy user
thường, không có CAP_SYS_ADMIN, và Ubuntu 24.04 còn chặn user namespace không đặc quyền bằng
AppArmor. Nên trong Docker, hai mức rào `read-only` (mode suggest) và `workspace-write` (mode
auto) của Codex KHÔNG BAO GIỜ khởi động được. Loop tạo từ chat mặc định là suggest, nên mọi
việc nền chạy bằng ChatGPT trong Docker đều câm theo đúng kiểu này. Chạy bằng Claude thì không
sao vì Javis chặn theo TỪNG TOOL qua chính SDK, không cần bubblewrap.

Chủ repo chốt hướng xử lý (2026-08-07): ảnh Docker tắt rào riêng của Codex, để chính container
làm rào. Test này khoá ba thứ:
  1. cờ `JAVIS_CODEX_SANDBOX` đổi được bản đồ mức quyền → cờ sandbox của Codex
  2. ảnh Docker THẬT SỰ đặt cờ đó (không thì bản vá chỉ nằm trên giấy)
  3. Javis nhận ra dấu vết bwrap và dán lời giải thích vào chính bản báo cáo, thay vì để chủ
     đọc một bài model tự kể chuyện
"""
import os
import sys
import tempfile

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-codexsb-"))
os.environ.pop("JAVIS_CODEX_SANDBOX", None)     # test tự đặt, đừng để môi trường máy chen vào

from _paths import ROOT, SERVER  # noqa: E402,F401

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import claude_cli  # noqa: E402

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


# ---- 1. Bản đồ mức quyền → cờ sandbox ----
def _ban_do():
    return {m: claude_cli.codex_sandbox_cho_mode(m) for m in ("suggest", "auto", "full")}


check("mặc định (không đặt cờ): giữ nguyên rào theo mức quyền",
      _ban_do() == {"suggest": "read-only", "auto": "workspace-write", "full": None})

for tat in ("off", "OFF", "0", "false", "none"):
    os.environ["JAVIS_CODEX_SANDBOX"] = tat
    check(f"JAVIS_CODEX_SANDBOX={tat!r} → bỏ rào ở MỌI mức",
          _ban_do() == {"suggest": None, "auto": None, "full": None})

os.environ["JAVIS_CODEX_SANDBOX"] = "auto"
check("JAVIS_CODEX_SANDBOX=auto → bật lại rào như cũ",
      _ban_do() == {"suggest": "read-only", "auto": "workspace-write", "full": None})
os.environ["JAVIS_CODEX_SANDBOX"] = "linh tinh"
check("giá trị lạ → giữ hành vi mặc định chứ không nổ",
      _ban_do()["suggest"] == "read-only")
os.environ.pop("JAVIS_CODEX_SANDBOX", None)

check("mức lạ (không có trong bản đồ) → không đặt rào, không nổ",
      claude_cli.codex_sandbox_cho_mode("mức-chưa-có") is None
      and claude_cli.codex_sandbox_cho_mode("") is None)


# ---- 2. Đường dây thật: aux_engine phải đi qua hàm này, không đọc dict cứng ----
import aux_engine  # noqa: E402


class _Vo:
    cwd = None
    tag = "loop"
    system_prompt = None
    javis_vault = None
    javis_mode = "suggest"


os.environ["JAVIS_CODEX_SANDBOX"] = "off"
cc = aux_engine._build_codex({"model": "gpt-5.5"}, _Vo(), "suggest", "loop")
check("loop mode suggest + cờ off → CodexCLI không nhận cờ --sandbox", cc.sandbox is None)
check("argv không còn --sandbox, và dùng đường bypass", "--sandbox" not in cc._build_args()
      and "--dangerously-bypass-approvals-and-sandbox" in cc._build_args())
os.environ["JAVIS_CODEX_SANDBOX"] = "auto"
cc2 = aux_engine._build_codex({"model": "gpt-5.5"}, _Vo(), "suggest", "loop")
check("cờ auto → loop suggest vẫn chạy read-only như cũ", cc2.sandbox == "read-only")
check("argv có --sandbox read-only kèm không hỏi duyệt",
      "--sandbox" in cc2._build_args() and "read-only" in cc2._build_args()
      and "never" in cc2._build_args())
os.environ.pop("JAVIS_CODEX_SANDBOX", None)


# ---- 3. Ảnh Docker phải THẬT SỰ tắt rào, không thì bản vá chỉ nằm trên giấy ----
DOCKERFILE = (ROOT / "Dockerfile").read_text(encoding="utf-8")
check("Dockerfile đặt JAVIS_CODEX_SANDBOX=off", "ENV JAVIS_CODEX_SANDBOX=off" in DOCKERFILE)
check("Dockerfile nói rõ vì sao (bubblewrap không chạy nổi trong container)",
      "bubblewrap" in DOCKERFILE and "CAP_SYS_ADMIN" in DOCKERFILE)
check("Dockerfile nói rõ ĐÁNH ĐỔI, không lặng lẽ hạ rào",
      "suggest" in DOCKERFILE and "MCP Hub" in DOCKERFILE)
# Chú thích phải nằm NGOÀI khối ENV nối dòng: chen vào giữa các dòng nối bằng "\" là trò may
# rủi theo phiên bản trình dựng, mà hỏng Dockerfile thì VPS không cập nhật được nữa.
_khoi_env = DOCKERFILE[DOCKERFILE.index("ENV JAVIS_HOST"):DOCKERFILE.index("ENV JAVIS_CODEX_SANDBOX")]
_noi_dong = _khoi_env[:_khoi_env.rindex("\\") + 1] if "\\" in _khoi_env else ""
check("không chen chú thích vào giữa khối ENV nối dòng",
      not any(d.strip().startswith("#") for d in _noi_dong.split("\n")))


# ---- 4. Nhận ra dấu vết bwrap và nói ra bằng tiếng người ----
DAU_VET = ('{"type":"item.completed","item":{"type":"command_execution","aggregated_output":'
           '"bwrap: Failed to make / slave: Permission denied\\n"}}')
check("nhận ra dấu vết bwrap trong dòng thô của Codex",
      bool(claude_cli._SANDBOX_HONG.search(DAU_VET)))
check("không bắt nhầm một lượt chạy bình thường",
      not claude_cli._SANDBOX_HONG.search('{"item":{"type":"command_execution",'
                                          '"aggregated_output":"đã ghi xong báo cáo"}}'))
NOTE = claude_cli._NOTE_SANDBOX_HONG
check("lời giải thích nói đúng thủ phạm chứ không đổ cho lượt chạy",
      "container" in NOTE and "không phải lỗi của lượt chạy" in NOTE)
check("lời giải thích chỉ đủ HAI lối ra thật",
      "JAVIS_CODEX_SANDBOX=off" in NOTE and "Claude" in NOTE)
check("lời giải thích không dùng em dash (luật CLAUDE.md)", "—" not in NOTE)

SRC = (SERVER / "claude_cli.py").read_text(encoding="utf-8")
check("lời giải thích được dán vào chính bản báo cáo cuối lượt",
      "_NOTE_SANDBOX_HONG" in SRC.split("turn.completed")[1][:600])
check("aux_engine gọi hàm chung, không đọc lại dict cứng",
      "codex_sandbox_cho_mode(" in (SERVER / "aux_engine.py").read_text(encoding="utf-8"))


if _fails:
    raise SystemExit(f"\nFAIL - test_codex_sandbox_docker: {len(_fails)} lỗi: {_fails}")
print("\nOK - test_codex_sandbox_docker: tất cả pass")
