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
updated: '2026-09-09'
---

Mỗi vòng CHỈ đăng đúng 1 Fanpage, 1 bài duy nhất, rồi DỪNG NGAY. Tuyệt đối KHÔNG đăng 2 page trong cùng một vòng. Cấm chạy song song. Cấm fb_page_delete.

BẮT BUỘC: Nếu kết quả có NEXT=1, bạn PHẢI THỰC THI LIÊN TỤC TRỌN VẸN TỪ BƯỚC 1 ĐẾN HẾT BƯỚC 5 TRONG CÙNG VÒNG NÀY. Tuyệt đối KHÔNG dừng lại chỉ để báo cáo, KHÔNG đề xuất, KHÔNG chờ đợi. Phải đăng thật ra post_id rồi mới kết thúc vòng.

## QUY TRÌNH 5 BƯỚC BẮT BUỘC:

1. **Kiểm tra và chọn Fanpage tiếp theo**:
   Chạy lệnh terminal:
   `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py"`

2. **Xử lý kết quả điều phối**:
   - Nếu output có `NEXT=NONE`: 
     Báo cáo đúng 1 dòng: `NEXT=NONE het-hang-hom-nay` và DỪNG NGAY VÒNG.
   - Nếu output có `NEXT=1`: 
     Lấy ngay các thông số: `page_id`, `ten`, `the`, `kit`, `folder` và toàn bộ khối `CHAN_TRANG`. Tiếp tục ngay sang bước 3.

3. **Tạo ảnh truyền thông AI mới 100% chuẩn VUÔNG 1:1**:
   - Đọc `skills/dang-bai-facebook/SKILL.md`. Chọn kiểu bằng `(ngày trong tháng + 2 số cuối page_id) % 6`: học viên thực hành, thao tác kèm icon phần mềm, thành quả học viên, tình huống trước-sau, giảng viên kèm học viên, hoặc ứng dụng trong công việc.
   - Ảnh kể chuyện bằng ngữ cảnh, logo nhỏ, tối đa 1 câu móc 3-6 từ. Cấm chữ tuyển sinh, CTA lớn, bảng liệt kê và nền neon xanh phủ toàn ảnh.
   Lập tức gọi tool:
   `javis_generate_image(prompt="Ảnh truyền thông Facebook vuông cho khóa <the> Sao Việt. Kiểu <0-5 và mô tả kiểu>. Bám Highlights khóa học, có hành động cuốn hút, nhân vật Việt Nam. Logo nhỏ, câu móc 3-6 từ, lề an toàn 20%. Xanh dương và cam chỉ làm điểm nhấn. Cấm chữ tuyển sinh, CTA, bảng liệt kê và nền neon phủ toàn ảnh", aspect_ratio="square", save_under="attachments/dataset/_xuat", ai_render_brand=true)`
   Lấy đường dẫn ảnh vừa tạo (dạng `attachments/dataset/_xuat/...png`). TUYỆT ĐỐI CẤM dùng lại ảnh cover cũ.

4. **Đăng Album Fanpage chuẩn Tỷ Lệ Vàng 2026**:
   - Soạn caption theo giọng các bài mẫu Sao Việt: đầy đặn 32-45 dòng, chưa tính `CHAN_TRANG`, nhưng mở bài phải gọn. Bố cục: tiêu đề mạnh; 2-3 câu dẫn chỉ nêu 1 nhu cầu; 1 câu nối vào khóa học; 6-8 dòng nội dung học cụ thể; 3-5 dòng phương pháp/quyền lợi; 1-2 dòng CTA. Viết trực diện, dùng emoji và danh sách như bài mẫu, không viết thành bài văn giải thích. Chỉ dùng claim, ưu đãi, học phí, thời lượng và chứng chỉ có trong course/brand kit hiện hành; không bê dữ kiện cũ từ bài mẫu. Cấm lặp cùng nỗi đau hoặc lợi ích dưới nhiều cách nói. Gắn toàn bộ khối `CHAN_TRANG` ở cuối.
   - Lập tức gọi tool đăng bài thật:
     `fb_page_album(page="<page_id>", photos="auto", course="<the>", cover="<đường_dẫn_ảnh_AI_vừa_tạo>", message="<caption_đầy_đủ>")`

5. **Xác nhận và kết thúc**:
   - Khi có `post_id` trả về từ Facebook, chạy lệnh cập nhật:
     `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --ok <page_id> <the>`
   - Báo cáo kết thúc đúng 1 dòng chuẩn cú pháp:
     `POST_OK post_id=<post_id> status=verified link=https://www.facebook.com/<post_id> | <ten> | <the>`
   - Không ghi thêm các câu nhận định ngoài lề như "không sửa file nào" để tránh lỗi kiểm chứng.
