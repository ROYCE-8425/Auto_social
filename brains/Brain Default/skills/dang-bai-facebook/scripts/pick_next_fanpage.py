# -*- coding: utf-8 -*-
"""Chọn ĐÚNG 1 Fanpage + 1 thẻ khoá học cho vòng đăng hôm nay.

Luật:
- 1 ngày / 1 page / tối đa 1 bài OK.
- Fail: ghi skip, thử lại 1 lần sau >= 2 giờ; lần 2 fail thì bỏ page đó tới ngày mai.
- Không chọn page đã OK hôm nay.
- Thẻ lấy ngẫu nhiên trong Thẻ khoá học của kit (all = mọi id trong `_the-khoa-hoc.md`).

In ra khối NEXT=... để loop đọc. Không gọi Facebook.
"""
from __future__ import annotations

import json
import random
import re
import sys
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TZ = ZoneInfo("Asia/Ho_Chi_Minh")
VAULT = Path(__file__).resolve().parents[3]
if VAULT.name != "Brain Default" and not (VAULT / "wiki" / "brand-kits").is_dir():
    VAULT = Path(__file__).resolve().parents[4]
KITS = VAULT / "wiki" / "brand-kits"
STATE = VAULT / "Javis" / "dang-hang-ngay.json"
SKIP_FILES = {"royce-shop.md", "royce.md"}

CONTENT_ANGLES = ["meo_thuc_chien", "tinh_huong", "tai_lieu", "tuyen_sinh"]
ANGLE_LABELS = {
    "meo_thuc_chien": "Mẹo & Thủ thuật / Phím tắt thực chiến",
    "tinh_huong": "Tình huống thực tế & Giải pháp nghề nghiệp",
    "tai_lieu": "Tặng tài liệu & Thư viện file mẫu",
    "tuyen_sinh": "Tuyển sinh & Khai giảng khóa kèm 1-1",
}


def pick_next_angle(last_angle: str = "") -> str:
    """Xoay tua tuần tự 4 góc nội dung: meo_thuc_chien -> tinh_huong -> tai_lieu -> tuyen_sinh -> ..."""
    if last_angle in CONTENT_ANGLES:
        idx = CONTENT_ANGLES.index(last_angle)
        return CONTENT_ANGLES[(idx + 1) % len(CONTENT_ANGLES)]
    return "meo_thuc_chien"


def registry_tags():
    """Mọi id trong wiki/brand-kits/_the-khoa-hoc.md — thêm ngành = thêm dòng bảng + folder."""
    p = KITS / "_the-khoa-hoc.md"
    ids = []
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|", line)
            if not m:
                continue
            tid = m.group(1).strip()
            if not tid or tid.lower() in ("id", "---") or set(tid) <= {"-"}:
                continue
            ids.append(tid)
    return ids or ["tin-hoc _ai", "do-hoa", "ke-toan", "ve-ky-thuat"]


def field(md, *labels):
    for lab in labels:
        m = re.search(r"^[ \t]*[-*][ \t]*" +
                      re.escape(lab) + r":[ \t]*(.*)$", md, re.M)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def parse_tags(raw):
    raw = (raw or "").strip()
    if not raw or re.match(r"^(all|\*|full)$", raw, re.I):
        return list(registry_tags())
    parts = [p.strip() for p in re.split(r"[,;|/]+", raw) if p.strip()]
    out = []
    for p in parts:
        if re.match(r"^ve[\s_-]*ky[\s_-]*thuat$", p, re.I) or p == "VE KY THUAT":
            p = "ve-ky-thuat"
        if p not in out:
            out.append(p)
    return out or list(registry_tags())


def get_connected_page_tokens() -> dict[str, str]:
    """Lấy danh sách các Page ID đang có Access Token (từ Javis/page_tokens.json hoặc wiki/brand-kits/*.md)."""
    tokens = {}
    tok_file = VAULT / "Javis" / "page_tokens.json"
    if tok_file.is_file():
        try:
            data = json.loads(tok_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for pid, info in data.items():
                    if isinstance(info, dict) and info.get("access_token"):
                        tokens[str(pid)] = str(info["access_token"]).strip()
        except Exception:
            pass

    if KITS.is_dir():
        for p in KITS.glob("*.md"):
            if p.name.startswith("_"):
                continue
            try:
                md = p.read_text(encoding="utf-8")
                pid = field(md, "Page ID", "page_id")
                tok = field(md, "Access Token", "access_token",
                            "Page Token", "Token")
                if pid and tok and str(pid) not in tokens:
                    tokens[str(pid)] = str(tok).strip()
            except Exception:
                pass
    return tokens


def verify_token_live(page_id: str, token: str) -> tuple[bool, str]:
    """Kiểm tra nhanh qua Facebook Graph API xem token còn sống hay đã hết hạn (timeout 4s)."""
    if not token:
        return False, "chua-co-token"
    import urllib.request
    import urllib.error
    url = f"https://graph.facebook.com/v21.0/{page_id}?fields=id,name&access_token={token}"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "JavisOS/1.0"})
        with urllib.request.urlopen(req, timeout=4) as res:
            if res.status == 200:
                return True, "active"
            return False, f"http-{res.status}"
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8", errors="ignore"))
            err_msg = body.get("error", {}).get("message", str(e))
            return False, f"facebook-error: {err_msg}"
        except Exception:
            return False, f"http-error-{e.code}"
    except Exception as e:
        # Nếu mạng chập chờn hoặc timeout tạm thời thì vẫn cho qua để không chặn tiến trình
        return True, f"network-warning: {e}"


def remove_accents(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn").replace("đ", "d")


def infer_specialized_tag(name: str, slug: str = "", raw_tags: str = "") -> list[str]:
    """Nhận diện tự động và KHÓA CHẶT chuyên môn từng Fanpage theo Tên / Slug:
    - AutoCAD / Vẽ Kỹ Thuật: 've-ky-thuat' (CẤM đăng tin học/kế toán/đồ họa)
    - Thiết Kế Đồ Họa: 'do-hoa' (CẤM đăng tin học/kế toán/autocad)
    - Kế Toán: 'ke-toan' (CẤM đăng tin học/autocad/đồ họa)
    - Trẻ em: 'tre-em' hoặc 'tin-hoc _ai'
    - Tin học Sao Việt / AI / Chung: 'tin-hoc _ai'
    """
    norm = remove_accents(f"{name} {slug}")
    if any(k in norm for k in ["autocad", "cad", "ve ky thuat", "ban ve", "solidwork", "revit"]):
        return ["ve-ky-thuat"]
    if any(k in norm for k in ["do hoa", "thiet ke do hoa", "photoshop", "illustrator", "corel", "indesign"]):
        return ["do-hoa"]
    if any(k in norm for k in ["ke toan", "ketoan", "thue", "misa"]):
        return ["ke-toan"]
    if any(k in norm for k in ["tre em", "kid", "scratch"]):
        return ["tin-hoc _ai"]
    if any(k in norm for k in ["game", "bsn"]):
        return ["game-bsn"]

    if raw_tags:
        parsed = parse_tags(raw_tags)
        if parsed and len(parsed) == 1 and parsed[0] in registry_tags():
            return [_canonical_tag(parsed[0])]

    return ["tin-hoc _ai"]


def load_pages(include_royce=False, connected_only=True):
    rows = []
    if not KITS.is_dir():
        return rows
    connected_tokens = get_connected_page_tokens() if connected_only else {}
    for p in sorted(KITS.glob("*.md")):
        if p.name.startswith("_"):
            continue
        if p.name in SKIP_FILES and not include_royce:
            continue
        md = p.read_text(encoding="utf-8")
        pid = field(md, "Page ID", "page_id")
        if not re.fullmatch(r"\d+", pid or ""):
            continue
        if connected_only and pid not in connected_tokens:
            continue
        tok = connected_tokens.get(pid, "") or field(
            md, "Access Token", "access_token", "Page Token", "Token")
        page_name = field(md, "Tên Fanpage") or p.stem
        page_slug = field(md, "slug") or p.stem
        spec_tags = infer_specialized_tag(page_name, page_slug, field(md, "Thẻ khoá học"))
        rows.append({
            "file": p.name,
            "slug": page_slug,
            "name": page_name,
            "page_id": pid,
            "token": tok,
            "tags": spec_tags,
            "address": field(md, "Cơ sở / địa chỉ"),
            "hotline": field(md, "Hotline / Zalo", "Hotline riêng", "Hotline"),
            "email": field(md, "Email Fanpage", "Email"),
            "web": field(md, "Web Fanpage", "Web"),
            "logo": field(md, "Logo chính") or "attachments/dataset/chung/thsv-logo-2025.png",
            "logo_white": field(md, "Logo trắng") or "",
            "color_pri": field(md, "Màu chính") or "#6C3BFF",
            "color_sec": field(md, "Màu phụ") or "#00D4FF",
            "fonts": field(md, "Font") or "",
            "voice": field(md, "Tone of voice") or "",
            "layout": field(md, "Quy tắc bố cục") or "",
            "image_style": field(md, "Phong cách hình ảnh") or "",
            "donts": field(md, "Điều không được làm") or "",
        })
    return rows


def _canonical_tag(t: str) -> str:
    s = (t or "").strip().lower()
    if re.search(r"tin[\s_-]*hoc[\s_-]*ai|tin[\s_-]*hoc\b", s):
        return "tin-hoc _ai"
    if re.search(r"do[\s_-]*hoa", s):
        return "do-hoa"
    if re.search(r"ke[\s_-]*toan", s):
        return "ke-toan"
    if re.search(r"ve[\s_-]*ky[\s_-]*thuat|autocad", s):
        return "ve-ky-thuat"
    if re.search(r"tre[\s_-]*em", s):
        return "tin-hoc _ai"
    if re.search(r"game[\s_-]*bsn|game", s):
        return "game-bsn"
    return (t or "").strip()


def load_state(today):
    st = {
        "date": today,
        "ok": [],
        "skip": [],
        "cursor": 0,
        "page_last_course": {},
        "page_last_angle": {},
        "pending_course": {},
        "pending_angle": {},
    }
    if STATE.exists():
        try:
            raw = json.loads(STATE.read_text(encoding="utf-8"))
            if isinstance(raw.get("page_last_course"), dict):
                st["page_last_course"] = raw["page_last_course"]
            if isinstance(raw.get("page_last_angle"), dict):
                st["page_last_angle"] = raw["page_last_angle"]
            if isinstance(raw.get("pending_course"), dict):
                st["pending_course"] = raw["pending_course"]
            if isinstance(raw.get("pending_angle"), dict):
                st["pending_angle"] = raw["pending_angle"]
            if "cursor" in raw:
                try:
                    st["cursor"] = int(raw.get("cursor") or 0)
                except Exception:
                    pass
            st["last_angle"] = raw.get("last_angle", "")
            if raw.get("date") == today:
                st["ok"] = list(raw.get("ok") or [])
                st["skip"] = list(raw.get("skip") or [])
                st["last_course"] = raw.get("last_course", "")
            # Tự động dọn dẹp các page_id trong pending_course/pending_angle đã nằm trong ok
            if st.get("ok"):
                ok_set = set(str(x) for x in st["ok"])
                if isinstance(st.get("pending_course"), dict):
                    st["pending_course"] = {
                        k: v for k, v in st["pending_course"].items() if str(k) not in ok_set}
                if isinstance(st.get("pending_angle"), dict):
                    st["pending_angle"] = {
                        k: v for k, v in st["pending_angle"].items() if str(k) not in ok_set}
            # Đồng bộ pending_course và pending_angle: chỉ giữ lại các page_id có mặt ở cả hai
            if isinstance(st.get("pending_course"), dict) and isinstance(st.get("pending_angle"), dict):
                common_pending = set(st["pending_course"].keys()) & set(st["pending_angle"].keys())
                st["pending_course"] = {k: v for k, v in st["pending_course"].items() if k in common_pending}
                st["pending_angle"] = {k: v for k, v in st["pending_angle"].items() if k in common_pending}
        except Exception:
            pass
    return st


def save_state(st):
    """Ghi state dạng atomic qua temp file + os.replace để tránh kẹt quyền root-owned trong Docker/Linux."""
    import os
    STATE.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(st, ensure_ascii=False, indent=2) + "\n"
    tmp_file = STATE.parent / f".{STATE.name}.tmp.{os.getpid()}"
    try:
        tmp_file.write_text(content, encoding="utf-8")
        try:
            os.chmod(tmp_file, 0o666)
        except Exception:
            pass
        os.replace(tmp_file, STATE)
        try:
            os.chmod(STATE, 0o666)
        except Exception:
            pass
        return
    except Exception:
        if tmp_file.exists():
            try:
                tmp_file.unlink()
            except Exception:
                pass
    # Fallback ghi trực tiếp nếu replace không hỗ trợ
    STATE.write_text(content, encoding="utf-8")
    try:
        os.chmod(STATE, 0o666)
    except Exception:
        pass


def posted_pages_from_loop_log(today: str) -> set[str]:
    """Đọc POST_OK hôm nay từ loop-log để chống đăng lặp khi state bị reset/ghi thiếu."""
    log_file = VAULT / "Javis" / "loop-log" / f"{today}.md"
    if not log_file.is_file():
        return set()
    try:
        text = log_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return set()
    pages = set()
    for m in re.finditer(r"^POST_OK\s+post_id=(\d+)_\d+\s+status=verified\b", text, re.M):
        pages.add(m.group(1))
    return pages


def merge_posted_log_into_state(st, today: str) -> bool:
    """Bổ sung các page đã POST_OK trong log hôm nay vào ok để picker không chọn lại."""
    posted = posted_pages_from_loop_log(today)
    if not posted:
        return False
    ok_list = [str(x) for x in (st.get("ok") or [])]
    ok_set = set(ok_list)
    changed = False
    for pid in sorted(posted):
        if pid not in ok_set:
            ok_list.append(pid)
            ok_set.add(pid)
            changed = True
    if changed:
        st["ok"] = ok_list
    if isinstance(st.get("pending_course"), dict):
        before = len(st["pending_course"])
        st["pending_course"] = {
            k: v for k, v in st["pending_course"].items() if str(k) not in ok_set}
        changed = changed or len(st["pending_course"]) != before
    if isinstance(st.get("pending_angle"), dict):
        before = len(st["pending_angle"])
        st["pending_angle"] = {
            k: v for k, v in st["pending_angle"].items() if str(k) not in ok_set}
        changed = changed or len(st["pending_angle"]) != before
    return changed


BRANCHES_HCM = {
    "binh_thanh": "🏫 Bình Thạnh: 193 Nguyễn Xí, phường Bình Thạnh, TP.HCM (Quận Bình Thạnh cũ)",
    "quan_7": "🏫 Quận 7: Căn hộ Florita, KĐT Him Lam, phường Tân Hưng, TP.HCM (Quận 7 cũ)",
    "binh_tan": "🏫 Bình Tân: 510 Kinh Dương Vương, phường An Lạc, TP.HCM (Quận Bình Tân cũ)",
    "quan_6": "🏫 Bình Tân: 510 Kinh Dương Vương, phường An Lạc, TP.HCM (Quận Bình Tân cũ)",
    "quan_12": "🏫 Quận 12: A23 Lê Thị Riêng, KDC Thới An, phường Thới An, TP.HCM (Quận 12 cũ)",
    "thu_duc": "🏫 TP. Thủ Đức: 133/2 Đỗ Xuân Hợp, phường Phước Long, TP.HCM (TP. Thủ Đức cũ)",
    "tay_thanh": "🏫 CN Tây Thạnh: 11/23 Hồ Đắc Di, phường Tây Thạnh, TP.HCM (Quận Tân Phú cũ)",
    "tan_binh": "🏫 CN Tây Thạnh: 11/23 Hồ Đắc Di, phường Tây Thạnh, TP.HCM (Quận Tân Phú cũ)",
}

BRANCHES_BINH_DUONG = [
    "🏫 Dĩ An: 184/19/11 Đặng Văn Mây, phường Dĩ An, TP.HCM (TP. Dĩ An, Bình Dương cũ)",
    "🏫 Thuận An: 69 D32, Làng chuyên gia Oasis, phường An Phú, TP.HCM (Thuận An, Bình Dương cũ)",
    "🏫 Thủ Dầu Một: 107 D5, KDC Phú Hòa 1, phường Phú Lợi, TP.HCM (TP. Thủ Dầu Một, Bình Dương cũ)",
    "🏫 Tân Uyên: 20 Đường ĐX12, phường Tân Khánh, TP.HCM (TP. Tân Uyên, Bình Dương cũ)",
]

BRANCHES_DONG_NAI = [
    "🏫 Biên Hòa: 91 Đoàn Văn Cự, phường Tam Hiệp, TP. Đồng Nai (TP. Biên Hòa cũ)",
    "🏫 Long Thành: 72 Đinh Bộ Lĩnh, xã Long Thành, TP. Đồng Nai (Lộc An, huyện Long Thành cũ)",
]

BRANCHES_VUNG_TAU = [
    "🏫 Vũng Tàu: 293 Bình Giã, phường Tam Thắng, TP.HCM (TP. Vũng Tàu, Bà Rịa - Vũng Tàu cũ)",
]

BRANCHES_13_STANDARD = [
    "🏫 Bình Thạnh: 193 Nguyễn Xí, phường Bình Thạnh, TP.HCM (Quận Bình Thạnh cũ)",
    "🏫 Quận 7: Căn hộ Florita, KĐT Him Lam, phường Tân Hưng, TP.HCM (Quận 7 cũ)",
    "🏫 Bình Tân: 510 Kinh Dương Vương, phường An Lạc, TP.HCM (Quận Bình Tân cũ)",
    "🏫 Quận 12: A23 Lê Thị Riêng, KDC Thới An, phường Thới An, TP.HCM (Quận 12 cũ)",
    "🏫 TP. Thủ Đức: 133/2 Đỗ Xuân Hợp, phường Phước Long, TP.HCM (TP. Thủ Đức cũ)",
    "🏫 CN Tây Thạnh: 11/23 Hồ Đắc Di, phường Tây Thạnh, TP.HCM (Quận Tân Phú cũ)",
    "🏫 Biên Hòa: 91 Đoàn Văn Cự, phường Tam Hiệp, TP. Đồng Nai (TP. Biên Hòa cũ)",
    "🏫 Long Thành: 72 Đinh Bộ Lĩnh, xã Long Thành, TP. Đồng Nai (Lộc An, huyện Long Thành cũ)",
    "🏫 Dĩ An: 184/19/11 Đặng Văn Mây, phường Dĩ An, TP.HCM (TP. Dĩ An, Bình Dương cũ)",
    "🏫 Thuận An: 69 D32, Làng chuyên gia Oasis, phường An Phú, TP.HCM (Thuận An, Bình Dương cũ)",
    "🏫 Thủ Dầu Một: 107 D5, KDC Phú Hòa 1, phường Phú Lợi, TP.HCM (TP. Thủ Dầu Một, Bình Dương cũ)",
    "🏫 Tân Uyên: 20 Đường ĐX12, phường Tân Khánh, TP.HCM (TP. Tân Uyên, Bình Dương cũ)",
    "🏫 Vũng Tàu: 293 Bình Giã, phường Tam Thắng, TP.HCM (TP. Vũng Tàu, Bà Rịa - Vũng Tàu cũ)",
]

BRANCHES_KE_TOAN = [
    "📍 HỆ THỐNG 13 CHI NHÁNH TIN HỌC SAO VIỆT",
] + BRANCHES_13_STANDARD


def get_page_branches(row, tag=None):
    """Xác định danh sách địa chỉ cơ sở theo đúng TÊN FANPAGE (name):
    1. Nếu Tên Fanpage có chi nhánh TP.HCM (Bình Thạnh, Quận 12, Thủ Đức, Tân Bình/Tây Thạnh, Quận 7, Bình Tân/Quận 6):
       Chỉ hiện DUY NHẤT 1 địa chỉ của chi nhánh đó.
    2. Nếu Tên Fanpage có Bình Dương (hoặc Dĩ An, Thuận An, Thủ Dầu Một, Tân Uyên):
       Hiện ĐẦY ĐỦ cả 4 địa chỉ thuộc tỉnh Bình Dương.
    3. Nếu Tên Fanpage có Đồng Nai (hoặc Biên Hòa, Long Thành):
       Hiện ĐẦY ĐỦ cả 2 địa chỉ thuộc tỉnh Đồng Nai.
    4. Nếu Tên Fanpage có Vũng Tàu (hoặc Bà Rịa):
       Hiện địa chỉ cơ sở tại Vũng Tàu.
    5. Nếu Tên Fanpage KHÔNG ĐỀ CẬP địa danh nào (như Trung Tâm Đào Tạo AI Sao Việt, Tin Học Sao Việt, Royce Shop):
       ĐĂNG HẾT TẤT CẢ 13 CHI NHÁNH TIN HỌC SAO VIỆT.
    """
    page_name = row.get("name") or row.get("slug") or ""
    norm_name = remove_accents(page_name)

    # 0. Nếu Page có địa chỉ riêng khai trong kit (như Game Giá Rẻ BSN) và không phải hệ thống Sao Việt
    if row.get("address"):
        addr = row["address"].strip()
        if addr and "HE THONG 13 CHI NHANH" not in remove_accents(addr) and not any(k in norm_name for k in ["sao viet", "royce"]):
            return [b.strip() for b in addr.split("|") if b.strip()]

    # 1. Cơ sở TP.HCM: chỉ hiện 1 chi nhánh tương ứng theo tên page
    if "binh thanh" in norm_name:
        return [BRANCHES_HCM["binh_thanh"]]
    if re.search(r"\b(quan\s*12|q\.?\s*12)\b", norm_name):
        return [BRANCHES_HCM["quan_12"]]
    if "thu duc" in norm_name:
        return [BRANCHES_HCM["thu_duc"]]
    if any(k in norm_name for k in ["tan binh", "tay thanh", "tan phu"]):
        return [BRANCHES_HCM["tay_thanh"]]
    if re.search(r"\b(quan\s*7|q\.?\s*7)\b", norm_name):
        return [BRANCHES_HCM["quan_7"]]
    if re.search(r"\b(quan\s*6|q\.?\s*6|binh tan)\b", norm_name):
        return [BRANCHES_HCM["binh_tan"]]

    # 2. Bình Dương: hiện hết cả 4 cơ sở tại Bình Dương nếu tên page có đề cập Bình Dương / huyện thị
    if any(k in norm_name for k in ["binh duong", "di an", "thuan an", "thu dau mot", "tan uyen"]):
        return BRANCHES_BINH_DUONG

    # 3. Đồng Nai: hiện hết cả 2 cơ sở tại Đồng Nai nếu tên page có đề cập Đồng Nai / Biên Hòa / Long Thành
    if any(k in norm_name for k in ["dong nai", "bien hoa", "long thanh"]):
        return BRANCHES_DONG_NAI

    # 4. Vũng Tàu / Bà Rịa: hiện cơ sở Vũng Tàu nếu tên page có đề cập Vũng Tàu / Bà Rịa
    if any(k in norm_name for k in ["vung tau", "ba ria"]):
        return BRANCHES_VUNG_TAU

    # 5. KHÔNG ĐỀ CẬP ĐỊA DANH GÌ Ở TÊN FANPAGE -> ĐĂNG HẾT TẤT CẢ CÁC ĐỊA CHỈ
    return ["📍 HỆ THỐNG 13 CHI NHÁNH TIN HỌC SAO VIỆT"] + BRANCHES_13_STANDARD


def print_chan_trang(row, tag=None):
    print("CHAN_TRANG")
    print(row["name"])
    branches = get_page_branches(row, tag)
    for b in branches:
        print(b)
    if row.get("hotline"):
        hl = row["hotline"].strip()
        if not hl.startswith("📞") and not hl.startswith("☎"):
            hl_val = re.sub(
                r"^(Hotline/Zalo|Hotline|Zalo)[:\s]*", "", hl, flags=re.I).strip()
            print("📞 Hotline/Zalo: " + hl_val)
        else:
            print(hl)
    if row.get("email"):
        em = row["email"].strip()
        if not em.startswith("📧"):
            em_val = re.sub(r"^Email[:\s]*", "", em, flags=re.I).strip()
            print("📧 Email: " + em_val)
        else:
            print(em)
    if row.get("web"):
        wb = row["web"].strip()
        if not wb.startswith("🌐"):
            wb_val = re.sub(
                r"^(Website|Web)[:\s]*", "", wb, flags=re.I).strip()
            print("🌐 Website: " + wb_val)
        else:
            print(wb)
    print("HET_CHAN_TRANG")


def main(argv):
    now = datetime.now(TZ)
    today = now.strftime("%Y-%m-%d")
    include_royce = "--include-royce" in argv
    st = load_state(today)
    if merge_posted_log_into_state(st, today):
        save_state(st)
    specific_page = None
    if "--page" in argv:
        i = argv.index("--page")
        specific_page = argv[i + 1] if i + 1 < len(argv) else ""

    specific_angle = None
    if "--angle" in argv:
        i = argv.index("--angle")
        specific_angle = argv[i + 1] if i + 1 < len(argv) else ""
        if specific_angle not in CONTENT_ANGLES:
            specific_angle = None

    mark_ok = None
    mark_fail = None
    reason = ""
    if "--ok" in argv:
        i = argv.index("--ok")
        mark_ok = argv[i + 1] if i + 1 < len(argv) else ""
    if "--fail" in argv:
        i = argv.index("--fail")
        mark_fail = argv[i + 1] if i + 1 < len(argv) else ""
        reason = " ".join(argv[i + 2:]) if i + 2 < len(argv) else "POST_SKIP"

    if specific_page:
        all_pages = load_pages(include_royce=True, connected_only=False)
        row = None
        try:
            sys.path.insert(0, str(Path(VAULT) / "scratch"))
            import kit_tim
            best = kit_tim.resolve_kit(specific_page)
            if best:
                row = next(
                    (p for p in all_pages if p["file"] == best["filename"]), None)
        except Exception:
            pass
        if not row:
            q_clean = specific_page.lower().strip()
            row = next((p for p in all_pages if q_clean in p["name"].lower() or q_clean in p["slug"].lower(
            ) or q_clean in p["file"].lower() or q_clean == p["page_id"]), None)
        if not row:
            print(f"ERROR: khong-tim-thay-page query={specific_page}")
            return 1
        force = "--force" in argv
        if not force and row["page_id"] in (st.get("ok") or []):
            print(
                f"NEXT=NONE page-da-ok-hom-nay id={row['page_id']} name={row['name']}")
            return 0
        page_last = (st.get("page_last_course") or {}
                     ).get(row["page_id"]) or ""
        all_tags = [_canonical_tag(t) for t in (
            row.get("tags") or registry_tags())]
        unique_tags = []
        for t in all_tags:
            if t not in unique_tags:
                unique_tags.append(t)
        if len(unique_tags) > 1 and page_last:
            available_tags = [t for t in unique_tags if _canonical_tag(
                t) != _canonical_tag(page_last)]
            if not available_tags:
                available_tags = unique_tags
        else:
            available_tags = unique_tags
        tag = random.choice(available_tags or ["tin-hoc _ai"])

        # Xoay tua toàn cục (Global Round-Robin) giữa các bài đăng liên tiếp
        global_last_angle = st.get("last_angle") or ""
        page_last_angle = (st.get("page_last_angle") or {}).get(row["page_id"]) or ""
        angle = specific_angle or pick_next_angle(global_last_angle)
        if not specific_angle and page_last_angle and angle == page_last_angle:
            angle = pick_next_angle(angle)

        if "pending_course" not in st or not isinstance(st["pending_course"], dict):
            st["pending_course"] = {}
        st["pending_course"][row["page_id"]] = tag
        if "pending_angle" not in st or not isinstance(st["pending_angle"], dict):
            st["pending_angle"] = {}
        st["pending_angle"][row["page_id"]] = angle
        st["last_angle"] = angle
        save_state(st)
        print("NEXT=1")
        print("page_id=" + row["page_id"])
        print("ten=" + row["name"])
        print("slug=" + row["slug"])
        print("kit=" + row["file"])
        print("kit_path=wiki/brand-kits/" + row["file"])
        print("course_path=wiki/courses/" + tag + ".md")
        print("skill_path=skills/dang-bai-facebook/SKILL.md")
        print("the=" + tag)
        print("angle=" + angle)
        print("angle_label=" + ANGLE_LABELS.get(angle, angle))
        print("hotline=" + (row["hotline"] or ""))
        print("email=" + (row["email"] or ""))
        print("web=" + (row["web"] or ""))
        branches = get_page_branches(row, tag)
        print("dia_chi=" + " | ".join(branches))
        print("folder=attachments/dataset/" + tag + "/")
        print(
            "luat_anh=album 5-8 anh neu du dataset: photos[0]=cover AI moi, photos[1..]=anh that dung folder; chi fb_page_photo khi khong du anh")
        print("doc_he_thong=Đọc skills/dang-bai-facebook/SKILL.md, wiki/brand-kits/" + row["file"] + ", wiki/courses/" + tag + ".md")
        print("logo=" + (row.get("logo") or ""))
        print("logo_white=" + (row.get("logo_white") or ""))
        print("mau_chinh=" + (row.get("color_pri") or ""))
        print("mau_phu=" + (row.get("color_sec") or ""))
        print("font=" + (row.get("fonts") or ""))
        print("giong=" + (row.get("voice") or ""))
        print("bo_cuc=" + (row.get("layout") or ""))
        print("phong_cach_anh=" + (row.get("image_style") or ""))
        print("cam=" + (row.get("donts") or ""))
        print("KIT_VISUAL")
        print("Dung dung logo file: " + (row.get("logo") or ""))
        print("Mau poster: " + (row.get("color_pri") or "") +
              " + " + (row.get("color_sec") or ""))
        print("Font: " + (row.get("fonts") or ""))
        print("Giong caption: " + (row.get("voice") or ""))
        print("Bo cuc: " + (row.get("layout") or ""))
        print("Phong cach anh: " + (row.get("image_style") or ""))
        print("Cam: " + (row.get("donts") or ""))
        print("HET_KIT_VISUAL")
        print_chan_trang(row, tag)
        return 0

    connected_only = "--all-pages" not in argv
    no_verify = "--no-verify" in argv
    pages = load_pages(include_royce=include_royce,
                       connected_only=connected_only)

    if mark_ok:
        if mark_ok not in st["ok"]:
            st["ok"].append(mark_ok)
        course_done = None
        angle_done = None

        # Kiểm tra nếu truyền tham số: --ok <page_id> <course> <angle>
        pos = argv.index("--ok")
        if len(argv) > pos + 2 and not argv[pos + 2].startswith("-"):
            course_done = argv[pos + 2].strip()
        elif mark_ok in (st.get("pending_course") or {}):
            course_done = st["pending_course"].get(mark_ok)

        if len(argv) > pos + 3 and not argv[pos + 3].startswith("-"):
            angle_done = argv[pos + 3].strip()
        elif mark_ok in (st.get("pending_angle") or {}):
            angle_done = st["pending_angle"].get(mark_ok)

        if course_done:
            course_done = _canonical_tag(course_done)
            st["last_course"] = course_done
            if "page_last_course" not in st or not isinstance(st["page_last_course"], dict):
                st["page_last_course"] = {}
            st["page_last_course"][mark_ok] = course_done

        if angle_done and angle_done in CONTENT_ANGLES:
            st["last_angle"] = angle_done
            if "page_last_angle" not in st or not isinstance(st["page_last_angle"], dict):
                st["page_last_angle"] = {}
            st["page_last_angle"][mark_ok] = angle_done

        # Xóa khỏi pending_course & pending_angle để dọn dẹp state sạch sẽ
        if "pending_course" in st and isinstance(st["pending_course"], dict):
            st["pending_course"].pop(str(mark_ok), None)
            st["pending_course"].pop(mark_ok, None)
        if "pending_angle" in st and isinstance(st["pending_angle"], dict):
            st["pending_angle"].pop(str(mark_ok), None)
            st["pending_angle"].pop(mark_ok, None)

        st["skip"] = [x for x in st.get(
            "skip") or [] if x.get("id") != mark_ok]
        save_state(st)
        print("MARK_OK", mark_ok,
              f"course={st.get('page_last_course', {}).get(mark_ok, '')} angle={st.get('page_last_angle', {}).get(mark_ok, '')}")
        return 0

    if mark_fail:
        # Dọn dẹp pending_course & pending_angle khi thất bại
        if "pending_course" in st and isinstance(st["pending_course"], dict):
            st["pending_course"].pop(str(mark_fail), None)
            st["pending_course"].pop(mark_fail, None)
        if "pending_angle" in st and isinstance(st["pending_angle"], dict):
            st["pending_angle"].pop(str(mark_fail), None)
            st["pending_angle"].pop(mark_fail, None)

        skips = list(st.get("skip") or [])
        prev = next((x for x in skips if x.get("id") == mark_fail), None)
        lan = int((prev or {}).get("lan") or 0) + 1
        hard = bool(re.search(
            r"chan-trang|khong-retry|chua-co-brand-kit|khong-dung-the",
            reason, re.I))
        retry_at = (now + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
        rec = {"id": mark_fail,
               "ly_do": reason[:200], "lan": lan, "retry_after": retry_at}
        skips = [x for x in skips if x.get("id") != mark_fail]
        if hard or lan >= 2:
            rec["retry_after"] = today + " 23:59"
            rec["bo_toi_mai"] = True
            rec["lan"] = max(lan, 2)
        skips.append(rec)
        st["skip"] = skips
        save_state(st)
        print("MARK_FAIL", json.dumps(rec, ensure_ascii=False))
        return 0

    ok = set(st.get("ok") or [])
    skip_map = {x.get("id"): x for x in (st.get("skip") or []) if x.get("id")}
    n_all = len(pages)
    start_idx = int(st.get("cursor") or 0) % max(n_all, 1)
    selected_row = None
    selected_idx = None

    for offset in range(n_all):
        idx = (start_idx + offset) % max(n_all, 1)
        cand = pages[idx]
        pid = cand["page_id"]
        if pid in ok:
            continue
        sk = skip_map.get(pid)
        if sk:
            if sk.get("bo_toi_mai"):
                continue
            ra = sk.get("retry_after") or ""
            try:
                ra_dt = datetime.strptime(
                    ra, "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
            except ValueError:
                ra_dt = now
            if now < ra_dt:
                continue

        # Kiểm tra nhanh token còn sống trên Graph API
        if not no_verify and cand.get("token"):
            is_alive, live_msg = verify_token_live(pid, cand["token"])
            if not is_alive:
                print(
                    f"SKIP_EXPIRED_TOKEN page_id={pid} ten={cand['name']} ly_do={live_msg}")
                skips = [x for x in st.get("skip") or [] if x.get("id") != pid]
                skips.append(
                    {"id": pid, "ly_do": f"token-het-han: {live_msg[:100]}", "lan": 2, "bo_toi_mai": True})
                st["skip"] = skips
                save_state(st)
                continue

        selected_row = cand
        selected_idx = idx
        break

    eligible_count = sum(
        1 for p in pages
        if p["page_id"] not in ok and not (
            skip_map.get(p["page_id"]) and (
                skip_map[p["page_id"]].get("bo_toi_mai") or
                now < datetime.strptime(skip_map[p["page_id"]].get(
                    "retry_after", "2099-01-01 00:00"), "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
            )
        )
    )

    print("HANG_NGAY date=" + today)
    print("tong_page_ket_noi=" + str(n_all) + " da_ok=" +
          str(len(ok)) + " cho=" + str(eligible_count))
    if not selected_row:
        print("NEXT=NONE het-hang-hom-nay")
        return 0

    row = selected_row
    st["cursor"] = (selected_idx + 1) % max(n_all, 1)

    page_last = (st.get("page_last_course") or {}).get(row["page_id"]) or ""
    all_tags = [_canonical_tag(t)
                for t in (row.get("tags") or registry_tags())]
    unique_tags = []
    for t in all_tags:
        if t not in unique_tags:
            unique_tags.append(t)

    # Luật chống trùng: Nếu page có > 1 khóa học thì CẤM trùng khóa vừa đăng lần trước
    # Nếu page chỉ có đúng 1 khóa học thì được phép đăng trùng khóa duy nhất đó
    if len(unique_tags) > 1 and page_last:
        available_tags = [t for t in unique_tags if _canonical_tag(
            t) != _canonical_tag(page_last)]
        if not available_tags:
            available_tags = unique_tags
    else:
        available_tags = unique_tags

    tag = random.choice(available_tags or ["tin-hoc _ai"])

    # Xoay tua toàn cục (Global Round-Robin) giữa các bài đăng liên tiếp
    global_last_angle = st.get("last_angle") or ""
    page_last_angle = (st.get("page_last_angle") or {}).get(row["page_id"]) or ""
    angle = specific_angle or pick_next_angle(global_last_angle)
    if not specific_angle and page_last_angle and angle == page_last_angle:
        angle = pick_next_angle(angle)

    if "pending_course" not in st or not isinstance(st["pending_course"], dict):
        st["pending_course"] = {}
    st["pending_course"][row["page_id"]] = tag
    if "pending_angle" not in st or not isinstance(st["pending_angle"], dict):
        st["pending_angle"] = {}
    st["pending_angle"][row["page_id"]] = angle
    st["last_angle"] = angle
    save_state(st)
    print("NEXT=1")
    print("page_id=" + row["page_id"])
    print("ten=" + row["name"])
    print("slug=" + row["slug"])
    print("kit=" + row["file"])
    print("kit_path=wiki/brand-kits/" + row["file"])
    print("course_path=wiki/courses/" + tag + ".md")
    print("skill_path=skills/dang-bai-facebook/SKILL.md")
    print("the=" + tag)
    print("angle=" + angle)
    print("angle_label=" + ANGLE_LABELS.get(angle, angle))
    print("hotline=" + (row["hotline"] or ""))
    print("email=" + (row["email"] or ""))
    print("web=" + (row["web"] or ""))
    branches = get_page_branches(row, tag)
    print("dia_chi=" + " | ".join(branches))
    print("folder=attachments/dataset/" + tag + "/")
    print(
        "luat_anh=album 5-8 anh neu du dataset: photos[0]=cover AI moi, photos[1..]=anh that dung folder; chi fb_page_photo khi khong du anh")
    print("doc_he_thong=Đọc skills/dang-bai-facebook/SKILL.md, wiki/brand-kits/" + row["file"] + ", wiki/courses/" + tag + ".md")
    print("logo=" + (row.get("logo") or ""))
    print("logo_white=" + (row.get("logo_white") or ""))
    print("mau_chinh=" + (row.get("color_pri") or ""))
    print("mau_phu=" + (row.get("color_sec") or ""))
    print("font=" + (row.get("fonts") or ""))
    print("giong=" + (row.get("voice") or ""))
    print("bo_cuc=" + (row.get("layout") or ""))
    print("phong_cach_anh=" + (row.get("image_style") or ""))
    print("cam=" + (row.get("donts") or ""))
    print("KIT_VISUAL")
    print("Dung dung logo file: " + (row.get("logo") or ""))
    print("Mau poster: " + (row.get("color_pri") or "") +
          " + " + (row.get("color_sec") or ""))
    print("Font: " + (row.get("fonts") or ""))
    print("Giong caption: " + (row.get("voice") or ""))
    print("Bo cuc: " + (row.get("layout") or ""))
    print("Phong cach anh: " + (row.get("image_style") or ""))
    print("Cam: " + (row.get("donts") or ""))
    print("HET_KIT_VISUAL")
    print_chan_trang(row, tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
