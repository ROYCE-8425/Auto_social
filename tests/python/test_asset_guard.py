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

    print("\n=== TEST 5: Integration 1 - Resolve Docker Container Paths ===")
    test_cov = Path(ctx.vault_root) / "attachments" / "dataset" / "_xuat" / "docker_test_cover.png"
    test_cov.parent.mkdir(parents=True, exist_ok=True)
    test_cov.write_bytes(b"\x89PNG\r\n\x1a\ntest_docker_cover")
    try:
        # Test 1: Absolute path with container mount prefix /brains/Brain Default/...
        url, resolved, err = plugin._resolve_media("/brains/Brain Default/attachments/dataset/_xuat/docker_test_cover.png", ctx)
        assert resolved == test_cov.resolve(), f"Không resolve được /brains/...: {resolved}, err={err}"
        print("  OK: Resolve thành công path /brains/Brain Default/attachments/...")

        # Test 2: Relative path attachments/dataset/_xuat/...
        url, resolved, err = plugin._resolve_media("attachments/dataset/_xuat/docker_test_cover.png", ctx)
        assert resolved == test_cov.resolve(), f"Không resolve được relative path: {resolved}, err={err}"
        print("  OK: Resolve thành công relative path attachments/dataset/_xuat/...")

        # Test 3: Filename only
        url, resolved, err = plugin._resolve_media("docker_test_cover.png", ctx)
        assert resolved == test_cov.resolve(), f"Không resolve được filename: {resolved}, err={err}"
        print("  OK: Resolve thành công filename docker_test_cover.png")
    finally:
        if test_cov.exists(): test_cov.unlink()

    print("\n=== TEST 6: Integration 2 - Direct Auto Prepare Album với Container Path ===")
    dummy_cov = Path(ctx.vault_root) / "attachments" / "dataset" / "_xuat" / "direct_album_cover.png"
    dummy_cov.write_bytes(b"\x89PNG\r\n\x1a\ndirect_cover")
    try:
        container_p = "/brains/Brain Default/attachments/dataset/_xuat/direct_album_cover.png"
        photos, err = plugin._auto_prepare_album("do-hoa", container_p, ctx)
        assert err is None, f"Lỗi auto_prepare_album với container path: {err}"
        assert len(photos) >= 5, f"Không đủ ảnh: {len(photos)}"
        assert Path(photos[0]).name == "direct_album_cover.png", f"Cover đầu không khớp: {photos[0]}"
        print(f"  OK: fb_page_album direct path ăn ngay trong Docker ({len(photos)} ảnh, cover ở vị trí #0)")
    finally:
        if dummy_cov.exists(): dummy_cov.unlink()

    print("\n=== TEST 7: Integration 3 - Compact Result từ văn bản tự thuật lộn xộn ===")
    sys.path.insert(0, str(repo_root / "server"))
    import tasks
    task_obj = {"route": "wf:dang-bai-that-facebook"}
    messy_inputs = [
        ("Thiết kế đồ họa, dính wiki và brand kit",
         "Tôi đã đăng thành công bài viết cho khóa học Thiết kế đồ họa lên trang Royce Shop. "
         "Dựa theo wiki và brand kit Royce Shop, bài viết có 7 ảnh bao gồm cover AI. "
         "post_id: 122104593884849684_122104594244849684. page: Royce Shop",
         "do-hoa"),
        ("Tin học văn phòng & AI",
         "Đã đăng bài viết tuyển sinh Tin học văn phòng & AI cho page Royce Shop với 8 ảnh. "
         "post_id: 122104593884849684_99999999999999",
         "tin-hoc _ai"),
        ("Kế toán thực hành",
         "Hoàn thành đăng bài Kế toán thực hành trên page Royce Shop, "
         "post_id: 122104593884849684, gồm 6 ảnh.",
         "ke-toan"),
        ("AutoCAD ve-ky-thuat",
         "Đăng bài AutoCAD ve-ky-thuat lên page Royce Shop. "
         "Kết quả post_id: 122104593884849684_55667788990011, số lượng ảnh: 8 ảnh.",
         "ve-ky-thuat")
    ]
    for label, raw_txt, expected_course in messy_inputs:
        compact_res = tasks.TasksFeature._compact_fb_result(task_obj, raw_txt)
        assert "wiki" not in compact_res.lower(), f"Lỗi dính wiki: {compact_res}"
        assert "brand kit" not in compact_res.lower(), f"Lỗi dính brand kit: {compact_res}"
        assert expected_course in compact_res, f"Không khớp course {expected_course}: {compact_res}"
        assert "OK |" in compact_res
        print(f"  OK [{label}]: -> {compact_res}")

    print("\n>>> TẤT CẢ 7 TEST ASSET GUARD & INTEGRATION FLOW ĐỀU PASS 100% <<<")

if __name__ == "__main__":
    run_tests()
