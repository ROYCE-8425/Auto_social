"""Script: Import Demo Data Pack.

Giải nén `demo_pack.tar.gz` vào đúng vị trí các thư mục trong `brains/Brain Default/`.
Chạy trên VPS hoặc môi trường demo mới để phục hồi toàn bộ demo data chỉ với 1 lệnh.
"""
import sys
import tarfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_FILE = ROOT / "demo_pack.tar.gz"

def import_pack():
    if not ARCHIVE_FILE.is_file():
        print(f"Lỗi: Không tìm thấy file {ARCHIVE_FILE}.")
        print("Vui lòng đặt file demo_pack.tar.gz vào thư mục gốc của dự án trước khi chạy import.")
        return False

    print(f"Đang giải nén dữ liệu demo từ {ARCHIVE_FILE.name}...")
    with tarfile.open(ARCHIVE_FILE, "r:gz") as tar:
        tar.extractall(path=ROOT)
        names = tar.getnames()
        print(f"\nĐã giải nén thành công {len(names)} tệp/thư mục vào dự án.")
        for n in names[:10]:
            print(f"  -> {n}")
        if len(names) > 10:
            print(f"  ... và {len(names) - 10} tệp khác.")
    return True

if __name__ == "__main__":
    import_pack()
