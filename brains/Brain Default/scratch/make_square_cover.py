# -*- coding: utf-8 -*-
"""
Bộ tạo Cover Banner Vuông 1:1 (2000x2000) chuẩn Facebook 2026 cho Tin học Sao Việt.

ĐÃ XOÁ VĨNH VIỄN CÁC STYLE LỖI VÀ XẤU:
- Xoá 100% style vẽ hộp PIL cũ (khung viền vàng bằng khen, 4 nút vuông thô kệch dán 2 bên mép, ảnh lọt thỏm giữa nền đen).
- Xoá 100% style đè chữ lên mặt/lưng học viên và màn hình máy tính.

QUY CHUẨN ĐỒ HỌA MỚI:
- Luôn dùng Clean Classroom Bottom-Bar 1:1 (Ảnh chụp lớp học thực tế góc rộng sáng sủa)
  Giữ trọn 75% không gian lớp học sáng rõ, không đè chữ lên người hay máy tính.
  Vùng thông tin nằm gọn ở 25% chân trang dưới với dải gradient navy sâu lắng,
  thẻ lợi ích viên thuốc thanh lịch, logo Sao Việt đặt tinh tế.
"""
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

VAULT = Path(r"C:\Users\199X\OneDrive\Máy tính\javis\javis-os\brains\Brain Default")
LOGO_PATH = VAULT / "attachments/dataset/chung/thsv-logo-2025.png"
if not LOGO_PATH.exists():
    LOGO_PATH = VAULT / "attachments/dataset/chung/thsv-logo-big.png"


def get_font(size, bold=True):
    font_paths = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()


def create_clean_classroom_cover(
    title: str,
    subtitle: str,
    benefit1: str,
    benefit2: str,
    classroom_img_path: Path,
    out_path: Path,
    badge_tag: str = "ƯU ĐÃI 30% HỌC PHÍ",
    hotline: str = "093 1144 858",
    website: str = "tinhocsaoviet.com"
):
    """
    Cover Lớp học Thực tế Chuẩn Đồ họa 2026:
    - Ảnh thật góc rộng sáng rõ, không co nhỏ, không viền vàng bằng khen bao quanh.
    - Chữ nằm gọn ở 25% chân trang, tuyệt đối không đè lên lưng, mặt hay màn hình máy tính.
    - Dải gradient chuyển màu navy êm ái, thẻ lợi ích bo tròn hiện đại.
    """
    W, H = 2000, 2000
    if not classroom_img_path or not classroom_img_path.exists():
        raise FileNotFoundError(f"Khong tim thay anh lop hoc: {classroom_img_path}")

    sim = Image.open(classroom_img_path).convert("RGB")
    sw, sh = sim.size

    # Smart Crop 1:1
    if sw > sh:
        crop_w = sh
        crop_x = int((sw - crop_w) * 0.4)
        sim_cropped = sim.crop((crop_x, 0, crop_x + crop_w, sh))
    else:
        crop_h = sw
        crop_y = 0
        sim_cropped = sim.crop((0, crop_y, sw, crop_y + crop_h))

    base = sim_cropped.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")

    # 1. Subtle Logo Ambient Vignette (Top-left)
    top_shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tsd = ImageDraw.Draw(top_shadow)
    tsd.ellipse([-100, -100, 650, 450], fill=(7, 21, 43, 140))
    top_shadow = top_shadow.filter(ImageFilter.GaussianBlur(60))
    base = Image.alpha_composite(base, top_shadow)

    # 2. Logo Sao Viet Top Left - Modern Frosted Card
    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_w = 300
        scale = logo_w / logo.width
        logo = logo.resize((logo_w, int(logo.height * scale)), Image.Resampling.LANCZOS)
        lw, lh = logo.size
        lx, ly = 80, 80

        glass = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glass)
        gd.rounded_rectangle([lx - 16, ly - 10, lx + lw + 16, ly + lh + 10], radius=24, fill=(0, 0, 0, 80))
        glass = glass.filter(ImageFilter.GaussianBlur(12))
        base = Image.alpha_composite(base, glass)

        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([lx - 18, ly - 12, lx + lw + 18, ly + lh + 12], radius=22, fill=(255, 255, 255, 235), outline=(255, 215, 0, 220), width=3)
        base = Image.alpha_composite(base, card)
        base.paste(logo, (lx, ly), logo)

    # 3. Top Right: Badge Uu Dai Cam Nổi Khối
    if badge_tag:
        b_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(b_layer)
        font_tag = get_font(34, bold=True)
        t_bb = bd.textbbox((0, 0), badge_tag, font=font_tag)
        tw = t_bb[2] - t_bb[0]
        th = t_bb[3] - t_bb[1]

        rx = W - tw - 120
        ry = 85
        bd.rounded_rectangle([rx - 25, ry - 14, rx + tw + 25, ry + th + 18], radius=25, fill=(0, 0, 0, 90))
        b_layer = b_layer.filter(ImageFilter.GaussianBlur(10))
        base = Image.alpha_composite(base, b_layer)

        b_card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bcd = ImageDraw.Draw(b_card)
        bcd.rounded_rectangle([rx - 25, ry - 14, rx + tw + 25, ry + th + 18], radius=25, fill=(245, 124, 0, 245), outline=(255, 235, 59, 255), width=3)
        bcd.text((rx, ry), badge_tag, font=font_tag, fill="#FFFFFF")
        base = Image.alpha_composite(base, b_card)

    # 4. Deep Royal Navy Gradient Footer (Chỉ chiếm 28% phía dưới)
    grad_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad_layer)
    fade_start = 1400
    fade_height = H - fade_start
    for y in range(fade_start, H):
        t = (y - fade_start) / fade_height
        alpha = int(255 * (t ** 1.6))
        r = int(7 - 3 * t)
        g = int(21 - 8 * t)
        b = int(43 - 15 * t)
        gd.line([(0, y), (W, y)], fill=(r, g, b, alpha))
    base = Image.alpha_composite(base, grad_layer)

    # Đường chỉ vàng ánh kim tinh tế phân cách
    line_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line_layer)
    ld.line([(120, fade_start + 65), (W - 120, fade_start + 65)], fill=(255, 213, 79, 150), width=3)
    base = Image.alpha_composite(base, line_layer)

    # 5. Khối Typography Chuyên Nghiệp
    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_layer)

    font_title = get_font(72, bold=True)
    font_sub = get_font(38, bold=True)
    font_pill = get_font(32, bold=True)
    font_hotline = get_font(30, bold=True)

    # Tiêu đề khóa học
    t_bb = td.textbbox((0, 0), title, font=font_title)
    tw = t_bb[2] - t_bb[0]
    tx = (W - tw) // 2
    ty = fade_start + 95
    td.text((tx, ty), title, font=font_title, fill="#FFFFFF")

    # Mô tả phụ
    s_bb = td.textbbox((0, 0), subtitle, font=font_sub)
    sw = s_bb[2] - s_bb[0]
    sx = (W - sw) // 2
    sy = ty + 95
    td.text((sx, sy), subtitle, font=font_sub, fill="#FFD54F")

    # 2 Thẻ lợi ích viên thuốc (Pill badges)
    py = sy + 90
    pill_h = 74

    p1_text = f"•  {benefit1}"
    p1_bb = td.textbbox((0, 0), p1_text, font=font_pill)
    p1_w = p1_bb[2] - p1_bb[0] + 60

    p2_text = f"•  {benefit2}"
    p2_bb = td.textbbox((0, 0), p2_text, font=font_pill)
    p2_w = p2_bb[2] - p2_bb[0] + 60

    spacing = 40
    total_w = p1_w + p2_w + spacing
    p1_x = (W - total_w) // 2
    p2_x = p1_x + p1_w + spacing

    # Vẽ Pill 1
    td.rounded_rectangle([p1_x, py, p1_x + p1_w, py + pill_h], radius=pill_h // 2,
                         fill=(15, 34, 64, 230), outline=(255, 213, 79, 180), width=2)
    p1_tx = p1_x + 30
    p1_ty = py + (pill_h - (p1_bb[3] - p1_bb[1])) // 2 - 2
    td.text((p1_tx, p1_ty), p1_text, font=font_pill, fill="#FFFFFF")

    # Vẽ Pill 2
    td.rounded_rectangle([p2_x, py, p2_x + p2_w, py + pill_h], radius=pill_h // 2,
                         fill=(15, 34, 64, 230), outline=(255, 213, 79, 180), width=2)
    p2_tx = p2_x + 30
    p2_ty = py + (pill_h - (p2_bb[3] - p2_bb[1])) // 2 - 2
    td.text((p2_tx, p2_ty), p2_text, font=font_pill, fill="#FFFFFF")

    # Chân trang Hotline & Website
    ft_y = py + 120
    ft_line = f"TRUNG TÂM TIN HỌC SAO VIỆT  •  HOTLINE: {hotline}  •  {website.upper()}"
    f_bb = td.textbbox((0, 0), ft_line, font=font_hotline)
    fw = f_bb[2] - f_bb[0]
    fx = (W - fw) // 2
    td.text((fx, ft_y), ft_line, font=font_hotline, fill="#B0BEC5")

    base = Image.alpha_composite(base, txt_layer)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    res = base.convert("RGB")
    res.save(out_path, "JPEG", quality=95)
    print(f"[OK] Đã tạo Cover Lớp Học Thực Tế chuẩn: {out_path} ({res.size})")
    return out_path


def create_gemini_ai_cover(ctype: str, out_path: Path, api_key: str = None, raw_img_path: Path = None) -> bool:
    """Tao cover visual thuong mai bang Google Imagen (Imagen 4 / Imagen 3) ket hop anh that dataset."""
    import asyncio
    import shutil
    server_dir = str(VAULT.parent.parent / "server")
    if server_dir not in sys.path:
        sys.path.insert(0, server_dir)
    try:
        import image_gen
    except Exception as e:
        print(f"[WARN] Khong import duoc image_gen: {e}")
        return False

    prompts = {
        "tinhoc": (
            "Premium commercial education advertising photography for Modern Office Computer Skills Course (Word, Excel, PowerPoint, AI). "
            "A friendly, confident young Vietnamese student sitting in a sleek modern workspace with a high-end laptop. "
            "Glossy floating 3D icons of Microsoft Excel, Word, and PowerPoint with soft realistic shadows and subtle glassmorphism. "
            "Clean professional royal blue and white studio lighting, sharp focus, 4k, balanced commercial layout."
        ),
        "ketoan": (
            "Premium commercial education advertising photography for Practical Accounting & Taxation Course. "
            "A professional Vietnamese accountant working at a modern organized desk with a sleek laptop displaying clean financial charts. "
            "Glossy floating 3D financial icons, calculators, and tax balance sheets with soft studio lighting. "
            "Deep navy blue and emerald accents, high-end commercial aesthetic, 4k, razor sharp."
        ),
        "cad": (
            "Premium commercial education advertising photography for Mechanical & Architectural AutoCAD 2D 3D Drafting Course. "
            "A modern designer workstation with dual monitors showing intricate blueprints and 3D architectural models. "
            "Floating glowing technical drafting tools and 3D gears, clean studio lighting, 4k."
        ),
        "dohoa": (
            "Premium commercial education advertising photography for Graphic Design Masterclass (Photoshop, Illustrator, InDesign). "
            "An inspired young creative designer in an artistic studio with a graphics tablet and modern computer. "
            "Floating 3D vibrant colorful design elements, color palettes, and glossy icons, dynamic and inspiring commercial lighting, 4k."
        ),
        "ai": (
            "Premium commercial education advertising photography for Applied Artificial Intelligence Course (ChatGPT, Gemini, Automation). "
            "A modern high-tech desk setup with sleek laptop, glowing neural network data visualization in the air, 3D AI glowing core. "
            "Futuristic yet grounded commercial office environment, clean vibrant cyan and sapphire lighting, 4k."
        )
    }

    prompt = prompts.get(ctype, prompts["tinhoc"])
    print(f"[*] Dang tao Cover AI Gemini Imagen ket hop anh that cho khoa [{ctype}]...")
    refs = [str(raw_img_path)] if (raw_img_path and Path(raw_img_path).is_file()) else None
    try:
        res = asyncio.run(
            image_gen.generate_gemini(
                prompt=prompt,
                aspect_ratio="square",
                vault_root=str(VAULT),
                api_key=api_key,
                prefix=f"cover_{ctype}_ai",
                reference_images=refs,
            )
        )
    except Exception as e:
        print(f"[WARN] Loi goi Gemini Imagen: {e}")
        return False

    if res.get("ok") and res.get("abs_path"):
        src = Path(res["abs_path"])
        if src.exists():
            out_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out_path)
            print(f"[OK] Da tao Cover AI Gemini Imagen: {out_path}")
            return True
    print(f"[INFO] Gemini Imagen khong hoan thanh ({res.get('error')}) -> chuyen ve Cover Lop hoc chuan.")
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: make_square_cover.py <course_type: tinhoc|ketoan|cad|dohoa|ai> [style_or_photo] [photo_path] [--kieu1|--kieu2|--template <name>]")
        return

    ctype = sys.argv[1].lower()
    
    server_dir = str(VAULT.parent.parent / "server")
    if server_dir not in sys.path:
        sys.path.insert(0, server_dir)

    import random
    force_kieu_1 = any(arg.lower() in ("--kieu1", "--ai", "--gemini", "kieu1", "ai", "gemini") for arg in sys.argv[2:])
    force_kieu_2 = any(arg.lower() in ("--kieu2", "kieu2", "--banner") for arg in sys.argv[2:])
    
    # 7/3 Ratio: 70% Kiểu 2 (Authentic Banner), 30% Kiểu 1 (AI 3D Poster)
    use_kieu_2 = force_kieu_2 or (not force_kieu_1 and (random.random() < 0.70))

    chosen_template = None
    for i, arg in enumerate(sys.argv[2:]):
        if arg.lower() in ("--template", "-t") and i + 1 < len(sys.argv[2:]):
            chosen_template = sys.argv[2:][i + 1].strip()

    courses = {
        "tinhoc": {
            "title": "KHÓA HỌC TIN HỌC VĂN PHÒNG",
            "subtitle": "Word • Excel • PowerPoint Thực Chiến A - Z",
            "highlights": ["Thực hành 100% trên máy tính", "Kèm 1-1 cầm tay chỉ việc", "Thời gian học linh hoạt sáng - tối"],
            "benefit1": "Thực hành 100% trên máy",
            "benefit2": "Kèm 1-1 cầm tay chỉ việc",
            "folder": "tin-hoc _ai"
        },
        "ketoan": {
            "title": "KHÓA HỌC KẾ TOÁN THỰC HÀNH",
            "subtitle": "Kế Toán Thuế • Báo Cáo Tài Chính • MISA",
            "highlights": ["Học trên chứng từ thực tế", "Kèm 1-1 đến khi thành thạo", "Thành thạo phần mềm MISA"],
            "benefit1": "Học trên chứng từ sống",
            "benefit2": "Kèm 1-1 đến khi thành thạo",
            "folder": "ke-toan"
        },
        "cad": {
            "title": "KHÓA HỌC VẼ KỸ THUẬT AUTOCAD",
            "subtitle": "AutoCAD 2D & 3D • Đọc Hiểu & Bóc Tách Bản Vẽ",
            "highlights": ["Thực hành 100% bản vẽ thực tế", "Đọc hiểu bóc tách bản vẽ nhanh", "Giảng viên kỹ sư giàu kinh nghiệm"],
            "benefit1": "Thực hành 100% bản vẽ thực tế",
            "benefit2": "Học kèm trực tiếp trên máy",
            "folder": "ve-ky-thuat"
        },
        "dohoa": {
            "title": "KHÓA HỌC THIẾT KẾ ĐỒ HỌA",
            "subtitle": "Photoshop • Illustrator • CorelDRAW Thực Chiến",
            "highlights": ["Thiết kế banner poster chuyên nghiệp", "Tư duy bố cục và màu sắc chuẩn in", "Thực hành đồ án doanh nghiệp thực tế"],
            "benefit1": "Thực chiến banner - logo - in ấn",
            "benefit2": "Tặng kho tài nguyên 300GB",
            "folder": "do-hoa"
        },
        "ai": {
            "title": "AI ỨNG DỤNG VĂN PHÒNG",
            "subtitle": "ChatGPT • Copilot • Tự Động Hóa Công Việc",
            "highlights": ["Tối ưu Word Excel mỗi ngày", "Tăng 5x hiệu suất làm việc", "Dạy kèm 1-1 thực hành"],
            "benefit1": "Tăng năng suất làm việc x5",
            "benefit2": "Cầm tay chỉ việc ứng dụng thực tế",
            "folder": "tin-hoc _ai"
        }
    }

    info = courses.get(ctype, courses["tinhoc"])
    out_p = VAULT / f"attachments/dataset/_xuat/cover_{ctype}_style1_square.jpg"
    out_p2 = VAULT / f"attachments/dataset/_xuat/cover_{ctype}_style2_square.jpg"

    # Neu ty le chon Kieu 1 (AI 3D Poster qua Gemini Imagen 3)
    if not use_kieu_2:
        try:
            import image_gen
            has_key = bool(image_gen.get_gemini_api_key())
            if has_key:
                ok = create_gemini_ai_cover(ctype, out_p)
                if ok:
                    import shutil
                    shutil.copy2(out_p, out_p2)
                    return
        except Exception:
            pass

    # Kieu 2 (70%): Sinh Banner thuc chien tu anh lop hoc that + 5 layout Agency
    custom_photo = None
    for arg in sys.argv[2:]:
        p = Path(arg)
        if p.exists() and p.suffix.lower() in [".jpg", ".png", ".webp"]:
            custom_photo = p
            break

    folder_dir = VAULT / "attachments/dataset" / info["folder"]
    if not custom_photo or not custom_photo.exists():
        if folder_dir.exists():
            files = [p for p in folder_dir.iterdir() if p.suffix.lower() in [".jpg", ".png", ".webp"] and " (1)" not in p.name and not p.name.startswith(".")]
            if files:
                custom_photo = random.choice(files)

    if custom_photo and custom_photo.exists():
        (VAULT / "attachments/dataset/_xuat/cover_inner_photo.txt").write_text(str(custom_photo), encoding="utf-8")
        try:
            import banner_templates
            tpl1 = chosen_template or random.choice(banner_templates.TEMPLATE_CHOICES)
            tpl2 = "split_left" if tpl1 == "split_right" else "split_right"

            banner_templates.generate_authentic_banner(
                classroom_img_path=custom_photo,
                out_path=out_p,
                logo_path=LOGO_PATH,
                title=info["title"],
                subtitle=info["subtitle"],
                highlights=info["highlights"],
                template_name=tpl1,
            )
            banner_templates.generate_authentic_banner(
                classroom_img_path=custom_photo,
                out_path=out_p2,
                logo_path=LOGO_PATH,
                title=info["title"],
                subtitle=info["subtitle"],
                highlights=info["highlights"],
                template_name=tpl2,
            )
            print(f"[OK] Da tao 2 Cover Kieu 2 (Agency Banner: {tpl1}, {tpl2}): {out_p.name}, {out_p2.name}")
            return
        except Exception as e:
            print(f"[WARN] Banner templates loi ({e}), fallback sang PIL cu: {e}")
            create_clean_classroom_cover(
                title=info["title"],
                subtitle=info["subtitle"],
                benefit1=info["benefit1"],
                benefit2=info["benefit2"],
                classroom_img_path=custom_photo,
                out_path=out_p
            )
            create_clean_classroom_cover(
                title=info["title"],
                subtitle=info["subtitle"],
                benefit1=info["benefit1"],
                benefit2=info["benefit2"],
                classroom_img_path=custom_photo,
                out_path=out_p2
            )
    else:
        print(f"[WARN] Khong tim thay anh trong folder {info['folder']}. Vui long kiem tra dataset.")


if __name__ == "__main__":
    main()

