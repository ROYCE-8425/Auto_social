"""Dịch vụ quản lý kết nối và xuất bản mạng xã hội qua PostPeer Gateway API.

Hỗ trợ đa nền tảng:
- TikTok: Video ngắn và photo carousel 9:16.
- X (Twitter): Tweet văn bản, ảnh, media.
- Instagram: Ảnh, carousel và video Reels.
- YouTube: Video ngắn YouTube Shorts 9:16.

Nguyên tắc hệ thống:
- Minh bạch 100% về năng lực API: Chỉ claim "publish: true" nếu PostPeer hỗ trợ.
- Tuyệt đối không claim inbox/comment care cho PostPeer khi chưa có Webhook/Graph API trực tiếp.
- Ghi log persistent vào Javis/social-posts.jsonl kèm external_post_id thật.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

try:
    import config as cfgmod
    STATE_DIR = cfgmod.STATE_DIR
except Exception:
    STATE_DIR = Path(__file__).resolve().parent

ROOT = Path(__file__).resolve().parents[1]
BASE_POSTPEER = "https://api.postpeer.dev/v1"
CONNECTOR_ID = "postpeer"

# ============================================================
# 1. Connection & Token Management
# ============================================================

def get_postpeer_token() -> Optional[str]:
    """Lấy token xác thực PostPeer từ mcp_store."""
    # Kiểm tra biến môi trường trước (tiện cho unit test và docker)
    env_token = os.getenv("POSTPEER_KEY") or os.getenv("POSTPEER_ACCESS_KEY")
    if env_token and env_token.strip():
        return env_token.strip()

    try:
        import mcp_store
        for c in mcp_store.list_connections():
            if c.get("connector_id") == CONNECTOR_ID:
                secrets = mcp_store.connection_secrets(c["id"]) or {}
                token = (secrets.get("postpeer_key") or "").strip()
                if token:
                    return token
    except Exception:
        pass
    return None


def get_postpeer_connection() -> dict[str, Any]:
    """Lấy thông tin trạng thái kết nối PostPeer, ẩn access key."""
    try:
        import mcp_store
        key = get_postpeer_token()
        c = next((x for x in mcp_store.list_connections() if x.get("connector_id") == CONNECTOR_ID), None)
        if not c:
            return {"connected": bool(key), "perm": "readonly", "masked_key": "", "error": "Chưa có connection"}
        
        masked = ""
        if key:
            masked = key[:4] + "..." + key[-6:] if len(key) >= 10 else "***"
        return {
            "connected": bool(key),
            "perm": c.get("perm") or "full",
            "masked_key": masked,
            "connection_id": c.get("id") or "",
            "label": c.get("label") or "PostPeer Gateway",
        }
    except Exception as e:
        return {"connected": False, "perm": "readonly", "masked_key": "", "error": str(e)}


# ============================================================
# 2. Account Fetching & Normalization
# ============================================================

SOCIAL_GROUPS_REGISTRY = {
    "default": "Default",
    "bsn": "Game BSN",
    "game-bsn": "Game BSN",
    "saoviet": "Royce Shop",
    "royce": "Royce Shop",
}

def infer_social_group(username: str, platform: str) -> str:
    """Gán nhóm thương hiệu (Social Group) cho tài khoản."""
    u = username.lower()
    if "bsn" in u or "seotrum" in u:
        return "Game BSN"
    if "royce" in u or "daide" in u or "nhuy" in u:
        return "Royce Shop"
    return "Default"


def normalize_platform(raw_platform: str) -> str:
    """Chuẩn hóa tên nền tảng (twitter -> x)."""
    p = (raw_platform or "").strip().lower()
    if p in ("twitter", "x"):
        return "x"
    if p in ("instagram", "ig"):
        return "instagram"
    if p in ("youtube", "yt"):
        return "youtube"
    if p in ("tiktok", "tt"):
        return "tiktok"
    if p in ("facebook", "fb"):
        return "facebook"
    return p or "unknown"


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
                            uname = str(it.get("username") or it.get("displayName") or it.get("name") or "")
                            display_name = str(it.get("displayName") or it.get("name") or uname)
                            raw_plat = str(it.get("platform") or "tiktok")
                            plat = normalize_platform(raw_plat)
                            status_val = str(it.get("authStatus") or it.get("status") or "active").lower()
                            avatar = it.get("imageUrl") or it.get("avatarUrl") or it.get("avatar") or ""

                            out.append({
                                "id": acc_id,
                                "name": display_name or uname or acc_id,
                                "username": uname or acc_id,
                                "display_name": display_name,
                                "platform": plat,
                                "raw_platform": raw_plat,
                                "status": "connected" if status_val in ("active", "connected") else status_val,
                                "avatar_url": avatar,
                                "connected_at": it.get("connectedAt") or it.get("createdAt") or "",
                            })
                    return out
        except Exception:
            continue
    return []


async def fetch_postpeer_accounts() -> list[dict[str, Any]]:
    """Gọi PostPeer API bất đồng bộ."""
    return await asyncio.to_thread(fetch_postpeer_accounts_sync)


def normalize_account_data(it: dict[str, Any]) -> dict[str, Any]:
    """Chuẩn hóa một đối tượng tài khoản (PostPeer hoặc mạng xã hội khác) thành Account Model chuẩn."""
    acc_id = str(it.get("accountId") or it.get("id") or "")
    uname = str(it.get("username") or it.get("name") or acc_id)
    raw_plat = str(it.get("raw_platform") or it.get("platform") or "tiktok")
    plat = normalize_platform(raw_plat)
    status_val = str(it.get("status") or "active").lower()
    status = "connected" if status_val in ("active", "connected") else status_val
    avatar = it.get("avatarUrl") or it.get("avatar") or it.get("avatar_url") or ""
    conn_at = it.get("connectedAt") or it.get("createdAt") or it.get("connected_at") or ""
    social_grp = infer_social_group(uname, plat)

    if plat == "facebook":
        oauth_app = "Meta Graph API"
        caps = {
            "publish": True,
            "inbox": True,
            "comments": True,
            "analytics": False,
            "webhook": True,
        }
        note = "Kết nối trực tiếp Meta Pages Graph API v25.0 (Hỗ trợ Fanpage Care & Đăng bài)."
    else:
        oauth_app = "PostPeer"
        caps = {
            "publish": True,
            "inbox": False,
            "comments": False,
            "analytics": False,
            "webhook": False,
        }
        note = f"Xuất bản nội dung qua PostPeer Gateway ({plat.upper()}). Không hỗ trợ hộp thư/inbox trực tiếp."

    return {
        "id": acc_id,
        "platform": plat,
        "username": uname,
        "display_name": it.get("name") or uname,
        "avatar_url": avatar,
        "oauth_app": oauth_app,
        "social_group": social_grp,
        "connected_at": conn_at,
        "status": status,
        "capabilities": caps,
        "provider_note": note,
    }


def get_normalized_social_accounts(
    group_filter: Optional[str] = None,
    platform_filter: Optional[str] = None,
    facebook_pages: Optional[list[dict[str, Any]]] = None,
) -> list[dict[str, Any]]:
    """Lấy danh sách tài khoản đã chuẩn hóa theo đúng Account Model của hệ thống."""
    raw_accounts = fetch_postpeer_accounts_sync()
    normalized: list[dict[str, Any]] = []

    # 1. Accounts từ PostPeer
    for it in raw_accounts:
        normalized.append(normalize_account_data(it))

    # 2. Pages từ Facebook Meta Graph (nếu có cung cấp)
    if facebook_pages:
        for p in facebook_pages:
            pid = str(p.get("id") or "")
            pname = p.get("name") or pid
            fb_item = {
                "id": pid,
                "platform": "facebook",
                "username": pname,
                "name": pname,
                "avatarUrl": p.get("avatar_url") or f"https://graph.facebook.com/v25.0/{pid}/picture?type=normal",
                "connectedAt": p.get("connected_at") or "",
                "status": "connected",
            }
            normalized.append(normalize_account_data(fb_item))

    # Lọc theo group_filter và platform_filter
    results: list[dict[str, Any]] = []
    for model in normalized:
        plat = model.get("platform", "")
        social_grp = model.get("social_group", "Default")
        if group_filter and group_filter.lower() != "all" and social_grp.lower() != group_filter.lower():
            continue
        if platform_filter and platform_filter.lower() != "all" and plat.lower() != normalize_platform(platform_filter):
            continue
        results.append(model)

    return results


# ============================================================
# 3. Capabilities Matrix
# ============================================================

def get_social_capabilities_matrix() -> dict[str, Any]:
    """Trả về ma trận năng lực thực tế của từng nền tảng kết nối."""
    return {
        "ok": True,
        "matrix": {
            "facebook": {
                "platform": "facebook",
                "label": "Facebook & Messenger",
                "provider": "meta_graph",
                "api_version": "v25.0",
                "capabilities": {
                    "account_connection": True,
                    "publish": True,
                    "inbox": True,
                    "comments": True,
                    "analytics": False,
                    "webhook": True,
                },
                "status": "ready",
                "note": "Kết nối trực tiếp Meta Pages Graph API v25.0. Hỗ trợ Fanpage Care và đăng bài viết/album ảnh.",
            },
            "tiktok": {
                "platform": "tiktok",
                "label": "TikTok Video & Carousel",
                "provider": "postpeer",
                "api_version": "v1",
                "capabilities": {
                    "account_connection": True,
                    "publish": True,
                    "inbox": False,
                    "comments": False,
                    "analytics": False,
                    "webhook": False,
                },
                "status": "ready",
                "note": "Xuất bản qua PostPeer Content Distribution API. Không hỗ trợ hộp thư/inbox.",
            },
            "x": {
                "platform": "x",
                "label": "X (Twitter) Tweet & Media",
                "provider": "postpeer",
                "api_version": "v1",
                "capabilities": {
                    "account_connection": True,
                    "publish": True,
                    "inbox": False,
                    "comments": False,
                    "analytics": False,
                    "webhook": False,
                },
                "status": "ready",
                "note": "Xuất bản qua PostPeer Content Distribution API. Không hỗ trợ hộp thư Direct Messages.",
            },
            "instagram": {
                "platform": "instagram",
                "label": "Instagram Photo & Reels",
                "provider": "postpeer",
                "api_version": "v1",
                "capabilities": {
                    "account_connection": True,
                    "publish": True,
                    "inbox": False,
                    "comments": False,
                    "analytics": False,
                    "webhook": False,
                },
                "status": "ready",
                "note": "Xuất bản qua PostPeer Content Distribution API. Không hỗ trợ direct messages (DM).",
            },
            "youtube": {
                "platform": "youtube",
                "label": "YouTube Shorts & Video",
                "provider": "postpeer",
                "api_version": "v1",
                "capabilities": {
                    "account_connection": True,
                    "publish": True,
                    "inbox": False,
                    "comments": False,
                    "analytics": False,
                    "webhook": False,
                },
                "status": "ready",
                "note": "Xuất bản qua PostPeer Content Distribution API. Không hỗ trợ kiểm duyệt bình luận kênh.",
            },
        },
    }


# ============================================================
# 4. Persistent Social Posts Storage (social-posts.jsonl)
# ============================================================

def _get_social_posts_file(vault_root: Optional[Union[str, Path]] = None) -> Path:
    if vault_root:
        base = Path(vault_root)
    else:
        base = ROOT / "brains" / "Brain Default"
    p = base / "Javis" / "social-posts.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def get_social_posts(
    platform: Optional[str] = None,
    brand: Optional[str] = None,
    limit: int = 50,
    vault_root: Optional[Union[str, Path]] = None,
) -> list[dict[str, Any]]:
    """Đọc nhật ký bài đăng thực tế từ social-posts.jsonl (kèm fallback tiktok-posts.jsonl)."""
    f = _get_social_posts_file(vault_root)
    posts: list[dict[str, Any]] = []

    # 1. Đọc từ social-posts.jsonl
    if f.is_file():
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    posts.append(entry)
                except Exception:
                    continue
        except Exception:
            pass

    # 2. Hợp nhất thêm từ tiktok-posts.jsonl nếu có để giữ tính liên tục
    tt_file = f.parent / "tiktok-posts.jsonl"
    if tt_file.is_file():
        try:
            seen_ids = {p.get("id") or p.get("external_post_id") or p.get("postpeer_id") for p in posts}
            lines = tt_file.read_text(encoding="utf-8").splitlines()
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    pid = item.get("postpeer_id") or item.get("id") or ""
                    if pid and pid in seen_ids:
                        continue
                    posts.append({
                        "id": pid or f"tt_{item.get('ts', int(time.time()))}",
                        "platform": "tiktok",
                        "provider": "postpeer",
                        "account_id": item.get("accountId") or "",
                        "username": item.get("username") or "",
                        "brand": item.get("brand") or "",
                        "caption": item.get("caption") or "",
                        "media_count": item.get("photos_count") or (len(item.get("urls", []))),
                        "status": item.get("status") or "published",
                        "external_post_id": pid,
                        "permalink_url": item.get("tiktok_url") or "",
                        "created_at": item.get("datetime") or "",
                        "raw_response": {},
                    })
                except Exception:
                    continue
        except Exception:
            pass

    # Lọc theo platform
    if platform and platform.lower() != "all":
        target_p = normalize_platform(platform)
        posts = [p for p in posts if normalize_platform(p.get("platform", "")) == target_p]

    # Lọc theo brand
    if brand and brand.lower() != "all":
        b_clean = brand.lower()
        posts = [p for p in posts if b_clean in (p.get("brand") or "").lower()]

    # Sắp xếp mới nhất lên đầu
    posts.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)
    return posts[:limit]


def append_social_post_log(entry: dict[str, Any], vault_root: Optional[Union[str, Path]] = None) -> None:
    """Ghi persistent log một bài đăng vào social-posts.jsonl (và tiktok-posts.jsonl nếu là tiktok)."""
    f = _get_social_posts_file(vault_root)
    line = json.dumps(entry, ensure_ascii=False) + "\n"
    with open(f, "a", encoding="utf-8") as fp:
        fp.write(line)

    # Nếu là TikTok, ghi thêm vào tiktok-posts.jsonl để tương thích hoàn toàn
    if entry.get("platform") == "tiktok":
        tt_file = f.parent / "tiktok-posts.jsonl"
        tt_item = {
            "ts": int(time.time()),
            "datetime": entry.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "kit": entry.get("brand") or "tiktok",
            "brand": entry.get("brand") or "saoviet",
            "accountId": entry.get("account_id") or "",
            "username": entry.get("username") or "",
            "postpeer_id": entry.get("external_post_id") or entry.get("id") or "",
            "urls": entry.get("media_urls") or [],
            "caption": entry.get("caption") or "",
            "status": entry.get("status") or "published",
            "tiktok_url": entry.get("permalink_url") or "",
            "photos_count": entry.get("media_count") or len(entry.get("media_urls") or []),
        }
        with open(tt_file, "a", encoding="utf-8") as fp:
            fp.write(json.dumps(tt_item, ensure_ascii=False) + "\n")


# ============================================================
# 5. Social Publishing Dispatcher
# ============================================================

SUPPORTED_PUBLISH_PLATFORMS = {"tiktok", "x", "instagram", "youtube"}

def publish_social_post(
    platform: str,
    account_id: str,
    caption: str,
    media_urls: Optional[list[str]] = None,
    brand: str = "saoviet",
    idempotency_key: Optional[str] = None,
    vault_root: Optional[Union[str, Path]] = None,
    **kwargs,
) -> dict[str, Any]:
    """Xuất bản nội dung lên mạng xã hội qua PostPeer Gateway API.
    
    Yêu cầu:
    - Nền tảng phải thuộc SUPPORTED_PUBLISH_PLATFORMS.
    - account_id phải hợp lệ.
    - Ghi persistent log vào social-posts.jsonl kèm external_post_id.
    """
    plat = normalize_platform(platform)
    if plat not in SUPPORTED_PUBLISH_PLATFORMS:
        return {
            "ok": False,
            "error": f"Nền tảng '{platform}' không hỗ trợ xuất bản tự động qua cổng PostPeer Gateway.",
            "supported_platforms": sorted(list(SUPPORTED_PUBLISH_PLATFORMS)),
        }

    account_id = (account_id or "").strip()
    if not account_id:
        return {"ok": False, "error": "Thiếu 'account_id' của tài khoản đích."}

    token = get_postpeer_token()
    if not token:
        return {"ok": False, "error": "Chưa kết nối PostPeer hoặc thiếu API key."}

    media_urls = media_urls or []
    caption = (caption or "").strip()

    # Kiểm tra cờ Mock phục vụ unit test không gọi ra ngoài
    mock_mode = os.getenv("MOCK_POSTPEER", "").strip().lower() in ("1", "true", "yes")
    
    if mock_mode:
        external_id = f"postpeer_mock_{plat}_{int(time.time())}"
        permalink = f"https://{plat}.com/post/{external_id}"
        res_json = {
            "postId": external_id,
            "status": "published",
            "url": permalink,
            "mock": True,
        }
    else:
        # Gọi PostPeer Gateway API thực tế
        import requests
        headers = {
            "x-access-key": token,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Format platform mapping for PostPeer
        postpeer_platform = "twitter" if plat == "x" else plat
        payload: dict[str, Any] = {
            "content": caption,
            "accountId": account_id,
            "urls": media_urls,
            "platforms": [{
                "platform": postpeer_platform,
                "accountId": account_id,
            }],
            "mediaItems": [{"type": "image", "url": u} for u in media_urls],
            "publishNow": True,
        }
        if idempotency_key:
            payload["idempotencyKey"] = idempotency_key

        try:
            resp = requests.post(f"{BASE_POSTPEER}/posts", json=payload, headers=headers, timeout=60)
            res_json = resp.json() if resp.status_code in (200, 201, 202) else {}
            if resp.status_code not in (200, 201, 202):
                err_msg = res_json.get("message") or res_json.get("error") or resp.text[:300]
                return {"ok": False, "error": f"PostPeer API ({resp.status_code}): {err_msg}"}
        except Exception as e:
            return {"ok": False, "error": f"Lỗi kết nối tới PostPeer: {e}"}

    external_id = str(res_json.get("postId") or res_json.get("id") or "")
    permalink = str(res_json.get("postUrl") or res_json.get("url") or "")
    status = str(res_json.get("status") or "published")

    # Tạo log entry chuẩn hóa
    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "id": external_id or f"pp_{plat}_{int(time.time())}",
        "platform": plat,
        "provider": "postpeer",
        "account_id": account_id,
        "username": kwargs.get("username") or account_id,
        "brand": brand,
        "caption": caption,
        "media_count": len(media_urls),
        "media_urls": media_urls,
        "status": status,
        "external_post_id": external_id,
        "permalink_url": permalink,
        "created_at": now_iso,
        "raw_response": res_json,
    }

    # Ghi persistent log
    append_social_post_log(log_entry, vault_root=vault_root)

    return {
        "ok": True,
        "post": log_entry,
        "external_post_id": external_id,
        "permalink": permalink,
        "status": status,
    }
