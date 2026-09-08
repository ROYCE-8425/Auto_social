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

1. **Chọn khóa học xoay vòng (100% theo 5 nhóm dataset)**:
   `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --include-royce --page "Royce Shop"`
   Lấy kết quả: `the=<khoa_hoc>` (chỉ thuộc: tin-hoc _ai, do-hoa, ke-toan, ve-ky-thuat, tre-em) và `CHAN_TRANG`.
   Đọc file `wiki/courses/<the>.md` để lấy Tiêu đề (Title Hooks) và Highlights giáo trình thật.
   TUYỆT ĐỐI CẤM đăng khóa học ngoài dataset (CẤM kinh doanh online, CẤM bán hàng).
2. **Tạo 1 Ảnh Mới 100% bằng GPT Image 2**:
   Gọi thẳng tool `javis_generate_image` (GPT Image 2):
   - `prompt`: Banner tuyển sinh thực chiến khóa học <the> Sao Việt, tiêu đề '<tiêu_đề_trong_wiki>', các điểm nổi bật '<highlights_trong_wiki>', phong cách hiện đại công nghệ, màu sắc thương hiệu xanh & cam Sao Việt, độ nét cao.
   - `save_under`: `"attachments/dataset/_xuat"`
   - `ai_render_brand`: true
   Lấy đường dẫn ảnh vừa sinh: `photo_rel`. (NẾU lỗi tạo ảnh: dừng ngay).
3. **Đăng Bài Facebook (`fb_page_photo`)**:
   Soạn caption chuẩn 7 nhịp Sao Việt kèm `CHAN_TRANG`.
   Gọi tool đăng đúng 1 ảnh:
   `fb_page_photo(page="Royce Shop", photo="<photo_rel>", message="<caption>")`
   *(Hoàn toàn không ghép album, không lấy ảnh cũ từ dataset)*.
4. **Đánh dấu hoàn thành**:
   `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --ok 988656934325292 <the>`
5. **Trả về kết quả 1 dòng**:
   `POST_OK post_id=<post_id> link=<link>`
