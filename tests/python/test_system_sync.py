"""Test mirror_skills: copy cả cây con + cổng chữ ký stat. Chạy tay / CI:

    python tests/run.py system_sync

Không cần pytest, không chạm mạng. Tự dựng brain giả trong thư mục tạm.
Phủ: copy thư mục con (references/ scripts/), file phụ ngang hàng đổi thì mirror nhận
(bug CÓ SẴN), bỏ qua .disabled, add-only không xoá file lạ, không đổi gì thì KHÔNG copy
lại lần nào và KHÔNG còn đọc-và-băm SKILL.md, hai luồng đồng thời không treo, file nhị phân
qua nguyên vẹn. Phần đồng thời (ép bằng Event, KHÔNG sleep) tách bạch hai thứ khác nhau:
re-check bên trong khoá (luồng tới sau khi luồng trước đã xong thì không copy lặp) và BẢN
THÂN cái khoá (2 luồng không copy đè nhau cùng lúc - check này tắt khi gỡ khoá). Cuối cùng
phủ 3 bẫy của cache chữ ký: nguồn đổi GIỮA CHỪNG lượt copy không được mất cập nhật, skill copy
lỗi phải được thử lại lượt sau, và skill hỏng VĨNH VIỄN chỉ được tốn rglob của riêng nó chứ
không kéo cả brain vào full copy mỗi lượt chat.

Cuối file: rào chống DEADLOCK cho sync_brain (gọi thẳng đường thật, không mô phỏng) - `_LOCK`
của module là threading.Lock KHÔNG reentrant, `sync_brain` giữ nó rồi gọi mirror_skills bên
trong; nếu mirror_skills/_mirror_lock/_mirror_signature lỡ lấy lại đúng khoá đó thì treo VĨNH
VIỄN, không exception. Check này chạy sync_brain trên luồng daemon với join có hạn giờ, biến
hết-giờ thành một dòng FAIL rõ tên, không phải một lần chạy treo CI. Kèm 1 kiểm AST tĩnh độc
lập (không chạy code, chỉ đọc token) soát đúng 3 hàm đó không nhắc tên _LOCK.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import ast
import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-synctest-"))

import system_sync  # noqa: E402

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


def _mk_brain(prefix):
    """Brain giả: 1 skill có cây con + 1 skill đã tắt. Trả (root, skill_dir, mirror_dir)."""
    root = Path(tempfile.mkdtemp(prefix=prefix))
    sk = root / "skills" / "co-tai-lieu"
    (sk / "references").mkdir(parents=True)
    (sk / "scripts").mkdir(parents=True)
    (sk / "SKILL.md").write_text("---\nname: Có tài liệu\ndescription: Thử cây con.\n---\nthân\n",
                                 encoding="utf-8")
    (sk / "references" / "chi-tiet.md").write_text("chi tiết v1\n", encoding="utf-8")
    (sk / "scripts" / "chay.py").write_text("print('hi')\n", encoding="utf-8")
    (sk / "anh.png").write_bytes(b"\x89PNG\r\n\x1a\n binary")
    dis = root / "skills" / ".disabled" / "da-tat"
    dis.mkdir(parents=True)
    (dis / "SKILL.md").write_text("---\nname: Đã tắt\n---\nx\n", encoding="utf-8")
    return root, sk, root / ".claude" / "skills" / "co-tai-lieu"


# ---- copy đệ quy ----
_ROOT, _SK, _MIR = _mk_brain("javis-mirror-")
system_sync.mirror_skills(_ROOT)
check("mirror có SKILL.md", (_MIR / "SKILL.md").is_file())
check("mirror có references/chi-tiet.md", (_MIR / "references" / "chi-tiet.md").is_file())
check("mirror có scripts/chay.py", (_MIR / "scripts" / "chay.py").is_file())
check("mirror giữ nguyên byte của file nhị phân",
      (_MIR / "anh.png").is_file()
      and (_MIR / "anh.png").read_bytes() == b"\x89PNG\r\n\x1a\n binary")
check("KHÔNG mirror skill đã tắt", not (_ROOT / ".claude" / "skills" / "da-tat").exists())

# ---- đổi references/ mà SKILL.md không đổi -> mirror PHẢI nhận (bug CÓ SẴN) ----
(_SK / "references" / "chi-tiet.md").write_text("chi tiết v2\n", encoding="utf-8")
system_sync.mirror_skills(_ROOT)
try:
    actual = (_MIR / "references" / "chi-tiet.md").read_text(encoding="utf-8")
    check("đổi references/ (SKILL.md không đổi) -> mirror nhận bản mới",
          actual == "chi tiết v2\n")
except FileNotFoundError:
    check("đổi references/ (SKILL.md không đổi) -> mirror nhận bản mới", False)

# ---- đổi file phụ NGANG HÀNG mà SKILL.md không đổi -> mirror PHẢI nhận (bug CÓ SẴN) ----
(_SK / "anh.png").write_bytes(b"\x89PNG\r\n\x1a\n DOI ROI")
system_sync.mirror_skills(_ROOT)
try:
    actual = (_MIR / "anh.png").read_bytes()
    check("đổi file phụ ngang hàng (SKILL.md không đổi) -> mirror nhận bản mới",
          actual == b"\x89PNG\r\n\x1a\n DOI ROI")
except FileNotFoundError:
    check("đổi file phụ ngang hàng (SKILL.md không đổi) -> mirror nhận bản mới", False)

# ---- add-only: file lạ trong mirror KHÔNG bị xoá ----
(_MIR / "nguoi-dung-them.md").write_text("giữ tôi lại\n", encoding="utf-8")
(_SK / "SKILL.md").write_text("---\nname: Có tài liệu\ndescription: Đổi để ép copy.\n---\nthân 2\n",
                              encoding="utf-8")
system_sync.mirror_skills(_ROOT)
check("add-only: không xoá file lạ ở mirror", (_MIR / "nguoi-dung-them.md").is_file())

# ---- không đổi gì -> KHÔNG copy lại lần nào ----
# KHÔNG kiểm bằng mtime: shutil.copy2 giữ nguyên mtime của NGUỒN nên đích luôn cùng mtime
# dù có copy lại hay không -> test kiểu đó xanh cả khi code sai. Phải ĐẾM copy2 thật sự.
_copies = []
_orig_copy2 = shutil.copy2


def _spy_copy2(src, dst, *a, **kw):
    _copies.append(str(dst))
    return _orig_copy2(src, dst, *a, **kw)


shutil.copy2 = _spy_copy2
try:
    system_sync.mirror_skills(_ROOT)
    system_sync.mirror_skills(_ROOT)
finally:
    shutil.copy2 = _orig_copy2
check(f"không đổi gì -> KHÔNG copy lại lần nào (đếm được {len(_copies)})", len(_copies) == 0)

# ---- không đổi gì -> KHÔNG còn đọc-và-băm SKILL.md như bản cũ ----
# CHÍNH XÁC ĐIỀU NÀY CHỨNG MINH: bản cũ đọc SKILL.md qua Path.read_text để băm, mỗi skill
# hai lần (nguồn + đích), mỗi lượt gọi - đó là 52ms. Spy này bắt đúng đường đó biến mất.
# ĐIỀU NÓ *KHÔNG* CHỨNG MINH: "không đọc file nào cả". shutil.copy2 đọc bằng open() chứ
# không qua Path.read_text, nên nếu copy vẫn chạy thì spy này VẪN im. Việc chứng minh không
# copy là của check _copies ở trên. Hai check bù nhau, đừng gộp.
_reads = []
_orig_rt = Path.read_text
_orig_rb = Path.read_bytes


def _spy_rt(self, *a, **kw):
    _reads.append(str(self))
    return _orig_rt(self, *a, **kw)


def _spy_rb(self, *a, **kw):
    _reads.append(str(self))
    return _orig_rb(self, *a, **kw)


Path.read_text = _spy_rt
Path.read_bytes = _spy_rb
try:
    system_sync.mirror_skills(_ROOT)
finally:
    Path.read_text = _orig_rt
    Path.read_bytes = _orig_rb
check(f"không đổi gì -> KHÔNG còn đọc-và-băm SKILL.md (đếm được {len(_reads)} lượt read_text/read_bytes)",
      len(_reads) == 0)

# ---- hai luồng đồng thời trên cùng root -> không treo ----
_R2, _SK2, _MIR2 = _mk_brain("javis-mirrorpar-")
_done = []


def _race():
    system_sync.mirror_skills(_R2)
    _done.append(1)


_ts = [threading.Thread(target=_race) for _ in range(4)]
[t.start() for t in _ts]
[t.join(timeout=20) for t in _ts]
check("4 luồng đồng thời -> không treo, cả 4 xong", len(_done) == 4)
check("4 luồng đồng thời -> mirror vẫn đúng", (_MIR2 / "references" / "chi-tiet.md").is_file())

# ---- RE-CHECK trong khoá: luồng tới SAU khi luồng trước đã xong thì KHÔNG copy lặp ----
# TÊN CHECK NÀY NÓI ĐÚNG THỨ NÓ CHỨNG MINH: nó phủ lần kiểm THỨ HAI (re-check bên trong khoá)
# của mẫu double-checked locking, KHÔNG phủ bản thân cái khoá. Gỡ hẳn khoá đi mà giữ re-check
# thì check này VẪN xanh - đã thử. Việc chứng minh khoá có tác dụng là của check kế tiếp.
# Khe hở được ép: luồng T2 đọc chữ ký (thấy cây đã đổi, cache còn cũ) RỒI mới xin khoá - nếu
# đúng lúc đó T1 đã copy xong + cập nhật cache + NHẢ khoá, T2 xin khoá THÀNH CÔNG (khoá đang
# rảnh) và nếu không kiểm lại chữ ký sau khi cầm khoá thì T2 copy LẶP một lượt vô ích.
# Ép thứ tự bằng threading.Event (không sleep nên không phập phù): brain fresh (lần gọi ĐẦU
# nên cache chắc chắn trống -> "cây đã đổi" với MỌI luồng), giữ T2 đứng tại _mirror_lock
# (patch tạm hàm này) cho tới khi T1 chạy xong TOÀN BỘ (join thật, không đoán), rồi mới thả
# T2 ra xin khoá. Skill chỉ 1 file nên đếm copy2 = đếm số LƯỢT copy: đúng phải ra 1, bug ra 2.
_R3 = Path(tempfile.mkdtemp(prefix="javis-mirrorrace-"))
_sk3 = _R3 / "skills" / "chi-1-file"
_sk3.mkdir(parents=True)
(_sk3 / "SKILL.md").write_text("---\nname: Chỉ 1 file\ndescription: Test đua khoá.\n---\nthân\n",
                               encoding="utf-8")

_t2_reached_lock = threading.Event()   # T2 đã đọc chữ ký (thấy lệch) và vừa gọi tới _mirror_lock
_t1_fully_done = threading.Event()     # T1 đã join xong thật sự (copy xong + đã nhả khoá)
_orig_mirror_lock = system_sync._mirror_lock


def _lock_hook(key):
    if threading.current_thread().name == "T2":
        _t2_reached_lock.set()
        if not _t1_fully_done.wait(timeout=10):
            print("CẢNH BÁO: T1 không xong trong 10s - test đua có thể treo")
    return _orig_mirror_lock(key)


_race_copies = []
_orig_copy2_race = shutil.copy2


def _spy_copy2_race(src, dst, *a, **kw):
    _race_copies.append(str(dst))
    return _orig_copy2_race(src, dst, *a, **kw)


system_sync._mirror_lock = _lock_hook
shutil.copy2 = _spy_copy2_race
try:
    _t2 = threading.Thread(target=lambda: system_sync.mirror_skills(_R3), name="T2")
    _t2.start()
    _t2_reached_lock.wait(timeout=10)   # đảm bảo T2 đã kẹt đúng tại cửa xin khoá

    _t1 = threading.Thread(target=lambda: system_sync.mirror_skills(_R3), name="T1")
    _t1.start()
    _t1.join(timeout=10)                # T1 chạy TỰ DO, không bị chặn -> copy xong, nhả khoá
    _t1_fully_done.set()                # báo T2: giờ mới được xin khoá (chắc chắn khoá đã rảnh)

    _t2.join(timeout=10)
finally:
    shutil.copy2 = _orig_copy2_race
    system_sync._mirror_lock = _orig_mirror_lock

# BẮT BUỘC: nếu T2 chết trước khi tới hook thì số copy vẫn là 1 và check dưới xanh mà KHÔNG
# chứng minh gì cả. Phải khẳng định T2 đã thật sự tới đúng khe hở mình định ép.
check("T2 đã tới cửa xin khoá (khe hở được ép thật)", _t2_reached_lock.is_set())
check(f"re-check trong khoá: luồng tới sau khi luồng trước XONG -> không copy lặp "
      f"(đếm được {len(_race_copies)})", len(_race_copies) == 1)

# ---- KHOÁ tự thân: 2 luồng KHÔNG được copy2 ĐÈ NHAU cùng lúc lên cùng đường dẫn đích ----
# Đây mới là check TẮT khi gỡ khoá (đã kiểm: có khoá B copy 0 lần, gỡ khoá B copy 1 lần).
# Lý do khoá tồn tại: 2 luồng cùng copy2 lên CÙNG file đích = nguy cơ file rách (torn write).
# Ép xác định: giữ A ĐỨNG YÊN BÊN TRONG vòng copy (hook copy2 của A chờ tại đó => A chắc chắn
# đang GIỮ khoá), rồi mới thả B chạy. Có khoá: B trượt acquire(blocking=False) -> về luôn, B
# copy 0 lần. Không khoá: B chui thẳng vào vòng copy (re-check vẫn thấy cache cũ vì A chưa kịp
# ghi) -> B copy đè lên A. Không sleep, chỉ Event.
_R4 = Path(tempfile.mkdtemp(prefix="javis-mirrorlock-"))
_sk4 = _R4 / "skills" / "chi-1-file"
_sk4.mkdir(parents=True)
(_sk4 / "SKILL.md").write_text("---\nname: Chỉ 1 file\ndescription: Test khoá.\n---\nthân\n",
                               encoding="utf-8")

_a_inside_copy = threading.Event()   # A đang Ở TRONG vòng copy => A đang giữ khoá
_b_finished = threading.Event()      # B đã chạy xong trọn vẹn
_lock_copies = {"A": 0, "B": 0}
_orig_copy2_lock = shutil.copy2
_a_has_waited = {"done": False}


def _spy_copy2_lock(src, dst, *a, **kw):
    _name = threading.current_thread().name
    if _name in _lock_copies:
        _lock_copies[_name] += 1
    if _name == "A" and not _a_has_waited["done"]:
        _a_has_waited["done"] = True
        _a_inside_copy.set()          # A đã vào trong vòng copy, đang giữ khoá
        if not _b_finished.wait(timeout=10):
            print("CẢNH BÁO: B không xong trong 10s - test khoá có thể treo")
    return _orig_copy2_lock(src, dst, *a, **kw)


_b_ran_through = []


def _b_target():
    system_sync.mirror_skills(_R4)
    _b_ran_through.append(1)      # chỉ append khi mirror_skills TRẢ VỀ thật sự


shutil.copy2 = _spy_copy2_lock
try:
    _ta = threading.Thread(target=lambda: system_sync.mirror_skills(_R4), name="A")
    _ta.start()
    _a_reached = _a_inside_copy.wait(timeout=10)

    _tb = threading.Thread(target=_b_target, name="B")
    _tb.start()
    _tb.join(timeout=10)     # B chạy trọn vẹn TRONG LÚC A vẫn đang kẹt giữa vòng copy
    _b_finished.set()
    _ta.join(timeout=10)
finally:
    shutil.copy2 = _orig_copy2_lock

check("A đã kẹt trong vòng copy (khe hở được ép thật)", _a_reached)
# ĐỐI XỨNG với guard của T2: "B copy 0 lần" cũng XANH khi B không chạy gì cả (vd target rỗng,
# hoặc join hết giờ) - lúc đó check dưới chẳng chứng minh gì. Phải khẳng định B ĐÃ chạy hết.
check("B đã chạy trọn vẹn (khe hở được ép thật)", len(_b_ran_through) == 1)
check(f"khoá: B KHÔNG copy đè khi A đang copy dở (B copy {_lock_copies['B']} lần)",
      _lock_copies["B"] == 0)

# ---- nguồn ĐỔI GIỮA CHỪNG lượt copy -> KHÔNG được mất cập nhật ----
# Cache phải ghi chữ ký ẢNH CHỤP mà lượt copy dựa vào, KHÔNG phải chữ ký tính lại sau khi
# copy xong. POST /skills ghi skill giữa phiên là kịch bản CÓ THẬT của đường nóng này. Nếu
# tính lại: ta vừa chép nội dung CŨ nhưng cache lại ghi chữ ký MỚI -> cache nói dối -> tầng 1
# thoát vĩnh viễn -> mirror kẹt ở bản cũ mãi. Ép bằng hook copy2: chép xong file đầu tiên thì
# ghi đè nguồn bằng nội dung mới, đúng như một ghi ngoài xen vào giữa lượt.
_R5 = Path(tempfile.mkdtemp(prefix="javis-mirrormid-"))
_sk5 = _R5 / "skills" / "skill-x"
_sk5.mkdir(parents=True)
_src5 = _sk5 / "SKILL.md"
_src5.write_text("v1", encoding="utf-8")
_mir5 = _R5 / ".claude" / "skills" / "skill-x" / "SKILL.md"

_orig_copy2_mid = shutil.copy2
_mid_injected = {"done": False}


def _spy_copy2_mid(src, dst, *a, **kw):
    _r = _orig_copy2_mid(src, dst, *a, **kw)
    if not _mid_injected["done"]:      # mô phỏng POST /skills ghi xen GIỮA lượt copy
        _mid_injected["done"] = True
        _src5.write_text("v2-bản-mới", encoding="utf-8")
        os.utime(_src5, (1, 1))        # ép mtime khác hẳn để chữ ký chắc chắn đổi
    return _r


shutil.copy2 = _spy_copy2_mid
try:
    system_sync.mirror_skills(_R5)     # lượt 1: chép v1, rồi nguồn nhảy sang v2 giữa chừng
finally:
    shutil.copy2 = _orig_copy2_mid

system_sync.mirror_skills(_R5)         # lượt 2: PHẢI nhận ra nguồn còn mới hơn -> chép lại
check("nguồn đổi GIỮA CHỪNG lượt copy -> lượt sau vẫn bắt kịp, không mất cập nhật",
      _mir5.is_file() and _mir5.read_text(encoding="utf-8") == "v2-bản-mới")

# ---- 1 skill copy LỖI -> KHÔNG cache thành công, lượt sau phải THỬ LẠI ----
# Lỗi tạm thời (AV quét / handle đang mở trên Windows - đúng hazard mà chính comment trong
# _mirror_signature cảnh báo) không được biến thành "skill vắng mặt vĩnh viễn tới khi restart".
_R6 = Path(tempfile.mkdtemp(prefix="javis-mirrorerr-"))
for _n in ("skill-a", "skill-b"):
    _d6 = _R6 / "skills" / _n
    _d6.mkdir(parents=True)
    (_d6 / "SKILL.md").write_text(f"nội dung {_n}", encoding="utf-8")
_mir6 = _R6 / ".claude" / "skills"

_orig_copy2_err = shutil.copy2
_boom = {"fired": False}


def _spy_copy2_err(src, dst, *a, **kw):
    if not _boom["fired"] and "skill-a" in str(src):
        _boom["fired"] = True          # hỏng ĐÚNG MỘT LẦN rồi thôi
        raise PermissionError("giả lập AV quét đang giữ file")
    return _orig_copy2_err(src, dst, *a, **kw)


shutil.copy2 = _spy_copy2_err
try:
    system_sync.mirror_skills(_R6)     # lượt 1: skill-a lỗi, skill-b vẫn phải qua
finally:
    shutil.copy2 = _orig_copy2_err

check("1 skill lỗi KHÔNG chặn skill khác", (_mir6 / "skill-b" / "SKILL.md").is_file())
system_sync.mirror_skills(_R6)         # lượt 2: lỗi đã hết -> PHẢI thử lại skill-a
check("skill copy lỗi -> lượt sau THỬ LẠI (không bị cache là đã xong)",
      (_mir6 / "skill-a" / "SKILL.md").is_file())

# ---- skill hỏng VĨNH VIỄN -> lượt sau CHỈ chép lại nó, KHÔNG phạt skill lành ----
# Lỗi vĩnh viễn (MAX_PATH trên cây references/ sâu, file vướng ACL, file bị process khác giữ)
# KHÔNG tự khỏi. Nếu "có lỗi thì không cache chữ ký" thì mỗi lượt chat lại full rglob + copy2
# CẢ BRAIN: đo thật trên brain 27 skill/135 file là 161ms/lượt (so 18ms khi tầng 1 ăn) - tệ hơn
# cả bản ~52ms mà task này sinh ra để giết, tức là làm hỏng đúng mục đích của chính mình.
# Đúng phải là: vẫn cache chữ ký, nhưng nhớ RIÊNG slug nào lỗi và lượt sau chỉ thử lại nó.
_R7 = Path(tempfile.mkdtemp(prefix="javis-mirrorperm-"))
for _n in ("skill-hong", "skill-lanh"):
    _d7 = _R7 / "skills" / _n
    (_d7 / "references").mkdir(parents=True)
    (_d7 / "SKILL.md").write_text(f"nội dung {_n}", encoding="utf-8")
    (_d7 / "references" / "phu.md").write_text(f"phụ {_n}", encoding="utf-8")

_orig_copy2_perm = shutil.copy2
_perm_copies = []


def _spy_copy2_perm(src, dst, *a, **kw):
    _perm_copies.append(str(src))
    if "skill-hong" in str(src):
        raise PermissionError("hỏng VĨNH VIỄN, không bao giờ tự khỏi")
    return _orig_copy2_perm(src, dst, *a, **kw)


shutil.copy2 = _spy_copy2_perm
try:
    system_sync.mirror_skills(_R7)     # lượt 1: chép tất, skill-hong lỗi
    _perm_copies.clear()               # chỉ quan tâm CÁC LƯỢT SAU
    system_sync.mirror_skills(_R7)
    system_sync.mirror_skills(_R7)
finally:
    shutil.copy2 = _orig_copy2_perm

_lanh_lai = [c for c in _perm_copies if "skill-lanh" in c]
_hong_lai = [c for c in _perm_copies if "skill-hong" in c]
check(f"skill hỏng vĩnh viễn: skill LÀNH không bị chép lại mỗi lượt (chép lại {len(_lanh_lai)} lần)",
      len(_lanh_lai) == 0)
check(f"skill hỏng vĩnh viễn: vẫn được thử lại đều (thử {len(_hong_lai)} lần / 2 lượt)",
      len(_hong_lai) > 0)

# ---- CRITICAL 1: tắt rồi bật lại một skill KHÔNG được làm mất bản mirror vĩnh viễn ----
# Lặp lại ĐÚNG chuỗi hành động của server/main.py (endpoint /skills/toggle, cả hai nhánh):
#   TẮT: rename skills/<slug> -> skills/.disabled/<slug>, rmtree bản mirror, rồi gọi lại
#        mirror_skills(root) NGAY TẠI ĐÓ (dòng vừa thêm để vá CRITICAL 1).
#   BẬT: rename ngược lại rồi gọi mirror_skills(root) (nhánh này chưa bao giờ đổi).
# Vì sao cần dòng mirror_skills() ở nhánh TẮT: `rename` giữ NGUYÊN st_mtime_ns/st_size, nên nếu
# nhánh tắt không tự gọi mirror_skills để cache ghi nhận chữ ký-đã-tắt, thì nhánh BẬT sau đó tính
# ra chữ ký-cây-nguồn Y HỆT giá trị cache còn nhớ từ TRƯỚC KHI TẮT (cache đó chưa từng được cập
# nhật ở giữa) -> tầng 1 tưởng "cây không đổi gì" -> bỏ qua -> bản mirror vừa rmtree ở nhánh tắt
# KHÔNG BAO GIỜ được tạo lại, cho tới khi khởi động lại tiến trình. Gỡ dòng mirror_skills() ở
# nhánh tắt bên dưới (đặt `_DISABLE_CALLS_MIRROR = False`) để xem test này RED lại đúng như trước
# khi vá - đã kiểm bằng tay, xem báo cáo b4-final-fix-report.md.
_DISABLE_CALLS_MIRROR = True   # main.py bản đã vá: nhánh tắt CÓ gọi lại mirror_skills

_R8 = Path(tempfile.mkdtemp(prefix="javis-mirrortoggle-"))
_slug8 = "bat-tat"
_sk8 = _R8 / "skills" / _slug8
_sk8.mkdir(parents=True)
(_sk8 / "SKILL.md").write_text("---\nname: Bật tắt\ndescription: Test toggle.\n---\nthân\n",
                               encoding="utf-8")
_dis8 = _R8 / "skills" / ".disabled" / _slug8
_mir8 = _R8 / ".claude" / "skills" / _slug8 / "SKILL.md"

system_sync.mirror_skills(_R8)   # lượt mirror đầu tiên, y hệt build_system_prompt lượt chat đầu
check("toggle: sau mirror đầu tiên -> có mirror", _mir8.is_file())

# TẮT - y hệt main.py: rename sang .disabled rồi rmtree bản mirror.
_dis8.parent.mkdir(parents=True, exist_ok=True)
_sk8.rename(_dis8)
if _mir8.parent.is_dir():
    shutil.rmtree(_mir8.parent)
if _DISABLE_CALLS_MIRROR:
    system_sync.mirror_skills(_R8)   # dòng main.py vá CRITICAL 1 ở nhánh tắt
check("toggle: sau TẮT -> mirror đã gỡ", not _mir8.is_file())

# BẬT lại - y hệt main.py: rename ngược lại rồi gọi mirror_skills (nhánh này không đổi).
_dis8.rename(_sk8)
system_sync.mirror_skills(_R8)
check("toggle: TẮT rồi BẬT lại -> mirror PHẢI được tạo lại (CRITICAL 1)", _mir8.is_file())

shutil.rmtree(_R8, ignore_errors=True)

# ---- REGRESSION GUARD: sync_brain không được DEADLOCK (mirror_skills lỡ lấy lại _LOCK) ----
# VÌ SAO CHECK NÀY TỒN TẠI - ĐỪNG XOÁ VÌ TƯỞNG TRÙNG VỚI SOÁT AST Ở DƯỚI:
# `_LOCK` (system_sync.py, module-level) là threading.Lock THƯỜNG - KHÔNG PHẢI RLock, nên
# KHÔNG reentrant. `sync_brain` giữ nó suốt (`with _LOCK:`) rồi, NGAY BÊN TRONG khối đó, gọi
# `mirror_skills(root)`. Bản 0.9.64 cố tình cho mirror_skills một khoá RIÊNG (_MIRROR_LOCKS,
# canh bởi _MIRROR_LOCKS_GUARD) đúng để nó KHÔNG BAO GIỜ đụng _LOCK - xem lời giải ở
# docs/superpowers/specs/2026-07-17-mirror-skills-tree-design.md, mục "Sáu blocker cũ...",
# blocker 3. Điều đó hôm nay chỉ được xác nhận MỘT LẦN bằng mắt lúc review (đọc code, đếm
# 2 chỗ _LOCK bị lấy). Không gì NGĂN một sửa sau này (vô tình) thêm một lượt acquire _LOCK
# vào mirror_skills/_mirror_lock/_mirror_signature - lúc đó luồng đang giữ _LOCK tự xin lại
# CHÍNH khoá đó -> tự khoá mình -> TREO VĨNH VIỄN, không ném exception, không log gì cả. Vì
# sync_brain/ensure_synced chạy ở ĐƯỜNG NÓNG (build_system_prompt, mỗi lượt chat dashboard/
# Telegram/Kanban/loop/nhắc hẹn), lỗi này treo NGAY LƯỢT CHAT ĐẦU TIÊN CỦA MỌI BRAIN trong
# production - và trước bản vá này, KHÔNG MỘT TEST NÀO trong server/ gọi sync_brain hay
# ensure_synced (đã grep xác nhận), nên một sửa như vậy sẽ đi qua trót lọt: 13 file test khác
# xanh hết, byte-compile qua, và chỉ lộ ra khi người dùng thật báo "app treo".
#
# CÁI KHÓ: test một cái TREO mà không được tự treo theo. Gọi sync_brain thẳng trên luồng
# chính sẽ chặn vô thời hạn nếu deadlock thật xảy ra -> CI timeout sau hàng chục phút, không
# có tín hiệu gì hữu ích (không rõ vì sao đỏ, có khi tưởng nhầm máy CI chậm). Giải: chạy
# sync_brain trên MỘT LUỒNG DAEMON, join với thời hạn. Hết hạn mà luồng còn sống = hết-giờ
# biến thành một FAIL có TÊN RÕ RÀNG ngay lập tức - không phải một lần chạy treo, không phải
# một lần pass ngầm (im lặng bỏ qua thì chính là cái bẫy dự án này đã dính một lần: một cửa
# sổ-thời-gian không bao giờ mở ra phải in ra FAIL, không phải xanh). daemon=True nghĩa là dù
# luồng có thật sự kẹt, tiến trình vẫn thoát được ngay khi script kết thúc (không cần kill tay).
#
# Đi ĐƯỜNG THẬT, không mô phỏng: gọi thẳng system_sync.sync_brain(root) (không phải
# ensure_synced - hàm đó memo theo _SYNCED_ROOTS nên gọi lần hai trên cùng root sẽ no-op, và
# đằng nào _LOCK cũng bị giữ ngay trong sync_brain chứ không phải ở lớp memo của
# ensure_synced). root là brain rỗng dựng bằng tempfile.mkdtemp - sync_brain sẽ cài các skill/
# loop HỆ THỐNG thật của chính repo này vào đó (đọc từ .claude/skills + system/loops thật),
# giống hệt lượt sync đầu tiên của một brain mới trong production.
#
# TIỀN ĐỀ PHẢI TỰ KHẲNG ĐỊNH, KHÔNG ĐƯỢC GIẢ ĐỊNH (bài học review, xém ship lỗi này):
# "không treo" CHỈ có nghĩa khi cửa sổ deadlock THẬT SỰ được mở ra. mirror_skills trả về NGAY
# nếu <root>/skills không tồn tại (system_sync.py:263-264), mà thư mục đó chỉ có nhờ
# _system_items() (:143-161) đọc skill/loop từ .claude/skills + system/loops của CHÍNH REPO
# NÀY - không phải từ root tạm. Nếu nguồn đó rỗng thì sync_brain không cài gì, <root>/skills
# không sinh ra, mirror_skills thoát ở early-return và KHÔNG BAO GIỜ chạm tới chỗ có thể
# deadlock -> check thời gian ở dưới báo "ok" trong ~0.5s trong khi deadlock vẫn nằm nguyên
# trong code (đã tái hiện được: mutation còn sống + nguồn rỗng = xanh giả). Hôm nay repo ship
# vài skill hệ thống nên may mà chạy đúng, nhưng một lần reorg repo / sparse checkout / dời
# .claude/skills sẽ âm thầm THÁO NGÒI cái guard này mà không có tín hiệu đỏ nào - đúng kiểu
# "cửa sổ không bao giờ mở ra mà vẫn xanh" mà dự án này đã dính một lần. (Repo không còn loop
# hệ thống nào - guard này bám vào skill hệ thống nên vẫn mở được cửa sổ deadlock.)
# Nên: sau khi sync_brain trả về, BẮT BUỘC khẳng định vòng copy của mirror_skills đã CHẠY
# THẬT - ít nhất 1 skill hệ thống có mặt ở CẢ <root>/skills/*/SKILL.md LẪN
# <root>/.claude/skills/*/SKILL.md. Giao của hai tập chứng minh đúng điều đó: trên brain tạm
# mới tinh, KHÔNG gì khác tạo ra .claude/skills (migrate_brain đi CHIỀU NGƯỢC LẠI - dời
# .claude/skills -> skills/), nên slug nằm ở cả hai phía chỉ có thể do vòng copy sinh ra.
def _kiem_sync_brain_khong_deadlock():
    root = Path(tempfile.mkdtemp(prefix="javis-syncbrain-deadlock-"))
    ket_qua = {}

    def _chay():
        try:
            ket_qua["r"] = system_sync.sync_brain(root)
        except Exception as e:  # noqa: BLE001 - muốn thấy MỌI lỗi, kể cả lỗi lạ
            ket_qua["loi"] = e

    t = threading.Thread(target=_chay, name="sync_brain_deadlock_probe", daemon=True)
    t.start()
    t.join(timeout=15)
    con_treo = t.is_alive()
    check("REGRESSION mirror_skills/_mirror_lock/_mirror_signature lấy lại _LOCK (không "
          "reentrant) trong lúc sync_brain đang giữ -> treo production ngay lượt chat đầu "
          f"(đã chờ 15s, luồng {'CÒN SỐNG - TREO THẬT' if con_treo else 'đã xong'})",
          not con_treo)
    if con_treo:
        # KHÔNG rmtree khi còn treo: luồng daemon có thể vẫn đang cầm handle file bên trong
        # root (nhất là trên Windows). Để process thoát tự dọn - đây chính xác là lý do dùng
        # daemon=True thay vì cố join thêm hoặc cố dọn cho sạch.
        return

    def _slug_co_skill(base: Path) -> set:
        try:
            return {p.parent.name for p in base.glob("*/SKILL.md") if p.is_file()}
        except OSError:
            return set()

    _nguon = _slug_co_skill(root / "skills")
    _guong = _slug_co_skill(root / ".claude" / "skills")
    _da_chep = _nguon & _guong
    # TÊN NÓI ĐÚNG THỦ PHẠM: check này đỏ nghĩa là TIỀN ĐỀ của check deadlock ở trên sụp
    # (guard tự tháo ngòi), KHÔNG phải mirror_skills hỏng. Ai gặp đỏ ở đây sau một lần reorg
    # repo thì đi tìm ở nguồn skill hệ thống (.claude/skills + system/loops), ĐỪNG đào
    # mirror_skills. Lưu ý result["ok"] KHÔNG thay được check này: nó chỉ phản ánh lỗi từng
    # item trong vòng manifest (system_sync.py:494-496), còn exception trong mirror_skills bị
    # bắt và chỉ in ra stderr (:503-506) nên ok vẫn True.
    check("TIỀN ĐỀ cho check deadlock ở trên: sync_brain phải cài skill hệ thống THẬT rồi "
          "mirror_skills phải CHÉP sang .claude/skills - rỗng = cửa sổ deadlock chưa từng mở "
          "ra, 'không treo' vô nghĩa, guard đã tự tháo ngòi (repo reorg / sparse checkout / "
          f".claude/skills dời chỗ?), KHÔNG phải mirror hỏng (nguồn {sorted(_nguon)}, "
          f"mirror {sorted(_guong)})", bool(_da_chep))
    check("sync_brain (đường thật, không giả lập) chạy xong không lỗi và trả ok=True",
          "loi" not in ket_qua and isinstance(ket_qua.get("r"), dict) and ket_qua["r"].get("ok") is True)
    shutil.rmtree(root, ignore_errors=True)


_kiem_sync_brain_khong_deadlock()

# ---- Soát tĩnh AST bổ sung: không hàm nào trong 3 hàm đó NHẮC TÊN _LOCK ----
# Check này CHẾT VÌ LÝ DO KHÁC với check hành vi ở trên - giữ CẢ HAI, đừng rút gọn về một:
#   - Check hành vi (trên) CHỈ đỏ khi deadlock THẬT SỰ xảy ra lúc chạy - bằng chứng mạnh nhất
#     (đường thật) nhưng phải trả giá 15s chờ mỗi khi ai đó thật sự gây ra deadlock.
#   - Check AST (đây) đỏ NGAY LẬP TỨC (đọc token, không chạy), và bắt được cả kiểu sửa mà may
#     rủi khiến check hành vi KHÔNG kích hoạt được đường thi hành có lỗi (vd nhắc _LOCK trong
#     một nhánh if hiếm khi True lúc test chạy, hoặc gán _LOCK cho biến khác rồi .acquire()
#     tên biến đó - AST vẫn thấy tên `_LOCK` xuất hiện trong thân hàm dù chưa chắc luôn thực
#     thi). Ngược lại AST không chứng minh được HÀNH VI (vd nếu ai đó đổi _LOCK thành RLock,
#     AST vẫn thấy tên _LOCK xuất hiện y hệt dù lúc đó không còn deadlock nữa - lúc đó check
#     hành vi mới là trọng tài đúng). Hai check bù nhau, không cái nào thay được cái kia.
#
# GIỚI HẠN ĐÃ BIẾT CỦA CHECK AST - ĐỪNG QUÁ TIN NÓ RỒI BỎ CHECK HÀNH VI VÌ "CHẬM 15s":
# nó chỉ soát tên `_LOCK` xuất hiện TRỰC TIẾP trong thân ĐÚNG 3 hàm kể trên, nên nó MÙ với:
#   - gián tiếp qua hàm phụ: đẩy `with _LOCK:` vào một helper tên khác rồi gọi helper đó từ
#     _mirror_lock (reviewer đã thử: AST báo sạch `phạm: []` trong khi deadlock vẫn nổ THẬT
#     và chỉ check hành vi bắt được);
#   - tra cứu động: globals()["_LOCK"], getattr(system_sync, "_LOCK") - không có ast.Name nào
#     tên _LOCK để mà thấy.
# Đó KHÔNG phải lỗi cần vá ở đây (soát hết mọi đường gián tiếp = phải phân tích liên thủ tục,
# quá đắt và giòn cho một test) - chính xác là LÝ DO check hành vi ở trên phải tồn tại và
# phải chạy đường thật: nó bắt mọi kiểu trên mà không cần hiểu code viết thế nào.
def _kiem_ast_khong_lock_trong_mirror():
    src = Path(system_sync.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src, filename=system_sync.__file__)
    ten_can_soat = {"mirror_skills", "_mirror_lock", "_mirror_signature"}
    pham = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in ten_can_soat:
            for con in ast.walk(node):
                if isinstance(con, ast.Name) and con.id == "_LOCK":
                    pham.append(f"{node.name}:{con.lineno}")
    check(f"AST tĩnh: mirror_skills/_mirror_lock/_mirror_signature không nhắc tên _LOCK "
          f"(phạm: {pham})", not pham)


_kiem_ast_khong_lock_trong_mirror()

# ---- dọn ----
for _d in (_ROOT, _R2, _R3, _R4, _R5, _R6, _R7):
    shutil.rmtree(_d, ignore_errors=True)

if _fails:
    print(f"\nFAIL - test_system_sync: {len(_fails)} lỗi: {_fails}")
    sys.exit(1)
print("\nOK - test_system_sync: tất cả pass")
