"""Module xử lý đa kênh Brand Kit (Facebook & TikTok).
docs/dev/2026-09-17-kenh-tiktok-va-nen-tang.md (PR T1)

Nguyên tắc:
1. Một file kit = một thương hiệu (Sao Việt cơ sở X, hoặc Game BSN).
2. Trích xuất khối '## Kênh Facebook' và '## Kênh TikTok' (case-insensitive).
3. Tương thích ngược: Nếu thiếu khối kênh:
   - Facebook: suy luận từ 'Page ID:' cũ -> enabled=True nếu có page_id.
   - TikTok: enabled=False.
4. Trả về cấu trúc KitChannel nhất quán.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


@dataclass
class KitChannel:
    platform: str  # 'facebook' | 'tiktok'
    enabled: bool = False
    ids: dict[str, str] = field(default_factory=dict)
    caption_mode: str = "long"  # 'long' (album) | 'short' (8-18 dòng)
    aspect_ratio: str = "1:1"  # '1:1' | '9:16'
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ParsedBrandKit:
    filename: str
    brand: str  # 'saoviet' | 'bsn' | etc.
    name: str = ""
    facebook: KitChannel = field(default_factory=lambda: KitChannel(platform="facebook"))
    tiktok: KitChannel = field(default_factory=lambda: KitChannel(platform="tiktok", aspect_ratio="9:16", caption_mode="short"))
    raw_content: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "brand": self.brand,
            "name": self.name,
            "facebook": self.facebook.to_dict(),
            "tiktok": self.tiktok.to_dict(),
        }


def detect_brand_from_kit(kit_name_or_stem: str) -> str:
    """Suy luận brand từ tên file hoặc slug.
    game-gia-re-bsn -> 'bsn'
    còn lại -> 'saoviet'
    """
    stem = Path(kit_name_or_stem).stem.lower().strip()
    if "bsn" in stem or "game" in stem:
        return "bsn"
    return "saoviet"


def _parse_bool(val: str, default: bool = False) -> bool:
    v = (val or "").strip().lower()
    if v in ("true", "1", "yes", "bật", "bat", "on", "có", "co"):
        return True
    if v in ("false", "0", "no", "tắt", "tat", "off", "không", "khong"):
        return False
    return default


def _extract_section(md: str, heading_pattern: str) -> str:
    """Trích xuất nội dung của một section markdown bắt đầu bằng heading."""
    m = re.search(rf"^##\s+{heading_pattern}[ \t]*$", md, re.IGNORECASE | re.MULTILINE)
    if not m:
        return ""
    start = m.end()
    # Tìm section tiếp theo (bắt đầu bằng ## hoặc #)
    next_sec = re.search(r"^(?:##?|---)[ \t]+", md[start:], re.MULTILINE)
    if next_sec:
        return md[start:start + next_sec.start()].strip()
    return md[start:].strip()


def _get_line_val(sec_text: str, *labels: str) -> Optional[str]:
    """Tìm giá trị sau dấu : của một trong các labels."""
    for lbl in labels:
        m = re.search(rf"^[ \t]*[-*][ \t]*{re.escape(lbl)}[ \t]*:[ \t]*(.*)$", sec_text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()
    return None


def parse_brand_kit_channels(content_or_path: str | Path, filename: str = "") -> ParsedBrandKit:
    """Parse toàn diện các kênh Facebook và TikTok từ nội dung hoặc đường dẫn Brand Kit markdown."""
    if isinstance(content_or_path, Path):
        try:
            content = content_or_path.read_text(encoding="utf-8")
        except OSError:
            content = ""
        if not filename:
            filename = content_or_path.name
    else:
        content = str(content_or_path)

    brand = detect_brand_from_kit(filename)
    
    # 1. Trích xuất tên Fanpage / Kit
    name = ""
    m_name = re.search(r"^[ \t]*[-*][ \t]*Tên Fanpage:[ \t]*(.*)$", content, re.M)
    if m_name and m_name.group(1).strip():
        name = m_name.group(1).strip()
    else:
        m_head = re.search(r"^#\s*Kit trang(?: test)?:[ \t]*(.*)$", content, re.M)
        if m_head and m_head.group(1).strip():
            name = m_head.group(1).strip()

    # 2. Xử lý Kênh Facebook
    fb_sec = _extract_section(content, r"Kênh\s+Facebook")
    if fb_sec:
        fb_enabled = _parse_bool(_get_line_val(fb_sec, "Bật", "Bat", "enabled") or "true", default=True)
        page_id = _get_line_val(fb_sec, "Page ID", "page_id", "ID Trang", "ID Fanpage") or ""
        ratio = _get_line_val(fb_sec, "Tỷ lệ ảnh", "Tỷ lệ", "aspect_ratio") or "1:1"
        cap_mode = _get_line_val(fb_sec, "Caption", "caption_mode") or "long"
        
        fb_channel = KitChannel(
            platform="facebook",
            enabled=fb_enabled and bool(page_id),
            ids={"page_id": page_id},
            aspect_ratio=ratio,
            caption_mode=cap_mode,
        )
    else:
        # Tương thích ngược kit cũ: Tìm Page ID ở root markdown
        m_pid = re.search(r"^[ \t]*[-*][ \t]*(?:Page ID|page_id|ID Fanpage|ID Trang)[ \t]*:[ \t]*(.*)$", content, re.I | re.M)
        page_id = m_pid.group(1).strip() if m_pid else ""
        fb_channel = KitChannel(
            platform="facebook",
            enabled=bool(page_id),
            ids={"page_id": page_id} if page_id else {},
            aspect_ratio="1:1",
            caption_mode="long",
        )

    # 3. Xử lý Kênh TikTok
    tt_sec = _extract_section(content, r"Kênh\s+TikTok")
    if tt_sec:
        tt_enabled = _parse_bool(_get_line_val(tt_sec, "Bật", "Bat", "enabled") or "false", default=False)
        account_id = _get_line_val(tt_sec, "accountId", "account_id", "TikTok accountId") or ""
        # Bỏ qua nếu là placeholder chưa nối
        if account_id.upper() in ("CHƯA_NỐI", "CHUA_NOI", "NONE", ""):
            account_id = ""
            tt_enabled = False

        username = _get_line_val(tt_sec, "username", "TikTok username", "@user") or ""
        ratio = _get_line_val(tt_sec, "Tỷ lệ", "aspect_ratio") or "9:16"
        cap_mode = _get_line_val(tt_sec, "Caption", "caption_mode") or "short"
        
        raw_hashtags = _get_line_val(tt_sec, "Hashtag", "hashtags") or ""
        hashtags = [h.strip() for h in re.split(r"[\s,]+", raw_hashtags) if h.strip().startswith("#")]

        disable_duet = _parse_bool(_get_line_val(tt_sec, "Tắt Duet", "disable_duet") or "true", default=True)
        disable_stitch = _parse_bool(_get_line_val(tt_sec, "Tắt Stitch", "disable_stitch") or "true", default=True)
        video_cdn = _get_line_val(tt_sec, "Video CDN", "video_cdn", "cdn") or ""

        tt_channel = KitChannel(
            platform="tiktok",
            enabled=tt_enabled and bool(account_id),
            ids={"account_id": account_id, "accountId": account_id, "username": username},
            aspect_ratio=ratio,
            caption_mode=cap_mode,
            extras={
                "hashtags": hashtags,
                "hashtag": " ".join(hashtags),
                "disable_duet": disable_duet,
                "disable_stitch": disable_stitch,
                "video_cdn": video_cdn,
            },
        )
    else:
        # Kit không có khối TikTok -> tắt
        tt_channel = KitChannel(
            platform="tiktok",
            enabled=False,
            ids={},
            aspect_ratio="9:16",
            caption_mode="short",
            extras={"hashtags": [], "disable_duet": True, "disable_stitch": True},
        )

    return ParsedBrandKit(
        filename=filename,
        brand=brand,
        name=name,
        facebook=fb_channel,
        tiktok=tt_channel,
        raw_content=content,
    )


def load_all_brand_kits(vault_dir: Path | str) -> list[ParsedBrandKit]:
    """Quét và parse toàn bộ brand kit trong thư mục wiki/brand-kits."""
    v = Path(vault_dir)
    bk_dir = v / "wiki" / "brand-kits"
    if not bk_dir.is_dir():
        return []

    kits = []
    for f in sorted(bk_dir.glob("*.md")):
        if f.name.startswith(("_anh", "_the", "_index")):
            continue
        try:
            txt = f.read_text(encoding="utf-8")
            kits.append(parse_brand_kit_channels(txt, f.name))
        except OSError:
            continue
    return kits


def get_active_tiktok_channels(vault_dir: Path | str) -> list[ParsedBrandKit]:
    """Lấy danh sách các brand kit có kênh TikTok đã bật và có accountId hợp lệ."""
    all_kits = load_all_brand_kits(vault_dir)
    return [k for k in all_kits if k.tiktok.enabled and k.tiktok.ids.get("account_id")]
