"""Đường dẫn dùng chung cho mọi test Python, và nạp server/ vào sys.path.

Vì sao có file này: trước 0.9.242 các test nằm CHUNG thư mục với mã nguồn, nên chúng lấy
đường dẫn bằng `Path(__file__).parent` (ra server/) và `Path(__file__).parent.parent` (ra
gốc repo). Khi test dọn sang tests/python/ thì cả hai lệch một tầng, và 37 chỗ như vậy nằm
rải trong 30 file. Gom về một chỗ thì sửa một lần, và lần sau có dời nữa cũng chỉ sửa ở đây.

Import nó cũng đồng thời NẠP server/ vào sys.path, nên test gọi `import main` được từ bất kỳ
thư mục làm việc nào. Trước đây test phải chạy đúng từ server/ mới import được; nay không còn
ràng buộc đó, kể cả với các test mở file nguồn bằng đường dẫn.

    from _paths import ROOT, SERVER     # đặt TRƯỚC mọi `import <module server>`
"""
import sys
from pathlib import Path

# tests/python/_paths.py -> parents[0]=python, [1]=tests, [2]=gốc repo
ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "server"
DASHBOARD = ROOT / "dashboard"
SYSTEM = ROOT / "system"

if str(SERVER) not in sys.path:
    sys.path.insert(0, str(SERVER))
