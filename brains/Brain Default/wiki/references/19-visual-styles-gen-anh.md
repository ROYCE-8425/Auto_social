# Thư Viện 19 Visual Styles Tạo Ảnh AI — Hệ Thống Đào Tạo Sao Việt

Tài liệu tham chiếu chuẩn hóa 19 phong cách thiết kế hình ảnh AI (Prompt Templates) cho hệ thống Tin Học Sao Việt, Trung Tâm Đào Tạo AutoCAD Sao Việt, Trung Tâm Đào Tạo Kế Toán Sao Việt và Trung Tâm Thiết Kế Đồ Họa Sao Việt.

> 📐 **Quy chuẩn tỷ lệ**:
> - **Mặc định Facebook Album (Chuẩn Tỷ Lệ Vàng 2026)**: Xuất bản ảnh VUÔNG 1:1 (`1024×1024px`) đồng bộ với các ảnh lớp học thật.
> - **Kênh TikTok / Facebook Reels Carousel / Story**: Chuyển sang khung DỌC 9:16 (`1080×1920px`) với vùng an toàn Safe Zone (Y 320–1480px, X 120–960px).

> 🎨 **Bảng màu nhận diện thương hiệu chuẩn (Brand Palette)**:
> - `#5EB9F0`: Xanh dương nhận diện Sao Việt (Primary Blue)
> - `#343F52`: Xanh đen đậm uy tín (Deep Navy)
> - `#FAB758`: Cam vàng kim tạo điểm nhấn (Gold Accent)
> - `#0077C8`: Xanh đậm nút hành động (CTA Blue)
> - `#F0F8FE`: Nền trắng tuyết dịu mắt (Warm Ice White)

---

## BẢN ĐỒ ÁNH XẠ: CHUYÊN MÔN KHOÁ HỌC ➔ VISUAL STYLES NÊN DÙNG

| Nhóm ngành đào tạo | Visual Styles phù hợp nhất | Bố cục & Visual Elements |
| :--- | :--- | :--- |
| **Bản vẽ kỹ thuật & AutoCAD** | • Mẫu 4: Isometric 3D Workspace<br>• Mẫu 5: Before / After Split Screen<br>• Mẫu 12: Bold Typography Poster | Bàn làm việc 3D kỹ thuật, bản vẽ CAD 2D/3D, màn hình layer, kích thước chuẩn, chia đôi trước/sau. |
| **Kế toán thực hành** | • Mẫu 19: Corporate Professional<br>• Mẫu 18: Resource & Document Catalog<br>• Mẫu 5: Before / After Chứng từ | Sổ sách, hóa đơn VAT, bảng kê khai thuế, phần mềm kế toán MISA/Excel, biểu đồ báo cáo tài chính. |
| **Thiết kế đồ họa** | • Mẫu 10: Magazine Editorial<br>• Mẫu 17: Gradient Mesh (Apple/Stripe)<br>• Mẫu 16: Flat Illustration (Notion/Figma) | Tạp chí hiện đại, màu chuyển sắc tinh tế, sản phẩm thiết kế truyền thông, poster, typography thanh lịch. |
| **Tin học văn phòng & AI** | • Mẫu 2: High-Conversion AI Banner<br>• Mẫu 7: Glassmorphism UI (Kính mờ)<br>• Mẫu 9: Neon Tech Banner<br>• Mẫu 3: Infographic Roadmap | Dashboard dữ liệu, bảng tính Excel, thẻ quy trình AI, giao diện kính mờ hiện đại, neon phát sáng nhẹ. |
| **Tin học & Lập trình thiếu nhi** | • Mẫu 14: Pastel Friendly Kids | Phong cách Bắc Âu pastel nhẹ nhàng, khối lệnh Scratch nhiều màu, robot thân thiện, vừa mắt phụ huynh & trẻ. |
| **Cảm nhận học viên (Feedback)** | • Mẫu 13: Student Feedback Messenger | Bong bóng tin nhắn Messenger/Facebook thật, đánh giá 5 sao, card cam kết đào tạo thực tế. |
| **Tuyển sinh & Khai giảng tổng quan** | • Mẫu 1: Canva Grid 2x2 hoặc 4 khung<br>• Mẫu 8: Modern Recruitment / Opening Ad | Bố cục card bo góc hiện đại, các pill badge quyền lợi, tương phản mạnh, thu hút trên di động. |

---

## CHI TIẾT 19 PROMPT VISUAL STYLES (CHUẨN VUÔNG 1:1 & DIACRITICS)

### Mẫu 1: 2x2 Canva-style Grid (Bố cục 4 khung kể chuyện)
```text
Create a modern 2x2 Canva-style educational advertising banner (1024x1024px, 1:1 square ratio) for:
COURSE NAME: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Style: bright, clean, modern Facebook education ads, realistic Canva poster design, highly readable, professional educational marketing style.
Color palette: #F0F8FE background, #5EB9F0 primary blue, #343F52 deep navy, #FAB758 gold accent, #0077C8 CTA blue, #FFFFFF cards.
Layout: connected 2x2 grid, each panel has different composition but connected as one campaign:
- Panel 1: course introduction with professional workspace and course-related interface.
- Panel 2: common beginner problems / messy workflow related to the course.
- Panel 3: learning transformation and optimized practical workflow.
- Panel 4: professional result, completed project, success.
Safe Zone: keep all text and graphics inside center 80% safe zone with 15-20% margin from all edges.
Logo handling: Do not draw or recreate logo. Keep natural quiet negative space at top-left.
Vietnamese text to render: "[TIÊU_ĐỀ_KHÓA]" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 2: High-Conversion AI Education Banner
```text
Design a modern high-conversion tech education banner (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: premium corporate AI productivity workspace, clean light blue background (#F0F8FE), modern floating workflow cards, laptop screen displaying smart tools, report outline, automated dashboard.
Color palette: #5EB9F0 primary blue, #343F52 deep navy, #FAB758 accent gold, #00C2D8 cyan glow.
Layout: centered card layout with generous whitespace, bold typography hierarchy.
Safe Zone: keep all text and graphics inside center 80% safe zone with 15-20% margin from all edges.
Logo handling: Do not draw or recreate logo. Keep natural quiet negative space at top-left.
Vietnamese text to render: "[TIÊU_ĐỀ_KHÓA]" · "HỌC THỰC HÀNH — ỨNG DỤNG NGAY" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 3: Infographic Roadmap (Lộ trình học trực quan)
```text
Design an infographic learning-roadmap education banner (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: clean modern learning path with 4 sequential milestone badges connected by a #5EB9F0 dotted line:
1. "GIAI ĐOẠN 1" — Nền tảng & Phím tắt
2. "GIAI ĐOẠN 2" — Thực hành dự án thật
3. "GIAI ĐOẠN 3" — Tối ưu quy trình & Xử lý lỗi
4. "HOÀN THÀNH" — Sẵn sàng đi làm (badge #FAB758)
Color palette: #FFFFFF cards, #F0F8FE background, #5EB9F0 primary, #343F52 text, #FAB758 accent.
Safe Zone: 15-20% margin from all edges. No text touching boundaries.
Logo handling: Do not draw or recreate logo. Keep quiet negative space at top-left.
Vietnamese text to render: "LỘ TRÌNH HỌC [TÊN_KHÓA]" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 4: Isometric 3D Workspace (Bàn làm việc 3D công nghệ)
```text
Design a clean isometric 3D workspace education banner (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: modern isometric 3D illustration of a professional desk setup — computer screen displaying course software UI, technical drawings/spreadsheets, floating 3D icons in #FAB758 (certificate, gear, lightbulb, star), neat desk plant, coffee cup.
Color palette: #F0F8FE background, #5EB9F0 workspace elements, #343F52 dark accents, #FAB758 highlights.
Layout: centered 3D desk with bold typography above and below.
Safe Zone: 15-20% padding from all borders.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "[TIÊU_ĐỀ_KHÓA]" · "ĐÀO TẠO KÈM 1-1 THỰC CHIẾN" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 5: Before / After Split Screen (Chia đôi so sánh trước - sau)
```text
Design a split before/after comparison education banner (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Layout: 50/50 split screen (left vs right or top vs bottom inside safe zone):
- Side 1 (TRƯỚC KHI HỌC): messy workspace, confusing errors, slow manual workflow, muted #343F52 and subtle red warning tone. Label: "TRƯỚC".
- Side 2 (SAU KHI HỌC): clean professional workspace, completed project, fast automated result, bright #5EB9F0 and gold #FAB758 stars. Label: "SAU".
Divider: clean gradient line with arrow.
Safe Zone: 15-20% margin from all edges.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "TRƯỚC KHI HỌC" · "SAU KHI HỌC" · "[TÊN_KHÓA_HỌC]" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 6: Creative Comparison & Workflow Upgrade
```text
Create a modern creative educational comparison banner (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: realistic educational creative advertising, contrast between slow outdated methods and modern high-speed tools. High contrast, premium Canva poster aesthetic.
Color palette: #F0F8FE ice white, #5EB9F0 cyan blue, #343F52 dark navy, #FAB758 energetic gold.
Safe Zone: 15-20% padding from all canvas borders.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "[TIÊU_ĐỀ_KHÓA]" · "TỐI ƯU HIỆU SUẤT ĐI LÀM" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 7: Glassmorphism UI (Kính mờ công nghệ cao)
```text
Design a glassmorphism-style vertical/square education banner (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: modern frosted glass UI cards floating on a soft gradient background (#041C3F dark navy → #343F52 with blurred #5EB9F0 and #FAB758 gradient blobs).
Glass cards: semi-transparent white rgba(255,255,255,0.15) with subtle #5EB9F0 border glow, soft depth blur.
Content: course title bold white, 3 stat pill badges ("100% Thực hành" · "Kèm 1-1" · "Cam kết việc làm").
Safe Zone: 15-20% margin from all edges.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "[TÊN_KHÓA_HỌC]" · "CÔNG NGHỆ THỰC CHIẾN" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 8: Modern Recruitment / Opening Ad (Tuyển sinh & Khai giảng)
```text
Design a modern educational opening-class poster (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: bold, clean, attention-grabbing education ad. Large white card with soft shadow, big readable typography, 3 benefit pill tags ("Học kèm 1-1" · "Thời gian linh hoạt" · "Cấp chứng chỉ").
Color palette: #F0F8FE background, #5EB9F0 primary, #343F52 headline, #FAB758 accent star, #0077C8 CTA.
Safe Zone: 15-20% padding from all borders.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "KHAI GIẢNG LỚP MỚI" · "[TÊN_KHÓA_HỌC]" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 9: Neon Tech Banner (Công nghệ & Tông tối hiện đại)
```text
Design a modern tech-education banner (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: deep navy gradient background (#041C3F → #343F52), subtle cyan #5EB9F0 neon glow, floating UI cards showing course software and data streams, gold #FAB758 highlight points.
Typography: bold white headlines, #E5F4FD subtext.
Safe Zone: 15-20% margin from all edges.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "[TÊN_KHÓA_HỌC]" · "LÀM CHỦ KỸ NĂNG CÔNG NGHỆ" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 10: Magazine Editorial (Tạp chí thời thượng & Nghệ thuật)
```text
Design a premium magazine-style editorial education banner (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: high-end editorial magazine layout, sophisticated typography, generous whitespace, clean flat-lay of course-related tools on a designer desk, thin rule lines.
Color palette: warm ice white #F0F8FE, deep navy #343F52 headline, #5EB9F0 accent rules, #FAB758 category label.
Safe Zone: 15-20% margin from all edges.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "CHUYÊN ĐỀ ĐÀO TẠO" · "[TÊN_KHÓA_HỌC]" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 11: Glassmorphism Card Infographic
```text
Design an advanced glassmorphism infographic banner (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: frosted glass information cards showing course modules and practical competencies. Blurred organic ambient background, sleek drop shadows.
Color palette: #0B1F45, #5EB9F0, #FAB758, frosted white cards rgba(255,255,255,0.18).
Safe Zone: 15-20% margin from all edges.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "[TÊN_KHÓA_HỌC]" · "LỘ TRÌNH THỰC CHIẾN" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 12: Bold Typography Poster (Chữ lớn phong cách Thụy Sĩ)
```text
Design a bold typography-driven education poster (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: Swiss/International typographic design. Course name fills ~40% of canvas in ultra-bold condensed sans-serif, maximum readability, strong solid background (#5EB9F0), clean white typography (#FFFFFF), geometric accent shape in gold (#FAB758).
Safe Zone: 15-20% margin from all edges.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "[TÊN_KHÓA_HỌC]" · "HỌC LÀ LÀM ĐƯỢC" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 13: Student Feedback Review Messenger (Cảm nhận học viên)
```text
Design a student-feedback review education banner (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: 2-3 realistic Messenger chat bubble cards with glowing reaction icons and 5-star ratings, demonstrating student satisfaction and real career progress. Beside it, a badge of training guarantees.
Color palette: #F0F8FE background, #FFFFFF cards with soft shadows, #5EB9F0 accents, #FAB758 5-star badges.
Safe Zone: 15-20% margin from all edges.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "ĐÁNH GIÁ TỪ HỌC VIÊN" · "[TÊN_KHÓA_HỌC]" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 14: Pastel Friendly Kids (Lập trình & Tin học thiếu nhi)
```text
Design a friendly pastel education banner for kids coding & computer classes (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: Scandinavian children's education illustration, friendly robot and laptop with colorful Scratch code blocks, pastel stars, lightbulbs, game controllers. Soft rounded corners, gentle and appealing to both parents and kids.
Color palette: #F0F8FE background, pastel sky blue #5EB9F0 (50%), soft sunny yellow #FAB758 (60%), mint green, peach, deep navy text #343F52.
Safe Zone: 15-20% margin from all edges.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "[TÊN_KHÓA_HỌC]" · "ƯƠM MẦM TƯ DUY CÔNG NGHỆ" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 15: Dark Premium (Đào tạo chuyên sâu & Doanh nghiệp)
```text
Design a luxury dark-theme vertical/square education banner (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: exclusive dark premium theme, deep navy gradient #041C3F → #343F52, gold #FAB758 fine lines and milestone bullets, glossy 3D render of course emblem/laptop with reflection.
Color palette: luxury dark navy, gold accent #FAB758, silver white text #E5F4FD.
Safe Zone: 15-20% margin from all edges.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "CHƯƠNG TRÌNH CHUYÊN SÂU" · "[TÊN_KHÓA_HỌC]" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 16: Flat Illustration (Minh họa phẳng phong cách Notion / Figma)
```text
Design a modern flat vector illustration education banner (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: modern geometric flat vector illustration (Notion / Slack brand style), clean collaboration scene with stylized characters working with course software, progress checkmarks, stars.
Color palette: #F0F8FE background, #5EB9F0 primary shapes, #343F52 dark accents, #FAB758 gold points.
Safe Zone: 15-20% margin from all edges.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "[TÊN_KHÓA_HỌC]" · "HỌC THỰC HÀNH — LÀM ĐƯỢC VIỆC" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 17: Gradient Mesh (Lưới Gradient hiện đại phong cách Apple / Stripe)
```text
Design a contemporary gradient-mesh education banner (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: fluid organic gradient mesh #5EB9F0 → #0077C8 → #343F52 with subtle warm #FAB758 glow, frosted glass pill tags, clean bold white typography with subtle shadow.
Safe Zone: 15-20% margin from all edges.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "[TÊN_KHÓA_HỌC]" · "TIÊU CHUẨN ĐÀO TẠO 2026" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 18: Resource & Document Catalog (Thư viện tài liệu & File mẫu)
```text
Design a modern educational resource catalog banner (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: clean Canva grid / catalog showcasing practical templates, sample files, calculation sheets, technical libraries. Realistic icons, badge "TẶNG MIỄN PHÍ" in energetic gold #FAB758.
Color palette: #F0F8FE background, #5EB9F0 blue, #343F52 navy, #FAB758 accent.
Safe Zone: 15-20% margin from all edges.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "TRỌN BỘ TÀI LIỆU THỰC CHIẾN" · "[TÊN_KHÓA_HỌC]" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```

### Mẫu 19: Corporate Professional (Đào tạo doanh nghiệp B2B)
```text
Design a corporate professional training banner (1024x1024px, 1:1 square ratio).
COURSE: [TÊN_KHÓA_HỌC]
BRAND: [TÊN_BRAND]
Visual style: McKinsey / Deloitte corporate presentation quality. Deep navy header block (#343F52), gold accent line #FAB758, white body text, enterprise training benefits (in-house training, customized syllabus, completion certificate).
Color palette: #343F52 dark navy, #FFFFFF, #FAB758 gold, #5EB9F0 secondary.
Safe Zone: 15-20% margin from all edges.
Logo handling: Do not draw logo. Keep quiet negative space at top-left.
Vietnamese text to render: "ĐÀO TẠO DOANH NGHIỆP" · "[TÊN_KHÓA_HỌC]" · "[TÊN_BRAND]"
All Vietnamese text must be rendered with full, correct Vietnamese diacritics (dấu thanh + dấu mũ/móc). Do NOT omit, simplify, romanize, or alter any diacritical marks.
```
