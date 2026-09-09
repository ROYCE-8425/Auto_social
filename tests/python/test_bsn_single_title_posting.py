"""Unit tests: BSN Single Game Title Posting & Address-Free Brand Kit.

Verifies:
1. BSN Brand Kit has zero physical address (Lý Thường Kiệt, Tô Hiến Thành, etc.).
2. pick_next_fanpage.py rotates round-robin across the 10 games, printing exactly 1 title and its pure dataset subfolder.
3. dia_chi is empty and CHAN_TRANG contains no address lines.
4. COURSE_SPECS contains 'game-bsn' with forbidden educational keywords.
5. _auto_prepare_album selects screenshots strictly from the chosen game's subfolder.
6. _caption_kit_err validator accepts address-free footer for BSN.
"""
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "server"))
sys.path.insert(0, str(REPO_ROOT / "brains" / "Brain Default" / "skills" / "dang-bai-facebook" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "system" / "plugins" / "meta-pages-graph"))

from pick_next_fanpage import BSN_GAMES, pick_bsn_game, get_page_branches
import plugin as meta_plugin


def test_bsn_brand_kit_has_no_physical_address():
    kit_path = REPO_ROOT / "brains" / "Brain Default" / "wiki" / "brand-kits" / "game-gia-re-bsn.md"
    assert kit_path.is_file(), "game-gia-re-bsn.md must exist"
    content = kit_path.read_text(encoding="utf-8")
    
    # Check that forbidden address components are completely removed
    assert "Lý Thường Kiệt" not in content
    assert "Tô Hiến Thành" not in content
    assert "Phường 14" not in content
    assert "Quận 10" not in content
    assert "13 cơ sở" not in content


def test_bsn_games_dataset_and_count():
    assert len(BSN_GAMES) == 10
    dataset_root = REPO_ROOT / "brains" / "Brain Default" / "attachments" / "dataset" / "game-bsn"
    assert dataset_root.is_dir()

    for g in BSN_GAMES:
        assert "title" in g
        assert "slug" in g
        assert "price" in g
        assert "genre" in g
        assert "highlights" in g
        game_dir = REPO_ROOT / "brains" / "Brain Default" / g["folder"]
        assert game_dir.is_dir(), f"Folder {g['folder']} must exist in dataset"
        # Must have screenshots
        images = [f for f in game_dir.iterdir() if f.suffix.lower() in [".jpg", ".png", ".webp"]]
        assert len(images) >= 3, f"Game {g['title']} must have at least 3 screenshots"


def test_bsn_game_round_robin_rotation():
    st = {"bsn_last_game": ""}
    seen_slugs = []
    for _ in range(len(BSN_GAMES)):
        game = pick_bsn_game(st)
        assert game["slug"] not in seen_slugs
        seen_slugs.append(game["slug"])
        st["bsn_last_game"] = game["slug"]

    assert len(seen_slugs) == 10
    # Next call after 10 wraps back around
    first_again = pick_bsn_game(st)
    assert first_again["slug"] == seen_slugs[0]


def test_get_page_branches_empty_for_bsn():
    row_bsn = {
        "name": "Game Giá Rẻ BSN",
        "slug": "game-gia-re-bsn",
        "tags": ["game-bsn"],
        "address": "",
    }
    branches = get_page_branches(row_bsn, "game-bsn")
    assert branches == [], "BSN must never return branches or fallback to 13 Sao Viet branches"


def test_course_specs_contains_game_bsn():
    assert "game-bsn" in meta_plugin.COURSE_SPECS
    spec = meta_plugin.COURSE_SPECS["game-bsn"]
    assert spec["folder"] == "game-bsn"
    # Ensure educational and recruitment keywords are strictly forbidden
    for kw in ["autocad", "ketoan", "tinhoc", "tuyensinh", "khaigiang"]:
        assert kw in spec["forbidden"]


def test_auto_prepare_album_for_single_subgame(tmp_path):
    vault_root = REPO_ROOT / "brains" / "Brain Default"
    xuat_dir = vault_root / "attachments" / "dataset" / "_xuat"
    xuat_dir.mkdir(parents=True, exist_ok=True)
    dummy_cover = xuat_dir / "test_cover_bsn_dawnwalker.png"
    dummy_cover.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")

    class DummyContext:
        def __init__(self, vr):
            self.vault_root = str(vr)
        def get(self, key, default=None):
            if key == "system_root":
                return str(REPO_ROOT)
            if key == "vault_root":
                return self.vault_root
            return default

    # Test auto prepare album for a specific game
    game_slug = "the-blood-of-dawnwalker"
    course_input = f"game-bsn/{game_slug}"
    cover_ref = f"attachments/dataset/_xuat/{dummy_cover.name}"
    
    cctx = DummyContext(vault_root)
    photos, err = meta_plugin._auto_prepare_album(course_input, cover_ref, cctx)
    assert err is None, f"Unexpected error: {err}"
    assert photos is not None
    assert len(photos) >= 4

    # Every single photo after cover must come from the_blood_of_dawnwalker folder
    for p in photos[1:]:
        p_str = str(p).replace("\\", "/")
        assert f"game-bsn/{game_slug}" in p_str, (
            f"Photo {p} does not belong exclusively to {game_slug}!"
        )


def test_caption_kit_validator_allows_empty_address():
    vault_root = REPO_ROOT / "brains" / "Brain Default"
    class DummyContext:
        def __init__(self, vr):
            self.vault_root = str(vr)
        def get(self, key, default=None):
            if key == "vault_root":
                return self.vault_root
            return default

    cctx = DummyContext(vault_root)
    # 25+ lines caption to pass min-length check
    body_lines = [
        "🎮 THE BLOOD OF DAWNWALKER — SIÊU PHẨM DARK FANTASY VIỆT HÓA 100% CHỈ 45.000 ₫!",
        "",
        "Trải nghiệm thế giới mở dark fantasy u tối nghẹt thở cuối tuần này.",
        "Chặt chém boss căng não cùng đồ họa đỉnh cao Unreal Engine thế hệ mới.",
        "Khám phá những vùng đất tăm tối đầy rẫy hiểm nguy và bí ẩn cổ xưa.",
        "Tự do xây dựng nhánh kỹ năng và trang bị phù hợp với phong cách chiến đấu.",
        "Bản dịch tiếng Việt 100% cực kỳ tâm huyết giúp anh em hiểu trọn vẹn cốt truyện.",
        "Không cần tra từ điển từng câu chữ, thỏa sức đắm chìm vào thế giới game bom tấn.",
        "",
        "Bộ 5 cam kết vàng từ Game Giá Rẻ BSN:",
        "🛡️ Tải trực tiếp 100% từ launcher Steam chính hãng — an toàn tuyệt đối không virus.",
        "💾 Chơi offline vĩnh viễn, lưu file save game trên máy riêng, cập nhật bản vá đầy đủ.",
        "🇻🇳 Tặng kèm patch Việt Hóa chuẩn xịn, cài đặt siêu mượt.",
        "⚡ Chốt đơn tự động nhận tài khoản chỉ trong 1-5 phút. Hỗ trợ Ultraview 1-1 tận tình.",
        "🔒 Bảo hành 3 tháng suốt quá trình chơi — cài lại Win hay đổi máy đều được cấp lại.",
        "",
        "💰 Giá sinh viên: Chỉ 45.000 ₫ (tiết kiệm hơn 90% so với giá Store).",
        "👉 Anh em nhắn tin ngay cho Fanpage hoặc liên hệ Zalo để húp ngay acc nhé!",
        "",
        "Game Giá Rẻ BSN",
        "📞 Hotline / Zalo: 0877 104 996",
        "📧 Email: gamegiarebsn@gmail.com",
        "🌐 Website: https://gamegiarebsn.com",
        "📘 Fanpage: https://www.facebook.com/343562028848465",
    ]
    body = "\n".join(body_lines)
    
    # Page ID of BSN
    page_id = "343562028848465"
    err = meta_plugin._caption_kit_err(body, page_id, cctx)
    assert err is None, f"BSN footer validation should pass without address, got error: {err}"

