---
type: loop
name: Đăng bài hàng ngày - Xoay tua tất cả Fanpage
slug: dang-bai-hang-ngay-xoay-tua-tat-ca-fanpage
enabled: false
goal: custom
mode: full
interval_min: 5
workspace: vault
tools_profile: vault-safe
quiet_hours: ''
max_runs_per_day: 0
owner_chat: ''
notify: true
updated: '2026-09-11'
---

Mỗi vòng CHỈ đăng đúng 1 Fanpage, 1 bài duy nhất, rồi DỪNG NGAY. Tuyệt đối KHÔNG đăng 2 page trong cùng một vòng. Cấm chạy song song. Cấm fb_page_delete.

BẮT BUỘC: Nếu kết quả có NEXT=1, bạn PHẢI THỰC THI LIÊN TỤC TRỌN VẸN TỪ BƯỚC 1 ĐẾN HẾT BƯỚC 5 TRONG CÙNG VÒNG NÀY. Tuyệt đối KHÔNG dừng lại chỉ để báo cáo, KHÔNG đề xuất, KHÔNG chờ đợi. Phải đăng thật ra post_id rồi mới kết thúc vòng.

## QUY TRÌNH 5 BƯỚC BẮT BUỘC:

1. **Kiểm tra và chọn Fanpage tiếp theo**:
   Chạy lệnh terminal:
   - Trên VPS (trong container / vault): `python skills/dang-bai-facebook/scripts/pick_next_fanpage.py`
   - Trên Local (gốc project): `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py"`

2. **Xử lý kết quả điều phối**:
   - Nếu output có `NEXT=NONE`: 
     Báo cáo đúng 1 dòng: `NEXT=NONE het-hang-hom-nay` và DỪNG NGAY VÒNG.
   - Nếu output có `NEXT=1`: 
     Lấy ngay các thông số: `page_id`, `ten`, `the`, `angle`, `angle_label`, `kit`, `folder` và toàn bộ khối `CHAN_TRANG`. Tiếp tục ngay sang bước 3.

3. **Tạo ảnh truyền thông AI mới 100% chuẩn VUÔNG 1:1 theo đúng `<angle>`**:
   - Đọc `skills/dang-bai-facebook/SKILL.md`. Chọn phong cách visual phù hợp với `<angle>`:
     * `meo_thuc_chien`: Phong cách Isometric 3D workspace hoặc infographic phím tắt, giao diện làm việc. TUYỆT ĐỐI CẤM chữ "Tuyển sinh".
     * `tinh_huong`: Bố cục Before / After split screen hoặc phân tích xử lý sự cố. TUYỆT ĐỐI CẤM chữ "Tuyển sinh".
     * `tai_lieu`: Bố cục Canva Grid / Clean Resource Catalog chia sẻ bộ file mẫu, template. TUYỆT ĐỐI CẤM chữ "Tuyển sinh".
     * `tuyen_sinh`: Banner Modern Educational Ad tuyển sinh thực hành kèm 1-1 chuẩn nhận diện Sao Việt.
   - Lập tức gọi tool:
     `javis_generate_image(prompt="Ảnh truyền thông Facebook vuông 1:1 cho khóa học <the> Sao Việt theo góc <angle> (<angle_label>). Bám Highlights khóa học, lề an toàn cách đều 4 mép 15-20%, phong cách thiết kế hiện đại, nhận diện xanh dương và cam Sao Việt làm điểm nhấn, độ nét cao. <Nếu không phải tuyen_sinh: Cấm chữ tuyển sinh, cấm nút đăng ký>", aspect_ratio="square", save_under="attachments/dataset/_xuat", ai_render_brand=true)`
   - Lấy đường dẫn ảnh vừa tạo (dạng `attachments/dataset/_xuat/...png`). TUYỆT ĐỐI CẤM dùng lại ảnh cover cũ.

4. **Đăng Album Fanpage chuẩn Tỷ Lệ Vàng 2026**:
   - Soạn caption theo skill `viet-bai-facebook`: độ dài 28-45 dòng (chưa tính `CHAN_TRANG`), mở bài gọn, ngắt dòng thoáng mắt trên mobile. TUYỆT ĐỐI CẤM các con số khẳng định phóng đại khó kiểm chứng ("gấp 3 lần", "trong 5 phút", "trong 30 giây") và CẤM bịa quà tặng, học phí, chứng chỉ nếu file course/brand kit không có.
   - Bố cục theo đúng `<angle>`:
     * Nếu `<angle>` là `tuyen_sinh`: Móc câu -> Nỗi đau (`👉`) -> Giải pháp kỹ năng -> Khối cam kết đào tạo (4-5 dòng `📌`) -> Khối ưu đãi học viên (3-4 dòng `🎁`) -> CTA tuyển sinh.
     * Nếu `<angle>` là `meo_thuc_chien` / `tinh_huong` / `tai_lieu`: Móc câu trực diện -> Tình huống/vấn đề thực tế -> Hướng dẫn chi tiết / Các bước xử lý / Bảng công thức, phím tắt -> Lời khuyên/Lưu ý -> CTA mềm 1-2 dòng (`👉 Lưu lại bài viết... / Nhắn tin Fanpage để nhận tư vấn...`). TUYỆT ĐỐI KHÔNG nhồi nhét khối `🎁` ưu đãi học phí hay `📌` tuyển sinh vào bài chia sẻ kiến thức.
   - Gắn toàn bộ khối `CHAN_TRANG` ở cuối.
   - Lập tức gọi tool đăng bài thật:
     `fb_page_album(page="<page_id>", photos="auto", course="<the>", cover="<đường_dẫn_ảnh_AI_vừa_tạo>", message="<caption_đầy_đủ>")`

5. **Xác nhận và kết thúc**:
   - Khi có `post_id` trả về từ Facebook, chạy lệnh cập nhật:
     - Trên VPS: `python skills/dang-bai-facebook/scripts/pick_next_fanpage.py --ok <page_id> <the> <angle>`
     - Trên Local: `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --ok <page_id> <the> <angle>`
   - Báo cáo kết thúc đúng 1 dòng chuẩn cú pháp:
     `POST_OK post_id=<post_id> status=verified link=https://www.facebook.com/<post_id> | <ten> | <the> | <angle_label>`
   - *(TUYỆT ĐỐI KHÔNG ghi thêm các câu nhận định ngoài lề như "không sửa file nào" hay nhắc lại câu điều kiện "nếu NEXT=NONE thì..." trong summary)*.
