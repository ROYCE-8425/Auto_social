---
type: workflow
name: Đăng TikTok carousel
slug: dang-tiktok-carousel
status: on
description: "Đăng carousel 4-6 ảnh dọc 9:16 lên TikTok qua PostPeer: Tự động gắn nhạc nền gợi ý (autoAddMusic), caption ngắn 8-18 dòng đúng brand kit (BSN @seotrum vs Tin học Sao Việt)."
steps:
  - agent: bien-tap-tiktok
    task: "Brief = {{input}}. Quy trình đăng CAROUSEL TikTok 9:16: (1) Đọc Brand Kit TikTok (Game Giá Rẻ BSN: kênh @seotrum / accountId 6aa3ba9df4c58f3c57921507; Sao Việt:...): chọn sản phẩm/chủ đề đúng brand, chuẩn bị 4-6 ảnh dọc 9:16 từ dataset hoặc _xuat-tiktok/ sang URL https://trannhuy.online/tiktok-media/..., tạo cover AI portrait mới nếu cần bằng javis_generate_image. (2) Soạn caption TikTok chuẩn 8-18 dòng (hook giật tít, 3 điểm nổi bật, CTA, 3-5 hashtag đúng brand kit), gọi tool native postpeer_tiktok_photos(account_id='<account_id>', images=['<url1>', ...], caption='<caption>', auto_add_music=True, disable_duet=True, disable_stitch=True). CẤM mock post_id, CẤM gọi tool Facebook fb_*, CẤM nhồi chân trang 13 cơ sở của Sao Việt."
updated: 2026-09-17
---
1 goal = 1 Kênh TikTok = 1 brief. Carousel 4-6 ảnh dọc 9:16 kèm auto gắn nhạc nền TikTok qua postpeer_tiktok_photos.
