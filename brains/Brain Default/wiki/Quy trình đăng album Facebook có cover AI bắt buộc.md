---
type: wiki
status: active
tags: [wiki]
origin: javis-learned
created: 2026-09-08
updated: 2026-09-08
source: [[conversations/2026-09-08]]
---
Quy trình được báo cáo gồm 2 bước: trước tiên agent phải gọi `javis_generate_image` hoặc `gemini_generate_image` để tạo cover mới theo đúng ngành học, sau đó mới gọi `fb_page_album(page="Royce Shop", course="<the>", cover="<ảnh_AI_vừa_gen>", message="<caption>", photos="auto")` để đăng album [[conversations/2026-09-08]].

Mục tiêu của quy trình là tránh bốc lại ảnh cũ trong `_xuat/`, tránh template Pillow có chữ hoặc giá mock, và bảo đảm ảnh số 1 là cover AI mới của đúng khóa học [[conversations/2026-09-08]].

Bộ `Strict Asset Guard` được mô tả là lớp kiểm duyệt bảo đảm cover và ảnh phụ thuộc đúng khóa học trước khi tải lên Facebook Graph API [[conversations/2026-09-08]].

Các claim như đã dọn sạch 60 file, `album_ready/` đã trống, và `tests/python/test_meta_pages.py` pass 58/58 là claim từ báo cáo, cần xác minh bằng runtime tại thời điểm kiểm tra trước khi ghi thành thực tế [[conversations/2026-09-08]].
