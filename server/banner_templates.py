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

from PIL import Image, ImageDraw, ImageFilter, ImageFont


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Tìm font TrueType hỗ trợ 100% tiếng Việt Unicode trên mọi hệ điều hành (Windows, Linux, Docker)."""
    root = _project_root()
    candidates = [
        root / "system" / "fonts" / ("arialbd.ttf" if bold else "arial.ttf"),
        root / "system" / "fonts" / "arial.ttf",
        Path(r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf"),
        Path(r"C:\Windows\Fonts\tahomabd.ttf" if bold else r"C:\Windows\Fonts\tahoma.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
    ]
    for p in candidates:
        if p.is_file():
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


def fit_title_font(draw: ImageDraw.ImageDraw, title: str, max_width: int, max_height: int, start_size: int = 76, min_size: int = 42) -> Tuple[ImageFont.ImageFont, List[str]]:
    """Tự động co kích thước font để tiêu đề nằm vừa vặn, không bao giờ tràn khung."""
    for sz in range(start_size, min_size - 1, -4):
        font = get_font(sz, bold=True)
        lines = wrap_text(draw, title, font, max_width)
        if not lines:
            return font, [title]
        total_h = 0
        fits = True
        for line in lines:
            bb = draw.textbbox((0, 0), line, font=font)
            total_h += (bb[3] - bb[1]) + int(sz * 0.25)
        if total_h <= max_height and len(lines) <= 3:
            return font, lines
    font = get_font(min_size, bold=True)
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


def paste_brand_logo(base: Image.Image, logo_path: Optional[Path], box: Tuple[int, int, int, int], bg_badge: bool = True) -> None:
    """Dán logo thương hiệu to rõ, nổi khối 3D với viền vàng ánh kim và bóng đổ mềm mại."""
    if not logo_path or not logo_path.is_file():
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

        logo_img = Image.open(logo_path).convert("RGBA")
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
    logo_path: Optional[Path],
    title: str,
    subtitle: str,
    highlights: List[str],
    badge_text: str = "ƯU ĐÃI 30% HỌC PHÍ",
    footer_text: str = "TRUNG TÂM TIN HỌC SAO VIỆT",
    hotline: str = "093 1144 858",
    brand_color: Tuple[int, int, int] = (11, 35, 65),  # Navy Sao Việt
) -> Image.Image:
    """Template 1: Chuẩn theo Ảnh 2 của user gửi.
    - Cột trái (50%): Ảnh lớp học thật, cắt dọc sắc nét.
    - Cột phải (50%): Khối thương hiệu Deep Navy, Logo Sao Việt ở góc trên, Tiêu đề lớn, Highlights chữ vàng rực rỡ."""
    W, H = 2000, 2000
    canvas = Image.new("RGBA", (W, H), (brand_color[0], brand_color[1], brand_color[2], 255))

    # 1. Ảnh lớp học thật bên trái
    split_x = 980
    left_img = smart_crop_and_enhance(classroom_img, split_x, H)
    canvas.paste(left_img, (0, 0))

    # Viền phân cách ánh kim mờ giữa ảnh và panel
    draw = ImageDraw.Draw(canvas)
    draw.line([(split_x, 0), (split_x, H)], fill=(255, 215, 0, 180), width=4)

    # 2. Logo Sao Việt góc trên phải
    badge_w, badge_h = 320, 110
    lx1 = W - badge_w - 70
    ly1 = 70
    paste_brand_logo(canvas, logo_path, (lx1, ly1, lx1 + badge_w, ly1 + badge_h), bg_badge=True)

    # 3. Badge ưu đãi nổi bật
    font_badge = get_font(32, bold=True)
    if badge_text:
        bx = split_x + 60
        by = 85
        draw_pill_badge(draw, badge_text, bx, by, font_badge,
                        bg_color=(230, 81, 0, 240), border_color=(255, 215, 0, 255))

    # 4. Tiêu đề chính cực lớn, sắc nét
    content_x = split_x + 60
    max_text_w = W - content_x - 60
    title_y = 260
    font_title, title_lines = fit_title_font(draw, title, max_text_w, 420, start_size=74, min_size=46)

    curr_y = title_y
    for line in title_lines:
        draw.text((content_x, curr_y), line, font=font_title, fill="#FFFFFF")
        bb = draw.textbbox((0, 0), line, font=font_title)
        curr_y += (bb[3] - bb[1]) + 20

    # Phân cách mỏng
    curr_y += 25
    draw.line([(content_x, curr_y), (content_x + 350, curr_y)], fill=(255, 193, 7, 220), width=4)
    curr_y += 45

    # 5. Phụ đề (Subtitle / Tagline) - Vàng nghệ bắt mắt
    if subtitle:
        font_sub = get_font(40, bold=True)
        sub_lines = wrap_text(draw, subtitle, font_sub, max_text_w)
        for sline in sub_lines:
            draw.text((content_x, curr_y), sline, font=font_sub, fill="#FFD54F")
            bb = draw.textbbox((0, 0), sline, font=font_sub)
            curr_y += (bb[3] - bb[1]) + 16
        curr_y += 35

    # 6. Highlights / Lợi ích thực chiến (Bullets)
    font_hl = get_font(34, bold=True)
    for hl in (highlights or [])[:4]:
        hl_text = f"•  {hl}"
        hl_lines = wrap_text(draw, hl_text, font_hl, max_text_w - 30)
        for hline in hl_lines:
            draw.text((content_x, curr_y), hline, font=font_hl, fill="#E2E8F0")
            bb = draw.textbbox((0, 0), hline, font=font_hl)
            curr_y += (bb[3] - bb[1]) + 14
        curr_y += 18

    # 7. Khối Hotline / Cam kết
    card_y = H - 280
    draw.rounded_rectangle([content_x, card_y, W - 60, card_y + 110], radius=16,
                           fill=(20, 50, 90, 255), outline=(255, 215, 0, 180), width=2)
    font_hotline = get_font(34, bold=True)
    hl_str = f"Hotline / Zalo: {hotline}"
    draw.text((content_x + 30, card_y + 36), hl_str, font=font_hotline, fill="#FFEB3B")

    # 8. Chân trang Footer
    font_ft = get_font(28, bold=True)
    ft_str = footer_text.upper()
    draw.text((content_x, H - 90), ft_str, font=font_ft, fill="#94A3B8")

    return canvas.convert("RGB")


def render_template_split_left(
    classroom_img: Image.Image,
    logo_path: Optional[Path],
    title: str,
    subtitle: str,
    highlights: List[str],
    badge_text: str = "ƯU ĐÃI 30% HỌC PHÍ",
    footer_text: str = "TRUNG TÂM TIN HỌC SAO VIỆT",
    hotline: str = "093 1144 858",
    brand_color: Tuple[int, int, int] = (11, 35, 65),
) -> Image.Image:
    """Template 2: Đổi bên (Trái: Panel thông tin thương hiệu, Phải: Ảnh lớp học thật)."""
    W, H = 2000, 2000
    canvas = Image.new("RGBA", (W, H), (brand_color[0], brand_color[1], brand_color[2], 255))

    split_x = 1020
    # Ảnh lớp học bên phải
    right_img = smart_crop_and_enhance(classroom_img, W - split_x, H)
    canvas.paste(right_img, (split_x, 0))

    draw = ImageDraw.Draw(canvas)
    draw.line([(split_x, 0), (split_x, H)], fill=(255, 215, 0, 180), width=4)

    # Logo góc trên trái
    badge_w, badge_h = 320, 110
    paste_brand_logo(canvas, logo_path, (60, 60, 60 + badge_w, 60 + badge_h), bg_badge=True)

    # Badge ưu đãi
    font_badge = get_font(32, bold=True)
    if badge_text:
        draw_pill_badge(draw, badge_text, split_x - 380, 80, font_badge,
                        bg_color=(230, 81, 0, 240), border_color=(255, 215, 0, 255))

    # Tiêu đề chính
    content_x = 60
    max_text_w = split_x - 120
    font_title, title_lines = fit_title_font(draw, title, max_text_w, 420, start_size=74, min_size=46)

    curr_y = 250
    for line in title_lines:
        draw.text((content_x, curr_y), line, font=font_title, fill="#FFFFFF")
        bb = draw.textbbox((0, 0), line, font=font_title)
        curr_y += (bb[3] - bb[1]) + 20

    curr_y += 25
    draw.line([(content_x, curr_y), (content_x + 350, curr_y)], fill=(255, 193, 7, 220), width=4)
    curr_y += 45

    if subtitle:
        font_sub = get_font(40, bold=True)
        sub_lines = wrap_text(draw, subtitle, font_sub, max_text_w)
        for sline in sub_lines:
            draw.text((content_x, curr_y), sline, font=font_sub, fill="#FFD54F")
            bb = draw.textbbox((0, 0), sline, font=font_sub)
            curr_y += (bb[3] - bb[1]) + 16
        curr_y += 35

    font_hl = get_font(34, bold=True)
    for hl in (highlights or [])[:4]:
        hl_text = f"•  {hl}"
        hl_lines = wrap_text(draw, hl_text, font_hl, max_text_w - 20)
        for hline in hl_lines:
            draw.text((content_x, curr_y), hline, font=font_hl, fill="#E2E8F0")
            bb = draw.textbbox((0, 0), hline, font=font_hl)
            curr_y += (bb[3] - bb[1]) + 14
        curr_y += 18

    card_y = H - 280
    draw.rounded_rectangle([content_x, card_y, split_x - 60, card_y + 110], radius=16,
                           fill=(20, 50, 90, 255), outline=(255, 215, 0, 180), width=2)
    font_hotline = get_font(34, bold=True)
    draw.text((content_x + 30, card_y + 36), f"Hotline / Zalo: {hotline}", font=font_hotline, fill="#FFEB3B")

    font_ft = get_font(28, bold=True)
    draw.text((content_x, H - 90), footer_text.upper(), font=font_ft, fill="#94A3B8")

    return canvas.convert("RGB")


def render_template_bottom_bar(
    classroom_img: Image.Image,
    logo_path: Optional[Path],
    title: str,
    subtitle: str,
    highlights: List[str],
    badge_text: str = "ƯU ĐÃI 30% HỌC PHÍ",
    footer_text: str = "TRUNG TÂM TIN HỌC SAO VIỆT",
    hotline: str = "093 1144 858",
    brand_color: Tuple[int, int, int] = (11, 35, 65),
) -> Image.Image:
    """Template 3: Ảnh thật góc rộng chiếm 60% trên, khối chân trang SOLID navy 40% phía dưới (cấm đè chữ lên người)."""
    W, H = 2000, 2000
    canvas = Image.new("RGBA", (W, H), (brand_color[0], brand_color[1], brand_color[2], 255))

    # 1. Ảnh lớp học thật chiếm 62% phía trên
    top_h = 1240
    top_img = smart_crop_and_enhance(classroom_img, W, top_h)
    canvas.paste(top_img, (0, 0))

    # Logo góc trên trái
    badge_w, badge_h = 320, 110
    paste_brand_logo(canvas, logo_path, (70, 70, 70 + badge_w, 70 + badge_h), bg_badge=True)

    # Badge ưu đãi góc trên phải
    draw = ImageDraw.Draw(canvas)
    font_badge = get_font(34, bold=True)
    if badge_text:
        draw_pill_badge(draw, badge_text, W - 460, 85, font_badge,
                        bg_color=(230, 81, 0, 245), border_color=(255, 215, 0, 255))

    # Đường chỉ vàng phân cách
    draw.line([(0, top_h), (W, top_h)], fill=(255, 215, 0, 220), width=6)

    # 2. Khối chân trang SOLID navy (tuyệt đối không đè lên người)
    curr_y = top_h + 45

    # Tiêu đề chính căn giữa
    font_title, title_lines = fit_title_font(draw, title, W - 180, 220, start_size=72, min_size=48)
    for line in title_lines:
        bb = draw.textbbox((0, 0), line, font=font_title)
        lw = bb[2] - bb[0]
        draw.text(((W - lw) // 2, curr_y), line, font=font_title, fill="#FFFFFF")
        curr_y += (bb[3] - bb[1]) + 15

    # Subtitle
    if subtitle:
        font_sub = get_font(40, bold=True)
        bb = draw.textbbox((0, 0), subtitle, font=font_sub)
        sw = bb[2] - bb[0]
        draw.text(((W - sw) // 2, curr_y), subtitle, font=font_sub, fill="#FFD54F")
        curr_y += (bb[3] - bb[1]) + 30

    # 2 Thẻ viên thuốc quyền lợi
    p1 = highlights[0] if highlights else "Thực hành 100% trên máy"
    p2 = highlights[1] if len(highlights) > 1 else "Kèm 1-1 đến khi thành thạo"
    font_pill = get_font(32, bold=True)

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

    # Chân trang Hotline
    font_ft = get_font(30, bold=True)
    ft_line = f"{footer_text.upper()}  •  HOTLINE: {hotline}"
    f_bb = draw.textbbox((0, 0), ft_line, font=font_ft)
    draw.text(((W - (f_bb[2] - f_bb[0])) // 2, H - 75), ft_line, font=font_ft, fill="#CBD5E1")

    return canvas.convert("RGB")


def render_template_floating_card(
    classroom_img: Image.Image,
    logo_path: Optional[Path],
    title: str,
    subtitle: str,
    highlights: List[str],
    badge_text: str = "ƯU ĐÃI 30% HỌC PHÍ",
    footer_text: str = "TRUNG TÂM TIN HỌC SAO VIỆT",
    hotline: str = "093 1144 858",
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
    badge_w, badge_h = 300, 105
    paste_brand_logo(base, logo_path, (card_x1 + 50, card_y1 + 45, card_x1 + 50 + badge_w, card_y1 + 45 + badge_h), bg_badge=True)

    # Badge ưu đãi
    font_badge = get_font(30, bold=True)
    if badge_text:
        draw_pill_badge(draw, badge_text, card_x2 - 380, card_y1 + 60, font_badge,
                        bg_color=(230, 81, 0, 245), border_color=(255, 215, 0, 255))

    # Tiêu đề khóa học
    max_text_w = (card_x2 - card_x1) - 100
    curr_y = card_y1 + 190
    font_title, title_lines = fit_title_font(draw, title, max_text_w, 400, start_size=70, min_size=46)
    for line in title_lines:
        draw.text((card_x1 + 50, curr_y), line, font=font_title, fill="#FFFFFF")
        bb = draw.textbbox((0, 0), line, font=font_title)
        curr_y += (bb[3] - bb[1]) + 18

    curr_y += 20
    draw.line([(card_x1 + 50, curr_y), (card_x1 + 350, curr_y)], fill=(255, 193, 7, 220), width=4)
    curr_y += 40

    if subtitle:
        font_sub = get_font(38, bold=True)
        sub_lines = wrap_text(draw, subtitle, font_sub, max_text_w)
        for sline in sub_lines:
            draw.text((card_x1 + 50, curr_y), sline, font=font_sub, fill="#FFD54F")
            bb = draw.textbbox((0, 0), sline, font=font_sub)
            curr_y += (bb[3] - bb[1]) + 15
        curr_y += 35

    font_hl = get_font(32, bold=True)
    for hl in (highlights or [])[:4]:
        hl_text = f"•  {hl}"
        hl_lines = wrap_text(draw, hl_text, font_hl, max_text_w)
        for hline in hl_lines:
            draw.text((card_x1 + 50, curr_y), hline, font=font_hl, fill="#F1F5F9")
            bb = draw.textbbox((0, 0), hline, font=font_hl)
            curr_y += (bb[3] - bb[1]) + 14
        curr_y += 18

    # Hotline box
    box_y = card_y2 - 200
    draw.rounded_rectangle([card_x1 + 50, box_y, card_x2 - 50, box_y + 95], radius=16,
                           fill=(22, 54, 98, 230), outline=(255, 215, 0, 160), width=2)
    font_hl_b = get_font(32, bold=True)
    draw.text((card_x1 + 80, box_y + 28), f"Hotline / Zalo: {hotline}", font=font_hl_b, fill="#FFEB3B")

    font_ft = get_font(26, bold=True)
    draw.text((card_x1 + 50, card_y2 - 65), footer_text.upper(), font=font_ft, fill="#94A3B8")

    return base.convert("RGB")


def render_template_diagonal_slice(
    classroom_img: Image.Image,
    logo_path: Optional[Path],
    title: str = "TIN HỌC VĂN PHÒNG & ỨNG DỤNG AI",
    subtitle: str = "Nâng Tầm Hiệu Suất - Đi Làm Ngay",
    highlights: Optional[List[str]] = None,
    badge_text: str = "ƯU ĐÃI 30% HỌC PHÍ",
    footer_text: str = "TRUNG TÂM TIN HỌC SAO VIỆT",
    hotline: str = "093 1144 858",
    brand_color: Tuple[int, int, int] = (8, 22, 45),
) -> Image.Image:
    """Template 5: Vát chéo công nghệ Agency (Diagonal Slant) chuẩn quốc tế:
    - Ảnh thật cắt vát góc động sắc nét, viền neon kép phát sáng vàng kim và xanh cyan.
    - Nền Deep Navy với họa tiết tech grid tinh tế.
    - Logo Sao Việt to rõ trên thẻ nổi khối 3D góc trên trái.
    - Tiêu đề Hero 2 tầng khổng lồ, bóng đổ 3D, vạch mạ vàng sang trọng.
    - 3 Hộp quyền lợi chuyên nghiệp có icon checkmark màu sắc.
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

    paste_brand_logo(canvas, logo_path, (70, 70, 450, 200), bg_badge=True)

    font_badge = get_font(34, bold=True)
    badge_w, badge_h = 430, 95
    bx = W - badge_w - 70
    by = 75
    draw_pill_badge(draw, badge_text, bx, by, font_badge,
                    bg_color=(230, 81, 0, 250), border_color=(255, 215, 0, 255),
                    pad_x=28, pad_y=16, radius=badge_h // 2)

    cx = 1140
    cw = W - cx - 70

    font_t, t_lines = fit_title_font(draw, title, cw, 220, start_size=66, min_size=42)
    title_y = 240
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

    font_sub = get_font(36, bold=True)
    draw.text((cx, sep_y + 26), subtitle.upper(), font=font_sub, fill="#E2E8F0")

    cards_start_y = sep_y + 95
    card_h = 105
    gap = 22
    features = [
        ("DẠY KÈM 1 KÈM 1", "Cầm tay chỉ việc theo năng lực từng học viên", (255, 171, 0)),
        ("THỰC HÀNH 100%", "Trên biểu mẫu & số liệu doanh nghiệp thực tế", (0, 230, 118)),
        ("KHÔNG GIỚI HẠN", "Học đến khi thành thạo làm được việc mới thôi", (64, 196, 255)),
    ]
    if highlights and len(highlights) >= 3:
        features = [
            (highlights[0].upper(), "Theo năng lực từng học viên", (255, 171, 0)),
            (highlights[1].upper(), "Dự án & số liệu thực tế", (0, 230, 118)),
            (highlights[2].upper(), "Học đến khi thành thạo", (64, 196, 255)),
        ]

    for i, (f_title, f_desc, accent_col) in enumerate(features):
        fc_y = cards_start_y + i * (card_h + gap)
        draw.rounded_rectangle([cx, fc_y, cx + cw, fc_y + card_h], radius=16,
                               fill=(14, 38, 72, 220), outline=(255, 215, 0, 130), width=2)
        sq_size = 65
        sq_x = cx + 20
        sq_y = fc_y + (card_h - sq_size) // 2
        draw.rounded_rectangle([sq_x, sq_y, sq_x + sq_size, sq_y + sq_size], radius=12, fill=accent_col)
        draw.line([(sq_x + 18, sq_y + 32), (sq_x + 28, sq_y + 44), (sq_x + 48, sq_y + 20)], fill="#08162D", width=6)

        font_ft1 = get_font(30, bold=True)
        font_ft2 = get_font(24, bold=False)
        draw.text((cx + 105, fc_y + 18), f_title, font=font_ft1, fill="#FFFFFF")
        draw.text((cx + 105, fc_y + 56), f_desc, font=font_ft2, fill="#CBD5E1")

    hotline_y = H - 280
    draw.rounded_rectangle([cx, hotline_y, cx + cw, hotline_y + 115], radius=20,
                           fill=(230, 81, 0, 240), outline=(255, 215, 0, 255), width=3)
    font_hl1 = get_font(26, bold=True)
    font_hl2 = get_font(40, bold=True)
    draw.text((cx + 35, hotline_y + 16), "TƯ VẤN LỘ TRÌNH & XẾP LỊCH HỌC NGAY:", font=font_hl1, fill="#FFF8E1")
    draw.text((cx + 35, hotline_y + 52), f"HOTLINE: {hotline}", font=font_hl2, fill="#FFFFFF")

    font_bot = get_font(26, bold=True)
    draw.text((cx, H - 90), f"{footer_text.upper()} • 13 CƠ SỞ ĐÀO TẠO", font=font_bot, fill="#94A3B8")

    return canvas.convert("RGB")


def render_template_curved_window(
    classroom_img: Image.Image,
    logo_path: Optional[Path],
    title: str = "TIN HỌC VĂN PHÒNG & ỨNG DỤNG AI",
    subtitle: str = "Thành Thạo Sau 1 Khóa Học - Đi Làm Ngay",
    highlights: Optional[List[str]] = None,
    badge_text: str = "ƯU ĐÃI 30% HỌC PHÍ",
    footer_text: str = "TRUNG TÂM TIN HỌC SAO VIỆT",
    hotline: str = "093 1144 858",
    brand_color: Tuple[int, int, int] = (10, 32, 66),
) -> Image.Image:
    """Template 7: Vòng cung nghệ thuật (Curved Inset Window):
    - Ảnh thật đóng khung trong cửa sổ bo góc mềm mại viền đôi mạ vàng phát sáng.
    - Nền Gradient thương hiệu đa sắc sang trọng.
    - Tiêu đề khổng lồ 3 tầng nổi bật bên trái.
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

    paste_brand_logo(canvas, logo_path, (70, 70, 450, 200), bg_badge=True)

    font_badge = get_font(34, bold=True)
    badge_w, badge_h = 430, 95
    bx = W - badge_w - 70
    by = 75
    draw_pill_badge(draw, badge_text, bx, by, font_badge,
                    bg_color=(230, 81, 0, 250), border_color=(255, 215, 0, 255),
                    pad_x=28, pad_y=16, radius=badge_h // 2)

    tx = 70
    tw = 680
    curr_y = 260

    font_t, t_lines = fit_title_font(draw, title, tw, 360, start_size=64, min_size=42)
    for i, tline in enumerate(t_lines):
        col = "#FFFFFF" if i == 0 else ("#FFD54F" if i == 1 else "#00E676")
        draw.text((tx + 2, curr_y + 2), tline, font=font_t, fill=(0, 0, 0, 160))
        draw.text((tx, curr_y), tline, font=font_t, fill=col)
        bb = draw.textbbox((0, 0), tline, font=font_t)
        curr_y += (bb[3] - bb[1]) + 16

    draw.line([(tx, curr_y), (tx + 360, curr_y)], fill=(255, 215, 0, 230), width=4)
    curr_y += 30

    font_sub = get_font(34, bold=True)
    draw.text((tx, curr_y), subtitle, font=font_sub, fill="#E2E8F0")
    curr_y += 65

    bullets = highlights if highlights else [
        "Dạy kèm 1 kèm 1 theo năng lực từng học viên",
        "Thực hành 100% trên dữ liệu thực tế",
        "Không giới hạn số buổi thực hành",
        "Học đến khi thành thạo làm được việc",
    ]

    font_bl = get_font(30, bold=True)
    for b_text in bullets[:4]:
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

    foot_h = 130
    foot_y = H - foot_h
    draw.rectangle([0, foot_y, W, H], fill=(255, 179, 0, 255))
    draw.line([(0, foot_y), (W, foot_y)], fill=(255, 235, 59, 255), width=5)

    font_f1 = get_font(38, bold=True)
    font_f2 = get_font(30, bold=True)
    draw.text((80, foot_y + 24), f"LIÊN HỆ TƯ VẤN & XẾP LỊCH: {hotline}", font=font_f1, fill="#0A1A30")
    draw.text((80, foot_y + 75), f"{footer_text.upper()} - 13 CƠ SỞ TP.HCM & ĐỒNG NAI", font=font_f2, fill="#1E293B")

    return canvas.convert("RGB")


def render_template_3d_pills(
    classroom_img: Image.Image,
    logo_path: Optional[Path],
    title: str,
    subtitle: str,
    highlights: List[str],
    badge_text: str = "ƯU ĐÃI 30% HỌC PHÍ",
    footer_text: str = "TRUNG TÂM TIN HỌC SAO VIỆT",
    hotline: str = "093 1144 858",
    brand_color: Tuple[int, int, int] = (11, 35, 65),
) -> Image.Image:
    """Template 6: '3d_pills' - Phiên bản nâng cấp có khung Frosted Glass che chắn thẩm mỹ."""
    W, H = 2000, 2000
    base = smart_crop_and_enhance(classroom_img, W, H).convert("RGBA")

    # Tạo một panel mờ nghệ thuật (Glassmorphism) ở nửa bên trái để các viên thuốc và logo không bị lọt thỏm
    glass_w = 900
    glass_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glass_layer)
    gd.rectangle([0, 0, glass_w, H], fill=(11, 35, 65, 230))
    gd.line([(glass_w, 0), (glass_w, H)], fill=(255, 215, 0, 200), width=4)
    base = Image.alpha_composite(base, glass_layer)

    paste_brand_logo(base, logo_path, (70, 70, 450, 200), bg_badge=True)

    x_start = 70
    y_start = 250
    max_allowed_w = glass_w - 140

    draw = ImageDraw.Draw(base)

    def draw_single_capsule(text: str, base_font_size: int, y_pos: int, highlight_token: Optional[str] = None) -> int:
        pad_x = 42
        pad_y = 22
        chosen_font = get_font(base_font_size, bold=True)
        for sz in range(base_font_size, 26, -2):
            f_test = get_font(sz, bold=True)
            bb = draw.textbbox((0, 0), text, font=f_test)
            if (bb[2] - bb[0]) + pad_x * 2 <= max_allowed_w:
                chosen_font = f_test
                break

        bb = draw.textbbox((0, 0), text, font=chosen_font)
        text_w = bb[2] - bb[0]
        text_h = bb[3] - bb[1]
        capsule_w = text_w + pad_x * 2
        capsule_h = text_h + pad_y * 2
        rad = capsule_h // 2

        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh_draw = ImageDraw.Draw(sh)
        sh_draw.rounded_rectangle([x_start, y_pos + 6, x_start + capsule_w, y_pos + capsule_h + 6],
                                  radius=rad, fill=(0, 0, 0, 110))
        sh = sh.filter(ImageFilter.GaussianBlur(12))
        nonlocal base
        base = Image.alpha_composite(base, sh)

        cap = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cap_draw = ImageDraw.Draw(cap)
        cap_draw.rounded_rectangle([x_start, y_pos, x_start + capsule_w, y_pos + capsule_h],
                                   radius=rad, fill=(brand_color[0], brand_color[1], brand_color[2], 252),
                                   outline=(255, 215, 0, 190), width=3)

        tx = x_start + pad_x
        ty = y_pos + pad_y - 3
        if highlight_token and highlight_token in text:
            parts = text.split(highlight_token, 1)
            cap_draw.text((tx, ty), parts[0], font=chosen_font, fill="#FFFFFF")
            p1_bb = cap_draw.textbbox((0, 0), parts[0], font=chosen_font)
            tx += (p1_bb[2] - p1_bb[0])
            cap_draw.text((tx, ty), highlight_token, font=chosen_font, fill="#FFD54F")
            hl_bb = cap_draw.textbbox((0, 0), highlight_token, font=chosen_font)
            tx += (hl_bb[2] - hl_bb[0])
            cap_draw.text((tx, ty), parts[1], font=chosen_font, fill="#FFFFFF")
        else:
            cap_draw.text((tx, ty), text, font=chosen_font, fill="#FFFFFF")

        base = Image.alpha_composite(base, cap)
        return y_pos + capsule_h + 28

    t_clean = (title or "TIN HỌC VĂN PHÒNG").upper()
    curr_y = draw_single_capsule(t_clean, 50, y_start)

    b_clean = (badge_text or "ƯU ĐÃI 30% HỌC PHÍ").upper()
    hl_token = "30%" if "30%" in b_clean else ("50%" if "50%" in b_clean else None)
    curr_y = draw_single_capsule(b_clean, 44, curr_y, highlight_token=hl_token)

    h_clean = ((highlights[0] if highlights else "DẠY KÈM 1-1") or "DẠY KÈM 1-1").upper()
    hl_token3 = "1-1" if "1-1" in h_clean else None
    curr_y = draw_single_capsule(h_clean, 44, curr_y, highlight_token=hl_token3)

    # Danh sách quyền lợi / highlights bổ sung
    font_hl = get_font(32, bold=True)
    curr_y += 35
    extra_hls = (highlights[1:] if len(highlights) > 1 else []) or [
        "Thực hành 100% trên máy tính",
        "Kèm 1-1 đến khi thành thạo",
        "Cấp chứng chỉ uy tín sau khóa học",
    ]
    for e_hl in extra_hls[:3]:
        hl_lines = wrap_text(draw, f"•  {e_hl}", font_hl, max_allowed_w - 20)
        for hline in hl_lines:
            draw.text((x_start + 10, curr_y), hline, font=font_hl, fill="#E2E8F0")
            bb = draw.textbbox((0, 0), hline, font=font_hl)
            curr_y += (bb[3] - bb[1]) + 14
        curr_y += 14

    # Khối Hotline / Chân trang ở đáy glass panel
    card_y = H - 260
    draw.rounded_rectangle([x_start, card_y, glass_w - 70, card_y + 100], radius=18,
                           fill=(20, 50, 90, 255), outline=(255, 215, 0, 180), width=2)
    font_hotline = get_font(32, bold=True)
    draw.text((x_start + 24, card_y + 32), f"Hotline / Zalo: {hotline}", font=font_hotline, fill="#FFEB3B")

    font_ft = get_font(26, bold=True)
    draw.text((x_start + 10, H - 90), footer_text.upper(), font=font_ft, fill="#94A3B8")

    return base.convert("RGB")


def render_template_bento_box(
    classroom_img: Image.Image,
    logo_path: Optional[Path],
    title: str = "TIN HỌC VĂN PHÒNG & ỨNG DỤNG AI",
    subtitle: str = "Thành Thạo Sau 1 Khóa Học - Đi Làm Ngay",
    highlights: Optional[List[str]] = None,
    badge_text: str = "ƯU ĐÃI 30% HỌC PHÍ",
    footer_text: str = "TRUNG TÂM TIN HỌC SAO VIỆT",
    hotline: str = "093 1144 858",
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
    draw.text((hx1 + 320, hy1 + 42), f"{footer_text.upper()} • 13 CƠ SỞ ĐÀO TẠO", font=font_hd2, fill="#FFFFFF")

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
    font_badge = get_font(30, bold=True)
    draw_pill_badge(draw, badge_text.upper(), inner_x, curr_y, font_badge,
                    bg_color=(badge_c[0], badge_c[1], badge_c[2], 245),
                    border_color=(accent_g[0], accent_g[1], accent_g[2], 255),
                    pad_x=26, pad_y=12, radius=18)
    curr_y += 90

    # Tiêu đề khóa học lớn
    font_t, t_lines = fit_title_font(draw, title, inner_w, 360, start_size=68, min_size=44)
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

    # 3 Bullet Lợi ích thực tế
    bullets = highlights if highlights else [
        "Dạy kèm 1-1 đến khi thành thạo",
        "Thực hành 100% trên dữ liệu thật",
        "Thời gian học linh hoạt sáng - tối",
    ]
    font_bl = get_font(30, bold=True)
    for b_item in bullets[:3]:
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
    draw.text((k3_x1 + 35, k3_y1 + 205), "ĐĂNG KÝ SỚM NHẬN ƯU ĐÃI 30%", font=font_sm, fill="#FFF9C4")
    draw.text((k3_x1 + 35, k3_y1 + 242), "KHAI GIẢNG HÀNG TUẦN MỌI CƠ SỞ", font=font_sm, fill="#FFFFFF")

    # -------------------------------------------------------------
    # ROW 4: FOOTER RIBBON (y: 1840 -> 1940, h: 100)
    # -------------------------------------------------------------
    fx1, fy1, fx2, fy2 = 60, 1840, 1940, 1940
    draw.rounded_rectangle([fx1, fy1, fx2, fy2], radius=16, fill=(10, 20, 36, 250),
                           outline=(accent_g[0], accent_g[1], accent_g[2], 140), width=2)
    font_ft = get_font(28, bold=True)
    ft_msg = f"{footer_text.upper()} • 13 CƠ SỞ TP.HCM & ĐỒNG NAI • CAM KẾT ĐẦU RA UY TÍN"
    ft_bb = draw.textbbox((0, 0), ft_msg, font=font_ft)
    draw.text((fx1 + (1880 - (ft_bb[2] - ft_bb[0])) // 2, fy1 + 32), ft_msg, font=font_ft, fill="#E2E8F0")

    return canvas.convert("RGB")


# ===========================================================================
# DISPATCHER CHỌN TEMPLATE
# ===========================================================================

TEMPLATES = {
    "bento_box": render_template_bento_box,
    "curved_window": render_template_curved_window,
    "diagonal_slice": render_template_diagonal_slice,
    "bottom_bar": render_template_bottom_bar,
    "split_right": render_template_split_right,
    "split_left": render_template_split_left,
    "floating_card": render_template_floating_card,
    "3d_pills": render_template_3d_pills,
}

# Danh sách trọng số: ưu tiên các mẫu thiết kế Agency đỉnh cao
TEMPLATE_CHOICES = [
    "bento_box",
    "curved_window",
    "diagonal_slice",
    "bottom_bar",
    "split_right",
    "split_left",
    "floating_card",
    "3d_pills",
]


def generate_authentic_banner(
    classroom_img_path: Union[str, Path],
    out_path: Union[str, Path],
    logo_path: Optional[Union[str, Path]] = None,
    title: str = "TIN HỌC VĂN PHÒNG CẤP TỐC",
    subtitle: str = "Thành Thạo Sau 1 Khóa Học",
    highlights: Optional[List[str]] = None,
    badge_text: str = "ƯU ĐÃI 30% HỌC PHÍ",
    footer_text: str = "TRUNG TÂM TIN HỌC SAO VIỆT",
    hotline: str = "093 1144 858",
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

    # KIỂM TRA CHẾ ĐỘ 1: Poster đồ họa đã thiết kế sẵn (có sẵn chữ/nội dung)
    premade_kws = ("khai-giang", "uu-dai", "poster", "banner", "thong-bao", "looker-studio", "trung-tam-dao-tao")
    is_premade = any(k in c_path.name.lower() for k in premade_kws)

    # Nếu ảnh là poster thiết kế sẵn và người dùng không ép buộc template -> Chỉ dán Logo Sao Việt hoàn thiện
    if is_premade and not template_name:
        try:
            raw_img = Image.open(c_path).convert("RGBA")
            W, H = raw_img.size
            # Nếu ảnh chưa phải hình vuông 1:1 thì crop nhẹ về vuông chuẩn Facebook
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

            # Dán Logo Sao Việt nổi khối 3D góc trên trái
            badge_w, badge_h = 420, 130
            paste_brand_logo(raw_img, logo_p, (60, 60, 60 + badge_w, 60 + badge_h), bg_badge=True)
            raw_img.convert("RGB").save(out_p, format="JPEG", quality=95)
            print(f"[banner_templates] Phát hiện poster sẵn ({c_path.name}) -> Chế độ 1: Dán Logo Sao Việt chuẩn đẹp đăng ngay.")
            return out_p
        except Exception as e:
            print(f"[banner_templates] Lỗi dán logo poster sẵn: {e}", file=sys.stderr)

    # KIỂM TRA CHẾ ĐỘ 2: Ảnh lớp học thật thô -> Áp dụng 8 Layout Agency & 5 Bảng màu
    if not highlights:
        highlights = [
            "Kèm 1-1 đến khi thành thạo",
            "Thực hành 100% trên máy tính",
            "Thời gian học linh hoạt sáng - tối",
        ]

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
