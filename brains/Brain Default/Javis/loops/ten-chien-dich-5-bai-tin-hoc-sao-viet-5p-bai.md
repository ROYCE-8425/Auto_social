---
type: loop
name: 'Tên: Chiến dịch 5 bài Tin học Sao Việt (5p/bài).'
slug: ten-chien-dich-5-bai-tin-hoc-sao-viet-5p-bai
enabled: false
goal: custom
mode: full
interval_min: 5
workspace: vault
tools_profile: vault-safe
quiet_hours: ''
max_runs_per_day: 5
owner_chat: ''
notify: true
updated: '2026-09-04'
---

Chiến dịch 5 bài đăng quảng cáo khoá học Sao Việt trên page Royce Shop.
Mỗi vòng thực hiện ĐÚNG 1 bài đăng:
1. Đọc file `05 - Projects/chien-dich-5-khoa-hoc-sao-viet.md` để lấy khoá học ở dòng đầu tiên chưa có `[x]`.
2. Tuân thủ triệt để skill `dang-bai-facebook` và `wiki/brand-kits/_y-chu-dang-bai.md`:
   - Lấy ảnh từ folder dataset tương ứng của khoá học (tin-hoc _ai, ke-toan, VE KY THUAT, do-hoa, ai).
   - Tạo cover poster BẮT BUỘC VUÔNG 1:1 (2000x2000 px) theo Style 1 (Mockup Studio Poster như `mau-poster-do-hoa.png`) hoặc Style 2 (Ảnh thật 1:1 + Khung thương hiệu thanh dưới). Tuyệt đối không dùng Style 3 Neon hay banner ngang 16:9.
   - Chọn và tự động chuẩn hóa album theo chuẩn Facebook 2026 (4, 6, 7 hoặc 8 ảnh) bằng lệnh: `python "brains/Brain Default/scratch/hub_call.py" pick_photos <folder> <cover_path> random`.
   - Đăng album lên page Royce Shop qua tool `fb_page_album`.
3. Sau khi đăng thành công, cập nhật đánh dấu `[x]` kèm post_id vào `05 - Projects/chien-dich-5-khoa-hoc-sao-viet.md`.
4. Nếu cả 5 dòng đều đã `[x]`: báo hoàn thành chiến dịch.
