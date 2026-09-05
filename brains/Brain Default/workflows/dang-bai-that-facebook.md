---
type: workflow
name: Đăng Facebook
slug: dang-bai-that-facebook
status: on
description: Co anh dataset thi album goc. Khong anh lien quan moi gen 1 tam.
steps:
  - agent: bien-tap-facebook
    task: "Brief = {{input}}. Doc dung 1 brand-kits/<page> (logo mau font giong dia chi). 1 cover AI = raw + file Logo chinh kit. Album anh goc qua pick_photos. Caption 7 phan 60-120 dong + CHAN_TRANG xuong dong. BAT BUOC DANG THAT LEN FACEBOOK bang fb_page_album (hoac fb_page_photo) va lay post_id. CAM dung lai o ban nhap, CAM hoi xin xac nhan duyet. POST_SKIP neu plugin chan. Cam fb_page_post."
updated: 2026-09-05
---
1 goal = 1 Fanpage = 1 brief. Chân trang pháp nhân đầy đủ.
