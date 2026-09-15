"""Cache đọc manifest/state của plugins_host: nhanh mà KHÔNG được thiu, KHÔNG được bẩn.

    python tests/run.py plugins_cache     (KHÔNG mạng)

Bối cảnh 0.9.237: describe() nằm trên đường nóng system prompt (mỗi lượt chat, mỗi task
Kanban, mỗi lần nhắc hẹn nổ, mỗi tick loop) mà lần nào cũng đọc + parse plugin.yaml của
MỌI plugin, cộng đọc lại plugins.json cho TỪNG plugin bundled. Nay cache theo
(mtime_ns, size).

Hai rủi ro thật của kiểu cache này, test khoá cả hai:
- THIU: sửa file mà cache không hết hạn -> user bật plugin mà Javis vẫn thấy tắt.
- BẨN: _read_state và _read_manifest đều bị nơi gọi SỬA TẠI CHỖ rồi ghi ngược ra file
  (plugins_host toggle), nên trả thẳng object trong cache là hỏng dữ liệu ngầm.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import json
import os
import sys
import tempfile
import time
from pathlib import Path

_STATE = tempfile.mkdtemp(prefix="javis-plgcache-")
os.environ.setdefault("JAVIS_STATE_DIR", _STATE)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import plugins_host  # noqa: E402

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


VAULT = Path(tempfile.mkdtemp(prefix="javis-plgcache-vault-"))
PDIR = VAULT / "plugins" / "thu-nghiem"
PDIR.mkdir(parents=True, exist_ok=True)
MANIFEST = PDIR / "plugin.yaml"


def ghi_manifest(enabled: bool, mo_ta: str):
    MANIFEST.write_text(
        f"name: Thử nghiệm\ndescription: {mo_ta}\nversion: 1.0\nenabled: {str(enabled).lower()}\n"
        f"min_mode: readonly\ntools: [thu_nghiem_tool]\n",
        encoding="utf-8")


ghi_manifest(False, "bản đầu")
(PDIR / "plugin.py").write_text("def register(ctx):\n    pass\n", encoding="utf-8")

# ---- 1. Cache có hiệu lực: lần 2 không đọc lại file ----
doc_that = Path.read_text
dem = {"n": 0}


def doc_dem(self, *a, **k):
    if self.name in ("plugin.yaml", "plugin.yml", "plugins.json"):
        dem["n"] += 1
    return doc_that(self, *a, **k)


plugins_host.invalidate()
Path.read_text = doc_dem
try:
    dem["n"] = 0
    plugins_host.describe(str(VAULT))
    lan1 = dem["n"]
    dem["n"] = 0
    plugins_host.describe(str(VAULT))
    lan2 = dem["n"]
finally:
    Path.read_text = doc_that

check(f"lần gọi đầu có đọc file thật ({lan1} lần đọc)", lan1 > 0)
check(f"lần gọi thứ hai KHÔNG đọc lại file nào ({lan2} lần đọc)", lan2 == 0)

# ---- 2. Không thiu: sửa manifest thì describe phải thấy ngay ----
def tim(vault, slug="thu-nghiem"):
    for p in plugins_host.describe(str(vault)):
        if p["slug"] == slug:
            return p
    return None


check("trước khi sửa: plugin đang TẮT, mô tả 'bản đầu'",
      (tim(VAULT) or {}).get("enabled") is False and (tim(VAULT) or {}).get("description") == "bản đầu")

time.sleep(0.01)
ghi_manifest(True, "bản sửa")
p = tim(VAULT)
check("sửa manifest xong describe thấy NGAY trạng thái mới (không thiu)",
      p is not None and p["enabled"] is True and p["description"] == "bản sửa")

# ---- 3. Không bẩn: sửa dict trả về không được làm hỏng cache ----
m1, _ = plugins_host._read_manifest(PDIR)
m1["enabled"] = "GIA TRI RAC"
m1["tools"].append("tool_chen_bay")
m2, _ = plugins_host._read_manifest(PDIR)
check("sửa manifest trả về không làm bẩn cache (enabled)", m2["enabled"] is True)
check("sửa list lồng bên trong cũng không làm bẩn cache (tools)",
      m2["tools"] == ["thu_nghiem_tool"])

_STATE_PATH = Path(_STATE) / "plugins.json"
_STATE_PATH.write_text(json.dumps({"disabled": ["mot-plugin"]}), encoding="utf-8")
s1 = plugins_host._read_state()
s1["disabled"].append("chen-bay")
s1["khoa_la"] = 1
s2 = plugins_host._read_state()
check("sửa state trả về không làm bẩn cache",
      s2 == {"disabled": ["mot-plugin"]})

# ---- 4. invalidate() dọn sạch cache đọc file ----
plugins_host.describe(str(VAULT))          # nạp cache
plugins_host.invalidate()
check("invalidate() xoá cache manifest", not plugins_host._MANIFEST_CACHE)
check("invalidate() xoá cache state", plugins_host._STATE_CACHE["sig"] is None)

# ---- 5. Bật/tắt rồi bật lại trong CÙNG một giây vẫn đúng (mtime thô 1 giây) ----
# Đây là lý do invalidate() phải dọn cache chứ không chỉ trông vào mtime.
for muon in (False, True, False):
    plugins_host.set_enabled("thu-nghiem", muon, str(VAULT))
    got = (tim(VAULT) or {}).get("enabled")
    check(f"toggle -> {muon} phản ánh ngay (đọc lại thấy {got})", got is muon)

# ---- 6. Manifest hỏng vẫn báo lỗi qua cache, không nuốt ----
time.sleep(0.01)
MANIFEST.write_text("name: [chua dong ngoac\n  : : :\n", encoding="utf-8")
p = tim(VAULT)
check("manifest hỏng: describe vẫn trả plugin kèm error", p is not None and bool(p.get("error")))
p2 = tim(VAULT)
check("manifest hỏng: lần đọc thứ hai (từ cache) vẫn giữ nguyên error",
      p2 is not None and p2.get("error") == p.get("error"))

print()
if _fails:
    print(f"FAIL {len(_fails)} test: " + ", ".join(_fails))
    sys.exit(1)
print("TẤT CẢ PASS")
