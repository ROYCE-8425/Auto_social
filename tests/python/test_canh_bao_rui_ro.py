"""Cảnh báo rủi ro của connector phải HIỆN LÚC NGƯỜI DÙNG QUYẾT ĐỊNH, không nằm im trong file.

    python tests/run.py canh_bao_rui_ro

Không cần pytest, không chạm mạng.

Bối cảnh: trường `risk` trong mcp-catalog.json trước đây CHỈ được vẽ ở luồng QR (openQrFlow) và ở
hộp thoại đổi quyền. 15/16 connector có cảnh báo thì không bao giờ hiện cảnh báo lúc bấm Kết nối,
gồm cả google-keep (token toàn quyền tài khoản Google) và zalo. Test này giữ cho lỗi đó không
quay lại.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import json
import os
import re
import sys
from pathlib import Path


_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


js = (ROOT / "dashboard" / "console.js").read_text(encoding="utf-8")


def than_ham(ten):
    """Cắt thân một hàm JS theo dấu ngoặc nhọn cân bằng."""
    i = js.index(f"function {ten}(")
    k = js.index("{", i)
    depth = 0
    for m in range(k, len(js)):
        if js[m] == "{":
            depth += 1
        elif js[m] == "}":
            depth -= 1
            if depth == 0:
                return js[k:m + 1]
    raise AssertionError(f"không cắt được thân hàm {ten}")


# ---- cả 3 luồng đấu nối đều phải vẽ cảnh báo ----
for ten in ("openApikeyFlow", "openOauthFlow", "openQrFlow"):
    than = than_ham(ten)
    check(f"{ten} có vẽ khối cảnh báo rủi ro (conn-risk)", "conn-risk" in than)
    check(f"{ten} chỉ vẽ khi connector THẬT SỰ có cảnh báo (không hiện hộp rỗng)",
          re.search(r"con\.risk\s*\?", than) is not None)

# ---- catalog: mọi connector rủi ro cao phải có cảnh báo ----
cat = json.loads((ROOT / "system" / "mcp-catalog.json").read_text(encoding="utf-8"))
by_id = {c["id"]: c for c in cat["connectors"]}

for cid in ("google-keep", "zalo"):
    check(f"{cid} có khai risk", bool((by_id.get(cid) or {}).get("risk")))

# ---- google-keep: mô tả trên THẺ phải nói rõ bán kính thiệt hại ----
# Người dùng thấy mô tả này TỪ NGOÀI danh sách, trước khi bấm vào. Tên connector là "Google Keep"
# nên mô tả đúng NĂNG LỰC, nhưng token lại có toàn quyền tài khoản - phải nói ra.
keep = by_id.get("google-keep") or {}
mota = keep.get("description", "")
check("mô tả thẻ google-keep cảnh báo token toàn quyền tài khoản",
      "toàn quyền" in mota.lower() and "google" in mota.lower())
check("mô tả thẻ nói rõ KHÔNG phải OAuth giới hạn phạm vi",
      "oauth" in mota.lower() or "phạm vi" in mota.lower())

# Javis chỉ LÀM được đúng Keep - đây là điểm trấn an, phải giữ đúng.
tm = keep.get("tool_meta") or {}
tat_ca = (tm.get("read") or []) + (tm.get("write") or []) + (tm.get("danger") or [])
check("google-keep vẫn chỉ khai tool Keep, không lan sang Gmail/Drive",
      tat_ca and not any(t.startswith(("gmail", "drive", "mail_", "file_")) for t in tat_ca))

# ---- LUẬT 1: có tool NGUY HIỂM thì BẮT BUỘC có cảnh báo ----
# Trước 0.9.116, pancake-pos (tạo đơn/giao dịch/công nợ/hoá đơn), botcake (gửi tin cho khách) và
# webcake-landing (đăng trang công khai) đều có tool nguy hiểm mà không một chữ cảnh báo nào.
thieu_canh_bao = [c["id"] for c in cat["connectors"]
                  if (c.get("tool_meta") or {}).get("danger") and not c.get("risk")]
check("mọi connector có tool nguy hiểm đều có cảnh báo: "
      + (", ".join(thieu_canh_bao) or "đạt"), not thieu_canh_bao)

# ---- LUẬT 2: chia sẻ dữ liệu ra người ngoài LUÔN là mức nguy hiểm ----
# Đẩy dữ liệu ra người khác khác về CHẤT với sửa nội dung trong nhà, nên phải cùng một chuẩn ở
# mọi connector. Keep xếp add_note_collaborator là nguy hiểm; google-sheets từng xếp *share* chỉ
# là ghi, mà nó mặc định ở mức Ghi nháp -> chia sẻ được bảng tính ngay từ mặc định.
DAU_HIEU_CHIA_SE = ("share", "collaborator", "permissionmember", "invite")
sai_chuan = []
for c in cat["connectors"]:
    tm = c.get("tool_meta") or {}
    for t in (tm.get("write") or []):
        if any(k in t.lower() for k in DAU_HIEU_CHIA_SE):
            sai_chuan.append(f'{c["id"]}:{t}')
check("tool chia sẻ dữ liệu không được xếp mức 'ghi': " + (", ".join(sai_chuan) or "đạt"),
      not sai_chuan)

# ---- LUẬT 3: cảnh báo phải TRÌNH BÀY được, giống hướng dẫn ----
# .conn-risk cũng dùng white-space: pre-line nên xuống dòng trong JSON hiện đúng.
DAI_CAN_NGAT = 200
khong_ngat, dong_dai = [], []
for c in cat["connectors"]:
    r = c.get("risk") or ""
    if not r:
        continue
    if len(r) > DAI_CAN_NGAT and "\n" not in r:
        khong_ngat.append(f'{c["id"]}({len(r)})')
    if any(len(l) > DAI_CAN_NGAT for l in r.split("\n")):
        dong_dai.append(c["id"])
check("cảnh báo dài đều có xuống dòng: " + (", ".join(khong_ngat) or "đạt"), not khong_ngat)
check("không dòng cảnh báo nào quá dài: " + (", ".join(dong_dai) or "đạt"), not dong_dai)

# ---- LUẬT 4: cảnh báo không được nói NHẸ hơn thực tế ----
# google-workspace từng viết mức Ghi nháp "chỉ soạn nháp, tạo lịch, tạo tài liệu" trong khi danh
# sách ghi có cả *modify* và *move* (sửa tài liệu có sẵn, di chuyển file Drive).
ws = by_id.get("google-workspace") or {}
_r = ws.get("risk", "")
_w = " ".join((ws.get("tool_meta") or {}).get("write") or [])
if "modify" in _w or "move" in _w:
    check("cảnh báo google-workspace không dùng chữ 'chỉ' để hạ thấp mức Ghi nháp",
          "chỉ soạn nháp" not in _r)
    check("cảnh báo google-workspace có nhắc sửa/di chuyển file có sẵn",
          any(k in _r.lower() for k in ("sửa tài liệu", "di chuyển", "file có sẵn", "sửa file")))

# ---- LUẬT 5: connector mặc định Toàn quyền phải cảnh báo thật đanh ----
for c in cat["connectors"]:
    if c.get("default_perm") != "full":
        continue
    r = c.get("risk") or ""
    check(f'{c["id"]} mặc định Toàn quyền -> cảnh báo phải nói rõ điều đó',
          "toàn quyền" in r.lower() and ("mặc định" in r.lower() or "đang bật" in r.lower()))
    check(f'{c["id"]} mặc định Toàn quyền -> phải chỉ cách hạ quyền xuống',
          any(k in r.lower() for k in ("hạ", "chỉ đọc", "ghi nháp")))

# ---- CANARY: chứng minh phép cắt thân hàm có quyền lực thật ----
_than_qr = than_ham("openQrFlow")
check("CANARY: thân openQrFlow cắt ra phải NGẮN hơn cả file rất nhiều "
      "-> tức đang soi đúng một hàm chứ không phải quét cả console.js",
      0 < len(_than_qr) < len(js) / 4)

if _fails:
    print(f"\nFAIL - test_canh_bao_rui_ro: {len(_fails)} lỗi: {_fails}")
    sys.exit(1)
print("\nOK - test_canh_bao_rui_ro: tất cả pass")
