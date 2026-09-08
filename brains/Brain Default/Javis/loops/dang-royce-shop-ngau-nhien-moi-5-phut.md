---
type: loop
name: Đăng Royce Shop ngẫu nhiên
slug: dang-royce-shop-ngau-nhien-moi-5-phut
enabled: false
mode: full
goal: custom
interval_min: 5
quiet_hours: 22-07
max_runs_per_day: 100
notify: false
updated: 2026-09-08
---

Mỗi vòng CHỈ đăng 1 bài duy nhất lên Fanpage Royce Shop (Page ID: 988656934325292) rồi DỪNG.
Tuyệt đối KHÔNG đọc loop-log hoặc transcript cũ để tránh phình token.

## Quy trình Đăng Bài Chuẩn (2 Bước - 1 Bài = 1 Ảnh AI Tạo Mới 100%):

1. **Chọn khóa học xoay vòng**:
   `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --include-royce --page "Royce Shop"`
   Lấy kết quả: `the=<khoa_hoc>` và `CHAN_TRANG`.
2. **AI Sáng Tạo 1 Ảnh Mới 100%**:
   Gọi tool `javis_generate_image` (dùng GPT Image) hoặc `gemini_generate_image` (dùng Google Imagen 3):
   - `prompt`: Banner tuyển sinh khóa học `<the>` Sao Việt, phong cách hiện đại công nghệ, màu sắc thương hiệu xanh & cam Sao Việt, độ nét cao.
   - `save_under`: `"attachments/dataset/_xuat"`
   - `ai_render_brand`: true
   Lấy đường dẫn ảnh vừa sinh: `photo_rel`.
3. **Đăng Bài Facebook (`fb_page_photo`)**:
   Soạn caption chuẩn 7 nhịp Sao Việt kèm `CHAN_TRANG`.
   Gọi tool đăng đúng 1 ảnh:
   `fb_page_photo(page="Royce Shop", photo="<photo_rel>", message="<caption>")`
   *(Hoàn toàn không ghép album, không lấy ảnh cũ từ dataset)*.
4. **Đánh dấu hoàn thành**:
   `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --ok 988656934325292 <the>`
5. **Trả về kết quả 1 dòng**:
   `POST_OK post_id=<post_id> link=<link>`
