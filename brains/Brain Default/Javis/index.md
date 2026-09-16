# Javis Index (tầng vận hành)

> Tự sinh từ file - ĐỪNG sửa tay. Chỉ mục mọi năng lực của Javis trong brain này để bất kỳ AI/engine đọc 1 chỗ là hiểu Javis làm được gì. Song song `wiki/index.md` (tri thức).

**Tổng quan:** 1 agents · 16 skills · 1 workflows (0 bật) · 3 loops (0 bật) · 13 plugins (12 chạy)

## Agents
- **Biên tập Facebook** (`bien-tap-facebook`) - Tạo 1 ảnh AI độc quyền mới 100%, soạn caption đúng brand kit và đăng lên Fanpage Facebook. · model gpt-5.5 · skills: dang-bai-facebook, viet-bai-facebook

## Skills
### AI
- **Đánh giá report model trước deploy** (`danh-gia-report-model-truoc-deploy`) - Đối chiếu report của model khác với code local, test và rủi ro trước khi đưa thay đổi lên VPS.
- **Ingest Source** (`ingest-source`) - Tiêu hoá một source thô vào Second Brain, chưng cất thành tri thức wiki tích luỹ.
- **Javis Builder** (`javis-builder`) - Tạo hoặc sửa năng lực của Javis: agent, skill, workflow, loop, plugin. Kèm mẫu file chuẩn và luật chống trùng.
- **Kiểm tra token workflow Javis** (`kiem-tra-token-workflow-javis`) - Rà soát workflow Javis để tìm nơi phình context, log, result và skill gây tốn token.
- **Lint Wiki** (`lint-wiki`) - Rà soát sức khoẻ wiki của Second Brain, trả về danh sách vấn đề. Không tự sửa hàng loạt.
- **Notes** (`notes`) - Lưu tin nhắn hiện tại nguyên văn vào sources/ (kèm ảnh), tự chưng cất lên wiki nếu note đáng.
- **Query Wiki** (`query-wiki`) - Khai thác tri thức trong Second Brain: tổng hợp, so sánh, giả thuyết. Trả lời có trích dẫn.
- **Kiểm tra lại năng lực của chính mình** (`verify-own-capabilities`) - Khi không chắc về một năng lực (vd: tạo ảnh), hãy kiểm tra danh sách tool/plugin đang hoạt động thay vì khẳng định là không có.
### Content
- **Viết bài Facebook** (`viet-bai-facebook`) - Skill viết caption Facebook cho hệ thống Sao Việt: rõ người học, rõ việc làm được, giọng tự nhiên, không văn mẫu AI, tối ưu đọc lướt trên di động.
### Facebook
- **Đăng bài Facebook** (`dang-bai-facebook`) - Đăng bài Fanpage Sao Việt: Album 6-8 ảnh chuẩn Tỷ Lệ Vàng 2026, cover AI mới 100%, luân phiên 4 Content Pillars kèm chân trang sạch.
- **Kiểm tra goal đăng bài Facebook** (`kiem-tra-goal-dang-bai-facebook`) - Kiểm tra goal Facebook vừa chạy: thời gian, token, post_id, ảnh đã dùng và lỗi sai khóa học.
- **Kiểm tra loop đăng bài Facebook** (`kiem-tra-loop-dang-bai-facebook`) - Kiểm tra loop đăng bài Facebook: trạng thái, lần chạy, treo ở đâu, token, post_id, ảnh và lỗi lặp page.
- **Vá chống lặp loop Facebook bằng log** (`va-chong-lap-loop-facebook-bang-log`) - Vá picker loop Facebook để không chọn lại page đã có POST_OK trong log hôm nay.
- **Xử lý token Meta Facebook an toàn** (`xu-ly-token-meta-facebook-an-toan`) - Tư vấn và kiểm tra token Meta/Facebook mà không lộ secret, ưu tiên OAuth và Page Token đúng chuẩn.
### Marketing
- **HTML sang Webcake** (`html-to-webcake`) - Chuyển trang HTML thành file .pke mở được trong trình dựng Webcake, giữ đúng màu, cỡ chữ, ảnh và bố cục của bản gốc.
- **Tạo poster Facebook khóa học** (`tao-poster-facebook-khoa-hoc`) - Tạo poster Facebook 1:1 cho khóa học bằng javis_generate_image, lưu vào vault và trả markdown ảnh.

## Workflows
- **Đăng Facebook** (`dang-bai-that-facebook`) - True · 1 bước [bien-tap-facebook] · Đăng bài Fanpage Facebook: Album 6-8 ảnh chuẩn Tỷ Lệ Vàng 2026 (1 cover AI mới 100% bằng GPT Image 2 + ảnh lớp học thật từ dataset), đăng bằng fb_page_album.

## Loops
- **đăng bài cho t3 t6 cho all fage** (`dang-bai-3-6-cho-all-fage`) - tắt · custom/full · mỗi 18 phút
- **Đăng bài hàng ngày - Xoay tua tất cả Fanpage** (`dang-bai-hang-ngay-xoay-tua-tat-ca-fanpage`) - tắt · custom/full · mỗi 5 phút
- **Đăng bài hàng ngày 1 page** (`dang-bai-hang-ngay`) - tắt · custom/full · mỗi 5 phút

## Plugins (tool/hook native cho mọi engine)
- **Thời gian & ngày** (`datetime-vn`) - bundled/chạy · tools: javis_now, javis_date_add · Xem ngày giờ hiện tại theo múi giờ đã cấu hình và tính ngày tương đối (mai, mốt, N ngày nữa, tuần trước). Thuần stdlib, chỉ đọc, không cần mạng.
- **Theo dõi Facebook (Apify)** (`fb-monitor-apify`) - bundled/chạy · tools: fb_monitor · Theo dõi Trang/Nhóm CÔNG KHAI Facebook tìm bài nhiều share qua dịch vụ Apify. Chỉ đọc, không đụng tài khoản cá nhân, chạy tốt trên VPS. Dùng token của kết nối "facebook-monitor".
- **Tạo ảnh (ChatGPT)** (`image-chatgpt`) - bundled/chạy · tools: javis_generate_image · Tạo ảnh từ mô tả bằng GÓI ChatGPT đang đăng nhập (OAuth) - không cần OpenAI API key. Dùng Codex Responses API + tool image_generation (gpt-image-2). Ảnh lưu vào attachments/ của vault để nhúng thẳng vào chat. Cần đã kết nối ChatGPT ở trang Model.
- **Tạo ảnh (Google Gemini / Imagen 3)** (`image-gemini`) - bundled/chạy · tools: gemini_generate_image · Tạo ảnh bằng Google Imagen / Gemini image (Nano Banana), chọn model ở trang Models. Ảnh lưu vào attachments/ của brain.
- **Đấu thêm MCP** (`javis-connect`) - bundled/chạy · tools: javis_add_mcp · Đấu một MCP server vào kho Kết nối của Javis ngay từ chat, để nó HIỆN ra trang Kết nối như mọi tài khoản khác. Trước tool này Javis chỉ còn đường `claude mcp add` - thứ rơi vào config riêng của Claude Code, không bộ não nào khác thấy và người dùng cũng không thấy trên trang Kết nối.
- **Đặt việc định kỳ & nhắc hẹn** (`javis-schedule`) - bundled/chạy · tools: javis_schedule · Tạo/liệt kê/huỷ việc chạy định kỳ và nhắc hẹn ngay từ chat. Tự chọn kho - việc lặp và bền thì ghi Javis/loops/<slug>.md để sửa được trong Obsidian; nhắc một lần hoặc lịch cron thì vào kho nhắc hẹn (đã có sẵn cron 5 trường). Thay cho việc gõ YAML tay hoặc curl.
- **Giao việc Kanban** (`javis-task`) - bundled/chạy · tools: javis_task · Giao một việc nền vào hàng đợi Kanban và xem việc đang chạy tới đâu, ngay từ chat. Trước tool này chỉ engine chạy được lệnh máy (Claude Code, Codex) mới giao việc được, vì đường duy nhất là curl POST /kanban/task - năm engine API đứng ngoài.
- **Meta Ads (Graph API)** (`meta-ads-graph`) - bundled/chạy · tools: meta_ads_accounts, meta_ads_insights, meta_ads_campaigns, meta_ads_get · Đọc số liệu quảng cáo Facebook/Instagram (tài khoản ads, chiến dịch, hiệu suất) qua Graph API, dùng token của kết nối "Meta Ads (tự tạo app)". CHỈ ĐỌC, không tiêu tiền.
- **Facebook Trang (Graph API)** (`meta-pages-graph`) - bundled/chạy · tools: fb_pages_list, fb_page_posts, fb_page_comments, fb_page_inbox_comments, fb_page_post, fb_page_photo, fb_page_album, fb_page_video, fb_page_edit, fb_page_delete, fb_page_reply, fb_page_comment_hide, fb_page_comment_like, fb_page_comment_delete, fb_conversations, fb_conversation_thread, fb_message_send · Quản lý Trang/Fanpage Facebook qua Graph API - liệt kê Trang, đọc bài và bình luận (chỉ đọc), đăng bài/ảnh/video/album, sửa chữ, xoá bài và trả lời bình luận (toàn quyền). Dùng token của kết nối "Facebook Trang (tự tạo app)".
- **TikTok (PostPeer)** (`postpeer-tiktok`) - bundled/chạy · tools: postpeer_accounts, postpeer_tiktok_creator, postpeer_post_get, postpeer_tiktok_post · Đăng video lên TikTok tự động qua PostPeer API. Hỗ trợ lấy danh sách tài khoản, creator info, đăng video 9:16 kèm caption và theo dõi bài đăng. Dùng token của kết nối "postpeer".
- **Nhật ký dùng tool** (`tool-audit`) - bundled/tắt · tools: javis_tool_stats · hooks: post_tool_call · Đếm số lần MỖI tool được engine gọi (qua hook post_tool_call) và cho xem thống kê tool hay dùng. Đây là ví dụ minh hoạ cơ chế HOOK của plugin. Mặc định TẮT - bật qua POST /plugins/toggle (slug=tool-audit) để thử.
- **Đọc video YouTube** (`youtube-read`) - bundled/chạy · tools: javis_youtube_read · Đọc lời thoại (phụ đề) của video YouTube từ link để tóm tắt. Tự đổi qua 6 kiểu trình phát rồi tới yt-dlp khi YouTube chặn máy chủ. Không cần đăng nhập, không cần API key.
- **Gửi ảnh & file qua Zalo** (`zalo-image`) - bundled/chạy · tools: zalo_send_image · Gửi ẢNH hoặc FILE qua Zalo kèm lời nhắn, bằng chính tài khoản đã quét QR ở trang Kết nối. Bù đúng chỗ MCP chuẩn của zalo-agent-cli còn thiếu - tool zalo_send_message của nó chỉ nhận chữ.
