# -*- coding: utf-8 -*-
"""
Tạo Cover Poster vuông 1:1 (2000x2000) chuẩn Facebook 2026 cho các khoá học Tin học Sao Việt.
Hỗ trợ 2 Style cốt lõi đẹp nhất (ĐÃ XOÁ STYLE 3 NEON DO LỖI CHỮ VÀ XẤU):
- Style 1: Studio Mockup Poster 1:1 (chuẩn như mẫu đồ hoạ mau-poster-do-hoa.png):
  Chữ to rõ trên nền xanh Sao Việt, ảnh người/lớp học trung tâm bo góc bóng mờ,
  huy hiệu 3D nổi khối hai bên, badge ưu đãi vàng, footer hotline.
- Style 2: Ảnh thật lớp học full khung 1:1 + Khung thương hiệu thanh dưới sắc nét.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

VAULT = Path(r"C:\Users\199X\OneDrive\Máy tính\javis\javis-os\brains\Brain Default")
LOGO_PATH = VAULT / "attachments/dataset/chung/thsv-logo-2025.png"
if not LOGO_PATH.exists():
    LOGO_PATH = VAULT / "attachments/dataset/chung/thsv-logo-big.png"

# Font loaders
def get_font(size, bold=True):
    font_file = r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"
    try:
        return ImageFont.truetype(font_file, size)
    except Exception:
        return ImageFont.load_default()

def create_square_cover_style1(
    title: str,
    subtitle: str,
    badge_text: str,
    student_img_path: Path,
    out_path: Path,
    tools_badges=None,
    hotline: str = "093 1144 858 - 0823 552 558",
    website: str = "tinhocsaoviet.com"
):
    """Style 1: Studio Mockup Poster 1:1 vuông (2000 x 2000) chuẩn như mẫu đồ hoạ."""
    W, H = 2000, 2000
    base = Image.new("RGB", (W, H), "#071B36")
    draw = ImageDraw.Draw(base)

    # 1. Subtle royal blue gradient background
    for y in range(H):
        r = int(7 + (18 - 7) * (y / H))
        g = int(27 + (55 - 27) * (y / H))
        b = int(54 + (115 - 54) * (y / H))
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Center soft ambient lighting behind photo
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([250, 450, 1750, 1650], fill=(0, 160, 255, 60))
    gd.ellipse([450, 250, 1550, 1350], fill=(255, 213, 79, 25))
    glow = glow.filter(ImageFilter.GaussianBlur(130))
    base = Image.alpha_composite(base.convert("RGBA"), glow)

    # Safe margin gold border line
    margin = 55
    bd_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bdd = ImageDraw.Draw(bd_layer)
    bdd.rounded_rectangle([margin, margin, W - margin, H - margin], radius=40, outline=(255, 213, 79, 180), width=4)
    base = Image.alpha_composite(base, bd_layer)

    # 2. Logo at Top Left
    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_w = 260
        scale = logo_w / logo.width
        logo = logo.resize((logo_w, int(logo.height * scale)), Image.Resampling.LANCZOS)
        lw, lh = logo.size
        lx, ly = 100, 95
        lpill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        lpd = ImageDraw.Draw(lpill)
        lpd.rounded_rectangle([lx - 25, ly - 15, lx + lw + 25, ly + lh + 15], radius=22, fill=(255, 255, 255, 245), outline=(255, 213, 79, 200), width=2)
        base = Image.alpha_composite(base, lpill)
        base.paste(logo, (lx, ly), logo)

    # 3. Main Title & Subtitle at Top
    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_layer)

    font_title = get_font(76, bold=True)
    font_sub = get_font(42, bold=True)
    font_badge = get_font(34, bold=True)
    font_footer = get_font(32, bold=True)

    # Title text
    bb = td.textbbox((0, 0), title, font=font_title)
    tw = bb[2] - bb[0]
    tx = (W - tw) // 2
    ty = 230
    td.text((tx + 3, ty + 3), title, font=font_title, fill=(0, 0, 0, 180))
    td.text((tx, ty), title, font=font_title, fill="#FFFFFF")

    # Subtitle
    sbb = td.textbbox((0, 0), subtitle, font=font_sub)
    sw = sbb[2] - sbb[0]
    sx = (W - sw) // 2
    sy = ty + 95
    td.text((sx + 2, sy + 2), subtitle, font=font_sub, fill=(0, 0, 0, 180))
    td.text((sx, sy), subtitle, font=font_sub, fill="#FFD54F")

    # Conversion Badge pill
    bbb = td.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbb[2] - bbb[0]
    bx = (W - bw) // 2
    by = sy + 75
    bpad_x, bpad_y = 40, 14
    pill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([bx - bpad_x, by - bpad_y, bx + bw + bpad_x, by + (bbb[3] - bbb[1]) + bpad_y],
                         radius=30, fill=(245, 124, 0, 240), outline=(255, 235, 59, 255), width=3)
    base = Image.alpha_composite(base, pill)
    td.text((bx, by), badge_text, font=font_badge, fill="#FFFFFF")

    # 4. Center Classroom / Student Photo
    if student_img_path and student_img_path.exists():
        sim = Image.open(student_img_path).convert("RGBA")
        card_w, card_h = 1540, 1040
        ratio = card_w / card_h
        if sim.width / sim.height > ratio:
            new_w = int(sim.height * ratio)
            cl = (sim.width - new_w) // 2
            sim = sim.crop((cl, 0, cl + new_w, sim.height))
        else:
            new_h = int(sim.width / ratio)
            ct = (sim.height - new_h) // 2
            sim = sim.crop((0, ct, sim.width, ct + new_h))
        sim = sim.resize((card_w, card_h), Image.Resampling.LANCZOS)

        mask = Image.new("L", (card_w, card_h), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle([0, 0, card_w, card_h], radius=36, fill=255)

        card_x = (W - card_w) // 2
        card_y = 520

        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle([card_x - 12, card_y - 6, card_x + card_w + 12, card_y + card_h + 16],
                             radius=44, fill=(0, 0, 0, 180))
        shadow = shadow.filter(ImageFilter.GaussianBlur(30))
        base = Image.alpha_composite(base, shadow)

        photo_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        photo_layer.paste(sim, (card_x, card_y), mask)
        pld = ImageDraw.Draw(photo_layer)
        pld.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h],
                              radius=36, outline=(255, 255, 255, 180), width=4)
        base = Image.alpha_composite(base, photo_layer)

    # 5. Floating 3D Badges
    if tools_badges:
        for i, (b_name, b_col, b_bg) in enumerate(tools_badges):
            badge_side = 95 if i % 2 == 0 else W - 235
            badge_y = 660 + (i // 2) * 230
            bi_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            bid = ImageDraw.Draw(bi_layer)
            bid.rounded_rectangle([badge_side + 5, badge_y + 8, badge_side + 145, badge_y + 148], radius=32, fill=(0, 0, 0, 150))
            bi_layer = bi_layer.filter(ImageFilter.GaussianBlur(12))
            base = Image.alpha_composite(base, bi_layer)

            b_fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            bfd = ImageDraw.Draw(b_fg)
            bfd.rounded_rectangle([badge_side, badge_y, badge_side + 140, badge_y + 140], radius=28, fill=b_bg, outline=b_col, width=4)
            bfont = get_font(42, bold=True)
            bbb = bfd.textbbox((0, 0), b_name, font=bfont)
            bw = bbb[2] - bbb[0]
            bh = bbb[3] - bbb[1]
            bfd.text((badge_side + (140 - bw) // 2, badge_y + (140 - bh) // 2 - 4), b_name, font=bfont, fill=b_col)
            base = Image.alpha_composite(base, b_fg)

    # 6. Branded Footer Bar
    foot_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ftd = ImageDraw.Draw(foot_layer)
    fy = 1710
    ftd.rounded_rectangle([80, fy, W - 80, fy + 160], radius=30, fill=(5, 15, 30, 240), outline=(255, 213, 79, 180), width=3)
    ft_line1 = f"TRUNG TÂM TIN HỌC SAO VIỆT  •  HOTLINE: {hotline}"
    ft_line2 = f"ĐÀO TẠO THỰC HÀNH 100% TRÊN MÁY  •  WEBSITE: {website.upper()}"
    
    f1_bb = ftd.textbbox((0, 0), ft_line1, font=font_footer)
    f1_w = f1_bb[2] - f1_bb[0]
    ftd.text(((W - f1_w) // 2, fy + 28), ft_line1, font=font_footer, fill="#FFD54F")

    font_footer_sub = get_font(26, bold=False)
    f2_bb = ftd.textbbox((0, 0), ft_line2, font=font_footer_sub)
    f2_w = f2_bb[2] - f2_bb[0]
    ftd.text(((W - f2_w) // 2, fy + 88), ft_line2, font=font_footer_sub, fill="#E0E0E0")

    base = Image.alpha_composite(base, foot_layer)
    base = Image.alpha_composite(base, txt_layer)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    res = base.convert("RGB")
    res.save(out_path, "JPEG", quality=95)
    print(f"[OK] Da tao Cover Vuong Style 1: {out_path} ({res.size})")
    return out_path


def create_square_cover_style2(
    title: str,
    subtitle: str,
    badge_text: str,
    classroom_img_path: Path,
    out_path: Path,
    hotline: str = "093 1144 858",
    website: str = "tinhocsaoviet.com"
):
    """Style 2: Ảnh thật lớp học full khung 1:1 + Khung thương hiệu thanh dưới sắc nét."""
    W, H = 2000, 2000
    if not classroom_img_path or not classroom_img_path.exists():
        raise FileNotFoundError(f"Khong tim thay anh lop hoc: {classroom_img_path}")

    sim = Image.open(classroom_img_path).convert("RGBA")
    side = min(sim.width, sim.height)
    l = (sim.width - side) // 2
    t = (sim.height - side) // 2
    base = sim.crop((l, t, l + side, t + side)).resize((W, H), Image.Resampling.LANCZOS)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(int(H * 0.45), H):
        factor = (y - int(H * 0.45)) / (H * 0.55)
        alpha = int(245 * (factor ** 1.3))
        od.line([(0, y), (W, y)], fill=(8, 20, 42, alpha))
    base = Image.alpha_composite(base, overlay)

    margin = 55
    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle([margin, margin, W - margin, H - margin], radius=40, outline="#FFD54F", width=4)

    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_w = 260
        scale = logo_w / logo.width
        logo = logo.resize((logo_w, int(logo.height * scale)), Image.Resampling.LANCZOS)
        lw, lh = logo.size
        lx, ly = 95, 95
        lpill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        lpd = ImageDraw.Draw(lpill)
        lpd.rounded_rectangle([lx - 20, ly - 12, lx + lw + 20, ly + lh + 12], radius=20, fill=(255, 255, 255, 245), outline=(255, 213, 79, 200), width=2)
        base = Image.alpha_composite(base, lpill)
        base.paste(logo, (lx, ly), logo)

    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_layer)

    font_title = get_font(74, bold=True)
    font_sub = get_font(42, bold=True)
    font_badge = get_font(34, bold=True)
    font_footer = get_font(30, bold=True)

    by = 1350
    bbb = td.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbb[2] - bbb[0]
    bx = (W - bw) // 2
    bpad_x, bpad_y = 35, 12
    td.rounded_rectangle([bx - bpad_x, by - bpad_y, bx + bw + bpad_x, by + (bbb[3] - bbb[1]) + bpad_y],
                         radius=26, fill=(245, 124, 0, 240), outline=(255, 235, 59, 255), width=3)
    td.text((bx, by), badge_text, font=font_badge, fill="#FFFFFF")

    tbb = td.textbbox((0, 0), title, font=font_title)
    tw = tbb[2] - tbb[0]
    tx = (W - tw) // 2
    ty = 1460
    td.text((tx + 3, ty + 3), title, font=font_title, fill=(0, 0, 0, 220))
    td.text((tx, ty), title, font=font_title, fill="#FFFFFF")

    sbb = td.textbbox((0, 0), subtitle, font=font_sub)
    sw = sbb[2] - sbb[0]
    sx = (W - sw) // 2
    sy = 1570
    td.text((sx + 2, sy + 2), subtitle, font=font_sub, fill=(0, 0, 0, 200))
    td.text((sx, sy), subtitle, font=font_sub, fill="#FFD54F")

    ft_line = f"TRUNG TÂM TIN HỌC SAO VIỆT  •  HOTLINE: {hotline}  •  {website.upper()}"
    fbb = td.textbbox((0, 0), ft_line, font=font_footer)
    fw = fbb[2] - fbb[0]
    fx = (W - fw) // 2
    fy = 1750
    td.rounded_rectangle([fx - 35, fy - 12, fx + fw + 35, fy + 48], radius=22, fill=(0, 0, 0, 180), outline=(255, 213, 79, 150), width=2)
    td.text((fx, fy), ft_line, font=font_footer, fill="#00E5FF")

    base = Image.alpha_composite(base, txt_layer)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    res = base.convert("RGB")
    res.save(out_path, "JPEG", quality=95)
    print(f"[OK] Da tao Cover Vuong Style 2: {out_path} ({res.size})")
    return out_path


def main():
    if len(sys.argv) < 3:
        print("Usage: make_square_cover.py <course_type: tinhoc|ketoan|cad|dohoa|ai> <style: 1|2> [photo_path]")
        return

    ctype = sys.argv[1].lower()
    style = sys.argv[2]
    custom_photo = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    courses = {
        "tinhoc": {
            "title": "KHÓA HỌC TIN HỌC VĂN PHÒNG",
            "subtitle": "Word • Excel • PowerPoint Thực Chiến A - Z",
            "badge": "ƯU ĐÃI 30% HỌC PHÍ • KÈM 1-1 CẦM TAY CHỈ VIỆC",
            "folder": "tin-hoc _ai",
            "badges": [("Word", "#2B579A", "#0D234A"), ("Excel", "#217346", "#0B381E"), ("PPT", "#D24726", "#4A170A"), ("Cert", "#FFD54F", "#3E2723")]
        },
        "ketoan": {
            "title": "KHÓA HỌC KẾ TOÁN THỰC HÀNH",
            "subtitle": "Kế Toán Thuế • Báo Cáo Tài Chính • MISA Thực Chiến",
            "badge": "⚡ ĐÀO TẠO TRÊN CHỨNG TỪ SỐNG • ƯU ĐÃI 30% HỌC PHÍ",
            "folder": "ke-toan",
            "badges": [("MISA", "#00B0FF", "#002B4A"), ("Thuế", "#00E676", "#04381A"), ("BCTC", "#FFD54F", "#3E2723"), ("Sổ Sách", "#FF5252", "#4A0808")]
        },
        "cad": {
            "title": "KHÓA HỌC VẼ KỸ THUẬT AUTOCAD",
            "subtitle": "AutoCAD 2D & 3D • Đọc Hiểu & Bóc Tách Bản Vẽ",
            "badge": "⚡ THỰC HÀNH 100% BẢN VẼ THỰC TẾ • GIẢM 30% HỌC PHÍ",
            "folder": "VE KY THUAT",
            "badges": [("CAD 2D", "#E51C24", "#4A0808"), ("CAD 3D", "#00B0FF", "#002B4A"), ("Cơ Khí", "#00E676", "#04381A"), ("Xây Dựng", "#FFD54F", "#3E2723")]
        },
        "dohoa": {
            "title": "KHÓA HỌC THIẾT KẾ ĐỒ HỌA",
            "subtitle": "Photoshop • Illustrator • CorelDRAW Thực Chiến",
            "badge": "⚡ ƯU ĐÃI 30% HỌC PHÍ • TẶNG THƯ VIỆN 300GB",
            "folder": "do-hoa",
            "badges": [("Ps", "#31A8FF", "#001E36"), ("Ai", "#FF9A00", "#331E00"), ("Corel", "#2ECC71", "#0B381E"), ("In Ấn", "#FFD54F", "#3E2723")]
        },
        "ai": {
            "title": "ỨNG DỤNG TRÍ TUỆ NHÂN TẠO AI",
            "subtitle": "ChatGPT • Gemini • Tự Động Hóa Công Việc Văn Phòng",
            "badge": "⚡ TĂNG NĂNG SUẤT X5 • ĐĂNG KÝ HỌC NGAY",
            "folder": "ai",
            "badges": [("GPT-4o", "#10A37F", "#042B21"), ("Gemini", "#4285F4", "#0A1D3A"), ("Midjourney", "#9C27B0", "#2E0836"), ("Auto", "#FFD54F", "#3E2723")]
        }
    }

    info = courses.get(ctype, courses["cad"])
    folder_dir = VAULT / "attachments/dataset" / info["folder"]
    if not custom_photo or not custom_photo.exists():
        files = [p for p in folder_dir.iterdir() if p.suffix.lower() in [".jpg", ".png", ".webp"]]
        custom_photo = files[0] if files else None

    out_p = VAULT / f"attachments/dataset/_xuat/cover_{ctype}_style{style}_square.jpg"

    if custom_photo:
        (VAULT / "attachments/dataset/_xuat/cover_inner_photo.txt").write_text(str(custom_photo), encoding="utf-8")

    if str(style) == "1":
        create_square_cover_style1(
            title=info["title"],
            subtitle=info["subtitle"],
            badge_text=info["badge"],
            student_img_path=custom_photo,
            out_path=out_p,
            tools_badges=info["badges"]
        )
    else:
        create_square_cover_style2(
            title=info["title"],
            subtitle=info["subtitle"],
            badge_text=info["badge"],
            classroom_img_path=custom_photo,
            out_path=out_p
        )

if __name__ == "__main__":
    main()
