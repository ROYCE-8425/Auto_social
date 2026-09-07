# -*- coding: utf-8 -*-
"""Test Strict Asset Guard: Bảo đảm không bao giờ bốc nhầm cover hoặc ảnh phụ giữa các ngành."""
import sys
from pathlib import Path

# Cấu hình encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root / "system" / "plugins" / "meta-pages-graph"))
import plugin  # noqa: E402

class MockContext:
    vault_root = str((repo_root / "brains" / "Brain Default").resolve())

ctx = MockContext()

def run_tests():
    print("=== TEST 1: Detect Course ===")
    test_cases = [
        ("tin-hoc", "tin-hoc"),
        ("Tin học văn phòng & AI", "tin-hoc"),
        ("autocad", "ve-ky-thuat"),
        ("ve-ky-thuat", "ve-ky-thuat"),
        ("Thiết kế đồ họa", "do-hoa"),
        ("do-hoa", "do-hoa"),
        ("ke-toan", "ke-toan"),
        ("Kế toán thực hành", "ke-toan"),
    ]
    for inp, expected in test_cases:
        ckey, spec = plugin._detect_course(inp)
        assert ckey == expected, f"Expected {expected}, got {ckey} for {inp}"
        print(f"  OK: '{inp}' -> '{ckey}'")

    print("\n=== TEST 2: Strict Cover Guard (Chặn cover sai ngành) ===")
    # Thử truyền cover đồ họa vào bài tin-hoc
    photos, err = plugin._auto_prepare_album("tin-hoc", "attachments/dataset/_xuat/test-dohoa-pro-poster.jpg", ctx)
    assert err is not None and "VIOLATION_ASSET_GUARD" in err, f"Chưa chặn cover sai ngành: {err}"
    print(f"  OK: Đã chặn cover đồ họa khi đăng tin-hoc: {err[:60]}...")

    # Thử truyền cover autocad vào bài ke-toan
    photos, err = plugin._auto_prepare_album("ke-toan", "attachments/dataset/_xuat/test-autocad-pro-poster.jpg", ctx)
    assert err is not None and "VIOLATION_ASSET_GUARD" in err, f"Chưa chặn cover sai ngành: {err}"
    print(f"  OK: Đã chặn cover AutoCAD khi đăng ke-toan: {err[:60]}...")

    print("\n=== TEST 3: Auto Prepare Album theo từng khóa (Chuẩn hóa & Đúng ngành) ===")
    for course in ["tin-hoc", "ve-ky-thuat", "do-hoa", "ke-toan"]:
        photos, err = plugin._auto_prepare_album(course, "auto", ctx)
        assert err is None, f"Lỗi tạo album cho {course}: {err}"
        assert len(photos) >= 5, f"Album {course} không đủ ảnh: {len(photos)}"
        print(f"  OK: [{course}] Đã tạo album {len(photos)} ảnh chuẩn hóa:")
        for i, p in enumerate(photos[:3]):
            print(f"       Ảnh #{i}: {Path(p).name}")

    print("\n=== TEST 4: Hub Call Auto Post Guard ===")
    hub_call_path = repo_root / "brains" / "Brain Default" / "scratch" / "hub_call.py"
    sys.path.insert(0, str(hub_call_path.parent))
    import hub_call  # noqa: E402

    ckey, spec = hub_call.detect_course("tin-hoc")
    assert ckey == "tin-hoc"
    photos = hub_call.unique_dataset_photos("tin-hoc _ai", forbidden=spec["forbidden"])
    assert len(photos) > 10
    # Đảm bảo không có bất kỳ file cad hay dohoa nào lọt vào
    for p in photos:
        p_stem = Path(p).stem.lower().replace(" ", "").replace("_", "").replace("-", "")
        for forb in spec["forbidden"]:
            assert forb not in p_stem, f"File vi phạm lọt vào: {p}"
    print(f"  OK: hub_call lọc {len(photos)} ảnh tin-hoc _ai 100% sạch, không dính forbidden keywords.")

    print("\n>>> TẤT CẢ TEST STRICT ASSET GUARD ĐỀU PASS 100% <<<")

if __name__ == "__main__":
    run_tests()
