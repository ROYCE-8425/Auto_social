"""Cho pytest tìm được module trong server/.

Hiện CI KHÔNG chạy pytest mà chạy từng file như script (`python tests/python/test_x.py`),
vì 61 trên 76 file gọi `sys.exit()` ngay ở mức module - dưới pytest thì bước collect import
từng file là chạy luôn assertion rồi thoát, huỷ cả lượt chạy. Chuyển dần sang pytest thật là
việc nền, không nằm trên đường găng.

File này tồn tại để khi chạy `pytest tests/python/test_abc.py` với một file ĐÃ chuyển sang
kiểu pytest thì nó import được module server. Import `_paths` là đủ: chính nó nạp server/
vào sys.path.
"""
import _paths  # noqa: F401
