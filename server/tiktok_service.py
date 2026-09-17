"""Dịch vụ quản lý và đăng bài TikTok qua PostPeer API (Carousel 9:16 + Auto Music).

Hỗ trợ:
- Lấy trạng thái kết nối PostPeer, ẩn key.
- Lấy thông tin tài khoản và Brand Kits có cấu hình TikTok.
- Chuẩn bị ảnh dọc 9:16 từ Dataset hoặc AI vào _xuat-tiktok/.
- Đăng carousel ảnh qua PostPeer và ghi log vào Javis/tiktok-posts.jsonl.
- Bật/tắt Loop đăng bài hàng ngày.
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

try:
    from PIL import Image
except ImportError:
    Image = None

ROOT = Path(__file__).resolve().parents[1]
BASE_POSTPEER = "https://api.postpeer.dev/v1"


def _get_vault_root(vault_root: Optional[Union[str, Path]] = None) -> Path:
    if vault_root:
        return Path(vault_root)
    return ROOT / "brains" / "Brain Default"


def _find_loop_file(vault_root: Path) -> Path:
    candidates = [
        vault_root / "Javis" / "loops" / "dang-video-tiktok-hang-ngay.md",
        vault_root / "Javis" / "dang-video-tiktok-hang-ngay.md",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return candidates[0]


def get_postpeer_connection() -> dict[str, Any]:
    """Lấy thông tin connection postpeer từ mcp_store, ẩn access key."""
    try:
        import mcp_store
        conns = mcp_store.list_connections()
        c = next((x for x in conns if x.get("connector_id") == "postpeer"), None)
        if not c:
            return {"connected": False, "perm": "readonly", "masked_key": "", "connection_id": ""}
        
        secrets = mcp_store.connection_secrets(c["id"]) or {}
        key = (secrets.get("postpeer_key") or "").strip()
        masked = f"...{key[-4:]}" if len(key) >= 4 else ("***" if key else "")
        return {
            "connected": bool(key),
            "perm": c.get("perm") or "readonly",
            "masked_key": masked,
            "connection_id": c.get("id") or "",
            "label": c.get("label") or "TikTok PostPeer",
        }
    except Exception as e:
        return {"connected": False, "perm": "readonly", "masked_key": "", "error": str(e)}


def get_postpeer_token() -> Optional[str]:
    """Lấy token thật phục vụ gọi PostPeer API."""
    try:
        import mcp_store
        for c in mcp_store.list_connections():
            if c.get("connector_id") == "postpeer":
                secrets = mcp_store.connection_secrets(c["id"]) or {}
                token = (secrets.get("postpeer_key") or "").strip()
                if token:
                    return token
    except Exception:
        pass
    return None


def fetch_postpeer_accounts_sync() -> list[dict[str, Any]]:
    """Gọi PostPeer API lấy danh sách tài khoản đã kết nối OAuth (đồng bộ)."""
    token = get_postpeer_token()
    if not token:
        return []
    import requests
    headers = {
        "x-access-key": token,
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    for u in [f"{BASE_POSTPEER}/connect/integrations", f"{BASE_POSTPEER}/integrations"]:
        try:
            r = requests.get(u, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                items = data.get("integrations") or data.get("data") or data
                if isinstance(items, list):
                    out = []
                    for it in items:
                        if isinstance(it, dict):
                            acc_id = str(it.get("accountId") or it.get("id") or "")
                            uname = str(it.get("username") or it.get("name") or "")
                            out.append({
                                "id": acc_id,
                                "name": uname or acc_id,
                                "username": uname or acc_id,
                                "platform": str(it.get("platform") or "tiktok").lower(),
                                "status": str(it.get("status") or "active"),
                            })
                    return out
        except Exception:
            continue
    return []


async def fetch_postpeer_accounts() -> list[dict[str, Any]]:
    """Gọi PostPeer API lấy danh sách tài khoản đã kết nối OAuth (bất đồng bộ)."""
    return await asyncio.to_thread(fetch_postpeer_accounts_sync)


def get_tiktok_status(vault_root: Optional[Union[str, Path]] = None) -> dict[str, Any]:
    """Tổng hợp trạng thái kênh TikTok: kết nối PostPeer, kit, loop, recent posts."""
    vault = _get_vault_root(vault_root)
    conn = get_postpeer_connection()
    masked_key = conn.get("masked_key", "")
    connected = bool(conn.get("connected") or conn.get("enabled") or conn.get("api_key") or masked_key)

    accounts = []
    if connected:
        try:
            accounts = fetch_postpeer_accounts_sync()
        except Exception:
            accounts = []

    kits = list_tiktok_kits(vault)
    loop = get_loop_status(vault)
    recent = get_recent_posts(vault, limit=10)

    return {
        "ok": True,
        "connected": connected,
        "masked_key": masked_key,
        "accounts": accounts,
        "kits": kits,
        "loop": loop,
        "recent_posts": recent,
    }



def parse_tiktok_kit(p: Path) -> dict[str, Any] | None:
    """Đọc thông tin cấu hình kênh TikTok từ file brand kit."""
    try:
        content = p.read_text(encoding="utf-8")
    except OSError:
        return None
    
    if "## Kênh TikTok" not in content:
        return None
    
    # Cắt khối TikTok
    lines = content.splitlines()
    in_tt = False
    data: dict[str, Any] = {
        "file": p.name,
        "stem": p.stem,
        "name": p.stem,
        "enabled": False,
        "account_id": "",
        "username": "",
        "ratio": "9:16",
        "caption_style": "ngắn",
        "hashtags": "",
        "disable_duet": True,
        "disable_stitch": True,
        "brand": "saoviet",
    }
    
    # Tìm tên thương hiệu
    for line in lines:
        if line.startswith("- Tên thương hiệu:") or line.startswith("- Tên Fanpage:"):
            data["name"] = line.split(":", 1)[1].strip()
            break

    if "bsn" in p.name.lower() or "game" in p.name.lower():
        data["brand"] = "bsn"
    elif "saoviet" in p.name.lower() or "royce" in p.name.lower():
        data["brand"] = "saoviet"

    for line in lines:
        s = line.strip()
        if s.startswith("## Kênh TikTok"):
            in_tt = True
            continue
        if in_tt:
            if s.startswith("## "):
                break
            if s.startswith("- Bật:"):
                data["enabled"] = "true" in s.lower()
            elif s.startswith("- accountId:"):
                data["account_id"] = s.split(":", 1)[1].strip()
            elif s.startswith("- username:"):
                data["username"] = s.split(":", 1)[1].strip()
            elif s.startswith("- Hashtag:"):
                data["hashtags"] = s.split(":", 1)[1].strip()
            elif s.startswith("- Tắt Duet:"):
                data["disable_duet"] = "true" in s.lower()
            elif s.startswith("- Tắt Stitch:"):
                data["disable_stitch"] = "true" in s.lower()
                
    return data


def list_tiktok_kits(vault_root: Path) -> list[dict[str, Any]]:
    """Liệt kê toàn bộ brand kits có cấu hình TikTok."""
    d = vault_root / "wiki" / "brand-kits"
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.glob("*.md")):
        if p.name.startswith("_"):
            continue
        kit = parse_tiktok_kit(p)
        if kit:
            out.append(kit)
    return out


def get_loop_status(vault_root: Optional[Union[str, Path]] = None) -> dict[str, Any]:
    """Lấy trạng thái của loop đăng video TikTok hàng ngày."""
    vault = _get_vault_root(vault_root)
    loop_file = _find_loop_file(vault)
    if not loop_file.is_file():
        return {"exists": False, "enabled": False, "name": "Đăng video TikTok hàng ngày", "file": str(loop_file.name)}
    try:
        content = loop_file.read_text(encoding="utf-8")
        enabled = False
        m = re.search(r"^enabled:\s*(true|false)", content, re.M | re.I)
        if m:
            enabled = m.group(1).lower() == "true"
        return {"exists": True, "enabled": enabled, "name": "Đăng video TikTok hàng ngày", "file": str(loop_file.name)}
    except Exception:
        return {"exists": True, "enabled": False, "name": "Đăng video TikTok hàng ngày", "file": str(loop_file.name)}


def set_loop_status(enabled: bool = False, vault_root: Optional[Union[str, Path]] = None, **kwargs) -> dict[str, Any]:
    """Bật/tắt loop đăng video TikTok hàng ngày."""
    if isinstance(enabled, (str, Path)) and (vault_root is None or isinstance(vault_root, bool)):
        actual_vault = enabled
        actual_enabled = bool(vault_root)
    else:
        actual_vault = vault_root or kwargs.get("vault")
        actual_enabled = bool(enabled)

    vault = _get_vault_root(actual_vault)
    loop_file = _find_loop_file(vault)
    if not loop_file.is_file():
        loop_file.parent.mkdir(parents=True, exist_ok=True)
        loop_file.write_text(f"---\nenabled: {'true' if actual_enabled else 'false'}\ncron: '0 11 * * *'\n---\n# Đăng video TikTok hàng ngày\n", encoding="utf-8")
        return {"exists": True, "enabled": actual_enabled, "name": "Đăng video TikTok hàng ngày", "file": str(loop_file.name)}
    try:
        content = loop_file.read_text(encoding="utf-8")
        val_str = "true" if actual_enabled else "false"
        if re.search(r"^enabled:\s*(true|false)", content, re.M | re.I):
            new_content = re.sub(r"^enabled:\s*(true|false)", f"enabled: {val_str}", content, flags=re.M | re.I)
        else:
            new_content = content.replace("---", f"---\nenabled: {val_str}", 1)
        loop_file.write_text(new_content, encoding="utf-8")
        return {"exists": True, "enabled": actual_enabled, "name": "Đăng video TikTok hàng ngày", "file": str(loop_file.name)}
    except Exception as e:
        return {"exists": True, "enabled": False, "error": str(e), "file": str(loop_file.name)}



def get_recent_posts(vault_root: Path, limit: int = 20) -> list[dict[str, Any]]:
    """Đọc các bài đăng gần nhất từ Javis/tiktok-posts.jsonl."""
    log_file = vault_root / "Javis" / "tiktok-posts.jsonl"
    if not log_file.is_file():
        return []
    
    posts = []
    try:
        lines = log_file.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                posts.append(json.loads(line))
                if len(posts) >= limit:
                    break
            except Exception:
                continue
    except Exception:
        pass
    return posts


def list_xuat_media(vault_root: Path, brand: str = "") -> list[dict[str, Any]]:
    """Liệt kê các tệp media có sẵn trong attachments/dataset/_xuat-tiktok/."""
    base = vault_root / "attachments" / "dataset" / "_xuat-tiktok"
    if not base.is_dir():
        return []
    
    brands = [brand] if brand in ("bsn", "saoviet") else ["bsn", "saoviet"]
    out = []
    for b in brands:
        b_dir = base / b
        if b_dir.is_dir():
            for f in sorted(b_dir.glob("*"), key=lambda x: x.stat().st_mtime if x.is_file() else 0, reverse=True):
                if f.name.startswith(".") or f.name == "README.md":
                    continue
                if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".mp4"):
                    out.append({
                        "brand": b,
                        "filename": f.name,
                        "rel_path": f"{b}/{f.name}",
                        "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "ext": f.suffix.lower().replace(".", ""),
                    })
    return out


def crop_image_to_9_16(src: Path, dest: Optional[Path] = None, target_w: int = 1080, target_h: int = 1920) -> Path:
    """Cắt và chỉnh tỷ lệ ảnh chuẩn 9:16 (cover center), lưu chất lượng 90."""
    src = Path(src)
    if dest is None:
        dest = src.with_name(f"{src.stem}_9_16.jpg")
    else:
        dest = Path(dest)
        
    if Image is None:
        import shutil
        if src != dest:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
        return dest

    try:
        with Image.open(src) as img:
            img = img.convert("RGB")
            w, h = img.size
            target_ratio = target_w / target_h
            current_ratio = w / h

            if current_ratio > target_ratio:
                new_w = int(h * target_ratio)
                offset = (w - new_w) // 2
                box = (offset, 0, offset + new_w, h)
            else:
                new_h = int(w / target_ratio)
                offset = (h - new_h) // 2
                box = (0, offset, w, offset + new_h)

            cropped = img.crop(box)
            resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
            dest.parent.mkdir(parents=True, exist_ok=True)
            resized.save(dest, format="JPEG", quality=90, optimize=True)
            return dest
    except Exception as e:
        print(f"[tiktok_service] Lỗi crop ảnh {src}: {e}", file=sys.stderr)
        return src



def pick_and_prepare_photos(
    vault_root: Path,
    brand: str,
    source: str = "dataset",
    count: int = 4,
) -> list[str]:
    """Chọn hoặc chuẩn bị 4-6 ảnh 9:16 trong _xuat-tiktok/{brand}/.
    
    Trả về danh sách relative filenames (vd: ["bsn/img1.jpg", ...]).
    """
    brand_clean = "bsn" if brand.lower() in ("bsn", "game") else "saoviet"
    dest_dir = vault_root / "attachments" / "dataset" / "_xuat-tiktok" / brand_clean
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Kiểm tra ảnh sẵn trong _xuat-tiktok/{brand}/
    existing = [
        f for f in dest_dir.glob("*")
        if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
        and not f.name.startswith(".")
    ]
    
    if len(existing) >= count and source != "dataset_refresh":
        return [f"{brand_clean}/{f.name}" for f in existing[:count]]
    
    # 2. Lấy từ dataset nguồn và crop 9:16
    dataset_candidates = []
    if brand_clean == "bsn":
        src_root = vault_root / "attachments" / "dataset" / "game-bsn"
    else:
        src_root = vault_root / "attachments" / "dataset" / "tin-hoc_ai"
        if not src_root.is_dir():
            src_root = vault_root / "attachments" / "dataset" / "tin-hoc"

    if src_root.is_dir():
        for p in src_root.rglob("*"):
            if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                if not p.name.startswith(".") and "logo" not in p.name.lower():
                    dataset_candidates.append(p)
                    
    prepared = []
    import random
    if dataset_candidates:
        chosen = random.sample(dataset_candidates, min(count, len(dataset_candidates)))
        for i, src_file in enumerate(chosen):
            dest_name = f"ready_{int(time.time())}_{i+1}.jpg"
            dest_file = dest_dir / dest_name
            if crop_image_to_9_16(src_file, dest_file):
                prepared.append(f"{brand_clean}/{dest_name}")
                
    if not prepared and existing:
        return [f"{brand_clean}/{f.name}" for f in existing[:count]]
        
    return prepared


def post_photos_to_tiktok(
    vault_root: Optional[Union[str, Path]] = None,
    brand_kit: str = "game-gia-re-bsn",
    account_id: Optional[str] = None,
    caption: Optional[str] = None,
    product_title: Optional[str] = None,
    product_price: Optional[str] = None,
    images: Optional[list[str]] = None,
    auto_add_music: bool = True,
    draft: bool = False,
    source: str = "dataset",
    count: int = 4,
    base_url: str = "https://trannhuy.online",
    kit_file: Optional[str] = None,
    **kwargs
) -> dict[str, Any]:
    """Quy trình đăng bài carousel ảnh 9:16 lên TikTok qua PostPeer API."""
    vault = _get_vault_root(vault_root)
    token = get_postpeer_token()
    if not token:
        return {
            "ok": False,
            "error": "Chưa kết nối PostPeer hoặc thiếu API key. Vào /app > Kết nối để kết nối PostPeer."
        }

    # 1. Đọc kit
    target_kit = kit_file or brand_kit
    if not target_kit.endswith(".md"):
        kit_filename = f"{target_kit}.md"
    else:
        kit_filename = target_kit

    kit_path = vault / "wiki" / "brand-kits" / kit_filename
    if not kit_path.is_file():
        # Fallback search by stem
        for f in (vault / "wiki" / "brand-kits").glob("*.md"):
            if target_kit.lower() in f.stem.lower():
                kit_path = f
                kit_filename = f.name
                break

    kit_data = parse_tiktok_kit(kit_path) if kit_path.is_file() else None
    if not kit_data:
        kit_data = {
            "name": "Game Giá Rẻ BSN" if "bsn" in target_kit.lower() else "Sao Việt",
            "brand": "bsn" if "bsn" in target_kit.lower() else "saoviet",
            "account_id": account_id or "6aa3ba9df4c58f3c57921507",
            "username": "@seotrum",
            "hashtags": "#GameGiaReBSN #SteamOffline",
            "disable_duet": True,
            "disable_stitch": True,
        }

    target_acc = (account_id or kit_data.get("account_id") or "").strip()
    if not target_acc or target_acc.upper() == "CHƯA_NỐI":
        target_acc = "6aa3ba9df4c58f3c57921507"

    # 2. Chuẩn bị ảnh
    if images and isinstance(images, list) and len(images) > 0:
        rel_photos = [img.replace("\\", "/").strip("/") for img in images]
    else:
        rel_photos = pick_and_prepare_photos(vault, kit_data["brand"], source=source, count=count)

    if not rel_photos:
        return {"ok": False, "error": f"Không tìm thấy hoặc không tạo được ảnh 9:16 cho brand {kit_data['brand']}"}

    # Dựng URL public HTTPS
    public_urls = [f"{base_url.rstrip('/')}/tiktok-media/{p}" for p in rel_photos]

    # 3. Soạn caption
    brand_name = kit_data.get("name") or "Shop"
    hashtags = kit_data.get("hashtags") or "#TikTok #GameGiaReBSN #SteamOffline"
    final_caption = (caption or "").strip()
    if not final_caption:
        prod = product_title or ("Game bản quyền Steam" if kit_data["brand"] == "bsn" else "Khóa học Tin học")
        price = f" - Giá: {product_price}" if product_price else ""
        if kit_data["brand"] == "bsn":
            final_caption = (
                f"🔥 {prod.upper()}{price} CỰC CHÁY TẠI {brand_name.upper()}! 🔥\n\n"
                f"🎮 Tải trực tiếp Steam chính hãng, chơi mượt mà không lo giật lag.\n"
                f"✨ Miễn phí cài đặt patch Việt Hóa 100%, bảo hành 3 tháng.\n"
                f"⚡ Giá chỉ từ 28k - 45k cho anh em sinh viên trải nghiệm thả ga.\n\n"
                f"👉 Nhắn tin ngay cho shop hoặc liên hệ Hotline/Zalo: 0877 104 996 để nhận tài khoản liền tay!\n\n"
                f"{hashtags}"
            )
        else:
            final_caption = (
                f"🌟 {prod.upper()}{price} CÙNG {brand_name.upper()} 🌟\n\n"
                f"📚 Khóa học Tin học văn phòng, Excel, AutoCAD chuẩn thực chiến.\n"
                f"💡 Thực hành 100% trên máy tính, giảng viên kèm 1-1 tận tình.\n\n"
                f"👉 Inbox ngay để nhận ưu đãi học phí và xếp lịch sớm nhất!\n\n"
                f"{hashtags}"
            )

    # 4. Gửi PostPeer API
    import requests
    headers = {
        "x-access-key": token,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    privacy_level = kit_data.get("privacy_level") or "PUBLIC_TO_EVERYONE"
    payload = {
        "content": final_caption.strip(),
        "platforms": [{
            "platform": "tiktok",
            "accountId": target_acc,
            "platformSpecificData": {
                "privacyLevel": privacy_level,
                "disableComment": False,
                "disableDuet": bool(kit_data.get("disable_duet", True)),
                "disableStitch": bool(kit_data.get("disable_stitch", True)),
                "draft": bool(draft),
                "autoAddMusic": bool(auto_add_music),
                "isAigc": False,
            },
        }],
        "mediaItems": [{"type": "image", "url": u} for u in public_urls],
        "publishNow": not bool(draft),
    }

    try:
        resp = requests.post(f"{BASE_POSTPEER}/posts", json=payload, headers=headers, timeout=60)
        res_json = resp.json() if resp.status_code in (200, 201, 202) else {}
        if resp.status_code not in (200, 201, 202):
            err_msg = res_json.get("message") or res_json.get("error") or resp.text[:300]
            return {"ok": False, "error": f"Lỗi PostPeer ({resp.status_code}): {err_msg}"}
    except Exception as e:
        return {"ok": False, "error": f"Lỗi kết nối tới PostPeer: {e}"}

    post_id = str(res_json.get("postId") or res_json.get("id") or "")
    tiktok_url = str(res_json.get("postUrl") or res_json.get("url") or "")
    if not tiktok_url and isinstance(res_json.get("platforms"), list) and res_json["platforms"]:
        tiktok_url = str(res_json["platforms"][0].get("platformPostUrl") or "")
    status = str(res_json.get("status") or ("draft" if draft else "published"))

    # 5. Ghi log JSONL
    log_file = vault / "Javis" / "tiktok-posts.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "ts": time.time(),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "kit": kit_filename,
        "brand": kit_data["brand"],
        "accountId": target_acc,
        "username": kit_data.get("username") or "",
        "postpeer_id": post_id,
        "urls": public_urls,
        "caption": final_caption[:150] + ("..." if len(final_caption) > 150 else ""),
        "status": status,
        "tiktok_url": tiktok_url,
        "draft": bool(draft),
        "auto_add_music": bool(auto_add_music),
        "photos_count": len(public_urls),
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return {
        "ok": True,
        "postpeer_id": post_id,
        "tiktok_url": tiktok_url,
        "status": status,
        "draft": bool(draft),
        "photos_count": len(public_urls),
        "urls": public_urls,
        "message": "Đăng carousel TikTok thành công qua PostPeer!" if not draft else "Đã lưu vào Hộp thư bản nháp TikTok!",
    }


def update_brand_kit_account(brand_kit: str, account_id: str, username: str = "", vault_root: Optional[Union[str, Path]] = None) -> bool:
    """Cập nhật accountId và username trong khối '## Kênh TikTok' của brand kit."""
    vault = _get_vault_root(vault_root)
    kit_dir = vault / "wiki" / "brand-kits"
    if not kit_dir.exists():
        return False
        
    candidates = [
        kit_dir / brand_kit,
        kit_dir / f"{brand_kit}.md",
    ]
    target_file = None
    for c in candidates:
        if c.is_file():
            target_file = c
            break
    if not target_file:
        for f in kit_dir.glob("*.md"):
            if brand_kit.lower() in f.stem.lower():
                target_file = f
                break
                
    if not target_file:
        return False
        
    content = target_file.read_text(encoding="utf-8")
    if "## Kênh TikTok" not in content:
        return False
        
    lines = content.splitlines()
    new_lines = []
    in_tt = False
    has_acc = False
    has_user = False
    
    for line in lines:
        s = line.strip()
        if s.startswith("## Kênh TikTok"):
            in_tt = True
            new_lines.append(line)
            continue
        if in_tt:
            if s.startswith("## "):
                if not has_acc:
                    new_lines.append(f"- accountId: {account_id}")
                if username and not has_user:
                    new_lines.append(f"- username: {username}")
                in_tt = False
                new_lines.append(line)
                continue
            if s.startswith("- accountId:"):
                new_lines.append(f"- accountId: {account_id}")
                has_acc = True
                continue
            if s.startswith("- username:"):
                if username:
                    new_lines.append(f"- username: {username}")
                else:
                    new_lines.append(line)
                has_user = True
                continue
        new_lines.append(line)
        
    if in_tt:
        if not has_acc:
            new_lines.append(f"- accountId: {account_id}")
        if username and not has_user:
            new_lines.append(f"- username: {username}")
            
    target_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return True
