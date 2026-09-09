---
type: loop
name: Đăng bài hàng ngày 1 page
slug: dang-bai-hang-ngay
enabled: false
mode: full
goal: custom
interval_min: 5
quiet_hours: 22-07
max_runs_per_day: 100
notify: false
updated: 2026-09-05
---

Mỗi vòng CHỈ đăng 1 Fanpage, 1 bài, rồi DỪNG. Cấm đăng 2 page trong cùng vòng. Cấm chạy song song. Cấm fb_page_delete.

Mục tiêu ngày: mỗi Fanpage có Brand Kit + Page ID được tối đa 1 bài OK. Khoá học lấy NGẪU NHIÊN từ thẻ đã tích trên kit đó.

## Bảo vệ server / API (bắt buộc)

- Gemini **Tier 1** (tính 2026-09): Flash ~150 RPM / ~1500 RPD; ảnh (Imagen/Nano Banana) ~10 IPM / ~500 RPD; trần chi **$10 / 10 phút**, cap billing **$250/tháng**. Quota theo **project**, reset RPD nửa đêm giờ Pacific.
- Không đọc 56 kit / fb_pages_list. Chân trang lấy từ CHAN_TRANG. Caption theo fast-path: 32-45 dòng, ads đầy đủ 45-70 dòng; hook thật, nỗi đau chọn lọc, thành quả, quyền lợi, CTA + chân trang. Cấm bài cụt, cấm bịa khóa ngoài thẻ trong kit. Cấm 20 lần đăng thử.
- Javis chỉ chạy 1 loop lúc một. Không tạo loop thứ hai cùng việc này.
- Không gọi image_gen quá 1 cover. Album ảnh gốc dataset, không gen 8 tấm.
- Không đọc fb_page_posts quá 1 lần (limit 5).
- Timeout: Facebook ERROR → POST_SKIP, không retry trong vòng. 429 Gemini → POST_SKIP, không spam.
- Không mở hết 56 kit. Chỉ đọc kit của page NEXT.
- Mục tiêu 55 page/ngày. Cửa sổ 07–22 = 15 giờ → ~50 khe nếu 18 phút/vòng. Fast-path: mỗi job chỉ 1 cover + 1 lần đăng, không đọc tài liệu vận hành dài.

## Quy trình 1 vòng

0. FAST_PATH: Lệnh `pick_next_fanpage.py` đã tự động lọc CHỈ Fanpage ĐANG HOẠT ĐỘNG (có Access Token hợp lệ & live-check 200 OK trên Meta Graph API). Không quét các trang chưa kết nối.
1. Chạy lệnh lấy Fanpage và khoá học:
   - Trên VPS / container Javis (thư mục chạy là vault):
     `python skills/dang-bai-facebook/scripts/pick_next_fanpage.py`
   - Trên máy Local (chạy từ thư mục gốc project):
     `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py"`
2. Nếu `NEXT=NONE`: Toàn bộ Fanpage đã đủ bài hoặc chưa có thêm Fanpage kết nối, DỪNG ngay.
3. Nếu `NEXT=1`:
   - Đọc đúng các file theo đường dẫn trả về:
     + Brand Kit: `wiki/brand-kits/<kit>` (từ biến `kit_path`)
     + Khóa học: `wiki/courses/<the>.md` (từ biến `course_path`)
     + Quy chuẩn: `skills/dang-bai-facebook/SKILL.md` (từ biến `skill_path`)
   - Lấy thông tin hotline, địa chỉ từ khối `CHAN_TRANG`. Cấm bịa ngoài brand kit.
   - Bước 1 (Cover AI): Gọi tool `javis_generate_image` tạo 1 cover AI mới 100% chuẩn tỉ lệ vuông 1:1, phong cách công nghệ Sao Việt, đúng chủ đề khoá học `<the>`. CẤM dùng lại cover cũ trong `_xuat`.
   - Bước 2 (Đăng Album): Soạn caption chi tiết chuyên sâu (45-65 dòng) đầy đủ chương trình từ `wiki/courses/<the>.md` kèm `CHAN_TRANG`, sau đó gọi tool `fb_page_album`:
     `fb_page_album(page="<page_id>", photos="auto", course="<the>", cover="<đường_dẫn_cover_vừa_tạo>", message="<caption_đầy_đủ>")`
4. Kết thúc vòng:
   - Thành công:
     + Trên VPS: `python skills/dang-bai-facebook/scripts/pick_next_fanpage.py --ok <page_id> <the>`
     + Trên Local: `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --ok <page_id> <the>`
     Báo cáo: `POST_OK post_id=<post_id> status=verified link=https://www.facebook.com/<post_id> | <tên_page> | <the>`
   - Thất bại:
     + Trên VPS: `python skills/dang-bai-facebook/scripts/pick_next_fanpage.py --fail <page_id> "<lý_do_lỗi>"`
     + Trên Local: `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --fail <page_id> "<lý_do_lỗi>"`
     Báo cáo: `FAIL | <tên_page> | lý do: <lý_do_lỗi>`

## Fail / rollback
- Fail = không có post_id. Không coi là đã đăng. Lịch sẽ đưa page đó lại sau 2 giờ (1 lần).
- Nếu bài đã lên tường (có post_id) thì KHÔNG rollback, KHÔNG xóa, đánh --ok.
- Tuyệt đối CẤM gọi fb_page_delete.

## Đầu ra vòng
Báo cáo đúng 1 dòng duy nhất rồi kết thúc vòng.
