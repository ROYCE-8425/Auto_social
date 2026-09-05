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
    """Dán logo thương hiệu vào vùng chỉ định, tùy chọn đặt trên badge trắng bo góc sắc nét."""
    if not logo_path or not logo_path.is_file():
        return
    try:
        logo_img = Image.open(logo_path).convert("RGBA")
        x1, y1, x2, y2 = box
        bw = x2 - x1
        bh = y2 - y1

        draw = ImageDraw.Draw(base)
        if bg_badge:
            draw.rounded_rectangle([x1, y1, x2, y2], radius=18, fill=(255, 255, 255, 250), outline=(255, 215, 0, 200), width=2)

        pad_x = 18
        pad_y = 10
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
# 5 TEMPLATES ĐỒ HỌA THỰC CHIẾN CHUẨN FACEBOOK 1:1 (2000x2000)
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
    title: str,
    subtitle: str,
    highlights: List[str],
    badge_text: str = "ƯU ĐÃI 30% HỌC PHÍ",
    footer_text: str = "TRUNG TÂM TIN HỌC SAO VIỆT",
    hotline: str = "093 1144 858",
    brand_color: Tuple[int, int, int] = (11, 35, 65),
) -> Image.Image:
    """Template 5: Cắt vát góc hiện đại (Diagonal Slant) phân tách giữa ảnh thật và panel thông tin."""
    W, H = 2000, 2000
    base = smart_crop_and_enhance(classroom_img, W, H).convert("RGBA")

    # Polygon vát chéo che bên phải (mở rộng vùng panel sang trái để chữ thoải mái)
    top_x = 980
    bot_x = 720
    poly = [(top_x, 0), (W, 0), (W, H), (bot_x, H)]

    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.polygon(poly, fill=(brand_color[0], brand_color[1], brand_color[2], 255))
    # Đường viền vát vàng
    pd.line([(top_x, 0), (bot_x, H)], fill=(255, 215, 0, 220), width=6)
    base = Image.alpha_composite(base, panel)

    draw = ImageDraw.Draw(base)

    # Logo góc trên phải
    badge_w, badge_h = 310, 110
    paste_brand_logo(base, logo_path, (W - badge_w - 70, 65, W - 70, 65 + badge_h), bg_badge=True)

    # Tiêu đề
    content_x = 1050
    max_text_w = W - content_x - 70
    curr_y = 250
    font_title, title_lines = fit_title_font(draw, title, max_text_w, 400, start_size=72, min_size=46)
    for line in title_lines:
        draw.text((content_x, curr_y), line, font=font_title, fill="#FFFFFF")
        bb = draw.textbbox((0, 0), line, font=font_title)
        curr_y += (bb[3] - bb[1]) + 18

    curr_y += 20
    draw.line([(content_x, curr_y), (content_x + 350, curr_y)], fill=(255, 193, 7, 220), width=4)
    curr_y += 40

    if subtitle:
        font_sub = get_font(38, bold=True)
        sub_lines = wrap_text(draw, subtitle, font_sub, max_text_w)
        for sline in sub_lines:
            draw.text((content_x, curr_y), sline, font=font_sub, fill="#FFD54F")
            bb = draw.textbbox((0, 0), sline, font=font_sub)
            curr_y += (bb[3] - bb[1]) + 15
        curr_y += 35

    font_hl = get_font(32, bold=True)
    for hl in (highlights or [])[:4]:
        hl_text = f"•  {hl}"
        hl_lines = wrap_text(draw, hl_text, font_hl, max_text_w)
        for hline in hl_lines:
            draw.text((content_x, curr_y), hline, font=font_hl, fill="#F1F5F9")
            bb = draw.textbbox((0, 0), hline, font=font_hl)
            curr_y += (bb[3] - bb[1]) + 14
        curr_y += 18

    if badge_text:
        font_badge = get_font(30, bold=True)
        draw_pill_badge(draw, badge_text, content_x, curr_y + 15, font_badge,
                        bg_color=(230, 81, 0, 245), border_color=(255, 215, 0, 255))

    card_y = H - 260
    draw.rounded_rectangle([content_x, card_y, W - 60, card_y + 105], radius=16,
                           fill=(20, 50, 90, 220), outline=(255, 215, 0, 150), width=2)
    font_hotline = get_font(32, bold=True)
    draw.text((content_x + 25, card_y + 34), f"Hotline / Zalo: {hotline}", font=font_hotline, fill="#FFEB3B")

    font_ft = get_font(26, bold=True)
    draw.text((content_x, H - 90), footer_text.upper(), font=font_ft, fill="#94A3B8")

    return base.convert("RGB")


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
    """Template 6: '3d_pills' - Chuẩn Agency 2026 cho ảnh 3D AI hoặc ảnh công nghệ hiện đại:
    - Nửa phải: Giữ nguyên vẹn 100% nhân vật 3D / không gian thực hành.
    - Nửa trái: Bộ 3 viên thuốc Navy bo tròn ôm khít chữ, bóng đổ 3D mềm mại, chữ chuẩn Unicode.
    - Góc trên: Logo Sao Việt trên badge trắng bo góc sắc nét.
    - 100% không lệch, không che mặt chủ thể, không lỗi font tiếng Việt."""
    W, H = 2000, 2000
    base = smart_crop_and_enhance(classroom_img, W, H).convert("RGBA")

    # Dán Logo Sao Việt vào góc trên phải
    badge_w, badge_h = 320, 115
    paste_brand_logo(base, logo_path, (W - badge_w - 70, 70, W - 70, 70 + badge_h), bg_badge=True)

    # Cột trái dành cho 3 thẻ viên thuốc: Canh lề trái tại X = 130
    x_start = 130
    y_start = 780
    font_pill_title = get_font(58, bold=True)
    font_pill_badge = get_font(52, bold=True)
    font_pill_highlight = get_font(52, bold=True)

    draw = ImageDraw.Draw(base)

    def draw_single_capsule(text: str, font: ImageFont.ImageFont, y_pos: int, highlight_token: Optional[str] = None) -> int:
        pad_x = 55
        pad_y = 26
        bb = draw.textbbox((0, 0), text, font=font)
        text_w = bb[2] - bb[0]
        text_h = bb[3] - bb[1]
        capsule_w = text_w + pad_x * 2
        capsule_h = text_h + pad_y * 2
        rad = capsule_h // 2

        # Đổ bóng mềm
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh_draw = ImageDraw.Draw(sh)
        sh_draw.rounded_rectangle([x_start, y_pos + 8, x_start + capsule_w, y_pos + capsule_h + 8],
                                  radius=rad, fill=(0, 0, 0, 120))
        sh = sh.filter(ImageFilter.GaussianBlur(15))
        nonlocal base
        base = Image.alpha_composite(base, sh)

        # Thân viên thuốc navy viền vàng
        cap = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cap_draw = ImageDraw.Draw(cap)
        cap_draw.rounded_rectangle([x_start, y_pos, x_start + capsule_w, y_pos + capsule_h],
                                   radius=rad, fill=(brand_color[0], brand_color[1], brand_color[2], 252),
                                   outline=(255, 215, 0, 180), width=3)

        # Vẽ chữ với tùy chọn highlight màu vàng
        tx = x_start + pad_x
        ty = y_pos + pad_y - 4
        if highlight_token and highlight_token in text:
            parts = text.split(highlight_token, 1)
            # Phần đầu
            cap_draw.text((tx, ty), parts[0], font=font, fill="#FFFFFF")
            p1_bb = cap_draw.textbbox((0, 0), parts[0], font=font)
            tx += (p1_bb[2] - p1_bb[0])
            # Phần highlight vàng
            cap_draw.text((tx, ty), highlight_token, font=font, fill="#FFD54F")
            hl_bb = cap_draw.textbbox((0, 0), highlight_token, font=font)
            tx += (hl_bb[2] - hl_bb[0])
            # Phần đuôi
            cap_draw.text((tx, ty), parts[1], font=font, fill="#FFFFFF")
        else:
            cap_draw.text((tx, ty), text, font=font, fill="#FFFFFF")

        base = Image.alpha_composite(base, cap)
        return y_pos + capsule_h + 36

    # 1. Viên thuốc 1: Tiêu đề khóa học
    t_clean = (title or "TIN HỌC VĂN PHÒNG").upper()
    curr_y = draw_single_capsule(t_clean, font_pill_title, y_start)

    # 2. Viên thuốc 2: Ưu đãi học phí
    b_clean = (badge_text or "ƯU ĐÃI 30% HỌC PHÍ").upper()
    hl_token = "30%" if "30%" in b_clean else ("50%" if "50%" in b_clean else None)
    curr_y = draw_single_capsule(b_clean, font_pill_badge, curr_y, highlight_token=hl_token)

    # 3. Viên thuốc 3: Điểm nổi bật / Kèm 1-1
    h_clean = ((highlights[0] if highlights else "DẠY KÈM 1-1") or "DẠY KÈM 1-1").upper()
    hl_token3 = "1-1" if "1-1" in h_clean else None
    draw_single_capsule(h_clean, font_pill_highlight, curr_y, highlight_token=hl_token3)

    return base.convert("RGB")


# ===========================================================================
# DISPATCHER CHỌN TEMPLATE
# ===========================================================================

TEMPLATES = {
    "split_right": render_template_split_right,
    "split_left": render_template_split_left,
    "bottom_bar": render_template_bottom_bar,
    "floating_card": render_template_floating_card,
    "diagonal_slice": render_template_diagonal_slice,
    "3d_pills": render_template_3d_pills,
}

# Danh sách trọng số: ưu tiên split_right, 3d_pills và bottom_bar
TEMPLATE_CHOICES = ["split_right", "3d_pills", "split_left", "bottom_bar", "floating_card", "diagonal_slice"]


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

    if not highlights:
        highlights = [
            "Kèm 1-1 đến khi thành thạo",
            "Thực hành 100% trên máy tính",
            "Thời gian học linh hoạt sáng - tối",
        ]

    b_color = brand_color or (11, 35, 65)  # Navy Sao Việt #0B2341

    if not template_name or template_name not in TEMPLATES:
        template_name = random.choice(TEMPLATE_CHOICES)

    render_fn = TEMPLATES.get(template_name, render_template_split_right)

    try:
        raw_img = Image.open(c_path)
        final_banner = render_fn(
            classroom_img=raw_img,
            logo_path=logo_p,
            title=title,
            subtitle=subtitle,
            highlights=highlights,
            badge_text=badge_text,
            footer_text=footer_text,
            hotline=hotline,
            brand_color=b_color,
        )
        final_banner.save(out_p, format="JPEG", quality=95)
        return out_p
    except Exception as e:
        print(f"[banner_templates] Lỗi tạo banner ({template_name}): {e}", file=sys.stderr)
        return None
