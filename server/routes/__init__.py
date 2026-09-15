"""Các nhóm route bóc ra khỏi main.py.

Mỗi module ở đây theo đúng khuôn đã có sẵn của các module tính năng (reminders.py, tasks.py,
self_improve.py, learn.py): dựng một APIRouter rồi `register(app, deps)` gọi
`app.include_router(router)`.

Hai luật bắt buộc, vi phạm là hỏng theo kiểu khó thấy:

1. KHÔNG `import main`. main.py là gốc lắp ráp, nó import xuống đây; import ngược lại là
   vòng. Thứ gì cần từ main thì nhận qua `deps` (tiêm phụ thuộc), đúng như 5 module tính năng
   đang làm.

2. Lời gọi `register(app, ...)` trong main.py phải đặt ĐÚNG vị trí dòng cũ của khối route.
   Starlette khớp route theo THỨ TỰ đăng ký, và tests/python/route_table.json khoá cả thứ tự.
   Đặt sai chỗ thì test bảng route đỏ ngay, kể cả khi ứng dụng vẫn chạy.
"""
