---
type: workflow
name: Đăng Facebook
slug: dang-bai-that-facebook
status: on
description: Co anh dataset thi mac dinh cover va album dung anh that. Neu brief ghi OpenAI/GPT Image/javis_generate_image/ai_render_brand=true/ai_full thi cho AI render poster full.
steps:
  - agent: bien-tap-facebook
    task: "Brief = {{input}}. Doc dung 1 brand-kits/<page> theo brief (neu royce thi doc royce-shop.md, page_id 988656934325292). Neu brief co OpenAI/GPT Image/gpt-image/javis_generate_image/ai_render_brand=true/ai_full/AI tu render/logo tieu de hotline thi Anh dau/cover BAT BUOC dung javis_generate_image voi ai_render_brand=true, page_id, save_under='attachments/dataset/_xuat', de GPT Image tu render poster full gom logo/chu/hotline; CAM dung anh that dataset + template chu bang code, CAM overlay template cu, CAM split-panel/panel navy/card trang bo san. Neu brief khong yeu cau AI full thi mac dinh cover = anh that dataset + file Logo chinh kit + template chu bang code; CAM ve lai nguoi/lop hoc bang AI. Album anh goc qua pick_photos neu co. Caption theo skills/viet-bai-facebook va BAT BUOC doc references/corpus-sao-viet-1txt.md de lay von tu dung nganh: tu nhien, doc luot mobile, co emoji dan mat vua du (👉 noi dau, 📌 y chot, ✅ thanh qua/quyen loi, 🎁 uu dai, 📩📞 CTA), mo bai toi da 5 dong, cam xa 6-8 cau noi dau lien tiep, mac dinh 32-45 dong than bai, bai ads day du 45-70 dong, khong mo dau bang 'Chien dich tuyen sinh', khong nhoi 8-10 module/quyen loi, chi them CHAN_TRANG dung kit xuong dong. BAT BUOC DANG THAT LEN FACEBOOK bang fb_page_album (hoac fb_page_photo) va lay post_id Graph API that. TUYET DOI CAM BIA HOAC MOCK post_id. CAM dung lai o ban nhap, CAM hoi xin xac nhan duyet. POST_SKIP neu plugin chan. Cam fb_page_post."
updated: 2026-09-05
---
1 goal = 1 Fanpage = 1 brief. Chân trang pháp nhân đầy đủ.
