---
type: loop
name: Đăng Royce Shop ngẫu nhiên
slug: dang-royce-shop-ngau-nhien-moi-5-phut
enabled: false
mode: full
goal: custom
interval_min: 5
quiet_hours: 22-07
max_runs_per_day: 100
notify: false
updated: 2026-09-08
---

Mỗi vòng CHỈ đăng 1 bài duy nhất lên Fanpage Royce Shop (Page ID: 988656934325292) rồi DỪNG.
Tuyệt đối KHÔNG đọc loop-log hoặc transcript cũ để tránh phình token.

## Quy trình Fast Path Deterministic (1 Turn):

1. Chạy lệnh chọn khóa học tiếp theo (tự động xoay vòng tránh trùng khóa học qua state):
   `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --include-royce --page "Royce Shop"`
2. Đọc khối `the=<khoa_hoc>` và `CHAN_TRANG` từ kết quả bước 1.
3. Soạn caption chuẩn 7 nhịp Sao Việt theo `wiki/brand-kits/royce-shop.md` (nhịp thị giác 👉 ✅ 📌 🎁 📩 📞) kèm chân trang.
4. Gọi đăng album bằng đúng 1 lệnh duy nhất:
   `fb_page_album(page="Royce Shop", course="<the>", message="<caption>", photos="auto")`
   hoặc:
   `python "brains/Brain Default/scratch/hub_call.py" auto_post "Royce Shop" "<the>" "<caption>"`
5. Đánh dấu hoàn thành:
   `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --ok 988656934325292 <the>`
6. Trả về kết quả 1 dòng: `POST_OK post_id=<post_id> link=<link>`
