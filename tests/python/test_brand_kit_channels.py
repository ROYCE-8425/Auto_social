"""Unit tests: Parser Brand Kit đa kênh Facebook & TikTok (PR T1).
docs/dev/2026-09-17-kenh-tiktok-va-nen-tang.md
"""
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "server"))

from brand_kit import (
    parse_brand_kit_channels,
    detect_brand_from_kit,
    ParsedBrandKit,
    KitChannel,
)


def test_detect_brand():
    assert detect_brand_from_kit("game-gia-re-bsn.md") == "bsn"
    assert detect_brand_from_kit("bsn_fanpage.md") == "bsn"
    assert detect_brand_from_kit("_mac-dinh.md") == "saoviet"
    assert detect_brand_from_kit("royce-shop.md") == "saoviet"
    assert detect_brand_from_kit("thsv-bien-hoa.md") == "saoviet"


def test_legacy_kit_without_channel_blocks():
    """Kit cũ chỉ có Page ID: ở root -> Facebook bật, TikTok tắt."""
    md = """# Kit trang: Tin Học Sao Việt Q7
- Page ID: 108426965133947
- Màu chính: #6C3BFF
- Font: Roboto
"""
    parsed = parse_brand_kit_channels(md, "thsv-q7.md")
    assert parsed.brand == "saoviet"
    assert parsed.facebook.enabled is True
    assert parsed.facebook.ids["page_id"] == "108426965133947"
    assert parsed.tiktok.enabled is False
    assert parsed.tiktok.ids == {}


def test_kit_with_both_channels_enabled():
    """Kit có đủ cả 2 khối kênh hợp lệ -> cả hai đều bật."""
    md = """# Kit trang: Game Giá Rẻ BSN
- Brand: BSN

## Kênh Facebook
- Bật: true
- Page ID: 343562028848465
- Tỷ lệ ảnh: 1:1
- Caption: dài (album)

## Kênh TikTok
- Bật: true
- accountId: acc_tt_bsn_999
- username: @gamegiarebsn
- Tỷ lệ: 9:16
- Caption: ngắn (8-18 dòng)
- Hashtag: #GameGiaReBSN #SteamOffline #GameBanQuyen
- Tắt Duet: true
- Tắt Stitch: true
- Video CDN: https://cdn.example.com/videos/bsn/
"""
    parsed = parse_brand_kit_channels(md, "game-gia-re-bsn.md")
    assert parsed.brand == "bsn"
    
    # Facebook check
    assert parsed.facebook.enabled is True
    assert parsed.facebook.ids["page_id"] == "343562028848465"
    assert parsed.facebook.aspect_ratio == "1:1"
    assert parsed.facebook.caption_mode == "dài (album)"

    # TikTok check
    assert parsed.tiktok.enabled is True
    assert parsed.tiktok.ids["account_id"] == "acc_tt_bsn_999"
    assert parsed.tiktok.ids["username"] == "@gamegiarebsn"
    assert parsed.tiktok.aspect_ratio == "9:16"
    assert "#GameGiaReBSN" in parsed.tiktok.extras["hashtags"]
    assert "#SteamOffline" in parsed.tiktok.extras["hashtags"]
    assert parsed.tiktok.extras["disable_duet"] is True
    assert parsed.tiktok.extras["video_cdn"] == "https://cdn.example.com/videos/bsn/"


def test_kit_with_unconnected_tiktok():
    """Kit có khối TikTok nhưng accountId là CHƯA_NỐI hoặc Bật: false -> TikTok tắt."""
    md = """# Kit trang: Royce Shop
## Kênh Facebook
- Bật: true
- Page ID: 988656934325292

## Kênh TikTok
- Bật: false
- accountId: CHƯA_NỐI
- username: @tinhocsaoviet
- Hashtag: #TinhocSaoViet #HocExcel
"""
    parsed = parse_brand_kit_channels(md, "royce-shop.md")
    assert parsed.brand == "saoviet"
    assert parsed.facebook.enabled is True
    assert parsed.tiktok.enabled is False
    assert parsed.tiktok.ids.get("account_id") == ""
