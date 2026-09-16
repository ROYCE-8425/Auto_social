# -*- coding: utf-8 -*-
"""Test TikTok queue picker with multi-channel brand kits."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "brains" / "Brain Default" / "skills" / "dang-video-tiktok" / "scripts" / "pick_next_tiktok.py"


def run_picker(cwd: Path) -> str:
    res = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return res.stdout.strip()


def test_picker_when_no_account_connected():
    """Tất cả kit mẫu hiện tại đều để accountId CHƯA_NỐI -> trả NEXT=NONE chua-noi-tiktok."""
    out = run_picker(ROOT)
    assert "NEXT=NONE chua-noi-tiktok" in out, f"Expected NEXT=NONE chua-noi-tiktok, got: {out}"


def test_picker_with_connected_saoviet_kit():
    """Khi có kit Sao Việt bật kênh TikTok và có accountId thật."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        tmp_path = Path(tmp_dir)
        bk_dir = tmp_path / "wiki" / "brand-kits"
        bk_dir.mkdir(parents=True, exist_ok=True)

        kit_content = """# Kit trang: Tin Học Sao Việt Quận 7
- Tên Fanpage: Tin Học Sao Việt Quận 7
- Hotline: 0935 195 118

## Kênh Facebook
- Bật: true
- Page ID: 108426965133947

## Kênh TikTok
- Bật: true
- accountId: acc_tt_saoviet_real_123
- username: @tinhocsaoviet_q7
- Hashtag: #TinhocSaoViet #HocExcel #ExcelQ7
- Tắt Duet: true
- Tắt Stitch: true
"""
        (bk_dir / "tin-hoc-sao-viet-quan-7.md").write_text(kit_content, encoding="utf-8")

        out = run_picker(tmp_path)
        assert "NEXT=1" in out
        assert "account_id=acc_tt_saoviet_real_123" in out
        assert "username=@tinhocsaoviet_q7" in out
        assert "brand=saoviet" in out
        assert "the=tin-hoc_ai" in out
        assert "#TinhocSaoViet" in out


def test_picker_with_connected_bsn_kit():
    """Khi có kit Game Giá Rẻ BSN bật kênh TikTok và có accountId thật."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        tmp_path = Path(tmp_dir)
        bk_dir = tmp_path / "wiki" / "brand-kits"
        bk_dir.mkdir(parents=True, exist_ok=True)

        kit_content = """# Kit trang: Game Giá Rẻ BSN
- Tên Fanpage: Game Giá Rẻ BSN
- Hotline: 0901 234 567

## Kênh Facebook
- Bật: true
- Page ID: 222333444

## Kênh TikTok
- Bật: true
- accountId: acc_tt_bsn_999
- username: @gamegiarebsn
- Hashtag: #GameGiaRe #SteamGame #SteamVN #GamingPC
- Tắt Duet: true
- Tắt Stitch: true
"""
        (bk_dir / "game-gia-re-bsn.md").write_text(kit_content, encoding="utf-8")

        out = run_picker(tmp_path)
        assert "NEXT=1" in out
        assert "account_id=acc_tt_bsn_999" in out
        assert "username=@gamegiarebsn" in out
        assert "brand=bsn" in out
        assert "the=game-bsn" in out
        assert "#GameGiaRe" in out
        assert "tin-hoc" not in out


def main():
    test_picker_when_no_account_connected()
    test_picker_with_connected_saoviet_kit()
    test_picker_with_connected_bsn_kit()
    print("OK - test_tiktok_queue_picker: tất cả pass")


if __name__ == "__main__":
    main()
