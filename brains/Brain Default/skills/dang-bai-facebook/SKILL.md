---
name: Đăng bài Facebook
description: "Đăng bài Fanpage Sao Việt thật nhanh: đọc đúng 1 brand kit, tạo đúng 1 cover, đăng thật bằng Facebook Graph."
group: Facebook
---

# Đăng bài Facebook - fast path

Mục tiêu: hoàn thành 1 bài đăng thật, không vòng vo, không hỏi lại, không bịa post_id.

## Luồng bắt buộc

1. Xác định đúng Fanpage từ brief.
2. Đọc đúng 1 file `wiki/brand-kits/<kit-page>.md`.
3. Viết caption theo `skills/viet-bai-facebook/SKILL.md`, dùng giọng/màu/hotline/chân trang trong kit.
4. Tạo đúng 1 cover mới trong `attachments/dataset/_xuat/`.
5. Đăng thật bằng `fb_page_album` nếu có nhiều ảnh, hoặc `fb_page_photo` nếu chỉ 1 ảnh.
6. Trả `post_id` thật và link bài viết.

Không đọc 56 kit. Không `fb_pages_list` nếu kit đã có Page ID. Không gọi `javis_search_tools` để đoán tool khi tool trực tiếp đã có.

## Chọn công cụ ảnh

Nếu brief có một trong các dấu hiệu sau:

- `OpenAI`
- `GPT Image`
- `gpt-image`
- `javis_generate_image`
- `ai_render_brand=true`
- `ai_full=true`
- yêu cầu AI tự render logo / tiêu đề / hotline

thì đi thẳng nhánh GPT Image:

```text
javis_generate_image(
  page_id="<kit/page slug>",
  save_under="attachments/dataset/_xuat",
  ai_render_brand=true,
  prompt="<brief ảnh + tên khóa + yêu cầu poster>"
)
```

Nhánh này bắt buộc:

- GPT Image tự render poster hoàn chỉnh gồm logo, tiêu đề, bullet ngắn, hotline.
- Brand kit của page được đưa trực tiếp vào prompt bởi tool `javis_generate_image`.
- Không dùng ảnh thật dataset + template code.
- Không overlay bằng Javis.
- Không dùng split-panel, panel navy lớn, card trắng bo góc kiểu cũ.
- Không bám mẫu `mau-khoa-hoc-co-anh-goc`, `A-split`.

Nếu brief không yêu cầu AI full:

- Dùng nhánh ảnh thật/template mặc định.
- Cover từ 1 ảnh raw dataset đúng ngành + logo kit.
- Không AI vẽ lại người/lớp học.

## Caption nhanh nhưng đủ chất lượng

- Bài thường: 28-45 dòng, chưa tính chân trang.
- Bài tuyển sinh/ads đầy đủ: 45-70 dòng, chưa tính chân trang.
- Không ép 60-120 dòng nếu brief không yêu cầu bài dài.
- Mở bài tối đa 5 dòng, chọn 2-3 nỗi đau thật, không xả danh sách dài.
- Có nhịp thị giác vừa phải: 👉 📌 ✅ 🎁 📩 📞
- Không Markdown `**`, không em dash, không mở đầu bằng "Chiến dịch tuyển sinh".
- Chân trang lấy nguyên từ đúng brand kit, mỗi cơ sở một dòng.

## Kiểm trước khi đăng

- Đúng page và đúng Page ID trong kit.
- Ảnh cover mới tạo trong `_xuat`, không dùng lại cover cũ.
- Nếu dùng GPT Image: không còn dấu hiệu template code cũ.
- Caption đúng ngành, đúng hotline, đúng địa chỉ.
- Gọi Facebook đúng 1 lần; nếu plugin báo lỗi thì `POST_SKIP ly-do=<lỗi cụ thể>`.

## Kết quả

Khi thành công, trả ngắn:

- Trang
- `POST_OK post_id=...`
- Link bài viết
- Ảnh đã dùng

Cấm: hỏi duyệt, bịa link, bịa post_id, đăng nhầm page, gọi `fb_page_post` chỉ chữ cho bài khóa học.
