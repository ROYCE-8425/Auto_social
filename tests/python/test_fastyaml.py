"""fastyaml (bộ nạp C) phải cho KẾT QUẢ Y HỆT yaml.safe_load (bộ nạp Python).

    python tests/run.py fastyaml     (KHÔNG mạng)

Đây là lưới an toàn của việc đổi bộ nạp YAML ở 0.9.237. Đổi bộ nạp là đụng vào đường
đọc frontmatter của MỌI skill/agent/workflow/plugin/note, nên nhanh mà sai thì hỏng
diện rộng và im lặng. Test đối chiếu trên chính corpus thật của repo chứ không phải
ví dụ tự bịa, cộng vài góc hiểm mà hai bộ nạp hay lệch nhau.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import os
import sys
from pathlib import Path


try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import yaml            # noqa: E402  - bộ nạp Python làm CHUẨN đối chiếu
import fastyaml        # noqa: E402

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


def pure(stream):
    """yaml.safe_load ép dùng bộ nạp Python, không phụ thuộc mặc định của PyYAML."""
    return yaml.load(stream, Loader=yaml.SafeLoader)


# ---- 1. libyaml phải thật sự có mặt, không thì đổi bộ nạp chẳng được gì ----
# Cố tình để FAIL chứ không cảnh báo suông: nếu môi trường deploy thiếu libyaml thì
# toàn bộ lý do của thay đổi này biến mất, và ta cần biết ngay chứ không phải đoán.
check("libyaml có mặt (fastyaml.HAS_C) - nếu FAIL thì mất sạch phần tăng tốc",
      fastyaml.HAS_C is True)

# ---- 2. Đối chiếu trên CORPUS THẬT của repo ----
CORPUS = []
for pat, base in ((("**/SKILL.md",), ROOT / "system"),
                  (("**/plugin.yaml",), ROOT / "system"),
                  (("**/SKILL.md", "**/plugin.yaml"), ROOT / "brains"),
                  (("**/*.md",), ROOT / "brains")):
    if not base.is_dir():
        continue
    for g in pat:
        CORPUS.extend(base.glob(g))
CORPUS = sorted(set(CORPUS))[:400]        # đủ đại diện, không để test chạy hàng phút


def frontmatter_of(p: Path):
    """Trả phần YAML thô giữa hai dấu ---, hoặc cả file nếu là .yaml."""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if p.suffix in (".yaml", ".yml"):
        return text
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    return parts[1] if len(parts) >= 3 else None


n_cmp, lech, py_loi_c_khong = 0, [], []
for p in CORPUS:
    raw = frontmatter_of(p)
    if raw is None or not raw.strip():
        continue
    try:
        want = pure(raw)
    except yaml.YAMLError:
        # Bộ nạp Python đã chê thì fastyaml chê hay không đều chấp nhận được,
        # miễn là KHÔNG nổ ra loại lỗi khác. Chỉ ghi nhận, không tính là lệch.
        try:
            fastyaml.safe_load(raw)
        except yaml.YAMLError:
            pass
        except Exception as e:
            py_loi_c_khong.append(f"{p.name}: {type(e).__name__}")
        continue
    got = fastyaml.safe_load(raw)
    n_cmp += 1
    if got != want:
        lech.append(p.name)

check(f"đối chiếu {n_cmp} frontmatter thật trong repo: khớp tuyệt đối"
      + (f" (LỆCH: {lech[:5]})" if lech else ""), not lech)
check("file YAML hỏng không đổi loại ngoại lệ"
      + (f" ({py_loi_c_khong[:3]})" if py_loi_c_khong else ""), not py_loi_c_khong)

# ---- 3. Góc hiểm: nơi hai bộ nạp hay lệch ----
GOC_HIEM = {
    "tiếng Việt có dấu": "name: Viết email cho khách\ndescription: Soạn thư ngỏ\n",
    "chuỗi nhiều dòng dấu |": "desc: |\n  dòng một\n  dòng hai\n",
    "chuỗi gấp dấu >": "desc: >\n  câu dài\n  bị gấp\n",
    "nháy đơn trong nháy kép": 'desc: "nó bảo \'ok\' rồi đi"\n',
    "dấu hai chấm trong giá trị": "url: https://javis.example.com/a:b\n",
    "danh sách lồng": "tools:\n  - a\n  - b\nmeta:\n  k: v\n",
    "giá trị rỗng": "description:\nname: x\n",
    "số và bool": "n: 007\nb: yes\nf: 1.50\nnull_val: ~\n",
    "khoá trùng": "a: 1\na: 2\n",
    "ký tự đặc biệt trong tên": "name: 'Báo cáo: doanh thu | tháng 7'\n",
    "emoji": "icon: 📊\nname: thống kê\n",
    "tab lẫn space trong body": "a: 1\nb:\n  c: 2\n",
    "chuỗi rất dài": "d: " + ("x" * 5000) + "\n",
    "frontmatter rỗng": "\n",
}
sai = []
for ten, src in GOC_HIEM.items():
    try:
        want = pure(src)
    except yaml.YAMLError:
        want = "<<YAMLError>>"
    try:
        got = fastyaml.safe_load(src)
    except yaml.YAMLError:
        got = "<<YAMLError>>"
    if got != want:
        sai.append(f"{ten}: {got!r} != {want!r}")
check("14 góc hiểm cho kết quả giống nhau" + (f" (SAI: {sai})" if sai else ""), not sai)

# ---- 4. Nhánh rơi về bộ nạp Python có chạy thật không ----
# Giả lập bộ nạp C từ chối một chuỗi mà bộ nạp Python đọc được: fastyaml phải trả về
# kết quả của bộ nạp Python chứ không ném lỗi ra ngoài.
class _LoaderLuonHong(yaml.SafeLoader):
    def __init__(self, *a, **k):
        raise yaml.YAMLError("giả lập bộ nạp C chê")


_that = fastyaml._CLoader
try:
    fastyaml._CLoader = _LoaderLuonHong
    ket_qua = fastyaml.safe_load("name: cuu duoc\nn: 3\n")
    check("bộ nạp C chê thì rơi về bộ nạp Python, không ném ra ngoài",
          ket_qua == {"name": "cuu duoc", "n": 3})
finally:
    fastyaml._CLoader = _that

check("khôi phục lại bộ nạp C sau khi giả lập", fastyaml._CLoader is _that)

# ---- 5. Không còn ai gọi yaml.safe_load trần trong mã nguồn (ngoài test) ----
import re  # noqa: E402
con_sot = []
for f in sorted(SERVER.glob("*.py")):
    if f.name.startswith("test_") or f.name == "fastyaml.py":
        continue
    if re.search(r"(^|[^a-z])yaml\.safe_load", f.read_text(encoding="utf-8", errors="replace")):
        con_sot.append(f.name)
check("không module nguồn nào còn gọi yaml.safe_load trần"
      + (f" (còn: {con_sot})" if con_sot else ""), not con_sot)

print()
if _fails:
    print(f"FAIL {len(_fails)} test: " + ", ".join(_fails))
    sys.exit(1)
print("TẤT CẢ PASS")
