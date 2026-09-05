---
type: source
updated: 2026-09-03
---
# Sieu poster Sao Viet (cong thuc 2026)

Gop tu: khung Gemini viral (giu anh goc), Nano Banana / Gemini (moi anh 1 vai, chu trong ngoac kep), DreamPoster (anh goc = lop raster, khong ve lai), Facebook feed (16:9, chu it, contrast cao).

Khong copy poster quan doi / esport. Khong gen mat nguoi moi.

## Truoc khi goi tool (2 buoc)

1. Viet xong TIEU DE + 2-3 dong loi ich (tieng Viet co dau) tren giay. Khong de AI tua chu.
2. Chi **1 lan gen / bai**. Dua dung 2 file anh: (1) 1 anh raw dataset, (2) logo kit `attachments/dataset/chung/thsv-logo-2025.png`. Khong gen logo. Khong gen them poster thu 2.

## Vai tung anh

Kieu 1 poster mockup: Anh 1 = logo file that, Anh 2 = mau-poster-do-hoa. Van phai khoa logo file.

Kieu 2 anh goc: Anh 1 dataset raw, Anh 2 logo file that, Anh 3 mau A-full. LOCK anh lop; PASTE logo, khong ve lai logo.

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

## Nguyên tắc thiết kế poster bắt mắt & chuyển đổi cao

1. **TUYỆT ĐỐI KHÔNG DÙNG TIẾNG ANH (100% TIẾNG VIỆT):**
   - Mọi tiêu đề, badge ưu đãi, nhãn kêu gọi đều phải bằng tiếng Việt có dấu.
   - CẤM các từ tiếng Anh như: `Enroll now!`, `PROFESSIONAL OFFICE IT`, `Register today`, `Master computer`.
   - Chuẩn tiếng Việt: `TIN HỌC VĂN PHÒNG`, `ƯU ĐÃI 30% HỌC PHÍ`, `DẠY KÈM 1-1`, `HỌC ĐẾN KHI THÀNH THẠO`.
2. **ƯU TIÊN DỮ LIỆU THẬT TỪ DATASET KHÓA HỌC:**
   - Luôn đưa ít nhất 1 ảnh raw từ dataset ngành (`tin-hoc _ai/`, `ke-toan/`, `do-hoa/`, `ve-ky-thuat/`) làm reference image.
   - AI bám sát thần thái học viên Việt Nam, không gian lớp học máy tính thực tế, thân thiện. CẤM tạo người mẫu Tây phương xa lạ hay học sinh tiểu học Tây.
3. **BẮT MẮT, THU HÚT NGƯỜI XEM TỐI ĐA (SCROLL-STOPPING VISUAL):**
   - Ánh sáng studio rực rỡ, tươi sáng, tạo cảm giác chuyên nghiệp, uy tín và năng động.
   - Phối màu tương phản cao: Xanh dương nhận diện Sao Việt (Royal Blue/Cyan) kết hợp điểm nhấn vàng gold rực rỡ trên badge ưu đãi.
   - Icon 3D phần mềm bay nổi khối (Excel, Word, Misa, AutoCAD, Photoshop...) có độ bóng và đổ bóng chân thực.
   - Bố cục VUÔNG 1:1 chuẩn mực, chữ nằm gọn trong vùng an toàn (safe margin 18%), không đè chữ, không cắt mép trên mobile.
4. **LOGO & BỐ CỤC:**
   - Logo Sao Việt đặt tự nhiên ở góc trên (trái hoặc phải). Không vẽ lại méo mó hay thêm chữ lạ.
   - Tuyệt đối KHÔNG viền mạch điện neon tối tăm (Style 3 neon đã bị xóa bỏ hoàn toàn).
   - Tuyệt đối CẤM in đường dẫn file (`attachments/...`, `.png`) lên ảnh.

## Prompt kiểu 1: Poster Mockup Studio 1:1 VUÔNG (Bắt mắt, thu hút, chuẩn chuyển đổi)

```
Deliverable: 1 Facebook cover poster SQUARE 1:1 (2000x2000 px), ultra eye-catching commercial education studio poster.

STYLE & LIGHTING:
- Vibrant, crisp, high-contrast commercial studio lighting. Bright and professional education brand atmosphere.
- Clean Corporate Royal Blue gradient background with soft modern 3D depth and subtle geometric lighting.

HERO SUBJECT (Grounding in Reference Image):
- A young, confident Vietnamese/Asian professional or student smiling sitting by a modern laptop.
- Must reflect authentic Vietnamese learners from the attached classroom reference photo, NOT Caucasian/Western stock models.

3D FLOATING ELEMENTS (Eye-Catching & Dynamic):
- Glossy floating 3D icons of industry tools with realistic lighting and soft drop shadows: [Word, Excel, PowerPoint for Office / AutoCAD gears for CAD / Misa & Excel charts for Accounting / Photoshop & Illustrator for Design].

TYPOGRAPHY (STRICTLY VIETNAMESE, NO ENGLISH WORDS):
- Top bold headline: "[TEN KHOA HOC IN HOA]" (Clean white/golden yellow bold sans-serif, high contrast).
- Sub-headline: "[Ky nang thuc chien - Cam tay chi viec]".
- Highlight Badge: Rounded golden yellow pill badge "UU DAI 30% HOC PHI - KEM 1-1".
- Top corner: Exact Sao Viet logo.
- Footer bar: "TRUNG TAM TIN HOC SAO VIET - Hotline: 093 1144 858".

CRITICAL QUALITY RULES:
- Zero English words (NO 'Enroll now', NO 'Office IT', NO 'Course').
- Razor-sharp typography within 18% safe margin, no overlapping letters, no dark neon circuits.
```

## Prompt kiểu 2: Ảnh gốc dataset 1:1 + Khung thương hiệu sắc nét

```
Deliverable: 1 Facebook cover poster SQUARE 1:1 (2000x2000 px).

BASE LAYER (Anh 1 - Raw Dataset):
- Use the authentic Vietnamese classroom photo from attachments/dataset as the primary background/central visual.
- Enhance lighting, color vibrancy, and clarity while keeping the real Vietnamese students and instructors genuine.

BRAND OVERLAY & BANNER:
- Bottom lower-third banner: Sleek Royal Blue gradient bar with crisp typography.
- Headline: "[TEN KHOA HOC IN HOA]" (Bold white text).
- Badge: "DẠY KÈM 1-1 - KHÔNG GIỚI HẠN SỐ BUỔI".
- Top Corner: Logo Sao Viet cleanly placed.
- Footer info: Hotline & Website.
- All text in Vietnamese with correct accents.
```

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
