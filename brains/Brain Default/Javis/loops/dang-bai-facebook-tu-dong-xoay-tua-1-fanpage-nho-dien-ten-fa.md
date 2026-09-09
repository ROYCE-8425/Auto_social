---
type: loop
name: Đăng bài Facebook tự động (Xoay tua 1 Fanpage)
slug: dang-bai-facebook-tu-dong-xoay-tua-1-fanpage-nho-dien-ten-fa
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

Mỗi vòng chỉ xử lý ĐÚNG 1 Fanpage và ĐÚNG 1 bài rồi dừng ngay. Không chạy song song, cấm gọi fb_page_delete.

Quy trình thực hiện:
1. Chạy lệnh để lấy Fanpage 

và khoá học tiếp theo:
   python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py"

2. Nếu trả về NEXT=NONE:
   Báo cáo "Hôm nay toàn bộ Fanpage đã đủ bài hoặc đang chờ giãn cách." và DỪNG.

3. Nếu trả về NEXT=1:
   - Đọc đúng 1 file wiki/brand-kits/<kit> được chỉ định và đọc skills/dang-bai-facebook/SKILL.md.
   - Lấy thông tin hotline, địa chỉ từ khối CHAN_TRANG. Cấm bịa ngoài brand kit.
   - Bước 1 (Cover AI): Gọi tool javis_generate_image tạo 1 cover AI mới 100% chuẩn tỉ lệ vuông 1:1, phong cách công nghệ Sao Việt, đúng chủ đề khoá học <the>. CẤM dùng lại cover cũ trong _xuat.
   - Bước 2 (Đăng Album): Soạn caption 7 nhịp (35-45 dòng) kèm CHAN_TRANG, sau đó gọi tool fb_page_album:
     fb_page_album(page="<page_id>", photos="auto", course="<the>", cover="<đường_dẫn_cover_vừa_tạo>", message="<caption_đầy_đủ>")

4. Kết thúc vòng:
   - Nếu đăng thành công (có post_id): Chạy lệnh:
     python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --ok <page_id> <the>
     Báo cáo 1 dòng: OK | <tên_page> | <the> | post_id: <post_id>
   - Nếu lỗi/thất bại: Chạy lệnh:
     python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --fail <page_id> "<lý_do_lỗi>"
     Báo cáo 1 dòng: FAIL | <tên_page> | lý do: <lý_do_lỗi>
