---
type: loop
name: đăng bài cho t3 t6 cho all fage
slug: dang-bai-3-6-cho-all-fage
enabled: false
goal: custom
mode: full
interval_min: 18
workspace: vault
tools_profile: vault-safe
quiet_hours: ''
max_runs_per_day: 0
owner_chat: ''
notify: true
updated: '2026-09-09'
---

Mỗi vòng CHỈ đăng 1 bài cho 1 Fanpage rồi DỪNG. Cấm đăng 2 page trong 1 vòng.

1. ĐIỀU PHỐI FANPAGE (Chỉ chạy Thứ 3 và Thứ 6, mỗi page tối đa 1 bài/ngày):
Chạy script:
- Trên VPS (trong container / vault): `python skills/dang-bai-facebook/scripts/pick_next_fanpage.py`
- Trên Local (gốc project): `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py"`
- Nếu xuất hiện "NEXT=NONE": Báo cáo ĐÚNG 1 DÒNG MÁY: `NEXT=NONE het-hang-hom-nay` và DỪNG NGAY.
- Nếu xuất hiện "NEXT=1": Lấy page_id, ten, the (khóa học), angle, angle_label, kit, CHAN_TRANG.

2. QUY LUẬT KHÓA HỌC:
- Thứ 3: Đăng khóa 'tin-hoc _ai' (hoặc 'ke-toan' theo tuần)
- Thứ 6: Đăng khóa 'do-hoa' (hoặc 've-ky-thuat' theo tuần)
(Ưu tiên theo biến the mà script đã chọn theo đúng Brand Kit của trang).

3. XUẤT BẢN BÀI VIẾT (TỶ LỆ VÀNG 2026):
- Đọc file wiki/courses/<the>.md lấy Tiêu đề và Highlights chuẩn theo góc `<angle>`.
- Gọi javis_generate_image (GPT Image 2) tạo 1 ảnh bìa AI vuông 1:1, lề an toàn cách đều 4 mép 15-20% theo đúng `<angle>`.
- Soạn caption chuẩn theo đúng khung sườn của `<angle>` từ SKILL.md kèm CHAN_TRANG của đúng Trang này.
- Gọi tool đăng album:
  fb_page_album(page="<ten>", photos="auto", course="<the>", cover="<ảnh_ai_vừa_tạo>", message="<caption>")

4. XỬ LÝ KẾT QUẢ & CHỊU LỖI:
- ĐĂNG THÀNH CÔNG: Chạy lệnh:
  + Trên VPS: `python skills/dang-bai-facebook/scripts/pick_next_fanpage.py --ok <page_id> <the> <angle>`
  + Trên Local: `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --ok <page_id> <the> <angle>`
  Báo cáo ĐÚNG 1 DÒNG DUY NHẤT: `POST_OK post_id=<post_id> status=verified link=https://www.facebook.com/<post_id> | <tên_page> | <the> | <angle_label>`
  *(TUYỆT ĐỐI KHÔNG giải thích thêm, KHÔNG nhắc lại câu điều kiện "nếu NEXT=NONE thì..." trong summary)*.
- BỊ LỖI: Bỏ qua ngay để không kẹt vòng bằng lệnh:
  + Trên VPS: `python skills/dang-bai-facebook/scripts/pick_next_fanpage.py --fail <page_id> "<lý_do>"`
  + Trên Local: `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --fail <page_id> "<lý_do>"`
  Báo cáo ĐÚNG 1 DÒNG DUY NHẤT: `FAIL | <tên_page> | lý do: <lý_do>`
