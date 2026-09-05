# -*- coding: utf-8 -*-
"""In chân trang bắt buộc cho 1 Fanpage (lấy từ Brand Kit).

Dùng trước khi đăng:
  python "brains/Brain Default/scratch/kit_chan_trang.py" <page_id>
Dán nguyên khối CHAN_TRANG vào cuối caption. Không thay hotline/địa chỉ mặc định.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[1]
KITS = VAULT / "wiki" / "brand-kits"


def field(md, *labels):
    for lab in labels:
        m = re.search(r"^[ \t]*[-*][ \t]*" + re.escape(lab) + r":[ \t]*(.*)$", md, re.M)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def load(page_id):
    pid = str(page_id or "").strip()
    for p in sorted(KITS.glob("*.md")):
        if p.name.startswith("_"):
            continue
        md = p.read_text(encoding="utf-8")
        if field(md, "Page ID", "page_id") == pid:
            return p, md
    return None, None


def footer_block(md, name):
    addr = field(md, "Cơ sở / địa chỉ")
    parts = [a.strip() for a in addr.split("|") if a.strip()] if addr else []
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
        print("USAGE: kit_chan_trang.py <page_id>", file=sys.stderr)
        return 2
    path, md = load(argv[1])
    if not md:
        print("ERROR: chua-co-brand-kit page_id=" + argv[1])
        return 1
    name = field(md, "Tên Fanpage") or path.stem
    print("CHAN_TRANG")
    print("kit=" + path.name)
    print(footer_block(md, name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
