---
type: source
updated: 2026-09-03
---
# Sieu poster Sao Viet (cong thuc 2026)

Gop tu: khung Gemini viral (giu anh goc), Nano Banana / Gemini (moi anh 1 vai, chu trong ngoac kep), DreamPoster (anh goc = lop raster, khong ve lai), Facebook feed (16:9, chu it, contrast cao).

Khong copy poster quan doi / esport. Khong gen mat nguoi moi.

## Truoc khi goi tool (2 buoc)

1. Viet xong TIEU DE + 2-3 dong loi ich (tieng Viet co dau) tren giay. Khong de AI tua chu.
2. Dan prompt duoi. `image_edit` kieu A. `image_gen` chi kieu B.

## Vai tung anh

Kieu 1 poster mockup: Anh 1 logo, Anh 2 `mau-poster-do-hoa.png`. Khong anh lop.

Kieu 2 anh goc: Anh 1 dataset, Anh 2 logo, Anh 3 mau A-full / khoa-hoc.

## Prompt kieu A (dan tool)

```
Deliverable: 1 Facebook cover poster landscape (3:2 hoac 16:9, vi du 1200x800 hoac 1200x675 px), top hero banner cho bo cuc 4 anh Facebook (1 anh ngang tren cung + 3 anh vuong ben duoi).

LOCK (Anh 1): Treat the classroom photo as an immutable photo layer. Same people, same room, same cameras. Do not redraw faces, do not replace students with AI people, no Western stock classroom, no children invented.

LOGO (Anh 2): Place exact logo top-left or top-right, small, clear, not warped.

LAYOUT (Anh 3): Follow THIS template geometry only. Teal inset poster = photo in a circle/rounded frame, colorful background, badges, NOT a navy 50/50 panel. Bottom-bar = photo full + text bar below. Split navy = only if this template is the split file. Never copy other-school logos, Bach Khoa, Truong Thinh, Zoom watermarks, or foreign hotlines. Do not copy old Vietnamese text from the template. Hotline if any: 0931144858.

BRAND: navy + gold. Safe margin 18% from all edges (CRITICAL: text must be centered and protected within the inner 64% safe zone). Headline largest, benefits smaller.

EXACT TEXT (Vietnamese, quoted, bold sans-serif, high contrast, no misspelling):
Headline: "[TIEU DE KHOA]"
Line 2: "[loi ich 1]"
Line 3: "[loi ich 2]"
Footer: "TRUNG TAM TIN HOC SAO VIET"

Text occupies under 20% of the frame, well within safe zone. No ghost letters, no duplicate layers, no FPT, no fake URL.
```

Page chinh Sao Viet (thsv-page-chinh): poster catalog **chu nhieu hon 20%**. Headline khoa + 3-6 loi ich / ten phan mem + logo. Van cam chu sai dau. Neu image_edit lech tieng Viet: giu layout, **ghep chu bang Pillow** (khong gen lai lan 3).

## Prompt kieu 1 poster mockup studio 1:1 VUONG (chuan mau-poster-do-hoa)

```
Deliverable: 1 Facebook cover poster SQUARE 1:1 (2000x2000 px hoac 1200x1200 px), premium commercial education studio poster.

STYLE & LIGHTING:
- Fresh, ultra-clean commercial studio aesthetic with vibrant corporate Royal Blue / Cyan gradient background.
- Crisp lighting, trustworthy education brand atmosphere.

HERO SUBJECT & 3D ELEMENTS:
- A young, smiling, confident Vietnamese/Asian student or professional sitting with a modern laptop.
- Glossy floating 3D icons of industry software with soft realistic drop shadows: [Word/Excel/PowerPoint for Office / AutoCAD gears for Mechanical / Misa & Excel charts for Accounting / Photoshop & Illustrator for Design / AI neural chip for AI].

TYPOGRAPHY & BRANDING (Safe margin 18% inside):
- Large bold headline at top: "[TEN KHOA HOC IN HOA]" (clean white/golden yellow sans-serif, high contrast).
- Sub-headline: "[Cong cu dao tao chuyen sau]".
- Conversion badge: Rounded pill badge "UU DAI 30% HOC PHI - KEM 1-1".
- Top corner: Exact Sao Viet star logo.
- Footer bar: "TRUNG TAM TIN HOC SAO VIET - Hotline: 093 1144 858 - tinhocsaoviet.com".

QUALITY:
- 1:1 square format. Razor sharp text, no overlapping letters, no dark sci-fi neon lines, no foreign hotlines.
```

*(Style 3 Neon viền mạch điện tối tăm đã xoá bỏ hoàn toàn khỏi hệ thống do lỗi đè chữ và xấu).*

## Prompt kieu B (le / thong bao)

```
New 16:9 poster. Do not overlay onto a previous holiday poster (no leftover QUOC KHANH text).

LOGO: Anh 1 exact Sao Viet logo top center.
LAYOUT: Anh 2 frame only (two cream cards).
Headline: "[THONG BAO ...]"
Card left: "Nghi: [ngay]"
Card right: "Hoc lai: [ngay]"
Footer: "TRUNG TAM TIN HOC SAO VIET"
Navy+gold or red+gold. Ornate but clean. No 4 identical lantern circles. No AI faces.
```

## Checklist truoc khi dang

- 3:2 hoac 16:9 cho cover album (hoac 1:1 / 4:5 cho bai 1 anh), chu doc duoc o thumbnail
- Mat/lop = dataset, khong AI
- Logo dung file chung
- Ngay tren anh = ngay caption
- Khong chu ma, khong 4 vong den

Nguon doc: Google Cloud Nano Banana prompting; DreamPoster (giu subject); JIMU ChatGPT Images (chu trong ngoac); Meta creative (chu <20% anh).
