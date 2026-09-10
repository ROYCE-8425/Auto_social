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
1. Chạy lệnh để lấy Fanpage và khoá học tiếp theo:
   - Trên VPS (trong container / vault): `python skills/dang-bai-facebook/scripts/pick_next_fanpage.py`
   - Trên Local (gốc project): `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py"`

2. Xử lý kết quả điều phối:
   - Nếu trả về NEXT=NONE:
     Báo cáo ĐÚNG 1 DÒNG MÁY: `NEXT=NONE het-hang-hom-nay` và DỪNG NGAY VÒNG.
   - Nếu trả về NEXT=1:
     Lấy các tham số: `page_id`, `ten`, `the`, `angle`, `angle_label`, `folder` và khối `CHAN_TRANG`.

3. Thực hiện đăng bài (khi NEXT=1):
   - Đọc đúng file theo đường dẫn trả về: `wiki/brand-kits/<kit>` (từ `kit_path`), `wiki/courses/<the>.md` (từ `course_path`), và `skills/dang-bai-facebook/SKILL.md`.
   - Lấy thông tin hotline, địa chỉ từ khối `CHAN_TRANG`. Cấm bịa ngoài brand kit.
   - Bước 1 (Cover AI): Gọi tool `javis_generate_image` tạo 1 cover AI mới 100% chuẩn tỉ lệ vuông 1:1, phong cách công nghệ Sao Việt, đúng góc nội dung `<angle>` trong `SKILL.md` (NẾU là mẹo/tình huống/tài liệu: TUYỆT ĐỐI KHÔNG CÓ chữ tuyển sinh/nút đăng ký). CẤM dùng lại cover cũ trong `_xuat`.
   - Bước 2 (Đăng Album): Soạn caption chi tiết chuyên sâu (45-65 dòng) theo đúng khung sườn của `<angle>` từ `SKILL.md` kèm `CHAN_TRANG`, sau đó gọi tool `fb_page_album`:
     `fb_page_album(page="<page_id>", photos="auto", course="<the>", cover="<đường_dẫn_cover_vừa_tạo>", message="<caption_đầy_đủ>")`

4. Kết thúc vòng:
   - Nếu đăng thành công (có post_id): Chạy lệnh:
     + Trên VPS: `python skills/dang-bai-facebook/scripts/pick_next_fanpage.py --ok <page_id> <the> <angle>`
     + Trên Local: `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --ok <page_id> <the> <angle>`
     Báo cáo ĐÚNG 1 DÒNG DUY NHẤT: `POST_OK post_id=<post_id> status=verified link=https://www.facebook.com/<post_id> | <tên_page> | <the> | <angle_label>`
     *(TUYỆT ĐỐI KHÔNG giải thích thêm, KHÔNG nhắc lại câu điều kiện "nếu NEXT=NONE thì..." trong summary để tránh server nhận diện nhầm)*.
   - Nếu lỗi/thất bại: Chạy lệnh:
     + Trên VPS: `python skills/dang-bai-facebook/scripts/pick_next_fanpage.py --fail <page_id> "<lý_do_lỗi>"`
     + Trên Local: `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --fail <page_id> "<lý_do_lỗi>"`
     Báo cáo ĐÚNG 1 DÒNG DUY NHẤT: `FAIL | <tên_page> | lý do: <lý_do_lỗi>`
