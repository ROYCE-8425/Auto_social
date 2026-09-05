---
type: wiki
updated: 2026-09-04
---
# Vận hành nhiều Fanpage

Một hệ, nhiều page. **Không** một goal đăng hết trang nếu thẻ ngành không khớp.

## 4 lớp (đừng trộn)

| Lớp | Chỗ | Việc |
|---|---|---|
| Giọng chung | `_mac-dinh.md` | USP, cấm, CTA, pháp nhân |
| Thẻ ngành | `_the-khoa-hoc.md` + folder `attachments/dataset/<id>/` | 1 thẻ = 1 khoá / 1 kho ảnh |
| Từng page | kit page (tên = tên Fanpage) | Page ID Facebook, thẻ 1–nhiều, địa chỉ |
| Chạy việc | Chat / Việc | 1 goal = 1 chủ đề; chỉ page **có kit** và **có thẻ khớp** |

Default kit: `Thẻ khoá học: all` (full, kể cả thẻ mới).
Page chuyên đồ họa: chỉ thẻ `do-hoa` → bài kế toán **không** lên page đó.

## Hai cửa

- **Soạn bài Facebook** → nháp `sources/facebook-nhap/<slug>/YYYY-MM-DD.md`, không lên tường.
- **Đăng Facebook** → lên tường, phải có `post_id`.

## Luật 1 chủ đề → nhiều page (lọc thẻ)

Khi user bảo “1 ngày 1 bài cho toàn bộ page”:

1. Xác định **1 thẻ** từ brief (đồ họa / kế toán / vẽ kỹ thuật / tin học-AI…).
2. Lấy danh sách kit page có `Page ID` và thẻ chứa id đó (hoặc `all`).
3. Page không kit hoặc không thẻ → `POST_SKIP ly-do=khong-dung-the`. Không gọi Facebook.

Ảnh lấy đúng folder `attachments/dataset/<id-the>/`. Không lấy ngành khác cho có.

### Map chữ brief → thẻ (folder trên đĩa)

- Word, Excel, văn phòng, MOS, AI văn phòng → `tin-hoc _ai`
- AutoCAD, SolidWorks, cơ khí, vẽ kỹ thuật, nội thất CAD → `VE KY THUAT`
- Kế toán, chứng từ, sổ sách, Misa → `ke-toan`
- Photoshop, Illustrator, đồ họa → `do-hoa`
- Thẻ mới: đúng `id` trong `_the-khoa-hoc.md`

Logo: `attachments/dataset/chung/` chỉ watermark.

## Ảnh

Kiểu A (có ảnh ngành): mẫu `_mau/mau-khoa-hoc-co-anh-goc.png`
Kiểu B (lịch lễ / không ảnh ngành): mẫu `_mau/mau-lich-le-tu-gen.png`
Lưu gen `_xuat/`. Cấm đăng file gốc dataset.

## Cấm

- Đăng page chưa có Brand Kit / chưa có Page ID
- Đăng sai thẻ (page đồ họa nhận bài kế toán)
- “Đăng hết page” cùng một brief khi thẻ không khớp
- Lấy Royce Shop (nếu còn) làm mẫu vận hành cả hệ — đó chỉ là page test nếu vẫn tồn tại
- Trộn 2 brief một bài; em dash; tự `fb_page_delete`

Muốn N page trong ngày: N goal lệch giờ, hoặc 1 chủ đề + hệ tự lọc theo thẻ.

## Nháp

`sources/facebook-nhap/<slug>/YYYY-MM-DD.md`
