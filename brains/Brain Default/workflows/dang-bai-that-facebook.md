---
type: workflow
name: Đăng Facebook
slug: dang-bai-that-facebook
status: on
description: Co anh dataset thi cover va album dung anh that. Khong ve lai nguoi/lop hoc bang AI.
steps:
  - agent: bien-tap-facebook
    task: "Brief = {{input}}. Doc dung 1 brand-kits/<page> theo brief (neu royce thi doc royce-shop.md, page_id 988656934325292). Anh dau/cover = anh that dataset + file Logo chinh kit + template chu bang code; CAM ve lai nguoi/lop hoc bang AI, CAM AI full poster tru khi brief ghi ro ai_full. Album anh goc qua pick_photos. Caption theo skills/viet-bai-facebook va BAT BUOC doc references/corpus-sao-viet-1txt.md de lay von tu dung nganh: tu nhien, doc luot mobile, mac dinh 32-45 dong than bai, bai ads day du 45-70 dong, khong mo dau bang 'Chien dich tuyen sinh', khong nhoi 8-10 module/quyen loi, chi them CHAN_TRANG dung kit xuong dong. BAT BUOC DANG THAT LEN FACEBOOK bang fb_page_album (hoac fb_page_photo) va lay post_id Graph API that. TUYET DOI CAM BIA HOAC MOCK post_id. CAM dung lai o ban nhap, CAM hoi xin xac nhan duyet. POST_SKIP neu plugin chan. Cam fb_page_post."
updated: 2026-09-05
---
1 goal = 1 Fanpage = 1 brief. Chân trang pháp nhân đầy đủ.
