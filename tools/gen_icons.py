#!/usr/bin/env python3
"""Sinh dashboard/vendor/lucide-icons.js từ dashboard/icons.manifest.json.

Chạy lại mỗi khi thêm/bớt icon trong manifest:

    python tools/gen_icons.py

Script tải SVG từ CDN của lucide-static rồi rút phần ruột (bỏ thẻ <svg> ngoài,
vì icons.js tự dựng thẻ bọc). Kết quả ghi vào vendor/ và ĐƯỢC COMMIT vào repo -
app không bao giờ gọi mạng lúc chạy, chạy được cả khi máy không có internet.

Cần internet KHI CHẠY SCRIPT. Nếu một tên icon không có thật, script dừng và
báo tên sai thay vì ghi ra file thiếu icon (icon thiếu = icon vô hình, rất khó
phát hiện bằng mắt).
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "dashboard" / "icons.manifest.json"
OUT = ROOT / "dashboard" / "vendor" / "lucide-icons.js"
OUT_CSS = ROOT / "dashboard" / "vendor" / "lucide-icons.css"

LUCIDE_VERSION = "1.27.0"
CDN = "https://cdn.jsdelivr.net/npm/lucide-static@{ver}/icons/{name}.svg"
TIMEOUT = 20

# Thuộc tính thẻ <svg> ngoài do icons.js dựng, nên rút bỏ khỏi phần ruột.
OUTER_SVG = re.compile(r"^.*?<svg\b[^>]*>(.*)</svg>\s*$", re.DOTALL)
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
WS = re.compile(r"\s+")


def load_manifest() -> tuple[list[str], list[str]]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    names: list[str] = []
    for group, items in data.get("groups", {}).items():
        if not isinstance(items, list):
            sys.exit(f"Nhóm '{group}' trong manifest phải là một danh sách.")
        names.extend(items)
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        sys.exit("Tên icon bị lặp trong manifest: " + ", ".join(dupes))

    css_vars = data.get("css_vars", []) or []
    missing = sorted(set(css_vars) - set(names))
    if missing:
        sys.exit(
            "css_vars có tên chưa nằm trong groups: " + ", ".join(missing) +
            "\nThêm chúng vào một nhóm trước đã."
        )
    return sorted(set(names)), sorted(set(css_vars))


def data_uri(body: str) -> str:
    """Bọc ruột icon thành data URI dùng được trong mask/background của CSS.

    Chỉ escape đúng những ký tự phá cú pháp url(...) trong CSS. Giữ nguyên phần
    còn lại cho file dễ đọc và nhẹ hơn so với base64.
    """
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
        "stroke='black' stroke-width='2' stroke-linecap='round' "
        "stroke-linejoin='round'>" + body.replace('"', "'") + "</svg>"
    )
    for ch, rep in (("%", "%25"), ("#", "%23"), ("<", "%3C"), (">", "%3E")):
        svg = svg.replace(ch, rep)
    return 'url("data:image/svg+xml,' + svg + '")'


def fetch(name: str) -> str:
    url = CDN.format(ver=LUCIDE_VERSION, name=name)
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            sys.exit(
                f"Không có icon '{name}' trong lucide-static@{LUCIDE_VERSION}.\n"
                f"Tra lại tên đúng ở https://lucide.dev/icons/ rồi sửa manifest."
            )
        sys.exit(f"Tải '{name}' lỗi HTTP {exc.code}: {url}")
    except urllib.error.URLError as exc:
        sys.exit(f"Không nối được CDN ({exc.reason}). Script này cần internet.")

    raw = COMMENT.sub("", raw)
    match = OUTER_SVG.match(raw)
    if not match:
        sys.exit(f"SVG của '{name}' không đúng khuôn mong đợi, không rút được ruột.")
    body = WS.sub(" ", match.group(1)).strip()
    if not body:
        sys.exit(f"Icon '{name}' rút ra rỗng.")
    return body


def main() -> None:
    names, css_vars = load_manifest()
    print(f"Manifest có {len(names)} icon. Đang tải từ lucide-static@{LUCIDE_VERSION}...")

    icons: dict[str, str] = {}
    for i, name in enumerate(names, 1):
        icons[name] = fetch(name)
        print(f"  [{i:3d}/{len(names)}] {name}")

    lines = [
        "// FILE TỰ SINH - ĐỪNG SỬA TAY.",
        f"// Nguồn: lucide-static@{LUCIDE_VERSION} (giấy phép ISC) - https://lucide.dev",
        "// Sinh lại: sửa dashboard/icons.manifest.json rồi chạy python tools/gen_icons.py",
        "window.LucideIcons = {",
    ]
    for name in names:
        lines.append(f'  {json.dumps(name)}: {json.dumps(icons[name])},')
    lines.append("};")
    lines.append(f'window.LucideIconsVersion = "{LUCIDE_VERSION}";')
    lines.append("")

    # newline="\n": cả repo dùng LF. Trên Windows, Python ở text mode tự đổi \n
    # thành \r\n, làm diff thành "cả file thay đổi" và che mất sửa đổi thật.
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    size = OUT.stat().st_size
    print(f"\nĐã ghi {OUT.relative_to(ROOT)} - {len(names)} icon, {size / 1024:.1f}KB.")

    css = [
        "/* FILE TỰ SINH - ĐỪNG SỬA TAY. */",
        f"/* Nguồn: lucide-static@{LUCIDE_VERSION} (giấy phép ISC) - https://lucide.dev */",
        "/* Sinh lại: sửa css_vars trong dashboard/icons.manifest.json rồi chạy",
        "   python tools/gen_icons.py */",
        "",
        "/* Icon dạng data URI cho những chỗ CHỈ CSS với tới được: content của",
        "   ::before/::after, background... Thẻ SVG không nhét vào content: được.",
        "   Dùng kèm lớp .ic-mask trong style.css để icon vẫn ăn currentColor. */",
        ":root {",
    ]
    for name in css_vars:
        css.append(f"  --ic-{name}: {data_uri(icons[name])};")
    css.append("}")
    css.append("")
    OUT_CSS.write_text("\n".join(css), encoding="utf-8", newline="\n")
    print(f"Đã ghi {OUT_CSS.relative_to(ROOT)} - {len(css_vars)} biến CSS, "
          f"{OUT_CSS.stat().st_size / 1024:.1f}KB.")


if __name__ == "__main__":
    main()
