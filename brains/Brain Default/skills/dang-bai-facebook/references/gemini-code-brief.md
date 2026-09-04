# Brief cho Gemini: KHÔNG viết lại hạ tầng Facebook

Repo: https://github.com/blogminhquy/javis-os (workspace hiện tại đã là fork/clone đó).

Bạn (Gemini) **không được** thêm connector, plugin Graph, route đăng bài, hay OAuth. Việc đó đã có trên `main`. Nhiệm vụ chỉ là **nạp brand kit rồi soạn caption**, đăng bằng tool sẵn.

## Đã có trên repo (cấm đụng / cấm clone)

| Việc | Chỗ sẵn | Dùng thế nào |
|---|---|---|
| OAuth Fanpage | connector `facebook-pages`, `oauth_mcp` | User đã đấu trên trang Kết nối |
| Đăng chữ | tool `fb_page_post` + `POST /facebook/post` | `page`, `message`, `link?` |
| Đăng ảnh/album/video | `fb_page_photo`, `fb_page_album`, `fb_page_video` | path vault hoặc URL |
| Liệt kê Trang / đọc bài | `fb_pages_list`, `fb_page_posts` | chọn page, tránh trùng caption |
| CLI | `tools/post_facebook.py` | không viết CLI mới |
| Plugin | `system/plugins/meta-pages-graph/` | không fork plugin |
| Engine Gemini | trang Models, `engine.py` | chat đã gọi Gemini được |
| Lịch / việc nền | `javis_schedule`, Kanban, loop | không tự bật loop `full` |
| Logo app Javis | `dashboard/branding.js` | **không** nhầm với brand kit Fanpage |

## Chỉ được làm (nếu còn thiếu trên máy)

1. Điền / giữ file vault `wiki/brand-voice.md` (đã có template).
2. Khi soạn: đọc file đó + `fb_page_posts` limit 5 + brief user. Prompt ghép: `skills/dang-bai-facebook/references/gemini-soan-bai.md`.
3. Trả nháp. Chỉ gọi `fb_page_post` / `fb_page_photo` khi user nói "đăng".
4. Nhiều Trang: bắt buộc `page` hoặc `page_id`. Không đoán.

## Cấm tuyệt đối

- Không thêm `GET/PUT /facebook/brand`, `POST /facebook/draft`.
- Không sửa `server/main.py` quanh `/facebook/post`.
- Không copy plugin `meta-pages-graph`.
- Không tạo Facebook App thứ hai, không lưu token trong file markdown.
- Không UI dashboard mới cho nút Đăng (chat + tool là đủ).
- Không hạ `min_mode` của tool đăng xuống dưới `full`.

## Definition of done

Chat: "viết bài bán X" → caption đúng `wiki/brand-voice.md`. Chat: "đăng" → `post_id` từ tool sẵn. Diff không chứa `server/` hay `system/plugins/`.
