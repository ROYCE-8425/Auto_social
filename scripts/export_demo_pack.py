"""Script: Export Demo Data Pack.

Gom các file brand riêng, course profile và dataset demo vào 1 file nén `demo_pack.tar.gz` (nằm trong .gitignore).
Dùng để backup và chuyển giao lên VPS mà không lộ dữ liệu riêng lên GitHub mã nguồn mở.
"""
import sys
import tarfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT / "demo_pack.tar.gz"

FILES_TO_PACK = [
    "brains/Brain Default/wiki/brand-kits/game-gia-re-bsn.md",
    "brains/Brain Default/wiki/brand-kits/royce-shop.md",
    "brains/Brain Default/wiki/courses/game-bsn.md",
    "brains/Brain Default/attachments/dataset/chung/Logo-wed-bsn.png",
    "brains/Brain Default/attachments/dataset/chung/logog-game-gia-re-bsn-512x512.png",
]

DIRS_TO_PACK = [
    "brains/Brain Default/attachments/dataset/game-bsn",
]

def export_pack():
    print(f"Đang đóng gói dữ liệu demo vào {OUTPUT_FILE.name}...")
    count_files = 0
    with tarfile.open(OUTPUT_FILE, "w:gz") as tar:
        for rel_file in FILES_TO_PACK:
            p = ROOT / rel_file
            if p.is_file():
                tar.add(p, arcname=rel_file)
                print(f"  + File: {rel_file}")
                count_files += 1
            else:
                print(f"  - Bỏ qua (không tồn tại): {rel_file}")

        for rel_dir in DIRS_TO_PACK:
            d = ROOT / rel_dir
            if d.is_dir():
                tar.add(d, arcname=rel_dir)
                total_in_dir = len(list(d.rglob("*")))
                print(f"  + Thư mục: {rel_dir} ({total_in_dir} tệp/thư mục)")
                count_files += total_in_dir
            else:
                print(f"  - Bỏ qua (không tồn tại): {rel_dir}")

    print(f"\nĐã xuất thành công {OUTPUT_FILE} ({count_files} files).")
    print("File này đã được khai báo trong .gitignore nên hoàn toàn an toàn.")

if __name__ == "__main__":
    export_pack()
