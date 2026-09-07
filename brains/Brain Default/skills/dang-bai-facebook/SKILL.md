---
name: Đăng bài Facebook
description: "Đăng bài Fanpage Sao Việt siêu tốc: 1 lượt gọi duy nhất, Python chuẩn bị album và verify deterministic, Model chỉ sáng tạo caption."
group: Facebook
---

# Đăng bài Facebook - Fast Path (Deterministic 1-Turn)

Mục tiêu: Đăng bài Fanpage thành công 100% trong tối đa 1-2 turns, giảm 95% token tiêu hao bằng cách chuyển toàn bộ cơ học (chọn ảnh, crop, resolve path, upload, verify) sang code Python. Model CHỈ tập trung sáng tạo caption chuẩn brand kit.

## Luồng thực hiện (1 Lần Gọi Duy Nhất)

1. **Xác định Fanpage & Brand Kit**: Đọc đúng 1 file `wiki/brand-kits/<kit-page>.md` theo brief (ví dụ: brief có "Royce Shop" -> đọc `wiki/brand-kits/royce-shop.md`). Lấy Page ID, hotline, địa chỉ và chân trang CHAN_TRANG.
2. **Sáng tạo Caption (Luồng 7 nhịp Sao Việt)**:
   - Bài thường: 32-45 dòng. Bài tuyển sinh/ads: 45-70 dòng (chưa tính chân trang).
   - Nhịp điệu: Móc câu -> Nỗi đau (`👉`) -> Giải pháp/thành quả (`✅`) -> Quyền lợi (`📌`) -> Ưu đãi/quà tặng (`🎁`) -> CTA (`📩`/`📞`) -> Chân trang CHAN_TRANG từ kit.
   - Không Markdown `**`, không em dash, không mở đầu bằng "Chiến dịch tuyển sinh".
3. **Đăng Album Tự Động (Python Deterministic)**:
   - **Cách 1 (Tool function - Khuyến nghị)**:
     ```text
     fb_page_album(
       page="<tên_page_hoặc_page_id>",
       course="<tên_khóa_học>",
       message="<nội_dung_caption_đầy_đủ>",
       photos="auto"
     )
     ```
   - **Cách 2 (Dòng lệnh CLI)**:
     ```text
     python "brains/Brain Default/scratch/hub_call.py" auto_post "<page>" "<khoa_hoc>" "<caption_text_hoặc_@file>"
     ```
   *(Hệ thống Python tự động: chọn 5-8 ảnh từ dataset, chuẩn hóa 1:1 cho ảnh chính và 3:2 cho ảnh phụ, resolve đường dẫn chuẩn xác, upload và verify qua Graph API)*.
4. **Nhận kết quả & Báo cáo ngắn gọn 1 dòng**:
   - `OK | <Trang> | <Khóa học> | <Số ảnh> ảnh | post_id: <post_id> | link: <link>`

## Quy định nghiêm ngặt:
- CẤM tự chạy vòng lặp ReAct dò tìm file ảnh, CẤM tự crop ảnh hay xem metadata ảnh.
- CẤM gọi subagent kiểm chứng độc lập (verifier) vì Graph API đã tự động verify kết quả.
- CẤM dán nguyên văn caption dài hay nhật ký suy luận vào kết quả cuối.
- CẤM bịa post_id hoặc dừng ở bản nháp hỏi lại.
