"""Test tích hợp: xóa não lan sang máy khác qua sync (remote file:// cục bộ). Chạy:
    python tests/run.py brain_delete_sync
Cần git trong PATH. KHÔNG mạng thật."""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import os, sys, time, tempfile, subprocess
from pathlib import Path
import git_brain as gb  # noqa: E402

_fails = []
def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond: _fails.append(name)

if not gb.has_git():
    print("SKIP: máy không có git"); sys.exit(0)

ROOT = Path(tempfile.mkdtemp(prefix="jv-delsync-")).resolve()
REMOTE = ROOT / "remote.git"
subprocess.run(["git", "init", "--bare", str(REMOTE)], capture_output=True)
URL = "file:///" + str(REMOTE).replace("\\", "/").lstrip("/")
TOKEN = "x"  # file:// không dùng token nhưng sync_brains yêu cầu non-empty

def machine(tag):
    b = ROOT / tag / "brains"; m = ROOT / tag / "mirror"; t = ROOT / tag / "trash"
    b.mkdir(parents=True, exist_ok=True)
    return str(b), str(m), str(t)

def seed(brains, name, text="hi"):
    d = Path(brains) / name; d.mkdir(parents=True, exist_ok=True)
    (d / "note.md").write_text(text, encoding="utf-8")

def sync(brains, mirror, trash):
    return gb.sync_brains(brains, mirror, URL, TOKEN, "main",
                          trash_dir=trash, protected_names={"Brain Default"})

# --- Dựng: A tạo Foo, đẩy lên; B kéo về -> cả hai + remote đều có Foo ---
Ab, Am, At = machine("A"); Bb, Bm, Bt = machine("B")
seed(Ab, "Foo"); sync(Ab, Am, At)
sync(Bb, Bm, Bt)
check("B nhận được Foo từ remote", (Path(Bb) / "Foo" / "note.md").exists())

# --- A xóa Foo (move trash + tombstone) rồi sync ---
gb.move_to_trash(str(Path(Ab) / "Foo"), At, "Foo")
gb.write_tombstone(Ab, "Foo")
r = sync(Ab, Am, At)
check("A: sync sau xóa ok", r.get("ok"))
check("A: Foo không còn trong brains", not (Path(Ab) / "Foo").exists())

# --- B sync -> Foo bị xóa ở B + vào thùng rác B, remote sạch ---
r2 = sync(Bb, Bm, Bt)
check("B: sync ok", r2.get("ok"))
check("B: Foo bị xóa khỏi brains", not (Path(Bb) / "Foo").exists())
trashed = list(Path(Bt).glob("Foo__*")) if Path(Bt).is_dir() else []
check("B: Foo nằm trong thùng rác B", len(trashed) == 1 and (trashed[0] / "note.md").exists())

# --- Chốt thời gian: tạo LẠI Foo mới ở A (mtime mới) rồi sync -> KHÔNG bị xóa, tombstone gỡ ---
seed(Ab, "Foo", "moi")
# mtime phải RÕ RÀNG > deleted_at + 1 (dung sai chống lệch đồng hồ trong _dir_newer_than). Đặt
# hẳn về tương lai, KHÔNG dùng "bây giờ": cả test chạy dưới 1 giây trên CI nhanh nên mtime=now
# chỉ nhỉnh hơn deleted_at chút, không vượt +1s -> Foo bị coi là vẫn xóa (đua giây, fail CI).
_future = time.time() + 10
os.utime(Path(Ab) / "Foo" / "note.md", (_future, _future))
r3 = sync(Ab, Am, At)
check("A: Foo dựng lại KHÔNG bị xóa (chốt thời gian)", (Path(Ab) / "Foo" / "note.md").exists())
check("A: tombstone Foo đã gỡ", not (Path(Ab) / gb.TOMBSTONE_DIR / "Foo.json").exists())

# --- Bảo vệ khi KHÔNG tombstone: xóa tay Bar khỏi brains B -> sync khôi phục, không mất ---
Cb, Cm, Ct = machine("C")
seed(Cb, "Bar"); sync(Cb, Cm, Ct)   # đẩy Bar lên remote
Db, Dm, Dt = machine("D"); sync(Db, Dm, Dt)  # D kéo Bar về
import shutil as _sh; _sh.rmtree(str(Path(Db) / "Bar"))  # xóa TAY, KHÔNG tombstone
sync(Db, Dm, Dt)
check("Bảo vệ: Bar biến mất không tombstone -> được khôi phục", (Path(Db) / "Bar").exists())

# --- Não mặc định miễn nhiễm: tombstone giả trỏ 'Brain Default' -> không bị xóa ---
Eb, Em, Et = machine("E")
seed(Eb, "Brain Default"); gb.write_tombstone(Eb, "Brain Default")
sync(Eb, Em, Et)
check("Não mặc định miễn nhiễm tombstone", (Path(Eb) / "Brain Default").exists())

# --- Bảo vệ ĐA NÃO khi KHÔNG tombstone (case THẬT của _restore_missing_brains): máy có
# NHIỀU não, xóa tay chỉ MỘT não -> não đó được khôi phục, não còn lại không đụng, remote
# không mất não đã xóa tay. Khác case "Bảo vệ" phía trên (chỉ 1 não Bar -> sau khi rmtree
# brains RỖNG hẳn -> _brains_has_content=False -> đi nhánh "restored", KHÔNG chạy nhánh
# snapshot/prune nên KHÔNG thật sự gọi tới _restore_missing_brains; test đó sẽ PASS VÔ CỚ
# dù có xóa hẳn hàm _restore_missing_brains đi). Ở đây "Keep" giữ brains không trống nên
# _brains_has_content=True, nhánh snapshot/prune chạy thật, mới đi qua đúng hàm cần bảo vệ.
Fb, Fm, Ft = machine("F"); Gb, Gm, Gt = machine("G")
seed(Fb, "Keep"); seed(Fb, "Gone")
sync(Fb, Fm, Ft)
sync(Gb, Gm, Gt)
check("Đa não: G nhận cả Keep lẫn Gone từ remote",
      (Path(Gb) / "Keep" / "note.md").exists() and (Path(Gb) / "Gone" / "note.md").exists())
_sh.rmtree(str(Path(Gb) / "Gone"))   # xóa TAY chỉ Gone, KHÔNG tombstone; Keep giữ nguyên
sync(Gb, Gm, Gt)
check("Đa não: Gone xóa tay được khôi phục trên G", (Path(Gb) / "Gone" / "note.md").exists())
check("Đa não: Keep không bị đụng tới", (Path(Gb) / "Keep" / "note.md").exists())
Hb, Hm, Ht = machine("H"); sync(Hb, Hm, Ht)   # máy thứ ba sync từ remote để soi remote còn Gone
check("Đa não: remote không mất Gone", (Path(Hb) / "Gone").exists())

# --- Rollback khi áp giấy báo tử LỖI: move_to_trash ném lỗi giữa chừng -> sync KHÔNG được
# push nửa vời (bất biến "áp giấy báo tử lỗi -> rollback mirror -> hoãn push" ở
# _apply_tombstones/_sync_brains_locked).
Ib, Im, It = machine("I"); Jb, Jm, Jt = machine("J")
seed(Ib, "Doomed"); sync(Ib, Im, It)
sync(Jb, Jm, Jt)
check("Rollback: J nhận Doomed từ remote", (Path(Jb) / "Doomed" / "note.md").exists())
gb.move_to_trash(str(Path(Ib) / "Doomed"), It, "Doomed")
gb.write_tombstone(Ib, "Doomed")
sync(Ib, Im, It)   # I đẩy tombstone + việc xóa Doomed lên remote

_orig_move_to_trash = gb.move_to_trash
def _boom_move_to_trash(*a, **k):
    raise RuntimeError("boom")
gb.move_to_trash = _boom_move_to_trash
try:
    r_fail = sync(Jb, Jm, Jt)
finally:
    gb.move_to_trash = _orig_move_to_trash

check("Rollback: sync báo KHÔNG ok khi áp giấy báo tử lỗi", r_fail.get("ok") is not True)
check("Rollback: sync báo lỗi cụ thể", bool(r_fail.get("error")))
check("Rollback: Doomed vẫn còn nguyên trên J (không nửa vời)",
      (Path(Jb) / "Doomed" / "note.md").exists())

print(); print("TẤT CẢ PASS" if not _fails else f"{len(_fails)} FAIL: {_fails}")
sys.exit(1 if _fails else 0)
