---
type: loop
name: Đăng bài hàng ngày 1 page
slug: dang-bai-hang-ngay
enabled: false
mode: full
goal: custom
interval_min: 18
quiet_hours: 22-07
max_runs_per_day: 48
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

0. FAST_PATH: đọc `skills/dang-bai-facebook/SKILL.md`; không đọc tài liệu hệ thống/reference dài trong mỗi vòng trừ khi thiếu dữ liệu bắt buộc.
1. `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py"`
2. `NEXT=NONE` → hết hàng, dừng.
3. `NEXT=1` → đọc **đúng 1 file** `wiki/brand-kits/<kit>` (dòng kit=) **và** khối `KIT_VISUAL` (logo file, màu, font, giọng, bố cục). Lấy địa chỉ/hotline từ `CHAN_TRANG`. CẤM bỏ qua kit. CẤM đọc 56 kit. Không `fb_pages_list`.
4. **Đọc** `skills/viet-bai-facebook/SKILL.md`. Caption 32-45 dòng hoặc 45-70 dòng nếu ads đầy đủ, giọng = kit. Dán CHAN_TRANG (mỗi cơ sở một dòng). Gen **đúng 1** cover. Nếu kit/brief dùng OpenAI/GPT Image/ai_render_brand/ai_full thì gọi thẳng `javis_generate_image`; nếu không thì raw dataset + logo kit. `pick_photos` nếu cần album. Đăng 1 lần. CẤM `fb_page_post`. CẤM gen 2 poster AI.
5. `--ok` hoặc `--fail`. Không đăng lần 2.

## Fail / rollback

- Fail = không có post_id. Không coi là đã đăng. Lịch sẽ đưa page đó lại sau 2 giờ (1 lần).
- Nếu bài đã lên tường (có post_id) thì KHÔNG rollback, KHÔNG xóa, đánh --ok.
- Cấm gọi fb_page_delete.

## Đầu ra vòng (ngắn)

`VONG page=<ten> id=<page_id> the=<the> ket_qua=OK|SKIP post_id=... ly_do=...`
