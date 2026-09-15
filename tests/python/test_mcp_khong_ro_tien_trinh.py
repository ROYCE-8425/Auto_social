"""Đóng session MCP stdio phải giết CẢ CÂY tiến trình, không riêng launcher.

    python tests/run.py mcp_khong_ro_tien_trinh     (KHÔNG mạng)

Lỗi thật (VPS Hostinger, 15/08): lệnh stdio hay là launcher (uvx/npx) spawn tiếp server
thật bên dưới. close() cũ chỉ proc.kill() launcher, server thật thành mồ côi (PPid=1)
và sống mãi. Cộng với _IDLE_TTL == HEALTH_INTERVAL == 600 nên session vừa bị dọn xong
ngay trước mỗi vòng quét sức khoẻ → vòng nào cũng đẻ tiến trình mới. Sau 20 giờ: 100
tiến trình mcp-google-sheets, 96 cái mồ côi, ăn 6,9/7,9 GB RAM của VPS.

Test dùng cây tiến trình THẬT (bash spawn cháu sleep) chứ không mock, vì chính hành vi
"cháu có chết theo không" là thứ cần chứng minh.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


import mcp_client        # noqa: E402
import connect_health    # noqa: E402

# ---- 1. Hai mốc thời gian phải LỆCH nhau ----
# TTL == interval là cái bẫy cộng hưởng: session bị dọn đúng trước lúc vòng quét tới,
# vòng nào cũng dựng server mới. TTL > interval thì chính vòng quét giữ session ấm.
check("CANARY: _IDLE_TTL > HEALTH_INTERVAL (chống cộng hưởng dọn-rồi-dựng-lại)",
      mcp_client._IDLE_TTL > connect_health.HEALTH_INTERVAL)

def _da_chet(pid):
    """Tiến trình coi là CHẾT nếu không còn, hoặc còn xác zombie chờ init reap.
    os.kill(pid, 0) với zombie vẫn OK nên không dùng được một mình: cháu mồ côi về
    PPid=1, môi trường container pid 1 có khi không reap ngay, xác nằm đó nhưng
    RAM đã trả - đúng mục tiêu của fix."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    try:
        st = open(f"/proc/{pid}/status", encoding="utf-8").read()
        return "State:\tZ" in st
    except FileNotFoundError:
        return True
    except Exception:
        return False


if os.name == "nt":
    # Nhánh Windows dùng taskkill /T - không kiểm được trên CI Linux, và ngược lại.
    print("ok   (bỏ qua phần cây tiến trình - Windows dùng taskkill /T)")
else:
    async def _kiem_cay():
        ket = {}
        # Launcher bash spawn CHÁU (sleep) rồi in pid của cháu ra stdout - đúng hình
        # dạng uvx spawn server Python thật. Cháu phải NGẬM /dev/null: nếu nó giữ ống
        # stdout thừa kế, asyncio Process.wait() sẽ đợi ống đóng chứ không riêng exit
        # code, và test treo vô hạn.
        sess = mcp_client.McpStdioSession(
            "bash", ["-c", "sleep 300 >/dev/null 2>&1 & echo $!; wait"], label="test-cay")
        await sess.start()
        line = await asyncio.wait_for(sess.proc.stdout.readline(), timeout=10)
        ket["chau_pid"] = int(line.strip())
        ket["launcher_pid"] = sess.proc.pid
        # start_new_session phải ăn: nhóm của child KHÁC nhóm của test/server.
        ket["nhom_rieng"] = os.getpgid(sess.proc.pid) != os.getpgid(0)
        ket["nhom_la_chinh_no"] = os.getpgid(sess.proc.pid) == sess.proc.pid
        # Cháu phải đang sống thật (không phải zombie) trước khi đóng.
        ket["chau_song_truoc"] = not _da_chet(ket["chau_pid"])
        await sess.close()
        await asyncio.sleep(0.3)
        ket["chau_chet_sau"] = _da_chet(ket["chau_pid"])
        return ket

    async def _kiem_launcher_chet_truoc():
        # Launcher chết TRƯỚC khi close (đúng ca uvx crash lúc import): cháu mồ côi
        # vẫn phải bị quét vì killpg đi theo group id, không cần leader còn sống.
        sess = mcp_client.McpStdioSession(
            "bash", ["-c", "sleep 300 >/dev/null 2>&1 & echo $!"], label="test-mo-coi")
        await sess.start()
        line = await asyncio.wait_for(sess.proc.stdout.readline(), timeout=10)
        chau = int(line.strip())
        await sess.proc.wait()          # bash thoát ngay sau echo → cháu mồ côi
        if _da_chet(chau):
            return False                # tiền đề hỏng: cháu phải đang sống
        await sess.close()
        await asyncio.sleep(0.3)
        return _da_chet(chau)

    ket = asyncio.run(_kiem_cay())
    check("child được tách nhóm riêng (start_new_session)", ket["nhom_rieng"])
    check("child là leader của nhóm nó (pgid == pid)", ket["nhom_la_chinh_no"])
    check("cháu sống trước khi close", ket["chau_song_truoc"])
    check("CANARY: close() giết được CHÁU, không riêng launcher", ket["chau_chet_sau"])
    check("CANARY: launcher chết trước thì cháu mồ côi vẫn bị dọn khi close",
          asyncio.run(_kiem_launcher_chet_truoc()))

if _fails:
    print(f"\nFAIL {len(_fails)} muc: " + ", ".join(_fails))
    sys.exit(1)
print("\nOK - test_mcp_khong_ro_tien_trinh: tat ca pass")
