# -*- coding: utf-8 -*-
"""In chân trang bắt buộc cho 1 Fanpage (lấy từ Brand Kit).

Hỗ trợ tìm kiếm thông minh bằng Page ID, slug, tên Fanpage hoặc từ khóa mờ.

Dùng trước khi đăng:
  python "brains/Brain Default/scratch/kit_chan_trang.py" <page_id_hoac_ten_page>
Dán nguyên khối CHAN_TRANG vào cuối caption. Không thay hotline/địa chỉ mặc định.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

VAULT = Path(__file__).resolve().parents[1]
KITS = VAULT / "wiki" / "brand-kits"


def field(md, *labels):
    for lab in labels:
        m = re.search(r"^[ \t]*[-*][ \t]*" + re.escape(lab) + r":[ \t]*(.*)$", md, re.M)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def load(query):
    pid = str(query or "").strip()
    if not pid:
        return None, None

    # 1. Tìm chính xác theo Page ID
    for p in sorted(KITS.glob("*.md")):
        if p.name.startswith("_"):
            continue
        try:
            md = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if field(md, "Page ID", "page_id") == pid:
            return p, md

    # 2. Tìm thông minh qua kit_tim nếu không phải số Page ID hoặc chưa tìm thấy
    try:
        from kit_tim import resolve_kit
        best = resolve_kit(pid)
        if best and best.get("path") and best.get("md"):
            return best["path"], best["md"]
    except Exception:
        pass

    return None, None


def footer_block(md, name):
    addr = field(md, "Cơ sở / địa chỉ")
    parts = []
    if addr:
        for a in addr.replace("|", "\n").splitlines():
            a = a.strip()
            if a:
                parts.append(a)
    hot = field(md, "Hotline / Zalo", "Hotline riêng", "Hotline")
    email = field(md, "Email Fanpage", "Email")
    web = field(md, "Web Fanpage", "Web")
    lines = [name] if name else []
    lines.extend(parts)
    if hot:
        lines.append("Hotline/Zalo: " + hot)
    if email:
        lines.append("Email: " + email)
    if web:
        lines.append("Web: " + web)
    return "\n".join(lines)


def main(argv):
    if len(argv) < 2:
        print("USAGE: kit_chan_trang.py <page_id_hoac_tu_khoa>", file=sys.stderr)
        return 2
    query = argv[1]
    path, md = load(query)
    if not md:
        print("ERROR: chua-co-brand-kit page=" + query)
        return 1
    name = field(md, "Tên Fanpage") or path.stem
    print("kit=" + path.name)
    print("logo=" + (field(md, "Logo chính") or "attachments/dataset/chung/thsv-logo-2025.png"))
    print("mau_chinh=" + (field(md, "Màu chính") or ""))
    print("mau_phu=" + (field(md, "Màu phụ") or ""))
    print("font=" + (field(md, "Font") or ""))
    print("giong=" + (field(md, "Tone of voice") or ""))
    print("KIT_VISUAL")
    print("Logo file (bat buoc dua vao gemini_generate_image): "
          + (field(md, "Logo chính") or "attachments/dataset/chung/thsv-logo-2025.png"))
    print("Mau: " + (field(md, "Màu chính") or "") + " / " + (field(md, "Màu phụ") or ""))
    print("Font: " + (field(md, "Font") or ""))
    print("Giong: " + (field(md, "Tone of voice") or ""))
    print("Bo cuc: " + (field(md, "Quy tắc bố cục") or ""))
    print("Phong cach: " + (field(md, "Phong cách hình ảnh") or ""))
    print("Cam: " + (field(md, "Điều không được làm") or ""))
    print("HET_KIT_VISUAL")
    print("CHAN_TRANG")
    print(footer_block(md, name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
