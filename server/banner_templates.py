# -*- coding: utf-8 -*-
"""
server/banner_templates.py - Hệ thống sinh Banner đồ họa thực chiến từ Ảnh thật Dataset.

Cung cấp các mẫu layout chuyên nghiệp, chuẩn Agency 2026:
- Template 1: 'split_right' (Chuẩn theo ảnh mẫu người dùng yêu cầu: Trái ảnh lớp thật, Phải panel xanh thương hiệu)
- Template 2: 'split_left' (Đổi bên: Trái panel thương hiệu, Phải ảnh lớp thật)
- Template 3: 'bottom_bar' (Ảnh thật lớp học góc rộng 70%, chân trang gradient navy 30% với badge viên thuốc)
- Template 4: 'floating_card' (Ảnh thật tràn nền, card thông tin kính mờ/navy nổi khối 3D)
- Template 5: 'diagonal_slice' (Cắt vát góc công nghệ hiện đại năng động)

100% font tiếng Việt Unicode chuẩn không lỗi dấu, tự động ngắt dòng thông minh, không lệch khung.
"""
from __future__ import annotations

import io
import math
import os
import random
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_font(
    size: int,
    bold: bool = True,
    weight: Optional[str] = None,
    family: Optional[str] = None,
) -> ImageFont.FreeTypeFont:
    """Tìm font TrueType hỗ trợ 100% tiếng Việt Unicode trên mọi hệ điều hành (Windows, Linux, Docker).
    Ưu tiên tuyệt đối:
    1. Be Vietnam Pro (Font chuẩn mực thiết kế riêng cho tiếng Việt, tối ưu diacritics hoàn hảo không đè dấu).
    2. Montserrat (Font hình học hiện đại, mạnh mẽ, đúng nhận diện Brand Kit Sao Việt).
    3. Fallback an toàn: Arial, Segoe UI, Tahoma, DejaVu Sans...
    """
    root = _project_root()
    sys_fonts = root / "system" / "fonts"

    # Xác định mức độ đậm (weight)
    w = (weight or "").lower()
    if not w:
        w = "bold" if bold else "regular"

    fam = (family or "").lower()
    candidates = []

    # 1. Be Vietnam Pro (Đặc trị tiếng Việt, đẹp nhất, cân đối dấu thanh)
    if fam in ("", "bevietnam", "vietnam", "default"):
        if w in ("extrabold", "black"):
            candidates.extend([
                sys_fonts / "BeVietnamPro-ExtraBold.ttf",
                sys_fonts / "BeVietnamPro-Bold.ttf",
                sys_fonts / "Montserrat-ExtraBold.ttf",
            ])
        elif w in ("bold",):
            candidates.extend([
                sys_fonts / "BeVietnamPro-Bold.ttf",
                sys_fonts / "BeVietnamPro-SemiBold.ttf",
                sys_fonts / "Montserrat-Bold.ttf",
            ])
        elif w in ("semibold", "medium"):
            candidates.extend([
                sys_fonts / "BeVietnamPro-SemiBold.ttf",
                sys_fonts / "BeVietnamPro-Medium.ttf",
                sys_fonts / "Montserrat-SemiBold.ttf",
            ])
        else:
            candidates.extend([
                sys_fonts / "BeVietnamPro-Regular.ttf",
                sys_fonts / "BeVietnamPro-Medium.ttf",
            ])

    # 2. Montserrat (Nhận diện thương hiệu Sao Việt)
    if fam in ("", "montserrat"):
        if w in ("extrabold", "black"):
            candidates.extend([
                sys_fonts / "Montserrat-ExtraBold.ttf",
                sys_fonts / "Montserrat-Bold.ttf",
            ])
        elif w in ("bold",):
            candidates.extend([
                sys_fonts / "Montserrat-Bold.ttf",
                sys_fonts / "Montserrat-SemiBold.ttf",
            ])
        elif w in ("semibold", "medium"):
            candidates.extend([
                sys_fonts / "Montserrat-SemiBold.ttf",
            ])

    # 3. Fallback hệ thống an toàn
    candidates.extend([
        sys_fonts / ("arialbd.ttf" if bold else "arial.ttf"),
        sys_fonts / "arial.ttf",
        Path(r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf"),
        Path(r"C:\Windows\Fonts\tahomabd.ttf" if bold else r"C:\Windows\Fonts\tahoma.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
    ])

    for p in candidates:
        if p and p.is_file():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                pass
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    """Ngắt dòng chữ thông minh bám theo chiều rộng tối đa, không ngắt đôi từ."""
    text = (text or "").strip()
    if not text:
        return []
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width or not current_line:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def fit_title_font(
    draw: ImageDraw.ImageDraw,
    title: str,
    max_width: int,
    max_height: int,
    start_size: int = 76,
    min_size: int = 42,
    weight: str = "extrabold",
    family: str = "bevietnam",
) -> Tuple[ImageFont.ImageFont, List[str]]:
    """Tự động co kích thước font để tiêu đề nằm vừa vặn, không bao giờ tràn khung."""
    for sz in range(start_size, min_size - 1, -4):
        font = get_font(sz, weight=weight, family=family)
        lines = wrap_text(draw, title, font, max_width)
        if not lines:
            return font, [title]
        total_h = 0
        for line in lines:
            bb = draw.textbbox((0, 0), line, font=font)
            total_h += (bb[3] - bb[1]) + int(sz * 0.25)
        if total_h <= max_height and len(lines) <= 3:
            return font, lines
    font = get_font(min_size, weight=weight, family=family)
    return font, wrap_text(draw, title, font, max_width)[:3]


def smart_crop_and_enhance(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Crop ảnh giữ góc nhìn trọng tâm, cân chỉnh độ tương phản và màu sắc tự nhiên."""
    img = img.convert("RGB")
    sw, sh = img.size
    target_ratio = target_w / float(target_h)
    src_ratio = sw / float(sh)

    if src_ratio > target_ratio:
        new_w = int(sh * target_ratio)
        offset_x = int((sw - new_w) * 0.45)
        cropped = img.crop((offset_x, 0, offset_x + new_w, sh))
    else:
        new_h = int(sw / target_ratio)
        offset_y = int((sh - new_h) * 0.2)
        cropped = img.crop((0, offset_y, sw, offset_y + new_h))

    resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
    return resized


def paste_brand_logo(base: Image.Image, logo_path: Optional[Union[Path, str]], box: Tuple[int, int, int, int], bg_badge: bool = True) -> None:
    """Dán logo thương hiệu to rõ, nổi khối 3D với viền vàng ánh kim và bóng đổ mềm mại."""
    if not logo_path:
        return
    lp = Path(logo_path)
    if not lp.is_file():
        return
    try:
        x1, y1, x2, y2 = box
        bw = x2 - x1
        bh = y2 - y1
        W, H = base.size

        if bg_badge:
            # 1. Đổ bóng mềm sau thẻ logo
            sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(sh)
            sd.rounded_rectangle([x1 + 4, y1 + 6, x2 + 4, y2 + 6], radius=22, fill=(0, 0, 0, 130))
            sh = sh.filter(ImageFilter.GaussianBlur(14))
            base.paste(Image.alpha_composite(base.convert("RGBA"), sh))

            # 2. Thân thẻ trắng bo góc viền vàng
            draw = ImageDraw.Draw(base)
            draw.rounded_rectangle([x1, y1, x2, y2], radius=22, fill=(255, 255, 255, 252),
                                   outline=(255, 215, 0, 230), width=3)

        logo_img = Image.open(lp).convert("RGBA")
        pad_x = 26
        pad_y = 16
        max_lw = bw - (pad_x * 2)
        max_lh = bh - (pad_y * 2)

        lw, lh = logo_img.size
        scale = min(max_lw / float(lw), max_lh / float(lh))
        final_lw = max(1, int(lw * scale))
        final_lh = max(1, int(lh * scale))
        resized_logo = logo_img.resize((final_lw, final_lh), Image.Resampling.LANCZOS)

        pos_x = x1 + (bw - final_lw) // 2
        pos_y = y1 + (bh - final_lh) // 2
        base.paste(resized_logo, (pos_x, pos_y), resized_logo)
    except Exception:
        pass


def draw_pill_badge(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, font: ImageFont.ImageFont,
                    bg_color: Tuple[int, int, int, int] = (245, 124, 0, 245),
                    text_color: str = "#FFFFFF", border_color: Tuple[int, int, int, int] = (255, 235, 59, 255),
                    pad_x: int = 24, pad_y: int = 10, radius: int = 16) -> Tuple[int, int, int, int]:
    """Vẽ huy hiệu viên thuốc bo tròn (Pill Badge) nổi bật."""
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]
    box_w = tw + pad_x * 2
    box_h = th + pad_y * 2
    draw.rounded_rectangle([x, y, x + box_w, y + box_h], radius=radius, fill=bg_color, outline=border_color, width=2)
    draw.text((x + pad_x, y + pad_y - 2), text, font=font, fill=text_color)
    return (x, y, x + box_w, y + box_h)


# ===========================================================================
# 5 BẢNG MÀU THƯƠNG HIỆU ĐA DẠNG (COLOR MOOD PALETTES)
# ===========================================================================
COLOR_PALETTES = {
    "royal_sapphire": {
        "name": "Royal Sapphire (Sao Việt Classic)",
        "bg_primary": (11, 35, 65),       # Deep Navy
        "bg_secondary": (18, 56, 102),    # Mid Navy
        "card_bg": (14, 42, 78, 235),
        "accent_gold": (255, 215, 0),     # Gold
        "accent_cyan": (0, 212, 255),     # Cyan
        "badge_bg": (230, 81, 0),         # Orange
        "text_main": "#FFFFFF",
        "text_sub": "#FFD54F",
        "text_muted": "#CBD5E1",
    },
    "ruby_urgency": {
        "name": "Ruby Urgency (Cấp Tốc / Ưu Đãi Lớn)",
        "bg_primary": (64, 10, 20),       # Deep Ruby
        "bg_secondary": (96, 16, 32),     # Mid Ruby
        "card_bg": (80, 14, 28, 235),
        "accent_gold": (255, 204, 0),     # Bright Gold
        "accent_cyan": (255, 112, 67),    # Coral Orange
        "badge_bg": (213, 0, 0),          # Pure Ruby Red
        "text_main": "#FFFFFF",
        "text_sub": "#FFE082",
        "text_muted": "#F1F5F9",
    },
    "cosmic_violet": {
        "name": "Cosmic Violet (Công Nghệ AI & Tương Lai)",
        "bg_primary": (24, 14, 48),       # Deep Cosmic Violet
        "bg_secondary": (44, 24, 86),     # Mid Violet
        "card_bg": (38, 20, 75, 235),
        "accent_gold": (255, 215, 0),     # Gold
        "accent_cyan": (0, 242, 254),     # Neon Aqua
        "badge_bg": (124, 58, 237),       # Royal Purple
        "text_main": "#FFFFFF",
        "text_sub": "#A7F3D0",
        "text_muted": "#E0E7FF",
    },
    "emerald_growth": {
        "name": "Emerald Growth (Kỹ Năng & Thăng Tiến)",
        "bg_primary": (8, 42, 34),        # Deep Emerald
        "bg_secondary": (16, 72, 58),     # Mid Emerald
        "card_bg": (12, 58, 46, 235),
        "accent_gold": (255, 215, 0),     # Gold
        "accent_cyan": (0, 230, 118),     # Mint Green
        "badge_bg": (230, 81, 0),         # Amber Orange
        "text_main": "#FFFFFF",
        "text_sub": "#69F0AE",
        "text_muted": "#E2E8F0",
    },
    "warm_editorial": {
        "name": "Warm Editorial (Thanh Lịch / Doanh Nhân)",
        "bg_primary": (36, 26, 22),       # Deep Espresso
        "bg_secondary": (64, 44, 36),     # Warm Mocha
        "card_bg": (52, 36, 28, 235),
        "accent_gold": (255, 183, 77),    # Amber
        "accent_cyan": (255, 138, 101),   # Warm Terra
        "badge_bg": (194, 65, 12),        # Rust Orange
        "text_main": "#FFFFFF",
        "text_sub": "#FEF3C7",
        "text_muted": "#F5F5F4",
    },
}


# ===========================================================================
# CÁC TEMPLATES ĐỒ HỌA THỰC CHIẾN CHUẨN FACEBOOK 1:1 (2000x2000)
# ===========================================================================

def render_template_split_right(
    classroom_img: Image.Image,
    logo_path: Optional[Path] = None,
    title: str = "TIN HỌC VĂN PHÒNG",
    subtitle: Optional[str] = None,
    highlights: Optional[List[str]] = None,
    badge_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    hotline: Optional[str] = None,
    brand_color: Tuple[int, int, int] = (11, 35, 65),
    **kwargs,
) -> Image.Image:
    """Mẫu split_right chia đôi ảnh đã được chuyển hướng sang Photo-First Cinematic
    để không bao giờ cắt đôi người hay để khoảng trống trơ trọi."""
    return render_template_photo_first_cinematic(
        classroom_img=classroom_img,
        logo_path=logo_path,
        title=title,
        subtitle=subtitle,
        highlights=highlights,
        badge_text=badge_text,
        footer_text=footer_text,
        hotline=hotline,
        brand_color=brand_color,
    )


def render_template_split_left(
    classroom_img: Image.Image,
    logo_path: Optional[Path] = None,
    title: str = "TIN HỌC VĂN PHÒNG",
    subtitle: Optional[str] = None,
    highlights: Optional[List[str]] = None,
    badge_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    hotline: Optional[str] = None,
    brand_color: Tuple[int, int, int] = (11, 35, 65),
    **kwargs,
) -> Image.Image:
    """Mẫu split_left chia đôi ảnh đã được chuyển hướng sang Modern Ribbon Wave
    để layout hài hòa chuẩn poster Sao Việt thương hiệu."""
    return render_template_modern_ribbon_wave(
        classroom_img=classroom_img,
        logo_path=logo_path,
        title=title,
        subtitle=subtitle,
        highlights=highlights,
        badge_text=badge_text,
        footer_text=footer_text,
        hotline=hotline,
        brand_color=brand_color,
    )


def render_template_bottom_bar(
    classroom_img: Image.Image,
    logo_path: Optional[Path] = None,
    title: str = "TIN HỌC VĂN PHÒNG",
    subtitle: Optional[str] = None,
    highlights: Optional[List[str]] = None,
    badge_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    hotline: Optional[str] = None,
    brand_color: Tuple[int, int, int] = (11, 35, 65),
) -> Image.Image:
    """Template 3: Ảnh thật góc rộng chiếm 60% trên, khối chân trang SOLID navy 40% phía dưới (cấm đè chữ lên người)."""
    W, H = 2000, 2000
    canvas = Image.new("RGBA", (W, H), (brand_color[0], brand_color[1], brand_color[2], 255))

    has_hl = bool(highlights and len(highlights) > 0)
    top_h = 1240 if has_hl else 1340
    top_img = smart_crop_and_enhance(classroom_img, W, top_h)
    canvas.paste(top_img, (0, 0))

    if logo_path:
        badge_w, badge_h = 320, 110
        paste_brand_logo(canvas, logo_path, (70, 70, 70 + badge_w, 70 + badge_h), bg_badge=True)

    draw = ImageDraw.Draw(canvas)
    if badge_text:
        font_badge = get_font(34, bold=True)
        draw_pill_badge(draw, badge_text, W - 460, 85, font_badge,
                        bg_color=(230, 81, 0, 245), border_color=(255, 215, 0, 255))

    draw.line([(0, top_h), (W, top_h)], fill=(255, 215, 0, 220), width=6)

    curr_y = top_h + (35 if has_hl else 55)

    start_sz = 72 if has_hl else 80
    font_title, title_lines = fit_title_font(draw, title, W - 180, 220, start_size=start_sz, min_size=48)
    for line in title_lines:
        bb = draw.textbbox((0, 0), line, font=font_title)
        lw = bb[2] - bb[0]
        draw.text(((W - lw) // 2, curr_y), line, font=font_title, fill="#FFFFFF")
        curr_y += (bb[3] - bb[1]) + 15

    if subtitle:
        font_sub = get_font(40, bold=True)
        bb = draw.textbbox((0, 0), subtitle, font=font_sub)
        sw = bb[2] - bb[0]
        draw.text(((W - sw) // 2, curr_y), subtitle, font=font_sub, fill="#FFD54F")
        curr_y += (bb[3] - bb[1]) + 30

    if has_hl:
        font_pill = get_font(32, bold=True)
        if len(highlights) == 1:
            p1 = highlights[0]
            bb1 = draw.textbbox((0, 0), f"•  {p1}", font=font_pill)
            pw1 = bb1[2] - bb1[0] + 60
            x1 = (W - pw1) // 2
            pill_y = curr_y + 10
            draw.rounded_rectangle([x1, pill_y, x1 + pw1, pill_y + 70], radius=35, fill=(20, 50, 90, 255), outline=(255, 215, 0, 180), width=2)
            draw.text((x1 + 30, pill_y + 15), f"•  {p1}", font=font_pill, fill="#FFFFFF")
        else:
            p1 = highlights[0]
            p2 = highlights[1]
            bb1 = draw.textbbox((0, 0), f"•  {p1}", font=font_pill)
            bb2 = draw.textbbox((0, 0), f"•  {p2}", font=font_pill)
            pw1 = bb1[2] - bb1[0] + 60
            pw2 = bb2[2] - bb2[0] + 60
            spacing = 40
            tot_w = pw1 + pw2 + spacing
            x1 = (W - tot_w) // 2
            x2 = x1 + pw1 + spacing
            pill_y = curr_y + 10
            draw.rounded_rectangle([x1, pill_y, x1 + pw1, pill_y + 70], radius=35, fill=(20, 50, 90, 255), outline=(255, 215, 0, 180), width=2)
            draw.text((x1 + 30, pill_y + 15), f"•  {p1}", font=font_pill, fill="#FFFFFF")
            draw.rounded_rectangle([x2, pill_y, x2 + pw2, pill_y + 70], radius=35, fill=(20, 50, 90, 255), outline=(255, 215, 0, 180), width=2)
            draw.text((x2 + 30, pill_y + 15), f"•  {p2}", font=font_pill, fill="#FFFFFF")

    font_ft = get_font(30, bold=True)
    ft_line = None
    if footer_text and hotline:
        ft_line = f"{footer_text.upper()}  •  HOTLINE: {hotline}"
    elif footer_text:
        ft_line = footer_text.upper()
    elif hotline:
        ft_line = f"HOTLINE / ZALO: {hotline}"

    if ft_line:
        f_bb = draw.textbbox((0, 0), ft_line, font=font_ft)
        draw.text(((W - (f_bb[2] - f_bb[0])) // 2, H - 75), ft_line, font=font_ft, fill="#CBD5E1")

    return canvas.convert("RGB")



def render_template_floating_card(
    classroom_img: Image.Image,
    logo_path: Optional[Path] = None,
    title: str = "TIN HỌC VĂN PHÒNG",
    subtitle: Optional[str] = None,
    highlights: Optional[List[str]] = None,
    badge_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    hotline: Optional[str] = None,
    brand_color: Tuple[int, int, int] = (11, 35, 65),
) -> Image.Image:
    """Template 4: Ảnh lớp học tràn nền 100%, Card nổi khối 3D bo góc ở bên phải."""
    W, H = 2000, 2000
    base = smart_crop_and_enhance(classroom_img, W, H).convert("RGBA")

    # Card kính nổi bên phải
    card_x1 = 980
    card_y1 = 90
    card_x2 = W - 70
    card_y2 = H - 90

    # Đổ bóng mềm mại cho card
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([card_x1 - 15, card_y1 - 10, card_x2 + 15, card_y2 + 20], radius=36, fill=(0, 0, 0, 130))
    shadow = shadow.filter(ImageFilter.GaussianBlur(25))
    base = Image.alpha_composite(base, shadow)

    # Thân card
    card_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card_layer)
    cd.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=30,
                         fill=(brand_color[0], brand_color[1], brand_color[2], 245),
                         outline=(255, 215, 0, 210), width=3)
    base = Image.alpha_composite(base, card_layer)

    draw = ImageDraw.Draw(base)

    # Logo trên đỉnh card
    if logo_path:
        badge_w, badge_h = 300, 105
        paste_brand_logo(base, logo_path, (card_x1 + 50, card_y1 + 45, card_x1 + 50 + badge_w, card_y1 + 45 + badge_h), bg_badge=True)

    # Badge ưu đãi
    if badge_text:
        font_badge = get_font(30, bold=True)
        draw_pill_badge(draw, badge_text, card_x2 - 380, card_y1 + 60, font_badge,
                        bg_color=(230, 81, 0, 245), border_color=(255, 215, 0, 255))

    # Tiêu đề khóa học
    max_text_w = (card_x2 - card_x1) - 100
    has_hl = bool(highlights and len(highlights) > 0)
    curr_y = card_y1 + (190 if badge_text else 140)
    start_sz = 70 if has_hl else 80
    font_title, title_lines = fit_title_font(draw, title, max_text_w, 480 if not has_hl else 400, start_size=start_sz, min_size=46)
    for line in title_lines:
        draw.text((card_x1 + 50, curr_y), line, font=font_title, fill="#FFFFFF")
        bb = draw.textbbox((0, 0), line, font=font_title)
        curr_y += (bb[3] - bb[1]) + (22 if not has_hl else 18)

    curr_y += 20
    draw.line([(card_x1 + 50, curr_y), (card_x1 + 350, curr_y)], fill=(255, 193, 7, 220), width=4)
    curr_y += 40

    if subtitle:
        font_sub = get_font(40 if not has_hl else 38, bold=True)
        sub_lines = wrap_text(draw, subtitle, font_sub, max_text_w)
        for sline in sub_lines:
            draw.text((card_x1 + 50, curr_y), sline, font=font_sub, fill="#FFD54F")
            bb = draw.textbbox((0, 0), sline, font=font_sub)
            curr_y += (bb[3] - bb[1]) + 15
        curr_y += 35

    if has_hl:
        font_hl = get_font(32, bold=True)
        for hl in highlights[:4]:
            hl_text = f"•  {hl}"
            hl_lines = wrap_text(draw, hl_text, font_hl, max_text_w)
            for hline in hl_lines:
                draw.text((card_x1 + 50, curr_y), hline, font=font_hl, fill="#F1F5F9")
                bb = draw.textbbox((0, 0), hline, font=font_hl)
                curr_y += (bb[3] - bb[1]) + 14
            curr_y += 18

    # Hotline box
    if hotline:
        box_y = card_y2 - (200 if footer_text else 140)
        draw.rounded_rectangle([card_x1 + 50, box_y, card_x2 - 50, box_y + 95], radius=16,
                               fill=(22, 54, 98, 230), outline=(255, 215, 0, 160), width=2)
        font_hl_b = get_font(32, bold=True)
        draw.text((card_x1 + 80, box_y + 28), f"Hotline / Zalo: {hotline}", font=font_hl_b, fill="#FFEB3B")

    if footer_text:
        font_ft = get_font(26, bold=True)
        draw.text((card_x1 + 50, card_y2 - 65), footer_text.upper(), font=font_ft, fill="#94A3B8")

    return base.convert("RGB")


def render_template_diagonal_slice(
    classroom_img: Image.Image,
    logo_path: Optional[Path] = None,
    title: str = "TIN HỌC VĂN PHÒNG & ỨNG DỤNG AI",
    subtitle: Optional[str] = None,
    highlights: Optional[List[str]] = None,
    badge_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    hotline: Optional[str] = None,
    brand_color: Tuple[int, int, int] = (8, 22, 45),
) -> Image.Image:
    """Template 5: Vát chéo công nghệ Agency (Diagonal Slant) chuẩn quốc tế:
    - Ảnh thật cắt vát góc động sắc nét, viền neon kép phát sáng vàng kim và xanh cyan.
    - Nền Deep Navy với họa tiết tech grid tinh tế.
    - Logo Sao Việt to rõ trên thẻ nổi khối 3D góc trên trái.
    - Tiêu đề Hero 2 tầng khổng lồ, bóng đổ 3D, vạch mạ vàng sang trọng.
    - Hộp quyền lợi chuyên nghiệp có icon checkmark màu sắc.
    - Dải hotline cam rực rỡ thu hút người nhìn."""
    W, H = 2000, 2000
    canvas = Image.new("RGBA", (W, H), (brand_color[0], brand_color[1], brand_color[2], 255))

    rw, rh = classroom_img.size
    scale = max(W / rw, H / rh)
    nw, nh = int(rw * scale), int(rh * scale)
    raw_res = classroom_img.resize((nw, nh), Image.Resampling.LANCZOS)
    xo = (nw - W) // 2
    yo = (nh - H) // 2
    photo_cropped = raw_res.crop((xo, yo, xo + W, yo + H)).convert("RGBA")

    slant_top = 1080
    slant_bot = 680
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.polygon([(0, 0), (slant_top, 0), (slant_bot, H), (0, H)], fill=255)
    canvas.paste(photo_cropped, (0, 0), mask)

    draw = ImageDraw.Draw(canvas)
    for w_glow, alpha in [(24, 30), (14, 70), (8, 140), (4, 255)]:
        draw.line([(slant_top, 0), (slant_bot, H)], fill=(255, 215, 0, alpha), width=w_glow)
    off = 36
    for w_glow, alpha in [(14, 30), (8, 80), (3, 220)]:
        draw.line([(slant_top + off, 0), (slant_bot + off, H)], fill=(0, 212, 255, alpha), width=w_glow)

    for gx in range(1180, W - 60, 60):
        for gy in range(80, H - 120, 60):
            draw.ellipse([gx - 2, gy - 2, gx + 2, gy + 2], fill=(255, 255, 255, 20))

    if logo_path:
        paste_brand_logo(canvas, logo_path, (70, 70, 450, 200), bg_badge=True)

    if badge_text:
        font_badge = get_font(34, bold=True)
        badge_w, badge_h = 430, 95
        bx = W - badge_w - 70
        by = 75
        draw_pill_badge(draw, badge_text, bx, by, font_badge,
                        bg_color=(230, 81, 0, 250), border_color=(255, 215, 0, 255),
                        pad_x=28, pad_y=16, radius=badge_h // 2)

    cx = 1140
    cw = W - cx - 70
    has_hl = bool(highlights and len(highlights) > 0)

    font_t, t_lines = fit_title_font(draw, title, cw, 280 if not has_hl else 220, start_size=74 if not has_hl else 66, min_size=42)
    title_y = 240 if badge_text else 170
    curr_y = title_y
    for i, tline in enumerate(t_lines):
        col = "#FFFFFF" if i == 0 else "#FFD54F"
        draw.text((cx + 3, curr_y + 3), tline, font=font_t, fill=(0, 0, 0, 180))
        draw.text((cx, curr_y), tline, font=font_t, fill=col)
        bb = draw.textbbox((0, 0), tline, font=font_t)
        curr_y += (bb[3] - bb[1]) + 16

    sep_y = curr_y + 15
    draw.line([(cx, sep_y), (cx + 380, sep_y)], fill=(255, 215, 0, 240), width=5)
    draw.line([(cx + 390, sep_y), (cx + 420, sep_y)], fill=(0, 212, 255, 220), width=5)

    if subtitle:
        font_sub = get_font(36, bold=True)
        draw.text((cx, sep_y + 26), subtitle.upper(), font=font_sub, fill="#E2E8F0")

    cards_start_y = sep_y + (95 if subtitle else 40)
    card_h = 105
    gap = 22

    if has_hl:
        colors = [(255, 171, 0), (0, 230, 118), (64, 196, 255)]
        for i, hl in enumerate(highlights[:3]):
            fc_y = cards_start_y + i * (card_h + gap)
            draw.rounded_rectangle([cx, fc_y, cx + cw, fc_y + card_h], radius=16,
                                   fill=(14, 38, 72, 220), outline=(255, 215, 0, 130), width=2)
            sq_size = 65
            sq_x = cx + 20
            sq_y = fc_y + (card_h - sq_size) // 2
            accent_col = colors[i % len(colors)]
            draw.rounded_rectangle([sq_x, sq_y, sq_x + sq_size, sq_y + sq_size], radius=12, fill=accent_col)
            draw.line([(sq_x + 18, sq_y + 32), (sq_x + 28, sq_y + 44), (sq_x + 48, sq_y + 20)], fill="#08162D", width=6)

            font_ft1 = get_font(30, bold=True)
            font_ft2 = get_font(24, bold=False)
            draw.text((cx + 105, fc_y + 18), hl.upper(), font=font_ft1, fill="#FFFFFF")
            draw.text((cx + 105, fc_y + 56), "Cam kết đào tạo chất lượng cao", font=font_ft2, fill="#CBD5E1")

    if hotline:
        hotline_y = H - 280
        draw.rounded_rectangle([cx, hotline_y, cx + cw, hotline_y + 115], radius=20,
                               fill=(230, 81, 0, 240), outline=(255, 215, 0, 255), width=3)
        font_hl1 = get_font(26, bold=True)
        font_hl2 = get_font(40, bold=True)
        draw.text((cx + 35, hotline_y + 16), "TƯ VẤN LỘ TRÌNH & XẾP LỊCH HỌC NGAY:", font=font_hl1, fill="#FFF8E1")
        draw.text((cx + 35, hotline_y + 52), f"HOTLINE: {hotline}", font=font_hl2, fill="#FFFFFF")

    if footer_text:
        font_bot = get_font(26, bold=True)
        draw.text((cx, H - 90), footer_text.upper(), font=font_bot, fill="#94A3B8")

    return canvas.convert("RGB")


def render_template_curved_window(
    classroom_img: Image.Image,
    logo_path: Optional[Path] = None,
    title: str = "TIN HỌC VĂN PHÒNG & ỨNG DỤNG AI",
    subtitle: Optional[str] = None,
    highlights: Optional[List[str]] = None,
    badge_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    hotline: Optional[str] = None,
    brand_color: Tuple[int, int, int] = (10, 32, 66),
) -> Image.Image:
    """Template 7: Vòng cung nghệ thuật (Curved Inset Window):
    - Ảnh thật đóng khung trong cửa sổ bo góc mềm mại viền đôi mạ vàng phát sáng.
    - Nền Gradient thương hiệu đa sắc sang trọng.
    - Tiêu đề khổng lồ nổi bật bên trái.
    - Điểm nhấn checkmark tròn vàng rực rỡ.
    - Dải Ribbon chân trang màu vàng rực rỡ chứa hotline."""
    W, H = 2000, 2000
    canvas = Image.new("RGBA", (W, H), (brand_color[0], brand_color[1], brand_color[2], 255))
    draw = ImageDraw.Draw(canvas)

    for i in range(H):
        ratio = i / float(H)
        r = min(255, int(brand_color[0] * (1.0 + 0.35 * ratio)))
        g = min(255, int(brand_color[1] * (1.0 + 0.35 * ratio)))
        b = min(255, int(brand_color[2] * (1.0 + 0.35 * ratio)))
        draw.line([(0, i), (W, i)], fill=(r, g, b, 255))

    wx1, wy1, wx2, wy2 = 780, 560, 1930, 1800
    ww = wx2 - wx1
    wh = wy2 - wy1
    rw, rh = classroom_img.size
    scale = max(ww / rw, wh / rh)
    nw, nh = int(rw * scale), int(rh * scale)
    raw_res = classroom_img.resize((nw, nh), Image.Resampling.LANCZOS)
    xo = (nw - ww) // 2
    yo = (nh - wh) // 2
    photo_cropped = raw_res.crop((xo, yo, xo + ww, yo + wh)).convert("RGBA")

    win_mask = Image.new("L", (ww, wh), 0)
    wmd = ImageDraw.Draw(win_mask)
    wmd.rounded_rectangle([0, 0, ww, wh], radius=48, fill=255)

    win_sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wsd = ImageDraw.Draw(win_sh)
    wsd.rounded_rectangle([wx1 + 8, wy1 + 10, wx2 + 8, wy2 + 10], radius=48, fill=(0, 0, 0, 160))
    win_sh = win_sh.filter(ImageFilter.GaussianBlur(20))
    canvas.alpha_composite(win_sh)

    canvas.paste(photo_cropped, (wx1, wy1), win_mask)

    draw.rounded_rectangle([wx1, wy1, wx2, wy2], radius=48, outline=(255, 215, 0, 240), width=5)
    draw.rounded_rectangle([wx1 + 8, wy1 + 8, wx2 - 8, wy2 - 8], radius=40, outline=(0, 212, 255, 180), width=2)

    if logo_path:
        paste_brand_logo(canvas, logo_path, (70, 70, 450, 200), bg_badge=True)

    if badge_text:
        font_badge = get_font(34, bold=True)
        badge_w, badge_h = 430, 95
        bx = W - badge_w - 70
        by = 75
        draw_pill_badge(draw, badge_text, bx, by, font_badge,
                        bg_color=(230, 81, 0, 250), border_color=(255, 215, 0, 255),
                        pad_x=28, pad_y=16, radius=badge_h // 2)

    tx = 70
    tw = 680
    curr_y = 260 if badge_text else 200
    has_hl = bool(highlights and len(highlights) > 0)

    font_t, t_lines = fit_title_font(draw, title, tw, 420 if not has_hl else 360, start_size=70 if not has_hl else 64, min_size=42)
    for i, tline in enumerate(t_lines):
        col = "#FFFFFF" if i == 0 else ("#FFD54F" if i == 1 else "#00E676")
        draw.text((tx + 2, curr_y + 2), tline, font=font_t, fill=(0, 0, 0, 160))
        draw.text((tx, curr_y), tline, font=font_t, fill=col)
        bb = draw.textbbox((0, 0), tline, font=font_t)
        curr_y += (bb[3] - bb[1]) + 16

    draw.line([(tx, curr_y), (tx + 360, curr_y)], fill=(255, 215, 0, 230), width=4)
    curr_y += 30

    if subtitle:
        font_sub = get_font(34, bold=True)
        draw.text((tx, curr_y), subtitle, font=font_sub, fill="#E2E8F0")
        curr_y += 65

    if has_hl:
        font_bl = get_font(30, bold=True)
        for b_text in highlights[:4]:
            circ_r = 24
            cy = curr_y + 16
            draw.ellipse([tx, cy - circ_r, tx + circ_r * 2, cy + circ_r], fill=(255, 215, 0, 250))
            draw.line([(tx + 12, cy), (tx + 20, cy + 10), (tx + 36, cy - 8)], fill="#0A2042", width=5)

            lines = wrap_text(draw, b_text, font_bl, tw - 65)
            ly = curr_y
            for ln in lines:
                draw.text((tx + 65, ly), ln, font=font_bl, fill="#FFFFFF")
                ly += 40
            curr_y = ly + 18

    if hotline or footer_text:
        foot_h = 130
        foot_y = H - foot_h
        draw.rectangle([0, foot_y, W, H], fill=(255, 179, 0, 255))
        draw.line([(0, foot_y), (W, foot_y)], fill=(255, 235, 59, 255), width=5)

        font_f1 = get_font(38, bold=True)
        font_f2 = get_font(30, bold=True)
        if hotline and footer_text:
            draw.text((80, foot_y + 24), f"LIÊN HỆ TƯ VẤN & XẾP LỊCH: {hotline}", font=font_f1, fill="#0A1A30")
            draw.text((80, foot_y + 75), footer_text.upper(), font=font_f2, fill="#1E293B")
        elif hotline:
            draw.text((80, foot_y + 40), f"HOTLINE / ZALO: {hotline}", font=font_f1, fill="#0A1A30")
        elif footer_text:
            draw.text((80, foot_y + 45), footer_text.upper(), font=font_f2, fill="#1E293B")

    return canvas.convert("RGB")


def render_template_3d_pills(
    classroom_img: Image.Image,
    logo_path: Optional[Path] = None,
    title: str = "TIN HỌC VĂN PHÒNG",
    subtitle: Optional[str] = None,
    highlights: Optional[List[str]] = None,
    badge_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    hotline: Optional[str] = None,
    brand_color: Tuple[int, int, int] = (11, 35, 65),
    **kwargs,
) -> Image.Image:
    """Mẫu 3d_pills chia cắt ảnh học viên và để panel trống phản cảm đã được LOẠI BỎ vĩnh viễn.
    Tự động chuyển sang Modern Ribbon Wave để đảm bảo 100% banner đẹp sang trọng chuẩn Sao Việt."""
    return render_template_modern_ribbon_wave(
        classroom_img=classroom_img,
        logo_path=logo_path,
        title=title,
        subtitle=subtitle,
        highlights=highlights,
        badge_text=badge_text,
        footer_text=footer_text,
        hotline=hotline,
        brand_color=brand_color,
    )



def render_template_bento_box(
    classroom_img: Image.Image,
    logo_path: Optional[Path] = None,
    title: str = "TIN HỌC VĂN PHÒNG & ỨNG DỤNG AI",
    subtitle: Optional[str] = None,
    highlights: Optional[List[str]] = None,
    badge_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    hotline: Optional[str] = None,
    brand_color: Tuple[int, int, int] = (11, 35, 65),
    palette: Optional[dict] = None,
) -> Image.Image:
    """Template 8: Bento Box Grid hiện đại chuẩn Agency 2026:
    - Chia ô lưới Bento Grid bất đối xứng, tối ưu hóa hiển thị trên Facebook/Instagram 1:1.
    - Ô 1 (Header): Thẻ Logo 3D và Dải thông tin tuyển sinh / hotline.
    - Ô 2 (Hero Content Card, Trái): Tiêu đề khóa học nổi bật, thẻ quyền lợi và nút CTA hành động.
    - Ô 3 (Hero Photo Window, Phải): Cửa sổ ảnh thật lớp học bo tròn góc lớn với badge tem dán nổi.
    - Ô 4, 5, 6 (Bento Stat Cards, Chân trang): 3 Thẻ thông số nổi bật (Kèm 1-1, 100% Thực hành, Hotline tư vấn).
    - Ô 7 (Footer): Dải ribbon thương hiệu sang trọng."""
    W, H = 2000, 2000
    pal = palette or COLOR_PALETTES.get("royal_sapphire", {})
    bg_p = brand_color or pal.get("bg_primary", (11, 35, 65))
    bg_s = pal.get("bg_secondary", (bg_p[0] + 8, bg_p[1] + 16, bg_p[2] + 28))
    card_bg = pal.get("card_bg", (bg_p[0] + 4, bg_p[1] + 8, bg_p[2] + 16, 235))
    accent_g = pal.get("accent_gold", (255, 215, 0))
    accent_c = pal.get("accent_cyan", (0, 212, 255))
    badge_c = pal.get("badge_bg", (230, 81, 0))
    txt_sub = pal.get("text_sub", "#FFD54F")

    canvas = Image.new("RGBA", (W, H), (bg_p[0], bg_p[1], bg_p[2], 255))
    draw = ImageDraw.Draw(canvas)

    # 1. Gradient nền mượt mà
    for y in range(H):
        ratio = y / float(H)
        r = int(bg_p[0] + (bg_s[0] - bg_p[0]) * ratio)
        g = int(bg_p[1] + (bg_s[1] - bg_p[1]) * ratio)
        b = int(bg_p[2] + (bg_s[2] - bg_p[2]) * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b, 255))

    # Họa tiết chấm lưới công nghệ tinh tế
    for gx in range(60, W - 40, 70):
        for gy in range(60, H - 40, 70):
            draw.ellipse([gx - 2, gy - 2, gx + 2, gy + 2], fill=(255, 255, 255, 18))

    # Helper đổ bóng card
    def drop_card_shadow(x1, y1, x2, y2, radius=24, alpha=130):
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle([x1 + 4, y1 + 8, x2 + 4, y2 + 8], radius=radius, fill=(0, 0, 0, alpha))
        sh = sh.filter(ImageFilter.GaussianBlur(16))
        canvas.alpha_composite(sh)

    # -------------------------------------------------------------
    # ROW 1: HEADER & LOGO BENTO (y: 60 -> 190, h: 130)
    # -------------------------------------------------------------
    # Ô 1A: Logo card bên trái (60, 60, 480, 190)
    if logo_path:
        paste_brand_logo(canvas, logo_path, (60, 60, 480, 190), bg_badge=True)

    # Ô 1B: Header info card bên phải (510, 60, 1940, 190)
    hx1, hy1, hx2, hy2 = 510, 60, 1940, 190
    drop_card_shadow(hx1, hy1, hx2, hy2, radius=20, alpha=110)
    draw.rounded_rectangle([hx1, hy1, hx2, hy2], radius=20, fill=card_bg, outline=(accent_g[0], accent_g[1], accent_g[2], 160), width=2)

    font_hd1 = get_font(30, bold=True)
    draw_pill_badge(draw, "TUYỂN SINH MỚI", hx1 + 30, hy1 + 34, font_hd1,
                    bg_color=(badge_c[0], badge_c[1], badge_c[2], 240),
                    border_color=(accent_g[0], accent_g[1], accent_g[2], 255),
                    pad_x=22, pad_y=10, radius=16)

    font_hd2 = get_font(34, bold=True)
    brand_line = f"{footer_text.upper()} • ĐÀO TẠO THỰC CHIẾN" if footer_text else "ĐÀO TẠO THỰC CHIẾN CHUYÊN NGHIỆP"
    draw.text((hx1 + 320, hy1 + 42), brand_line, font=font_hd2, fill="#FFFFFF")

    # -------------------------------------------------------------
    # ROW 2: HERO SPLIT BENTO (y: 220 -> 1360, h: 1140)
    # -------------------------------------------------------------
    # Ô 2 (Hero Content Card, Trái): (60, 220, 980, 1360)
    cx1, cy1, cx2, cy2 = 60, 220, 980, 1360
    cw = cx2 - cx1
    drop_card_shadow(cx1, cy1, cx2, cy2, radius=32, alpha=140)
    draw.rounded_rectangle([cx1, cy1, cx2, cy2], radius=32, fill=card_bg, outline=(accent_g[0], accent_g[1], accent_g[2], 180), width=3)

    inner_x = cx1 + 50
    inner_w = cw - 100
    curr_y = cy1 + 50

    # Badge Ưu Đãi
    if badge_text:
        font_badge = get_font(30, bold=True)
        draw_pill_badge(draw, badge_text.upper(), inner_x, curr_y, font_badge,
                        bg_color=(badge_c[0], badge_c[1], badge_c[2], 245),
                        border_color=(accent_g[0], accent_g[1], accent_g[2], 255),
                        pad_x=26, pad_y=12, radius=18)
        curr_y += 90

    # Tiêu đề khóa học lớn
    has_hl = bool(highlights and len(highlights) > 0)
    font_t, t_lines = fit_title_font(draw, title, inner_w, 420 if not has_hl else 360, start_size=74 if not has_hl else 68, min_size=44)
    for tline in t_lines:
        draw.text((inner_x + 2, curr_y + 2), tline, font=font_t, fill=(0, 0, 0, 160))
        draw.text((inner_x, curr_y), tline, font=font_t, fill="#FFFFFF")
        bb = draw.textbbox((0, 0), tline, font=font_t)
        curr_y += (bb[3] - bb[1]) + 16

    # Vạch phân cách mạ vàng và cyan
    curr_y += 10
    draw.line([(inner_x, curr_y), (inner_x + 300, curr_y)], fill=(accent_g[0], accent_g[1], accent_g[2], 230), width=4)
    draw.line([(inner_x + 315, curr_y), (inner_x + 360, curr_y)], fill=(accent_c[0], accent_c[1], accent_c[2], 230), width=4)
    curr_y += 30

    # Subtitle
    if subtitle:
        font_sb = get_font(34, bold=True)
        s_lines = wrap_text(draw, subtitle, font_sb, inner_w)
        for sline in s_lines:
            draw.text((inner_x, curr_y), sline, font=font_sb, fill=txt_sub)
            bb = draw.textbbox((0, 0), sline, font=font_sb)
            curr_y += (bb[3] - bb[1]) + 14
        curr_y += 24

    # Bullet Lợi ích thực tế (Chỉ vẽ khi có highlights)
    if has_hl:
        font_bl = get_font(30, bold=True)
        for b_item in highlights[:3]:
            cr = 20
            cy_b = curr_y + 14
            draw.ellipse([inner_x, cy_b - cr, inner_x + cr * 2, cy_b + cr], fill=(accent_g[0], accent_g[1], accent_g[2], 255))
            draw.line([(inner_x + 10, cy_b), (inner_x + 17, cy_b + 8), (inner_x + 31, cy_b - 6)], fill="#0B2341", width=4)

            b_lines = wrap_text(draw, b_item, font_bl, inner_w - 60)
            ly = curr_y
            for bline in b_lines:
                draw.text((inner_x + 55, ly), bline, font=font_bl, fill="#F8FAFC")
                ly += 38
            curr_y = ly + 14

    # Nút CTA bên trong Hero Card
    cta_y = cy2 - 130
    draw.rounded_rectangle([inner_x, cta_y, inner_x + inner_w, cta_y + 85], radius=18,
                           fill=(accent_g[0], accent_g[1], accent_g[2], 255),
                           outline=(255, 255, 255, 220), width=2)
    font_cta = get_font(32, bold=True)
    cta_txt = "ĐĂNG KÝ HỌC NGAY • XẾP LỚP TRONG NGÀY"
    c_bb = draw.textbbox((0, 0), cta_txt, font=font_cta)
    c_w = c_bb[2] - c_bb[0]
    draw.text((inner_x + (inner_w - c_w) // 2, cta_y + 23), cta_txt, font=font_cta, fill="#0A1A30")

    # Ô 3 (Hero Photo Window, Phải): (1010, 220, 1940, 1360)
    px1, py1, px2, py2 = 1010, 220, 1940, 1360
    pw = px2 - px1
    ph = py2 - py1
    drop_card_shadow(px1, py1, px2, py2, radius=32, alpha=150)

    # Resize crop ảnh lớp học
    rw, rh = classroom_img.size
    scale = max(pw / rw, ph / rh)
    nw, nh = int(rw * scale), int(rh * scale)
    raw_res = classroom_img.resize((nw, nh), Image.Resampling.LANCZOS)
    xo = (nw - pw) // 2
    yo = (nh - ph) // 2
    photo_cropped = raw_res.crop((xo, yo, xo + pw, yo + ph)).convert("RGBA")

    photo_mask = Image.new("L", (pw, ph), 0)
    pmd = ImageDraw.Draw(photo_mask)
    pmd.rounded_rectangle([0, 0, pw, ph], radius=32, fill=255)
    canvas.paste(photo_cropped, (px1, py1), photo_mask)

    # Viền đôi mạ vàng phát sáng
    draw.rounded_rectangle([px1, py1, px2, py2], radius=32, outline=(accent_g[0], accent_g[1], accent_g[2], 240), width=5)
    draw.rounded_rectangle([px1 + 8, py1 + 8, px2 - 8, py2 - 8], radius=24, outline=(accent_c[0], accent_c[1], accent_c[2], 190), width=2)

    # Sticker cam kết trên ảnh thật
    st_w, st_h = 440, 95
    st_x = px2 - st_w - 30
    st_y = py1 + 30
    draw.rounded_rectangle([st_x, st_y, st_x + st_w, st_y + st_h], radius=st_h // 2,
                           fill=(0, 0, 0, 210), outline=(accent_g[0], accent_g[1], accent_g[2], 255), width=3)
    font_st = get_font(28, bold=True)
    st_txt = "CAM KẾT THÀNH THẠO 100%"
    st_bb = draw.textbbox((0, 0), st_txt, font=font_st)
    draw.text((st_x + (st_w - (st_bb[2] - st_bb[0])) // 2, st_y + 30), st_txt, font=font_st, fill="#FFEB3B")

    # -------------------------------------------------------------
    # ROW 3: 3 BENTO STAT CARDS (y: 1390 -> 1810, h: 420)
    # -------------------------------------------------------------
    # Card 4 (Left): Kèm 1-1 (60, 1390, 660, 1810) - W=600
    k1_x1, k1_y1, k1_x2, k1_y2 = 60, 1390, 660, 1810
    drop_card_shadow(k1_x1, k1_y1, k1_x2, k1_y2, radius=24, alpha=120)
    draw.rounded_rectangle([k1_x1, k1_y1, k1_x2, k1_y2], radius=24, fill=card_bg,
                           outline=(accent_g[0], accent_g[1], accent_g[2], 170), width=2)
    font_tag = get_font(24, bold=True)
    draw.text((k1_x1 + 35, k1_y1 + 35), "PHƯƠNG PHÁP ĐÀO TẠO", font=font_tag, fill=txt_sub)
    font_stat = get_font(56, bold=True)
    draw.text((k1_x1 + 35, k1_y1 + 75), "KÈM 1 - 1", font=font_stat, fill="#FFFFFF")
    draw.line([(k1_x1 + 35, k1_y1 + 160), (k1_x1 + 220, k1_y1 + 160)], fill=(accent_g[0], accent_g[1], accent_g[2], 220), width=3)
    font_desc = get_font(26, bold=False)
    d_lines1 = wrap_text(draw, "Giảng viên hướng dẫn trực tiếp từng học viên. Không lo hổng kiến thức, học theo đúng tốc độ của bạn.", font_desc, 530)
    dy = k1_y1 + 185
    for dl in d_lines1:
        draw.text((k1_x1 + 35, dy), dl, font=font_desc, fill="#CBD5E1")
        dy += 34

    # Card 5 (Center): 100% Thực hành (690, 1390, 1310, 1810) - W=620
    k2_x1, k2_y1, k2_x2, k2_y2 = 690, 1390, 1310, 1810
    drop_card_shadow(k2_x1, k2_y1, k2_x2, k2_y2, radius=24, alpha=120)
    draw.rounded_rectangle([k2_x1, k2_y1, k2_x2, k2_y2], radius=24, fill=card_bg,
                           outline=(accent_c[0], accent_c[1], accent_c[2], 170), width=2)
    draw.text((k2_x1 + 35, k2_y1 + 35), "TIÊU CHUẨN THỰC CHIẾN", font=font_tag, fill="#69F0AE")
    draw.text((k2_x1 + 35, k2_y1 + 75), "100% THỰC HÀNH", font=font_stat, fill="#00E676")
    draw.line([(k2_x1 + 35, k2_y1 + 160), (k2_x1 + 280, k2_y1 + 160)], fill=(accent_c[0], accent_c[1], accent_c[2], 220), width=3)
    d_lines2 = wrap_text(draw, "Thực hành ngay trên máy tính cấu hình cao. Bộ bài tập & biểu mẫu doanh nghiệp thực tế 2026.", font_desc, 550)
    dy = k2_y1 + 185
    for dl in d_lines2:
        draw.text((k2_x1 + 35, dy), dl, font=font_desc, fill="#CBD5E1")
        dy += 34

    # Card 6 (Right): Hotline tư vấn (1340, 1390, 1940, 1810) - W=600
    k3_x1, k3_y1, k3_x2, k3_y2 = 1340, 1390, 1940, 1810
    drop_card_shadow(k3_x1, k3_y1, k3_x2, k3_y2, radius=24, alpha=140)
    if hotline:
        draw.rounded_rectangle([k3_x1, k3_y1, k3_x2, k3_y2], radius=24,
                               fill=(badge_c[0], badge_c[1], badge_c[2], 240),
                               outline=(accent_g[0], accent_g[1], accent_g[2], 255), width=3)
        font_hl_tag = get_font(26, bold=True)
        draw.text((k3_x1 + 35, k3_y1 + 32), "TƯ VẤN LỘ TRÌNH & XẾP LỊCH:", font=font_hl_tag, fill="#FFF8E1")
        font_phone = get_font(46, bold=True)
        draw.text((k3_x1 + 35, k3_y1 + 75), "HOTLINE / ZALO", font=get_font(28, bold=True), fill="#FFE082")
        draw.text((k3_x1 + 35, k3_y1 + 115), hotline, font=font_phone, fill="#FFFFFF")
        draw.line([(k3_x1 + 35, k3_y1 + 185), (k3_x1 + 350, k3_y1 + 185)], fill=(255, 255, 255, 180), width=2)
        font_sm = get_font(24, bold=True)
        draw.text((k3_x1 + 35, k3_y1 + 205), "ĐÀO TẠO KÈM 1-1 THỰC CHIẾN", font=font_sm, fill="#FFF9C4")
        draw.text((k3_x1 + 35, k3_y1 + 242), "KHAI GIẢNG HÀNG TUẦN", font=font_sm, fill="#FFFFFF")
    else:
        draw.rounded_rectangle([k3_x1, k3_y1, k3_x2, k3_y2], radius=24,
                               fill=card_bg,
                               outline=(accent_g[0], accent_g[1], accent_g[2], 200), width=3)
        font_hl_tag = get_font(26, bold=True)
        draw.text((k3_x1 + 35, k3_y1 + 35), "CHẤT LƯỢNG ĐÀO TẠO", font=font_hl_tag, fill=txt_sub)
        font_stat = get_font(50, bold=True)
        draw.text((k3_x1 + 35, k3_y1 + 75), "UY TÍN 10 NĂM", font=font_stat, fill="#FFFFFF")
        draw.line([(k3_x1 + 35, k3_y1 + 160), (k3_x1 + 280, k3_y1 + 160)], fill=(accent_g[0], accent_g[1], accent_g[2], 220), width=3)
        font_desc = get_font(26, bold=False)
        d_lines3 = wrap_text(draw, "Hệ thống cơ sở hiện đại, phòng máy lạnh cấu hình cao, giảng viên nhiệt tình hỗ trợ trọn đời.", font_desc, 530)
        dy = k3_y1 + 185
        for dl in d_lines3:
            draw.text((k3_x1 + 35, dy), dl, font=font_desc, fill="#CBD5E1")
            dy += 34

    # -------------------------------------------------------------
    # ROW 4: FOOTER RIBBON (y: 1840 -> 1940, h: 100)
    # -------------------------------------------------------------
    fx1, fy1, fx2, fy2 = 60, 1840, 1940, 1940
    draw.rounded_rectangle([fx1, fy1, fx2, fy2], radius=16, fill=(10, 20, 36, 250),
                           outline=(accent_g[0], accent_g[1], accent_g[2], 140), width=2)
    font_ft = get_font(28, bold=True)
    ft_msg = f"{footer_text.upper()} • CAM KẾT ĐẦU RA UY TÍN" if footer_text else "CAM KẾT ĐÀO TẠO THỰC CHIẾN • HỌC ĐẾN KHI THÀNH THẠO"
    ft_bb = draw.textbbox((0, 0), ft_msg, font=font_ft)
    draw.text((fx1 + (1880 - (ft_bb[2] - ft_bb[0])) // 2, fy1 + 32), ft_msg, font=font_ft, fill="#E2E8F0")

    return canvas.convert("RGB")


def render_template_dual_hexagon(
    classroom_img,
    logo_path=None,
    title="TIN HỌC VĂN PHÒNG",
    subtitle=None,
    highlights=None,
    badge_text=None,
    footer_text=None,
    hotline=None,
    brand_color=(11, 35, 65),
    palette=None,
    **kwargs,
):
    """Mẫu dual_hexagon đã bị loại bỏ hoàn toàn theo yêu cầu người dùng.
    Tự động chuyển hướng sang Photo-First Cinematic để giữ trọn vẹn vẻ đẹp ảnh thật."""
    return render_template_photo_first_cinematic(
        classroom_img=classroom_img,
        logo_path=logo_path,
        title=title,
        subtitle=subtitle,
        highlights=highlights,
        badge_text=badge_text,
        footer_text=footer_text,
        hotline=hotline,
        brand_color=brand_color,
        palette=palette,
    )


def render_template_bauhaus_grid(
    classroom_img: Image.Image,
    logo_path: Optional[Path] = None,
    title: str = "TIN HỌC VĂN PHÒNG & ỨNG DỤNG AI",
    subtitle: Optional[str] = None,
    highlights: Optional[List[str]] = None,
    badge_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    hotline: Optional[str] = None,
    brand_color: Optional[Tuple[int, int, int]] = None,
    palette: Optional[dict] = None,
) -> Image.Image:
    """Template 10: Bauhaus Color Block & Modern Grid (Dựa theo Mẫu 1 Magnific của user).
    - Bố cục lưới kiến trúc Bauhaus (Swiss Grid Architecture).
    - Các khối màu hình học bất đối xứng: Hộp tiêu đề Dark Charcoal/Navy, thanh accent Cobalt Blue.
    - Ảnh lớp học thực tế đóng khung hiện đại với viền sắc nét và khối đế màu offset.
    - Huy hiệu tròn nổi bật (Sticker tròn vàng) hiển thị ưu đãi học phí.
    - Typography chuẩn quốc tế Be Vietnam Pro tương phản cực mạnh, không bao giờ lỗi font."""
    W, H = 2000, 2000
    pal = palette or COLOR_PALETTES.get("royal_sapphire", {})
    bg_p = brand_color or pal.get("bg_primary", (11, 35, 65))
    accent_c = pal.get("accent_cyan", (0, 212, 255))
    accent_g = pal.get("accent_gold", (255, 215, 0))
    badge_c = pal.get("badge_bg", (230, 81, 0))

    # Nền canvas sáng phong cách giấy mỹ thuật hiện đại (Warm Slate)
    canvas = Image.new("RGBA", (W, H), (250, 250, 252, 255))
    draw = ImageDraw.Draw(canvas)

    # 1. Đường lưới kiến trúc Bauhaus (Architectural Grid Lines)
    grid_color = (226, 232, 240, 255)
    for x in [80, 520, 1000, 1480, 1920]:
        draw.line([(x, 0), (x, H)], fill=grid_color, width=2)
    for y in [80, 520, 1000, 1480, 1920]:
        draw.line([(0, y), (W, y)], fill=grid_color, width=2)

    # 2. Khối màu hình học phụ (Geometric Color Accents)
    # Khối xanh Cobalt lệch góc dưới ảnh
    draw.rectangle([1020, 1280, 1920, 1390], fill=(26, 86, 219, 255))
    # Khối đỏ / cam accent bên trái
    draw.rectangle([80, 920, 140, 1260], fill=(badge_c[0], badge_c[1], badge_c[2], 255))
    # Góc đen vát chéo Bauhaus góc dưới trái
    draw.polygon([(80, 1840), (80, 1920), (280, 1920)], fill=(15, 23, 42, 255))

    # 3. Khung ảnh lớp học thật bên phải
    # Khối đế offset tạo hiệu ứng layer Bauhaus
    draw.rectangle([1050, 260, 1870, 1310], fill=(11, 35, 65, 255))

    # Ảnh lớp học thật
    c_w, c_h = 820, 1050
    photo_cropped = smart_crop_and_enhance(classroom_img, c_w, c_h).convert("RGBA")
    canvas.paste(photo_cropped, (1000, 210))

    # Viền sắc nét cho ảnh
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([1000, 210, 1000 + c_w, 210 + c_h], outline=(255, 255, 255, 255), width=6)

    # 4. Huy hiệu tròn vàng ưu đãi học phí (Floating Circle Sticker at Top Right of Photo)
    import re
    discount_str = "50%"
    if badge_text:
        m = re.search(r"(\d+%)", badge_text)
        if m:
            discount_str = m.group(1)

    st_cx, st_cy = 1720, 230
    st_r = 145
    draw.ellipse([st_cx - st_r, st_cy - st_r, st_cx + st_r, st_cy + st_r],
                 fill=(245, 158, 11, 255), outline=(255, 255, 255, 255), width=8)

    font_st_sub = get_font(22, bold=True)
    font_st_big = get_font(72, weight="extrabold")

    bb_top = draw.textbbox((0, 0), "ƯU ĐÃI KHÓA HỌC", font=font_st_sub)
    draw.text((st_cx - (bb_top[2] - bb_top[0]) // 2, st_cy - 72), "ƯU ĐÃI KHÓA HỌC", font=font_st_sub, fill="#FFFFFF")

    bb_mid = draw.textbbox((0, 0), discount_str, font=font_st_big)
    draw.text((st_cx - (bb_mid[2] - bb_mid[0]) // 2, st_cy - 24), discount_str, font=font_st_big, fill="#FFFFFF")

    bb_bot = draw.textbbox((0, 0), "HỌC PHÍ 2026", font=font_st_sub)
    draw.text((st_cx - (bb_bot[2] - bb_bot[0]) // 2, st_cy + 52), "HỌC PHÍ 2026", font=font_st_sub, fill="#FEF3C7")

    # 5. Cột thông tin bên trái
    left_x = 140
    max_text_w = 780

    # Logo Sao Việt
    if logo_path and logo_path.is_file():
        paste_brand_logo(canvas, logo_path, (left_x, 120, left_x + 380, 120 + 120), bg_badge=True)
    draw = ImageDraw.Draw(canvas)

    # Tag trên cùng
    font_top = get_font(28, bold=True)
    draw.text((left_x, 280), "HỆ THỐNG ĐÀO TẠO THỰC CHIẾN SAO VIỆT", font=font_top, fill="#64748B")

    # Khối tiêu đề Bauhaus: Hộp đen khối vuông nổi bật
    title_box_y = 330
    t_font, t_lines = fit_title_font(
        draw, title, max_width=max_text_w - 60, max_height=320, start_size=74, min_size=46, weight="extrabold"
    )
    box_total_h = 0
    for tl in t_lines:
        tbb = draw.textbbox((0, 0), tl, font=t_font)
        box_total_h += (tbb[3] - tbb[1]) + 20
    box_total_h += 40

    # Khối nền đỏ/cam offset sau hộp đen
    draw.rectangle([left_x - 24, title_box_y - 20, left_x + 10, title_box_y + box_total_h - 10],
                   fill=(220, 38, 38, 255))
    # Hộp đen chính (Dark Charcoal / Navy)
    draw.rectangle([left_x, title_box_y, left_x + max_text_w, title_box_y + box_total_h],
                   fill=(15, 23, 42, 255))

    # Chấm tròn cam Bauhaus bên cạnh hộp tiêu đề
    draw.ellipse([left_x + max_text_w - 30, title_box_y + box_total_h // 2 - 50,
                  left_x + max_text_w + 70, title_box_y + box_total_h // 2 + 50],
                 fill=(245, 158, 11, 255))

    curr_y = title_box_y + 25
    for tl in t_lines:
        draw.text((left_x + 30, curr_y), tl, font=t_font, fill="#FFFFFF")
        tbb = draw.textbbox((0, 0), tl, font=t_font)
        curr_y += (tbb[3] - tbb[1]) + 20

    curr_y = title_box_y + box_total_h + 40

    # Phụ đề (Subtitle)
    sub_txt = subtitle or "Chương trình đào tạo từ cơ bản đến nâng cao, hướng dẫn trực tiếp từng thao tác trên máy tính."
    font_sub = get_font(30, weight="medium")
    sub_lines = wrap_text(draw, sub_txt, font_sub, max_text_w)
    for sl in sub_lines:
        draw.text((left_x, curr_y), sl, font=font_sub, fill="#334155")
        curr_y += 42
    curr_y += 30

    # Khối kỹ năng nổi bật (Red Banner Color Block)
    def_hl = [
        "THỰC HÀNH 100%", "KÈM 1-1", "DỰ ÁN DOANH NGHIỆP", "CHỨNG CHỈ QUỐC TẾ"
    ]
    bullets = highlights if (highlights and len(highlights) > 0) else def_hl
    hl_str = "    •    ".join(bullets[:4]).upper()

    font_skills = get_font(28, bold=True)
    sk_lines = wrap_text(draw, hl_str, font_skills, max_text_w - 40)
    banner_h = max(110, len(sk_lines) * 44 + 36)
    draw.rectangle([left_x, curr_y, left_x + max_text_w, curr_y + banner_h], fill=(220, 38, 38, 255))
    sk_y = curr_y + (banner_h - (len(sk_lines) * 40)) // 2
    for skl in sk_lines:
        draw.text((left_x + 20, sk_y), skl, font=font_skills, fill="#FFFFFF")
        sk_y += 42
    curr_y += banner_h + 40

    # 6. Hàng dưới cùng: CTA Button + Hotline + Website
    btn_w = 340
    btn_h = 76
    y_bot = 1720
    draw.rectangle([left_x, y_bot, left_x + btn_w, y_bot + btn_h], fill=(15, 23, 42, 255))
    font_btn = get_font(28, weight="extrabold")
    draw.text((left_x + 45, y_bot + 22), "ĐĂNG KÝ NGAY", font=font_btn, fill="#FFFFFF")

    # Website & Hotline
    web_x = left_x + btn_w + 40
    font_web = get_font(28, bold=True)
    draw.text((web_x, y_bot + 8), "🌐 www.tinhocsaoviet.edu.vn", font=font_web, fill="#1D4ED8")
    if hotline:
        font_hot = get_font(34, weight="extrabold")
        draw.text((web_x, y_bot + 42), f"📞 Hotline: {hotline}", font=font_hot, fill="#B45309")
    elif footer_text:
        font_ft = get_font(28, bold=True)
        draw.text((web_x, y_bot + 42), f"📍 {footer_text.upper()}", font=font_ft, fill="#475569")

    return canvas.convert("RGB")



def render_template_photo_first_cinematic(
    classroom_img: Image.Image,
    logo_path: Optional[Union[str, Path]] = None,
    title: str = "TIN HỌC VĂN PHÒNG CẤP TỐC",
    subtitle: Optional[str] = None,
    highlights: Optional[List[str]] = None,
    badge_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    hotline: Optional[str] = None,
    brand_color: Tuple[int, int, int] = (10, 25, 48),
    palette: Optional[dict] = None,
) -> Image.Image:
    """Template 11: Photo-First Cinematic (Thiết kế Lấy Ảnh Thật Làm Chủ Đạo - Chuẩn Agency Quốc Tế).
    - Triết lý cốt lõi: Ảnh lớp học thật là tài sản uy tín nhất, KHÔNG BAO GIỜ bị cắt xẻ, ép khối méo mó hay nhân bản người.
    - Xử lý ảnh chuyên nghiệp (Colorist Grading):
      + Tăng nhẹ contrast (+12%), đẩy độ rực màu ấm áp (+18%), tăng độ nét chi tiết (+25%).
      + Ảnh phủ rộng 75% - 80% không gian bên phải và trung tâm, giữ nguyên trọn vẹn chủ thể (học viên, giáo viên, màn hình máy tính).
    - Hiệu ứng chuyển cảnh điện ảnh (Cinematic Cosine Ease Gradient):
      + Chuyển màu mượt mà từ nền thương hiệu sẫm màu sang ảnh thật, không dùng vách ngăn hình học cứng.
    - Cột thông tin sang trọng bên trái:
      + Logo Sao Việt nổi bật với badge bảo chứng.
      + Tagline / Eyebrow hiện đại.
      + Tiêu đề chữ lớn sắc nét Be Vietnam Pro.
      + Huy hiệu đặc quyền (Pill badge) cam rực rỡ viền kim loại.
      + Phụ đề truyền tải giá trị khóa học.
      + Danh sách lợi ích với biểu tượng checkmark phát sáng.
      + Huy hiệu ưu đãi / bảo chứng nổi khối (Glow badge).
      + Chân trang: Nút CTA Đăng ký ngay + Hotline + Website.
    """
    W, H = 2000, 2000
    pal = palette or COLOR_PALETTES["royal_sapphire"]
    bg_pri = pal.get("bg_primary", brand_color)
    accent_gold = pal.get("accent_gold", (255, 215, 0))
    accent_cyan = pal.get("accent_cyan", (56, 189, 248))
    badge_bg = pal.get("badge_bg", (234, 88, 12))

    # 1. Tinh chỉnh màu chuyên nghiệp cho ảnh thật (Colorist Grading)
    raw_img = classroom_img.convert("RGB")
    enh_con = ImageEnhance.Contrast(raw_img).enhance(1.12)
    enh_col = ImageEnhance.Color(enh_con).enhance(1.18)
    enh_sharp = ImageEnhance.Sharpness(enh_col).enhance(1.25)

    # Scale photo để bao phủ 75% - 80% canvas bên phải
    target_pw = 1520
    target_ph = H
    sw, sh = enh_sharp.size
    scale = max(target_pw / float(sw), target_ph / float(sh))
    rw = int(sw * scale)
    rh = int(sh * scale)
    scaled_photo = enh_sharp.resize((rw, rh), Image.Resampling.LANCZOS)
    crop_top = max(0, (rh - target_ph) // 2)
    # Lấy góc 25% bên trái-giữa để bắt trọn học viên và màn hình máy tính, tránh lệch sang góc tường/lưng ghế
    crop_left = max(0, min(rw - target_pw, int((rw - target_pw) * 0.25)))
    cropped_photo = scaled_photo.crop((crop_left, crop_top, crop_left + target_pw, crop_top + target_ph))

    # 2. Canvas base: Nền Brand Color sẫm màu
    canvas = Image.new("RGBA", (W, H), (*bg_pri, 255))
    canvas.paste(cropped_photo.convert("RGBA"), (W - target_pw, 0))

    # 3. Cinematic Ease Gradient (Cosine Curve từ x = 720 đến x = 1520)
    grad_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad_layer)
    fade_start = 720
    fade_end = 1520
    for x in range(W):
        if x < fade_start:
            alpha = 255
        elif x > fade_end:
            alpha = 0
        else:
            t = (x - fade_start) / float(fade_end - fade_start)
            alpha = int(255 * (0.5 * (1.0 + math.cos(t * math.pi))))
        gd.line([(x, 0), (x, H)], fill=(*bg_pri, alpha))
    canvas = Image.alpha_composite(canvas, grad_layer)

    # Thêm vignette ở đáy canvas để đảm bảo chân trang dễ đọc 100%
    bot_grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bg_d = ImageDraw.Draw(bot_grad)
    for y in range(H - 450, H):
        t = (y - (H - 450)) / 450.0
        alpha = int(210 * (t ** 1.5))
        bg_d.line([(0, y), (W, y)], fill=(*bg_pri, alpha))
    canvas = Image.alpha_composite(canvas, bot_grad)

    draw = ImageDraw.Draw(canvas)

    # 4. Typography & Branding bên trái
    left_m = 120
    max_tw = 960

    # Logo Sao Việt
    if logo_path and Path(logo_path).is_file():
        paste_brand_logo(canvas, logo_path, (left_m, 120, left_m + 420, 120 + 130), bg_badge=True)
    draw = ImageDraw.Draw(canvas)

    # Tagline / Eyebrow
    font_tag = get_font(28, bold=True)
    draw.text((left_m, 290), "CHƯƠNG TRÌNH ĐÀO TẠO THỰC CHIẾN 2026", font=font_tag,
              fill=accent_cyan if isinstance(accent_cyan, str) else f"#{accent_cyan[0]:02x}{accent_cyan[1]:02x}{accent_cyan[2]:02x}")

    # Tiêu đề chính lớn
    font_title, t_lines = fit_title_font(draw, title, max_tw, 340, start_size=82, min_size=52, weight="extrabold")
    curr_y = 340
    for tl in t_lines:
        draw.text((left_m, curr_y), tl, font=font_title, fill="#FFFFFF")
        tbb = draw.textbbox((0, 0), tl, font=font_title)
        curr_y += (tbb[3] - tbb[1]) + 20

    # Pill Feature Badge
    curr_y += 10
    pill_txt = badge_text if (badge_text and len(badge_text) >= 2) else "ĐÀO TẠO THỰC CHIẾN - KÈM 1-1"
    font_pill = get_font(28, bold=True)
    pill_bbox = draw.textbbox((0, 0), pill_txt, font=font_pill)
    pill_w = (pill_bbox[2] - pill_bbox[0]) + 60
    draw.rounded_rectangle([left_m, curr_y, left_m + pill_w, curr_y + 60], radius=18,
                           fill=(*badge_bg, 250) if isinstance(badge_bg, tuple) else badge_bg,
                           outline=(*accent_gold, 255) if isinstance(accent_gold, tuple) else accent_gold,
                           width=2)
    draw.text((left_m + 30, curr_y + 14), pill_txt, font=font_pill, fill="#FFFFFF")
    curr_y += 105

    # Subtitle
    sub_txt = subtitle or "Giáo trình thực tế doanh nghiệp, cầm tay chỉ việc trên máy tính đến khi thành thạo."
    font_sub = get_font(32, weight="medium")
    sub_lines = wrap_text(draw, sub_txt, font_sub, max_tw)
    for sl in sub_lines:
        draw.text((left_m, curr_y), sl, font=font_sub, fill="#CBD5E1")
        curr_y += 44
    curr_y += 35

    # 4 Bullets Highlights với Checkmark phát sáng
    def_hl = [
        "Thực hành 100% trên máy tính và bài toán thực tế",
        "Kèm 1-1 theo sát tiến độ và năng lực từng học viên",
        "Lịch học linh hoạt ca sáng - chiều - tối mỗi ngày",
        "Cấp chứng chỉ tốt nghiệp chuẩn quốc tế đi làm ngay",
    ]
    bullets = highlights if (highlights and len(highlights) > 0) else def_hl
    font_hl = get_font(32, bold=True)
    for b in bullets[:4]:
        cx, cy, cr = left_m + 20, curr_y + 20, 20
        draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr],
                     fill=(*accent_cyan, 255) if isinstance(accent_cyan, tuple) else accent_cyan)
        draw.line([(cx - 7, cy), (cx - 2, cy + 7), (cx + 8, cy - 7)], fill="#FFFFFF", width=4)
        draw.text((left_m + 60, curr_y), b, font=font_hl, fill="#F8FAFC")
        curr_y += 75

    # Không vẽ sticker tròn lơ lửng đè lên ảnh học viên để giữ ảnh thật sạch đẹp, trang nhã

    # Bottom Row: CTA Button + Hotline + Website
    y_bot = 1750
    btn_w = 360
    btn_h = 84
    draw.rounded_rectangle([left_m, y_bot, left_m + btn_w, y_bot + btn_h], radius=24,
                           fill=(*badge_bg, 255) if isinstance(badge_bg, tuple) else badge_bg,
                           outline=(*accent_gold, 255) if isinstance(accent_gold, tuple) else accent_gold,
                           width=3)
    font_btn = get_font(32, weight="extrabold")
    draw.text((left_m + 48, y_bot + 21), "ĐĂNG KÝ NGAY", font=font_btn, fill="#FFFFFF")

    web_x = left_m + btn_w + 50
    font_web = get_font(28, bold=True)
    draw.text((web_x, y_bot + 12), "🌐 www.tinhocsaoviet.edu.vn", font=font_web,
              fill=accent_cyan if isinstance(accent_cyan, str) else f"#{accent_cyan[0]:02x}{accent_cyan[1]:02x}{accent_cyan[2]:02x}")
    if hotline:
        font_hot = get_font(36, weight="extrabold")
        draw.text((web_x, y_bot + 48), f"📞 Hotline: {hotline}", font=font_hot,
                  fill=accent_gold if isinstance(accent_gold, str) else f"#{accent_gold[0]:02x}{accent_gold[1]:02x}{accent_gold[2]:02x}")
    elif footer_text:
        font_ft = get_font(30, bold=True)
        draw.text((web_x, y_bot + 48), f"📍 {footer_text.upper()}", font=font_ft, fill="#E2E8F0")

    return canvas.convert("RGB")


# ===========================================================================
# TEMPLATE 12: MODERN RIBBON WAVE (Chuẩn phong cách Poster Sao Việt chuyên nghiệp)
# Lấy cảm hứng trực tiếp từ mẫu uu-dai-khoa-hoc-tin-hoc-van-phong.png:
# - Nền trắng sang trọng kết hợp họa tiết chấm bi Dot Matrix
# - Dải sóng lượn kép xanh dương & cam rực rỡ tạo chuyển động thị giác
# - Khung tròn nghệ thuật (Circular Portal) viền trắng nổi khối 3D lồng ảnh học viên
# - Thẻ Voucher ưu đãi 3D (Floating Discount Tickets)
# - Bảng học phí dạng viên thuốc (Price Pills) bo tròn hiện đại
# ===========================================================================
def render_template_modern_ribbon_wave(
    classroom_img: Image.Image,
    logo_path: Optional[Union[Path, str]] = None,
    title: str = "GIẢM HỌC PHÍ ĐẶC BIỆT",
    subtitle: Optional[str] = "HỌC THỰC CHIẾN - ĐI LÀM NGAY",
    highlights: Optional[list] = None,
    badge_text: Optional[str] = "ƯU ĐÃI LỚN NHẤT NĂM",
    footer_text: Optional[str] = None,
    hotline: Optional[str] = "0823 552 558",
    brand_color: Optional[tuple] = None,
    palette: Optional[dict] = None,
) -> Image.Image:
    W, H = 2000, 2000
    canvas = Image.new("RGBA", (W, H), (255, 255, 255, 255))

    # 1. Nền trên: Trắng sang trọng với gradient nhẹ xuống #F8FAFC
    bg_top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bg_d = ImageDraw.Draw(bg_top)
    for y in range(900):
        t = y / 900.0
        val = int(255 - t * 10)
        bg_d.line([(0, y), (W, y)], fill=(val, val, val + 2, 255))
    canvas = Image.alpha_composite(canvas, bg_top)

    # 2. Họa tiết lưới chấm bi (Dot Matrix) trang trí góc trên
    dot_d = ImageDraw.Draw(canvas)
    for r in range(8):
        for c in range(6):
            dx = 760 + c * 24
            dy = 320 + r * 24
            dot_d.ellipse([dx - 3, dy - 3, dx + 3, dy + 3], fill=(203, 213, 225, 255))

    for r in range(6):
        for c in range(5):
            dx = 1860 + c * 22
            dy = 1240 + r * 22
            dot_d.ellipse([dx - 3, dy - 3, dx + 3, dy + 3], fill=(255, 255, 255, 90))

    # 3. Lớp sóng xanh thương hiệu (Royal Blue Ribbon Wave)
    blue_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bld = ImageDraw.Draw(blue_layer)
    blue_pts = [
        (0, 960), (250, 920), (500, 860), (750, 820), (1000, 880),
        (1300, 980), (1600, 940), (1850, 850), (W, 780),
        (W, 1150), (1600, 1280), (1200, 1260), (800, 1180), (400, 1150), (0, 1200),
    ]
    bld.polygon(blue_pts, fill=(14, 82, 186, 255))
    sh_blue = blue_layer.filter(ImageFilter.GaussianBlur(12))
    canvas = Image.alpha_composite(canvas, sh_blue)
    canvas = Image.alpha_composite(canvas, blue_layer)

    # 4. Lớp sóng cam lớn chủ đạo phía dưới (Vibrant Orange Wave)
    orange_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    old = ImageDraw.Draw(orange_layer)
    orange_pts = [
        (0, 1120), (350, 1060), (750, 1020), (1150, 1080), (1500, 1160),
        (1800, 1090), (W, 1010), (W, H), (0, H),
    ]
    old.polygon(orange_pts, fill=(234, 88, 12, 255))
    sh_orange = orange_layer.filter(ImageFilter.GaussianBlur(16))
    canvas = Image.alpha_composite(canvas, sh_orange)
    canvas = Image.alpha_composite(canvas, orange_layer)

    # 5. Khung ảnh tròn nghệ thuật (Circular Portal) lồng ảnh học viên
    p_cx, p_cy, p_r = 1360, 940, 360
    pw, ph = p_r * 2, p_r * 2

    raw_img = classroom_img.convert("RGB")
    enh = ImageEnhance.Contrast(raw_img).enhance(1.12)
    enh = ImageEnhance.Color(enh).enhance(1.15)
    sw, sh = enh.size
    side = min(sw, sh)
    off_x = max(0, min(sw - side, int((sw - side) * 0.35)))
    off_y = (sh - side) // 2
    sq_img = enh.crop((off_x, off_y, off_x + side, off_y + side)).resize((pw, ph), Image.Resampling.LANCZOS)

    mask_circle = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(mask_circle).ellipse([0, 0, pw, ph], fill=255)
    circle_photo = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    circle_photo.paste(sq_img.convert("RGBA"), (0, 0), mask_circle)

    sh_circle = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh_circle).ellipse([p_cx - p_r - 6, p_cy - p_r + 6, p_cx + p_r + 6, p_cy + p_r + 18], fill=(0, 0, 0, 130))
    sh_circle = sh_circle.filter(ImageFilter.GaussianBlur(18))
    canvas = Image.alpha_composite(canvas, sh_circle)
    canvas.paste(circle_photo, (p_cx - p_r, p_cy - p_r), circle_photo)

    draw = ImageDraw.Draw(canvas)
    draw.ellipse([p_cx - p_r, p_cy - p_r, p_cx + p_r, p_cy + p_r], outline="#FFFFFF", width=14)

    # 6. Logo thương hiệu đặt chuẩn xác ở góc trên bên trái
    left_m = 120
    if logo_path:
        badge_w, badge_h = 320, 110
        paste_brand_logo(canvas, logo_path, (left_m, 60, left_m + badge_w, 60 + badge_h), bg_badge=True)
    draw = ImageDraw.Draw(canvas)

    # 7. Thẻ Voucher 3D nổi bật
    vc1_x, vc1_y, vc1_w, vc1_h = 1010, 160, 240, 310
    sh_vc = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh_vc).rounded_rectangle([vc1_x + 6, vc1_y + 8, vc1_x + vc1_w + 6, vc1_y + vc1_h + 8], radius=20, fill=(0, 0, 0, 80))
    sh_vc = sh_vc.filter(ImageFilter.GaussianBlur(12))
    canvas = Image.alpha_composite(canvas, sh_vc)
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle([vc1_x, vc1_y, vc1_x + vc1_w, vc1_y + vc1_h], radius=20, fill="#FEF3C7", outline="#F59E0B", width=3)
    f_vc_tag = get_font(22, bold=True)
    f_vc_num = get_font(68, weight="extrabold")
    f_vc_sub = get_font(20, bold=True)
    draw.text((vc1_x + 36, vc1_y + 20), "GIẢM NGAY", font=f_vc_tag, fill="#B45309")
    draw.text((vc1_x + 28, vc1_y + 55), "50%", font=f_vc_num, fill="#D97706")
    draw.text((vc1_x + 28, vc1_y + 145), "COMBO", font=f_vc_sub, fill="#92400E")
    draw.text((vc1_x + 18, vc1_y + 175), "Cơ Bản & Nâng Cao", font=f_vc_sub, fill="#78350F")
    draw.rounded_rectangle([vc1_x + 20, vc1_y + 230, vc1_x + vc1_w - 20, vc1_y + 280], radius=14, fill="#0284C7")
    draw.text((vc1_x + 36, vc1_y + 242), "ĐĂNG KÝ NGAY", font=get_font(20, weight="extrabold"), fill="#FFFFFF")

    vc2_x, vc2_y, vc2_w, vc2_h = 1280, 240, 240, 290
    draw.rounded_rectangle([vc2_x, vc2_y, vc2_x + vc2_w, vc2_y + vc2_h], radius=20, fill="#FFFFFF", outline="#0284C7", width=3)
    draw.text((vc2_x + 36, vc2_y + 18), "GIẢM NGAY", font=f_vc_tag, fill="#0369A1")
    draw.text((vc2_x + 28, vc2_y + 50), "30%", font=f_vc_num, fill="#0284C7")
    draw.text((vc2_x + 28, vc2_y + 135), "KHÓA CƠ BẢN", font=f_vc_sub, fill="#0F172A")
    draw.text((vc2_x + 24, vc2_y + 165), "Người Mới Bắt Đầu", font=f_vc_sub, fill="#475569")
    draw.rounded_rectangle([vc2_x + 20, vc2_y + 215, vc2_x + vc2_w - 20, vc2_y + 265], radius=14, fill="#EA580C")
    draw.text((vc2_x + 36, vc2_y + 227), "ĐĂNG KÝ NGAY", font=get_font(20, weight="extrabold"), fill="#FFFFFF")

    date_x = 1620
    draw.rounded_rectangle([date_x, 140, date_x + 240, 190], radius=16, fill="#EA580C")
    draw.text((date_x + 44, 150), "ÁP DỤNG TỪ", font=get_font(22, bold=True), fill="#FFFFFF")
    draw.rectangle([date_x - 10, 210, date_x + 250, 300], outline="#1E3A8A", width=3, fill="#FFFFFF")
    draw.text((date_x + 10, 222), "2026", font=get_font(44, weight="extrabold"), fill="#1E3A8A")
    draw.text((date_x + 10, 264), "ƯU ĐÃI NĂM MỚI", font=get_font(18, bold=True), fill="#64748B")

    # 8. Typography tiêu đề góc trên trái
    eyebrow = badge_text or "ƯU ĐÃI LỚN NHẤT NĂM"
    draw.text((left_m, 210), eyebrow.upper(), font=get_font(40, bold=True), fill="#334155")

    main_title = title if title else "GIẢM HỌC PHÍ ĐẶC BIỆT"
    font_t, t_lines = fit_title_font(draw, main_title, 820, 280, start_size=88, min_size=58, weight="extrabold")
    ty = 280
    for line in t_lines:
        draw.text((left_m, ty), line, font=font_t, fill="#0F3684")
        tbb = draw.textbbox((0, 0), line, font=font_t)
        ty += (tbb[3] - tbb[1]) + 20

    # 9. Phần nội dung dải cam phía dưới (tự động co chữ, cấm đè lên ảnh tròn)
    sub_title = subtitle or "HỌC THỰC CHIẾN - ĐI LÀM NGAY"
    max_sub_w = (p_cx - p_r) - left_m - 40
    f_sub_chosen = get_font(42, weight="extrabold")
    for sz in (48, 42, 36, 32, 28, 24):
        f_test = get_font(sz, weight="extrabold")
        bb = draw.textbbox((0, 0), sub_title.upper(), font=f_test)
        if (bb[2] - bb[0]) <= max_sub_w:
            f_sub_chosen = f_test
            break
    draw.text((left_m, 1260), sub_title.upper(), font=f_sub_chosen, fill="#FFFFFF")

    def_bullets = [
        "Tặng khóa học Online trọn đời trị giá 500K",
        "Không giới hạn số buổi học kèm 1-1 đến khi thành thạo",
        "Giáo trình 100% bài toán thực tế doanh nghiệp",
    ]
    blist = highlights if (highlights and len(highlights) > 0) else def_bullets
    by = 1360
    f_b = get_font(32, bold=True)
    for b in blist[:3]:
        draw.ellipse([left_m, by + 4, left_m + 38, by + 42], fill="#0284C7")
        draw.line([(left_m + 10, by + 22), (left_m + 18, by + 30), (left_m + 28, by + 14)], fill="#FFFFFF", width=4)
        draw.text((left_m + 56, by), b, font=f_b, fill="#FFFFFF")
        by += 68

    # 10. 3 Khối Học phí dạng Viên thuốc (Price Pills)
    pills_data = [
        ("Tin Học Văn Phòng Căn Bản", "Trọn khóa 800k"),
        ("Tin Học Văn Phòng & AI Ứng Dụng", "Trọn khóa 1.550k"),
        ("THVP & AI Doanh Nghiệp Chuyên Sâu", "Trọn khóa 2.950k"),
    ]
    py = 1340
    for c_name, price in pills_data:
        pill_w = 980
        pill_h = 82
        px = W - pill_w - 60
        draw.rounded_rectangle([px, py, px + pill_w, py + pill_h], radius=40, fill="#FFFFFF")
        tag_w = 195
        draw.rounded_rectangle([px, py, px + tag_w, py + pill_h], radius=40, fill="#F59E0B")
        draw.text((px + 22, py + 16), "Học phí", font=get_font(20, bold=True), fill="#FFFFFF")
        draw.text((px + 22, py + 42), "thấp nhất", font=get_font(22, weight="extrabold"), fill="#FFFFFF")
        draw.text((px + tag_w + 18, py + 26), c_name, font=get_font(24, bold=True), fill="#1E293B")
        font_pr = get_font(26, weight="extrabold")
        p_bb = draw.textbbox((0, 0), price, font=font_pr)
        draw.text((px + pill_w - (p_bb[2] - p_bb[0]) - 28, py + 25), price, font=font_pr, fill="#0369A1")
        py += 105

    # 11. Chân trang: Hotline & Website
    foot_y = 1880
    draw.rectangle([0, foot_y, W, H], fill="#0F172A")
    draw.text((120, foot_y + 36), "🌐 www.tinhocsaoviet.edu.vn", font=get_font(32, bold=True), fill="#38BDF8")
    draw.text((1150, foot_y + 34), f"📞 TƯ VẤN KHÓA HỌC: {hotline}", font=get_font(36, weight="extrabold"), fill="#FBBF24")

    return canvas.convert("RGB")


# ===========================================================================
# DISPATCHER CHỌN TEMPLATE
# ===========================================================================

TEMPLATES = {
    "modern_ribbon_wave": render_template_modern_ribbon_wave,
    "photo_first_cinematic": render_template_photo_first_cinematic,
    "dual_hexagon": render_template_photo_first_cinematic,
    "bauhaus_grid": render_template_bauhaus_grid,
    "bento_box": render_template_bento_box,
    "curved_window": render_template_curved_window,
    "diagonal_slice": render_template_photo_first_cinematic,
    "bottom_bar": render_template_bottom_bar,
    "split_right": render_template_photo_first_cinematic,
    "split_left": render_template_modern_ribbon_wave,
    "floating_card": render_template_floating_card,
    "3d_pills": render_template_modern_ribbon_wave,
}

# Danh sách trọng số: Ưu tiên cao nhất cho layout Sóng Marketing Sao Việt và Photo-First Cinematic
TEMPLATE_CHOICES = [
    "modern_ribbon_wave",
    "modern_ribbon_wave",
    "modern_ribbon_wave",
    "photo_first_cinematic",
    "photo_first_cinematic",
    "photo_first_cinematic",
    "bento_box",
    "curved_window",
    "floating_card",
    "bottom_bar",
    "bauhaus_grid",
]



def generate_authentic_banner(
    classroom_img_path: Union[str, Path],
    out_path: Union[str, Path],
    logo_path: Optional[Union[str, Path]] = None,
    title: str = "TIN HỌC VĂN PHÒNG CẤP TỐC",
    subtitle: Optional[str] = None,
    highlights: Optional[List[str]] = None,
    badge_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    hotline: Optional[str] = None,
    template_name: Optional[str] = None,
    brand_color: Optional[Tuple[int, int, int]] = None,
    palette_name: Optional[str] = None,
) -> Optional[Path]:
    """Hàm chính tạo ảnh cover từ ảnh thật dataset kết hợp layout mẫu đẹp chuẩn agency."""
    c_path = Path(classroom_img_path)
    if not c_path.is_file():
        return None

    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    logo_p = Path(logo_path) if logo_path else None
    if not logo_p or not logo_p.is_file():
        root = _project_root()
        for cand in [
            root / "brains" / "Brain Default" / "attachments" / "dataset" / "chung" / "thsv-logo-2025.png",
            root / "brains" / "Brain Default" / "attachments" / "dataset" / "chung" / "thsv-logo-big.png",
            root / "attachments" / "dataset" / "chung" / "thsv-logo-2025.png",
            root / "attachments" / "dataset" / "chung" / "thsv-logo-big.png",
        ]:
            if cand.is_file():
                logo_p = cand
                break

    # KIỂM TRA CHẾ ĐỘ 1: Poster đồ họa đã thiết kế sẵn (chỉ áp dụng cho file poster/standee thật)
    premade_kws = ("uu-dai-khoa-hoc", "poster", "banner", "mau-poster", "standee")
    is_premade = any(k in c_path.name.lower() for k in premade_kws)

    # Nếu ảnh là poster thiết kế sẵn -> Chế độ 1: Hoàn thiện poster chuẩn đăng ngay (không vẽ đè layout lên poster đồ họa)
    if is_premade:
        try:
            raw_img = Image.open(c_path).convert("RGBA")
            W, H = raw_img.size
            # Nếu ảnh chưa phải hình vuông 1:1 thì xử lý vuông chuẩn Facebook
            if abs(W - H) > 20:
                side = min(W, H)
                off_x = (W - side) // 2
                off_y = (H - side) // 2
                raw_img = raw_img.crop((off_x, off_y, off_x + side, off_y + side))
                raw_img = raw_img.resize((2000, 2000), Image.Resampling.LANCZOS)
                W, H = 2000, 2000
            elif W < 1500 or H < 1500:
                raw_img = raw_img.resize((2000, 2000), Image.Resampling.LANCZOS)
                W, H = 2000, 2000

            # Dán Logo Sao Việt nổi khối 3D góc trên trái nếu poster chưa có logo thương hiệu sẵn
            has_built_in_logo = any(k in c_path.name.lower() for k in ("sao-viet", "do-hoa", "autocad"))
            if not has_built_in_logo and logo_p:
                badge_w, badge_h = 420, 130
                paste_brand_logo(raw_img, logo_p, (60, 60, 60 + badge_w, 60 + badge_h), bg_badge=True)

            raw_img.convert("RGB").save(out_p, format="JPEG", quality=95)
            try:
                print(f"[banner_templates] Premade poster detected ({c_path.name}) -> Mode 1: Ready to post.")
            except Exception:
                pass
            return out_p
        except Exception as e:
            try:
                print(f"[banner_templates] Premade poster error: {e}", file=sys.stderr)
            except Exception:
                pass

    # KIỂM TRA CHẾ ĐỘ 2: Ảnh lớp học thật thô -> Áp dụng 8 Layout Agency & 5 Bảng màu
    # KHÔNG tự ý bơm highlights giả nếu caller không truyền!

    # Chọn bảng màu đa dạng nếu chưa chỉ định
    if palette_name and palette_name in COLOR_PALETTES:
        chosen_palette = COLOR_PALETTES[palette_name]
    else:
        chosen_palette = random.choice(list(COLOR_PALETTES.values()))

    b_color = brand_color or chosen_palette["bg_primary"]

    if not template_name or template_name not in TEMPLATES:
        template_name = random.choice(TEMPLATE_CHOICES)

    render_fn = TEMPLATES.get(template_name, render_template_bento_box)

    try:
        raw_img = Image.open(c_path)
        kwargs = {
            "classroom_img": raw_img,
            "logo_path": logo_p,
            "title": title,
            "subtitle": subtitle,
            "highlights": highlights,
            "badge_text": badge_text,
            "footer_text": footer_text,
            "hotline": hotline,
            "brand_color": b_color,
        }
        import inspect
        sig = inspect.signature(render_fn)
        if "palette" in sig.parameters:
            kwargs["palette"] = chosen_palette

        final_banner = render_fn(**kwargs)
        final_banner.save(out_p, format="JPEG", quality=95)
        return out_p
    except Exception as e:
        print(f"[banner_templates] Lỗi tạo banner ({template_name}): {e}", file=sys.stderr)
        return None


def render_ai_enhanced_banner(
    ai_background_img: Image.Image,
    logo_path: Optional[Path] = None,
    title: str = "TIN HỌC VĂN PHÒNG & ỨNG DỤNG AI",
    subtitle: Optional[str] = None,
    highlights: Optional[List[str]] = None,
    badge_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    hotline: Optional[str] = None,
    brand_color: Tuple[int, int, int] = (11, 35, 65),
) -> Image.Image:
    """Ghép chữ tiếng Việt chuẩn Unicode font Arial Bold và logo thương hiệu nổi khối 3D
    lên nền ảnh visual sinh từ Google Imagen 3 / Imagen 4.
    Đảm bảo 0% lỗi font, 0% méo chữ, kết hợp hoàn hảo giữa độ sâu visual của Imagen
    và tính chính xác tuyệt đối của typography tiếng Việt."""
    return render_template_floating_card(
        classroom_img=ai_background_img,
        logo_path=logo_path,
        title=title,
        subtitle=subtitle,
        highlights=highlights,
        badge_text=badge_text,
        footer_text=footer_text,
        hotline=hotline,
        brand_color=brand_color,
    )

