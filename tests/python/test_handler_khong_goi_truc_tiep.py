"""Không code nội bộ nào được gọi thẳng một route handler như hàm Python thường.

    python tests/run.py handler_khong_goi_truc_tiep     (KHÔNG mạng)

Bối cảnh 0.9.243: khối Telegram gọi thẳng 5 handler (`await list_agents(brain)`,
`await provider_models(provider=pid)`, `await list_brains()`, `await list_skills(brain)`,
`await list_workflows(brain)` - 6 chỗ). Chạy được nên không ai thấy, nhưng đó là bom hẹn giờ:
tham số mặc định của handler là ĐỐI TƯỢNG `fastapi.params.Query`, không phải chuỗi. Ngày nào
có người gọi thiếu đối số thì `brain` thành một Query object, `_brain_root` nhận vào rồi
`os.path.isdir(Query)` ném TypeError - và nó nổ ở Telegram chứ không ở chỗ vừa sửa.

Cách chữa đã áp dụng: handler chỉ còn là lớp vỏ HTTP mỏng bọc quanh một hàm THUẦN
(`agents_index`, `workflows_index`, `skills_index`, `provider_models_index`,
`_list_brains_sync`), và nội bộ gọi hàm thuần đó.

Test này quét bằng AST nên bắt được cả các khối khác, không chỉ Telegram.
"""
import ast
import sys

from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


HTTP = {"get", "post", "put", "delete", "patch", "websocket"}


def cay(path):
    return ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))


def handlers_cua(tree):
    """{tên handler -> dòng khai báo} trong một file."""
    out = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            f = dec.func if isinstance(dec, ast.Call) else dec
            # bắt cả @app.get(...) lẫn @router.get(...)
            if isinstance(f, ast.Attribute) and f.attr in HTTP:
                out[node.name] = node.lineno
    return out


# Quét TOÀN BỘ server/, không riêng main.py + routes/: bản trước chỉ soi hai chỗ đó nên
# `bench_hotpath.py` gọi `main.list_brains()` lọt lưới suốt.
FILES = sorted(SERVER.rglob("*.py"))
TREES = {}
for f in FILES:
    try:
        TREES[f] = cay(f)
    except SyntaxError:
        pass

# handler theo TỪNG MODULE (không gộp một rổ): cần biết `main.` hay `skill_router.` mới
# phân biệt được `main.list_brains()` (vi phạm) với `skill_router.list_skills()` (hàm khác
# trùng tên, hoàn toàn hợp lệ). Gộp một rổ là báo động giả hàng loạt.
H_THEO_MODULE = {f.stem: handlers_cua(t) for f, t in TREES.items()}
tong_h = sum(len(v) for v in H_THEO_MODULE.values())

vi_pham = []
for f, tree in TREES.items():
    cua_minh = H_THEO_MODULE.get(f.stem, {})
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if isinstance(fn, ast.Name):                      # gọi trần: list_brains()
            if fn.id in cua_minh:
                vi_pham.append(f"{f.name}:{node.lineno} gọi {fn.id}() "
                               f"(khai báo dòng {cua_minh[fn.id]})")
        elif isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name):
            # qua module khác: main.list_brains(). Chỉ tính khi module ĐÓ thật sự khai báo
            # handler tên đó -> không dính hàm thường trùng tên ở module không có route nào.
            khac = H_THEO_MODULE.get(fn.value.id)
            if khac and fn.attr in khac:
                vi_pham.append(f"{f.name}:{node.lineno} gọi {fn.value.id}.{fn.attr}() "
                               f"(handler khai báo ở {fn.value.id}.py dòng {khac[fn.attr]})")

check(f"quét được {tong_h} route handler trong {len(TREES)} file", tong_h > 100)
check("không chỗ nào gọi route handler như hàm thường"
      + ("\n       " + "\n       ".join(vi_pham) if vi_pham else ""), not vi_pham)

# ---- Các hàm lõi phải tồn tại và gọi được KHÔNG cần đối số kiểu FastAPI ----
import main  # noqa: E402

for ten in ("agents_index", "workflows_index", "skills_index", "_list_brains_sync"):
    check(f"main.{ten} tồn tại (lõi thuần cho nội bộ dùng)", callable(getattr(main, ten, None)))
check("main.provider_models_index tồn tại", callable(getattr(main, "provider_models_index", None)))

# Gọi thật với chuỗi thường - đây chính là thứ trước đây sẽ nổ nếu ai đó gọi handler thiếu đối số.
for ten in ("agents_index", "workflows_index", "skills_index"):
    try:
        getattr(main, ten)("brain")
        ok = True
    except Exception as e:
        ok = False
        print(f"       {ten} lỗi: {type(e).__name__}: {e}")
    check(f"{ten}('brain') chạy được với chuỗi thường", ok)

print()
if _fails:
    print(f"FAIL {len(_fails)} test: " + ", ".join(_fails))
    sys.exit(1)
print("TẤT CẢ PASS")
