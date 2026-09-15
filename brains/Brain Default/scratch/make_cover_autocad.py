# -*- coding: utf-8 -*-
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

VAULT = Path(r"C:\Users\199X\OneDrive\Máy tính\javis\javis-os\brains\Brain Default")
logo_path = VAULT / "attachments/dataset/chung/thsv-logo-big.png"
if not logo_path.exists():
    logo_path = VAULT / "attachments/dataset/chung/thsv-logo-2025.png"

out_path = VAULT / "attachments/dataset/_xuat/royce-shop-autocad-co-khi-cover-03.jpg"

W, H = 1920, 1080
base = Image.new("RGB", (W, H), "#030c17")

# Create rich neon background for AutoCAD / Mechanical
overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
od = ImageDraw.Draw(overlay)

# Ambient electric cyan & deep royal blue & amber gold nebula glows
od.ellipse([80, 80, 920, 900], fill=(0, 229, 255, 35))       # Electric Cyan glow
od.ellipse([1000, 100, 1860, 920], fill=(41, 121, 255, 32))  # Royal Blue glow
od.ellipse([500, 250, 1420, 890], fill=(255, 213, 79, 22))   # Warm Amber soft fill
overlay = overlay.filter(ImageFilter.GaussianBlur(130))
base = Image.alpha_composite(base.convert("RGBA"), overlay)

# Add subtle engineering blueprint grid / tech lines
grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(grid)
for x in range(0, W, 60):
    gd.line([(x, 0), (x, H)], fill=(0, 229, 255, 10), width=1)
for y in range(0, H, 60):
    gd.line([(0, y), (W, y)], fill=(0, 229, 255, 10), width=1)

# Glowing geometric neon rings (technical blueprint precision)
gd.ellipse([W//2 - 470, H//2 - 420, W//2 + 470, H//2 + 520], outline=(0, 229, 255, 45), width=2)
gd.ellipse([W//2 - 540, H//2 - 490, W//2 + 540, H//2 + 590], outline=(41, 121, 255, 35), width=1)

base = Image.alpha_composite(base, grid)

# Neon border frame (safe margin outer)
frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
fd = ImageDraw.Draw(frame)
margin = 45
fd.rounded_rectangle([margin, margin, W - margin, H - margin], radius=32, outline=(0, 229, 255, 140), width=4)
fd.rounded_rectangle([margin + 12, margin + 12, W - margin - 12, H - margin - 12], radius=24, outline=(41, 121, 255, 85), width=2)

# Corner accent glows
for cx, cy in [(margin, margin), (W - margin, margin), (margin, H - margin), (W - margin, H - margin)]:
    fd.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=(0, 229, 255, 95))
frame_glow = frame.filter(ImageFilter.GaussianBlur(16))
base = Image.alpha_composite(base, frame_glow)
base = Image.alpha_composite(base, frame)

# Load fonts
try:
    font_badge = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 28)
    font_main_title = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 66)
    font_sub_title = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 34)
    font_card_title = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 28)
    font_card_desc = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 22)
    font_footer = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 26)
    font_pill = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 26)
except Exception:
    font_badge = ImageFont.load_default()
    font_main_title = font_badge
    font_sub_title = font_badge
    font_card_title = font_badge
    font_card_desc = font_badge
    font_footer = font_badge
    font_pill = font_badge

# Paste Logo at Top-Center with clean glass backing
if logo_path.exists():
    logo = Image.open(logo_path).convert("RGBA")
    max_logo_w = 260
    scale = max_logo_w / logo.width
    logo = logo.resize((max_logo_w, int(logo.height * scale)), Image.Resampling.LANCZOS)
    lw, lh = logo.size
    lx = (W - lw) // 2
    ly = 75
    
    # Glass pill background for logo
    lpill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lpd = ImageDraw.Draw(lpill)
    pad_x, pad_y = 35, 12
    lpd.rounded_rectangle([lx - pad_x, ly - pad_y, lx + lw + pad_x, ly + lh + pad_y], radius=24, fill=(255, 255, 255, 245), outline=(0, 229, 255, 210), width=2)
    base = Image.alpha_composite(base, lpill)
    base.paste(logo, (lx, ly), logo)

# Draw Main Titles
text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
td = ImageDraw.Draw(text_layer)

title_text = "KHÓA HỌC VẼ KỸ THUẬT AUTOCAD 2D & 3D"
sub_text = "THIẾT KẾ CƠ KHÍ • BẢN VẼ XÂY DỰNG • NỘI THẤT THỰC CHIẾN"

# Main title neon shadow & glow
bbox = td.textbbox((0, 0), title_text, font=font_main_title)
tw = bbox[2] - bbox[0]
tx = (W - tw) // 2
ty = 230

glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gld = ImageDraw.Draw(glow_layer)
for offset in range(6, 0, -2):
    gld.text((tx, ty), title_text, font=font_main_title, fill=(0, 229, 255, 190))
glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(16))
base = Image.alpha_composite(base, glow_layer)

td.text((tx + 2, ty + 3), title_text, font=font_main_title, fill=(0, 0, 0, 220))
td.text((tx, ty), title_text, font=font_main_title, fill="#FFFFFF")

# Sub title
bbox_sub = td.textbbox((0, 0), sub_text, font=font_sub_title)
stw = bbox_sub[2] - bbox_sub[0]
stx = (W - stw) // 2
sty = 320
td.text((stx + 1, sty + 2), sub_text, font=font_sub_title, fill=(0, 0, 0, 200))
td.text((stx, sty), sub_text, font=font_sub_title, fill="#FFD54F")

# 3 Feature Cards for AutoCAD & Mechanical
cards = [
    ("AUTOCAD 2D THỰC CHIẾN", "Thiết lập bản vẽ chuẩn TCVN/ISO, lệnh tắt vẽ nhanh, quản lý Layer & Block", "#0D47A1", "#00E5FF"),
    ("MÔ HÌNH HÓA 3D CƠ KHÍ", "Dựng chi tiết máy 3D, Solid Modeling, lắp ráp cụm & xuất bản vẽ gia công", "#01579B", "#29B6F6"),
    ("KIẾN TRÚC & NỘI THẤT", "Khai triển mặt bằng kiến trúc, mặt cắt kết cấu & bóc tách khối lượng vật tư", "#1B5E20", "#00E676"),
]

card_w = 480
card_h = 245
gap = 45
total_cards_w = 3 * card_w + 2 * gap
start_cx = (W - total_cards_w) // 2
cards_y = 405

card_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
cd = ImageDraw.Draw(card_layer)

for i, (chead, cdesc, cbg, cneon) in enumerate(cards):
    cx = start_cx + i * (card_w + gap)
    cd.rounded_rectangle([cx, cards_y, cx + card_w, cards_y + card_h], radius=24, fill=(6, 22, 38, 235), outline=cneon, width=3)
    
    pill_w = card_w - 40
    cd.rounded_rectangle([cx + 20, cards_y + 20, cx + 20 + pill_w, cards_y + 80], radius=16, fill=cbg, outline=cneon, width=2)
    
    tbb = cd.textbbox((0, 0), chead, font=font_card_title)
    ctw = tbb[2] - tbb[0]
    cd.text((cx + 20 + (pill_w - ctw) // 2, cards_y + 34), chead, font=font_card_title, fill="#FFFFFF")
    
    words = cdesc.split()
    line1, line2 = "", ""
    for w in words:
        if len(line1) + len(w) < 32 and not line2:
            line1 += w + " "
        else:
            line2 += w + " "
    
    cd.text((cx + 25, cards_y + 110), "✔ " + line1.strip(), font=font_card_desc, fill="#E0E0E0")
    if line2:
        cd.text((cx + 42, cards_y + 145), line2.strip(), font=font_card_desc, fill="#B0BEC5")
    cd.text((cx + 25, cards_y + 188), "⭐ Đào tạo thực hành thực tế 100%", font=font_card_desc, fill="#FFD54F")

base = Image.alpha_composite(base, card_layer)

# 2 Conversion Badges / Pills below cards
badge_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bd = ImageDraw.Draw(badge_layer)

pills = [
    ("⚡ KÈM 1-1 CẦM TAY CHỈ VIỆC - HỌC ĐẾN KHI THÀNH THẠO", "#00E5FF", "#03283A"),
    ("🎁 ƯU ĐÃI 30% HỌC PHÍ - TẶNG THƯ VIỆN CAD 50GB & TEMPLATE CHUẨN", "#FFD54F", "#3E2723"),
]

pw = 700
ph = 64
pgap = 50
total_pills_w = 2 * pw + pgap
pills_start_x = (W - total_pills_w) // 2
pills_y = 710

for i, (ptext, pstroke, pfill) in enumerate(pills):
    px = pills_start_x + i * (pw + pgap)
    bd.rounded_rectangle([px, pills_y, px + pw, pills_y + ph], radius=32, fill=pfill, outline=pstroke, width=3)
    pbb = bd.textbbox((0, 0), ptext, font=font_pill)
    ptw = pbb[2] - pbb[0]
    bd.text((px + (pw - ptw) // 2, pills_y + 17), ptext, font=font_pill, fill=pstroke)

base = Image.alpha_composite(base, badge_layer)

# Class Schedule pill
info_text = "⏰ Ca học linh động: Sáng - Chiều - Tối (Thứ 2 đến Thứ 7) • Đăng ký là học ngay không chờ lớp"
ibb = td.textbbox((0, 0), info_text, font=font_badge)
itw = ibb[2] - ibb[0]
itx = (W - itw) // 2
ity = 825
td.text((itx + 1, ity + 1), info_text, font=font_badge, fill=(0, 0, 0, 200))
td.text((itx, ity), info_text, font=font_badge, fill="#FFFFFF")

# Footer Bar
footer_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ftd = ImageDraw.Draw(footer_layer)
ft_y = 900
ftd.rounded_rectangle([180, ft_y, W - 180, ft_y + 80], radius=24, fill=(4, 18, 30, 235), outline=(0, 229, 255, 160), width=2)

ft_text = "TRUNG TÂM TIN HỌC SAO VIỆT  •  HOTLINE: 0823 552 558 - 093 1144 858  •  TINHOCSAOVIET.COM"
fbb = ftd.textbbox((0, 0), ft_text, font=font_footer)
ftw = fbb[2] - fbb[0]
ftx = (W - ftw) // 2
ftd.text((ftx, ft_y + 24), ft_text, font=font_footer, fill="#00E5FF")

base = Image.alpha_composite(base, footer_layer)
base = Image.alpha_composite(base, text_layer)

# Convert to RGB and save
final_img = base.convert("RGB")
out_path.parent.mkdir(parents=True, exist_ok=True)
final_img.save(out_path, "JPEG", quality=95)
print("SUCCESS: Saved cover poster to", out_path)
print("Resolution:", final_img.size)
