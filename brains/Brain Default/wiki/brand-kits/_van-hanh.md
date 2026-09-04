---
type: wiki
updated: 2026-09-03
---
# Vận hành nhiều Fanpage Sao Việt

Một hệ, nhiều page. **Không** một goal đăng hết 11 trang.

## 3 lớp (đừng trộn)

| Lớp | Chỗ | Việc |
|---|---|---|
| Giọng chung | `_mac-dinh.md` + 2 logo `attachments/thsv-logo-*.png` | USP, cấm, CTA, hashtag gốc |
| Giọng từng page | `thsv-*.md` | Địa chỉ, khoá thế mạnh, hashtag địa phương |
| Chạy việc | trang Việc | 1 goal = 1 page = 1 bài |

Đổi giọng cả chuỗi: sửa mặc định. Đổi cơ sở Q.6: chỉ `thsv-q6.md`.

## Hai cửa (đừng nhầm Route)

- **Soạn bài Facebook** → nháp `sources/facebook-nhap/<slug>/YYYY-MM-DD.md`, **không** lên tường.
- **Đăng Facebook** → lên tường, xong phải có `post_id`. Goal ngắn đủ (vd Trung thu Royce Shop).

Mặc định hằng ngày: cửa Soạn. Cửa Đăng khi muốn lên tường.

## Luật 1-1-1 (Nghiệp vụ bắt buộc)

Mỗi thẻ Việc:
- 1 Fanpage (tên đầy đủ + slug)
- 1 chủ đề / 1 brief duy nhất
- 1 folder ảnh tương ứng theo chữ trong brief (không đoán bừa)

Engine đang chạy là Grok (hoặc engine user chọn). Gen ảnh bằng tool CỦA ENGINE (Grok: `image_gen` / `image_edit`). **CẤM** bắt ChatGPT. **CẤM** `javis_generate_image` nếu engine này không có tool đó. **CẤM** sửa `server/`. **CẤM** đăng file dataset gốc.

### 1. Chọn folder theo CHỮ brief
Mở folder, liệt kê file rồi chọn, không đoán bừa:
- Word / Excel / văn phòng / MOS → `attachments/dataset/tin-hoc/`
- AutoCAD / SolidWorks / cơ khí → `attachments/dataset/co-khi/`
- Kế toán / chứng từ / sổ sách → `attachments/dataset/ke-toan/`
- Photoshop / đồ họa → `attachments/dataset/do-hoa/`
- Ads / SEO / Marketing → `attachments/dataset/marketing/`
- AI / ChatGPT / Copilot → `attachments/dataset/ai/`
- Trẻ em / Scratch / Lập trình nhí → `attachments/dataset/tre-em/`
- Tiếng Hàn → `attachments/dataset/tieng-han/`
- Logo → `attachments/dataset/chung/` (chỉ làm watermark, không bao giờ làm ảnh bài)

Không file nào khớp chủ đề (lịch nghỉ, thông báo, sự kiện) → **KHÔNG** lấy ảnh ngành khác cho có.

### 2. Hai kiểu sinh ảnh (Lưu vào `attachments/dataset/_xuat/`)
- **Kiểu A - CÓ ảnh gốc phù hợp**:
  + Mẫu: `attachments/dataset/_mau/mau-khoa-hoc-co-anh-goc.png`
  + Gen/edit landscape: trái = ảnh gốc lớp/người; phải = panel xanh đậm, tiêu đề khoá TO, 2 lợi ích, logo Sao Việt góc trên (`chung/thsv-logo-2025.png`).
  + `images = [ảnh gốc đã chọn, logo, file mẫu A]`
- **Kiểu B - KHÔNG có ảnh phù hợp**:
  + Mẫu: `attachments/dataset/_mau/mau-lich-le-tu-gen.png`
  + Tự gen poster: logo Sao Việt, tiêu đề sự kiện, khối ngày/giờ hoặc thông tin, màu brand.
  + `images = [logo, file mẫu B]`

Lưu gen `_xuat/`. Phí: tối đa 3 gen, mặc định 1 cover gen + 4-5 gốc. Cover luôn `_xuat`. Kiểu B: 1 poster. Goal chỉ cần vài chữ, skill tự bung.

### 3. Caption + Chân trang SEO
- Đọc `wiki/brand-kits/_mac-dinh.md` + kit đúng slug (test: `royce-shop.md`, page = `Royce Shop`).
- 1 brief duy nhất: đúng trọng tâm, không trộn lẫn ngành.
- Chân trang bắt buộc: Pháp nhân Công Ty TNHH Giáo Dục Tin Học Sao Việt, MST 3603708616, Hotline 0931144858, email trungtamtinhocsaoviet@gmail.com, website tinhocsaoviet.com.

### 4. 4 điều cấm tuyệt đối (Chặn lỗi vận hành)
1. **CẤM đăng file dataset gốc**: Phải gen theo mẫu A hoặc B và lưu vào `attachments/dataset/_xuat/`. CẤM gọi `fb_page_photo` với đường dẫn file gốc trong `/tin-hoc/`, `/co-khi/`, `/ke-toan/`, `/chung/`.
2. **Bám sát file mẫu, cấm poster tối giản**: Kiểu A bám sát `attachments/dataset/_mau/mau-khoa-hoc-co-anh-goc.png`, kiểu B bám sát `attachments/dataset/_mau/mau-lich-le-tu-gen.png` (đủ họa tiết lễ hội đỏ vàng, đèn lồng, trăng, 2 khối lịch; cấm vẽ poster 4 vòng đèn tối giản).
3. **Khớp ngày tháng và số liệu**: Ngày tháng và số liệu giữa caption và chữ trên ảnh bắt buộc giống nhau 100%. Nếu lệch phải sửa caption theo ảnh trước khi đăng, tuyệt đối không đăng bài khi số liệu lệch nhau.
4. **Đăng đúng 1 lần, CẤM tự xóa bài**: Gọi `fb_page_photo` đúng 1 lần duy nhất. CẤM gọi `fb_page_delete` trừ khi user yêu cầu đích danh kèm post_id cần xóa; tuyệt đối không đăng thử rồi tự xóa bài.

Cấm: "1 tuần 10 bài", "đăng hết page". Meta dễ spam, worker Grok treo, kit bị trộn địa chỉ.

Muốn 5 page trong ngày: **5 goal**, lệch giờ (vd 8h, 10h, 12h, 15h, 18h), không bắn cùng phút.

## Lịch tuần (gợi ý, sửa theo lịch khai giảng)

| Ngày | Page (slug) | Góc |
|---|---|---|
| T2 | thsv-binh-thanh, thsv-q6 | Văn phòng + AI ca tối |
| T3 | thsv-cad-bien-hoa, thsv-q12 | AutoCAD / văn phòng Q.12 |
| T4 | thsv-do-hoa-vung-tau, thsv-ai | Đồ họa / AI |
| T5 | thsv-ads-bien-hoa, thsv-bien-hoa | Ads / tin học Biên Hòa |
| T6 | thsv-binh-duong, thsv-long-thanh | BD / Long Thành |
| T7 | thsv-vung-tau | Văn phòng Vũng Tàu |

Page chuyên môn **không bán chéo**: CAD không bán kế toán, Ads không bán Photoshop.

## Nháp theo page (đừng đè 1 file)

`sources/facebook-nhap/<slug>/YYYY-MM-DD.md`

File cũ `sources/facebook-nhap.md` chỉ là nháp lẻ. Nhiều page thì tách thư mục.

## Goal mẫu

Soạn:

```
Soạn 1 caption [khoá] cho trang [slug]
Route = Workflow Soạn bài Facebook
```

Đăng (Route = Workflow Đăng Facebook), Goal chỉ cần:

```
Trung thu Royce Shop
```

```
kế toán ca tối Royce Shop
```

## Ai duyệt

Nháp: workflow Soạn. Lên tường: workflow Đăng, Goal ngắn. Loop 24/7 tự đăng: không bật trừ khi bạn nói rõ.