---
type: source
updated: 2026-09-03
---
# Xoay mau cover (cam lap panel navy phai)

Logo luon file `chung/thsv-logo-2025.png`. Khong tin logo ve trong poster.

## GIU (brand Sao Viet)

- `mau-tre-em-teal-inset.png`: poster xanh ngoc, anh lop that trong vong, badge uu dai, Python/Scratch. Dung khoa tre em / lap trinh tre.
- `mau-tre-em-scratch-laptop.png`: nen mint, laptop Scratch, list Python/Scratch. Dung khoa tre em.
- `mau-A-full-thanh-duoi.jpg`: anh lop full khung, thanh chu DUOI, khong chia 50/50.
- `mau-khoa-hoc-co-anh-goc.png`: anh that + chu, khong bat buoc panel navy phai.
- `mau-A-split-navy.jpg`: TRAI anh / PHAI navy. Chi dung khi 2 cover gan nhat KHONG phai split.
- `mau-B-le-do-vang.jpg`, `mau-lich-le-tu-gen.png`: le Tet/Quoc khanh.
- `mau-B-thong-bao-navy.jpg`: CHI lay khung 2 the. Bo chu FPT/VNG.
- `mau-poster-do-hoa.png`: poster mockup (ban may, icon Ps/Ai, to roi, chu lon). Mau cho **kieu cover 1**. Do hoa uu tien file nay. Khoa khac van bam layout (icon + chu + CTA), doi chu dung nganh.
- `mau-poster-neon-do-hoa.png`: poster Master Graphic Design neon xanh navy, nam designer tap trung ben laptop, anh sang viền neon, icon Ps/Ai 3D phat quang, chu vang chanh noi bat. Mau cho **kieu cover 3**.
- `mau-poster-neon-tin-hoc-xanh.png`: poster Microsoft Office xanh ngoc - xanh duong, nu sinh vien cam laptop tuoi cuoi, huy hieu giam 50%, icon Word/Excel/PowerPoint bay 3D.
- `mau-poster-neon-tin-hoc-do.png`: poster do ruby bat mat, chu 3D trang, huy hieu uu dai hoc phi, icon Office, phong may phia sau.
- `mau-poster-neon-chuc-mung-tim.png`: poster tim neon cosmic, hoc vien an mung hao hung, dai song nang luong neon, icon Adobe 3D.
- `mau-poster-3d-trung-tam.png`: poster 3D toa nha / trung tam noi bat giua pho phuong, chu 3D do trang thong bao co so / he thong.

## BO (brand khac, cam lam mau)

- Poster Dai hoc Bach Khoa / BK.
- Trung tam Tin Hoc Truong Thinh Vung Tau (hotline 0933008831).
- Poster Zoom + giao trinh Python xanh la (logo khong phai Sao Viet).
- Bat ky logo/hotline/web khong phai Sao Viet.

## Cover = 6 Layout Agency Đồ Họa Thực Chiến 1:1 VUÔNG (Chuẩn Facebook 2026)

Mọi cover khóa học mặc định 100% sử dụng Deterministic Graphic Engine (banner_templates.py) kết hợp ảnh thật dataset hoặc ảnh 3D visual sạch + logo Sao Việt chuẩn vector/PNG + typography tiếng Việt chuẩn Unicode font Arial Bold / Segoe UI Bold:
1. **split_right:** Cột trái (50%) là ảnh lớp học thật, cột phải (50%) là panel xanh navy thương hiệu với logo góc trên, tiêu đề lớn, gạch phân cách vàng kim, 3 điểm nổi bật và hotline.
2. **split_left:** Đảo vị trí panel sang bên trái, ảnh thật bên phải nhằm tạo sự phong phú giữa các bài viết.
3. **bottom_bar:** Ảnh chụp lớp học góc rộng sáng sủa chiếm 70% phía trên, dải panel thương hiệu navy chiếm 30% chân trang cùng các huy hiệu viên thuốc bo tròn hiện đại.
4. **floating_card:** Ảnh lớp học tràn nền, một card thông tin bo góc nổi khối 3D với viền vàng ánh kim và bóng đổ mềm mại.
5. **diagonal_slice:** Đường cắt vát chéo góc công nghệ hiện đại, tạo cảm giác chuyển động và tràn đầy năng lượng.
6. **3d_pills:** Bố cục hiện đại cho ảnh 3D AI hoặc ảnh công sở: nhân vật thao tác ở nửa phải (50%), nửa trái là 3 thẻ viên thuốc xanh navy bo góc ôm khít chữ tiếng Việt chuẩn Unicode, logo Sao Việt trên thẻ trắng góc trên.

*(TUYỆT ĐỐI CẤM: Để AI tự vẽ chữ tiếng Việt lên ảnh dẫn đến lỗi font méo dấu như KÉ TOÀN, TÀI CHINC, PHỞNG, KẾM; CẤM để AI vẽ khung rỗng mất logo; CẤM style neon mạch điện tối tăm).*

Xoay luân phiên 6 kiểu cover 1:1 trên. Cấm 2 bài liên tiếp cùng 1 kiểu.
Logo: Bắt buộc dùng file `attachments/dataset/chung/thsv-logo-2025.png` trên thẻ bo góc nổi khối, luôn sắc nét 100%.
Hotline trên poster: Lấy đúng từ brand kit hoặc mặc định 0931144858 / 0823552558.
CẤM mở `_xuat/` để tái sử dụng. Đăng xong là xóa file tạm.

---

## MASTER SYSTEM PROMPT - KIẾN TRÚC TẠO ẢNH CHO MỌI KHÓA HỌC (CHỐNG LỖI FONT VÀ LỆCH BỐ CỤC 100%)

### 1. NGUYÊN TẮC BẤT BIẾN (IMMUTABLE RULES)
* **Quy tắc 1 (Zero Text in AI):** Mọi mô hình AI diffusion (Imagen 3, Flux, DALL-E, Midjourney) đều không có bộ gõ Unicode tiếng Việt, chỉ phỏng đoán pixel dẫn đến sai dấu. TUYỆT ĐỐI KHÔNG để AI vẽ chữ tiếng Việt hoặc logo. Chữ tiếng Việt và Logo luôn do code (Pillow Engine) hoặc phần mềm đồ họa chèn vào.
* **Quy tắc 2 (Strict Spatial Reservation - Chống lệch):** AI chỉ vẽ chủ thể ở nửa phải (x: 50% đến 100%). Nửa trái (x: 0% đến 50%) bắt buộc là không gian sạch (Clean Negative Space / Copy Space) với ánh sáng dịu để chèn chữ và logo.

### 2. BỘ KHUNG 5 KHỐI PHỔ QUÁT (THE UNIVERSAL 5-BLOCK FRAMEWORK)
Mọi prompt tạo ảnh cho bất kỳ ngành học nào đều cấu thành từ 5 khối:
* **[BLOCK 1 - SUBJECT]:** Nhân vật người Việt/Châu Á công sở, giảng viên hoặc học viên tự tin, tập trung làm việc trên máy tính/laptop trong văn phòng hiện đại.
* **[BLOCK 2 - COMPOSITION (CHỐNG LỆCH)]:** Tỷ lệ vuông 1:1 (2000x2000 px). Khóa chủ thể ở nửa bên phải (x: 50% đến 100%). Nửa bên trái (x: 0% đến 50%) là hậu cảnh văn phòng mờ sạch sẽ, hoàn toàn để trống làm copy space.
* **[BLOCK 3 - LIGHTING & BRAND PALETTE]:** Ánh sáng Studio thương mại cao cấp. Tông màu xanh Royal Navy Blue (#0B2341), điểm xuyết ánh vàng kim (#F59E0B / #FFD700) và sắc trắng trang nhã.
* **[BLOCK 4 - VISUAL ANCHORS (ICON 3D THEO NGÀNH)]:**
  - Tin học văn phòng & AI: Icon 3D bóng bẩy nổi trong không khí của Word, Excel, PowerPoint hoặc biểu tượng node AI.
  - Kế toán thực hành: Icon 3D bảng biểu tài chính MISA, biểu đồ tăng trưởng, hóa đơn điện tử.
  - AutoCAD / Vẽ kỹ thuật: Bản vẽ kỹ thuật 2D/3D wireframe, thước đo kỹ thuật số, chi tiết máy.
  - Thiết kế đồ họa: Icon 3D Photoshop, Illustrator, vòng tròn màu sắc palette, bút vẽ kỹ thuật số.
* **[BLOCK 5 - STRICT NEGATIVE (CẤM CHỮ TOÀN DIỆN)]:**
  `STRICT NEGATIVE: Absolutely NO text, NO words, NO letters, NO numbers, NO typography, NO watermark, NO logo, NO labels, NO gibberish, NO distorted anatomy, NO extra fingers, clean empty copy space on the left.`

---

### 3. NGUYÊN TẮC ĐỘC QUYỀN 1 TẦNG CHỮ (CHỐNG ĐÁ NHAU VÀ SAI CHÍNH TẢ 100%)

TUYỆT ĐỐI KHÔNG BAO GIỜ vừa yêu cầu AI vẽ chữ, vừa dùng code chèn thẻ chữ lên cùng một ảnh.
Thực tế đã chứng minh: Các mô hình AI diffusion luôn bị hallucinate sai chính tả tiếng Việt (như 'PoweProont', 'HỌY KỂM', mất dấu) và gây ra thảm họa 2 tầng chữ đè lên nhau.

QUY TRÌNH CHUẨN DUY NHẤT ÁP DỤNG TRÊN TOÀN HỆ THỐNG:
1. **AI (Google Imagen):** Chỉ vẽ nền visual sạch (nhân vật, bàn làm việc, laptop). Nửa bên trái bắt buộc là nền navy trơn/mờ sạch sẽ, cấm vẽ chữ 100%.
2. **Engine Đồ Họa (Pillow):** Là đơn vị duy nhất chịu trách nhiệm dán chữ (tiêu đề, ưu đãi, kèm 1-1) và dán logo Sao Việt chuẩn Unicode lên ảnh.

Nhờ vậy, bức ảnh chỉ có DUY NHẤT 1 tầng chữ sắc nét, 0% rủi ro sai chính tả, và 0% rủi ro bị đè/đá nhau!


