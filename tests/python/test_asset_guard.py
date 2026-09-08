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
    dummy_dohoa = Path(ctx.vault_root) / "attachments" / "dataset" / "do-hoa" / "temp_dohoa_poster.png"
    dummy_cad = Path(ctx.vault_root) / "attachments" / "dataset" / "ve-ky-thuat" / "temp_autocad_poster.png"
    dummy_dohoa.write_bytes(b"\x89PNG\r\n\x1a\nfake")
    dummy_cad.write_bytes(b"\x89PNG\r\n\x1a\nfake")
    try:
        # Thử truyền cover đồ họa vào bài tin-hoc
        photos, err = plugin._auto_prepare_album("tin-hoc", str(dummy_dohoa.relative_to(ctx.vault_root)), ctx)
        assert err is not None and "VIOLATION_ASSET_GUARD" in err, f"Chưa chặn cover sai ngành: {err}"
        print(f"  OK: Đã chặn cover đồ họa khi đăng tin-hoc: {err[:60]}...")

        # Thử truyền cover autocad vào bài ke-toan
        photos, err = plugin._auto_prepare_album("ke-toan", str(dummy_cad.relative_to(ctx.vault_root)), ctx)
        assert err is not None and "VIOLATION_ASSET_GUARD" in err, f"Chưa chặn cover sai ngành: {err}"
        print(f"  OK: Đã chặn cover AutoCAD khi đăng ke-toan: {err[:60]}...")
    finally:
        if dummy_dohoa.exists(): dummy_dohoa.unlink()
        if dummy_cad.exists(): dummy_cad.unlink()

    print("\n=== TEST 3: Auto Prepare Album - Chặn thiếu cover AI & Thành công khi có cover AI ===")
    # 3.1: Thử gọi không truyền cover hoặc cover='auto' -> PHẢI trả về POST_SKIP ly-do=thieu-cover-ai
    for course in ["tin-hoc", "ve-ky-thuat", "do-hoa", "ke-toan"]:
        photos, err = plugin._auto_prepare_album(course, "auto", ctx)
        assert err is not None and "POST_SKIP ly-do=thieu-cover-ai" in err, f"Chưa chặn thiếu cover AI cho {course}: {err}"
        print(f"  OK: Đã chặn thành công khi không có cover AI cho '{course}'")

    # 3.2: Khi có cover AI hợp lệ -> Tạo album thành công 100%, ảnh cover làm photos[0]
    dummy_covers = {}
    for course, alias in [("tin-hoc", "tinhoc"), ("ve-ky-thuat", "cad"), ("do-hoa", "dohoa"), ("ke-toan", "ketoan")]:
        cov_p = Path(ctx.vault_root) / "attachments" / "dataset" / "_xuat" / f"ai_gen_cover_{alias}_test.png"
        cov_p.write_bytes(b"\x89PNG\r\n\x1a\nfake_ai_cover")
        dummy_covers[course] = cov_p

    try:
        for course in ["tin-hoc", "ve-ky-thuat", "do-hoa", "ke-toan"]:
            cov_p = dummy_covers[course]
            photos, err = plugin._auto_prepare_album(course, str(cov_p.relative_to(ctx.vault_root)), ctx)
            assert err is None, f"Lỗi tạo album cho {course}: {err}"
            assert len(photos) >= 5, f"Album {course} không đủ ảnh: {len(photos)}"
            assert "ai_gen_cover" in Path(photos[0]).name, f"Ảnh đầu không phải cover AI: {photos[0]}"
            print(f"  OK: [{course}] Đã tạo album {len(photos)} ảnh chuẩn hóa với cover AI:")
            for i, p in enumerate(photos[:2]):
                print(f"       Ảnh #{i}: {Path(p).name}")
    finally:
        for p in dummy_covers.values():
            if p.exists(): p.unlink()

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
