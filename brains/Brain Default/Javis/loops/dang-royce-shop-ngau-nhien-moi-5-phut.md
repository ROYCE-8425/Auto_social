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

## Quy trình Đăng Bài Chuẩn (2 Bước - Cover AI Độc Quyền + Album Dataset Thật):

1. **Chọn khóa học xoay vòng**:
   `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --include-royce --page "Royce Shop"`
   Lấy kết quả: `the=<khoa_hoc>` và `CHAN_TRANG`.
2. **AI Sáng Tạo Ảnh Cover Mới 100%**:
   Gọi tool `javis_generate_image` (dùng GPT Image) hoặc `gemini_generate_image` (dùng Google Imagen 3):
   - `prompt`: Mô tả poster khóa học chuyên nghiệp theo `<the>`, phong cách đồ họa phẳng hiện đại hoặc không gian công nghệ 3D, nhận diện thương hiệu xanh & cam Sao Việt.
   - `save_under`: `"attachments/dataset/_xuat"`
   - `ai_render_brand`: true
   Lấy đường dẫn ảnh vừa sinh: `cover_rel`.
3. **Đăng Album Facebook**:
   Soạn caption chuẩn 7 nhịp Sao Việt kèm `CHAN_TRANG`.
   Gọi tool:
   `fb_page_album(page="Royce Shop", course="<the>", cover="<cover_rel>", message="<caption>", photos="auto")`
   Hệ thống tự động lấy ảnh AI vừa gen làm cover (`photos[0]`) và ghép 4-6 ảnh thật từ dataset của đúng ngành `<the>`.
4. **Đánh dấu hoàn thành**:
   `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --ok 988656934325292 <the>`
5. **Trả về kết quả 1 dòng**:
   `POST_OK post_id=<post_id> link=<link>`
