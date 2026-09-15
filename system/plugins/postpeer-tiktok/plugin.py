"""Plugin bundled: đăng video TikTok qua PostPeer API.

Tích hợp cổng đăng video TikTok tự động thông qua dịch vụ bên thứ ba PostPeer (postpeer.dev).
Dùng access key của kết nối "postpeer" (x-access-key).
Hỗ trợ:
- Lấy danh sách tài khoản đã kết nối OAuth (postpeer_accounts).
- Kiểm tra thông tin nhà sáng tạo và tuỳ chọn bảo mật TikTok (postpeer_tiktok_creator).
- Tra cứu trạng thái bài đăng (postpeer_post_get).
- Đăng video TikTok chuẩn 9:16 kèm caption (postpeer_tiktok_post, min_mode="full").
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

BASE = "https://api.postpeer.dev/v1"
CONNECTOR_ID = "postpeer"


def _secrets() -> dict[str, Any]:
    try:
        import mcp_store
    except Exception:
        return {}
    cid = _connected_id()
    if not cid:
        return {}
    return mcp_store.connection_secrets(cid) or {}


def _connected_id() -> Optional[str]:
    try:
        import mcp_store
    except Exception:
        return None
    for c in mcp_store.list_connections():
        if c.get("connector_id") == CONNECTOR_ID:
            return c.get("id")
    return None


def _token() -> Optional[str]:
    return (_secrets().get("postpeer_key") or "").strip() or None


def _check() -> Optional[str]:
    if not _token():
        return (
            "Chưa kết nối PostPeer. Vào trang Kết nối, chọn 'TikTok (PostPeer)', "
            "dán PostPeer access key rồi bấm Kết nối. Sau đó gọi lại tool này."
        )
    return None


def _headers(token: str) -> dict[str, str]:
    return {
        "x-access-key": token,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def _get_accounts(token: str) -> list[dict[str, Any]] | dict[str, Any]:
    """Lấy danh sách các tài khoản tích hợp trên PostPeer."""
    import httpx

    urls = [
        f"{BASE}/connect/integrations",
        f"{BASE}/integrations",
    ]
    last_err = ""
    async with httpx.AsyncClient(timeout=30) as c:
        for u in urls:
            try:
                r = await c.get(u, headers=_headers(token))
                if r.status_code == 200:
                    data = r.json()
                    items = data.get("integrations") or data.get("data") or data
                    if isinstance(items, list):
                        out = []
                        for it in items:
                            if isinstance(it, dict):
                                out.append({
                                    "accountId": str(it.get("accountId") or it.get("id") or ""),
                                    "platform": str(it.get("platform") or "").lower(),
                                    "username": str(it.get("username") or it.get("name") or ""),
                                    "avatarUrl": str(it.get("avatarUrl") or it.get("avatar") or ""),
                                    "status": str(it.get("status") or "active"),
                                })
                        return out
                elif r.status_code == 402:
                    return {"__error": "Hết credit trên PostPeer (402 Payment Required). Vui lòng nạp thêm credit trên postpeer.dev.", "__code": 402}
                else:
                    last_err = f"HTTP {r.status_code}: {r.text[:200]}"
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
    return {"__error": last_err or "Không lấy được danh sách tài khoản từ PostPeer"}


async def _get_creator_info(token: str, account_id: str) -> dict[str, Any]:
    """Lấy Creator Info cho tài khoản TikTok (bắt buộc trước khi post)."""
    import httpx

    urls = [
        f"{BASE}/connect/tiktok/creator-info",
        f"{BASE}/tiktok/creator-info",
    ]
    last_err = ""
    async with httpx.AsyncClient(timeout=30) as c:
        for u in urls:
            try:
                r = await c.get(u, params={"accountId": account_id}, headers=_headers(token))
                if r.status_code == 200:
                    data = r.json()
                    return data.get("creatorInfo") or data.get("data") or data
                elif r.status_code == 402:
                    return {"__error": "Hết credit trên PostPeer (402 Payment Required).", "__code": 402}
                else:
                    last_err = f"HTTP {r.status_code}: {r.text[:200]}"
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
    return {"__error": last_err or f"Không lấy được creator info cho tài khoản {account_id}"}


async def _post_media(token: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Gọi POST /v1/posts để xuất bản video lên TikTok."""
    import httpx

    url = f"{BASE}/posts"
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(url, headers=_headers(token), json=payload)
            if r.status_code in (200, 201, 202):
                return r.json()
            if r.status_code == 402:
                return {
                    "__error": "Hết credit trên PostPeer (402 Payment Required). Vui lòng nạp thêm credit trên postpeer.dev để tiếp tục đăng video.",
                    "__code": 402,
                }
            return {"__error": f"PostPeer API lỗi (HTTP {r.status_code}): {r.text[:300]}"}
    except Exception as e:
        return {"__error": f"{type(e).__name__}: {e}"}


async def _get_post_status(token: str, post_id: str) -> dict[str, Any]:
    """Lấy trạng thái bài đăng."""
    import httpx

    url = f"{BASE}/posts/{post_id}"
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(url, headers=_headers(token))
            if r.status_code == 200:
                return r.json()
            if r.status_code == 402:
                return {"__error": "Hết credit trên PostPeer (402 Payment Required).", "__code": 402}
            return {"__error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"__error": f"{type(e).__name__}: {e}"}


# ============================================================
# Tool Handlers
# ============================================================

async def _handle_accounts(args: dict[str, Any], ctx: Any) -> str:
    token = _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    res = await _get_accounts(token)
    if isinstance(res, dict) and res.get("__error"):
        return "ERROR: " + res["__error"]
    return json.dumps({"accounts": res}, ensure_ascii=False)


async def _handle_creator(args: dict[str, Any], ctx: Any) -> str:
    token = _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    account_id = str(args.get("account_id") or "").strip()
    if not account_id:
        return "ERROR: thiếu 'account_id' (ID tài khoản TikTok trên PostPeer)."
    res = await _get_creator_info(token, account_id)
    if isinstance(res, dict) and res.get("__error"):
        return "ERROR: " + res["__error"]
    return json.dumps({"creator_info": res}, ensure_ascii=False)


async def _handle_post_get(args: dict[str, Any], ctx: Any) -> str:
    token = _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    post_id = str(args.get("id") or "").strip()
    if not post_id:
        return "ERROR: thiếu 'id' của bài đăng trên PostPeer."
    res = await _get_post_status(token, post_id)
    if isinstance(res, dict) and res.get("__error"):
        return "ERROR: " + res["__error"]
    return json.dumps(res, ensure_ascii=False)


async def _handle_tiktok_post(args: dict[str, Any], ctx: Any) -> str:
    token = _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")

    args = args or {}
    account_id = str(args.get("account_id") or "").strip()
    video_url = str(args.get("video") or "").strip()
    caption = str(args.get("caption") or "").strip()

    if not account_id:
        return "ERROR: thiếu 'account_id' (ID tài khoản TikTok)."
    if not video_url:
        return "ERROR: thiếu 'video' (URL video https công khai)."
    if not caption:
        return "ERROR: thiếu 'caption' (nội dung bài đăng TikTok)."

    # Validate video URL format (must be public HTTPS)
    if not video_url.startswith("https://") and not video_url.startswith("http://"):
        return (
            "ERROR: Cần URL https công khai cho video (ví dụ CDN: "
            "https://laptrinhpython.tinhocsaoviet.com/storage/videos/ready/...). "
            "File local chưa được public lên internet."
        )

    # Resolve privacyLevel from creator_info
    creator_res = await _get_creator_info(token, account_id)
    privacy_opts: list[str] = []
    if isinstance(creator_res, dict) and not creator_res.get("__error"):
        opts = creator_res.get("privacyLevelOptions") or creator_res.get("privacy_level_options")
        if isinstance(opts, list):
            privacy_opts = [str(x) for x in opts]

    user_privacy = str(args.get("privacy_level") or "").strip()
    is_draft = bool(args.get("draft", False))

    if user_privacy and user_privacy in privacy_opts:
        privacy_level = user_privacy
    elif "PUBLIC_TO_EVERYONE" in privacy_opts:
        privacy_level = "PUBLIC_TO_EVERYONE"
    elif privacy_opts:
        privacy_level = privacy_opts[0]
        is_draft = True
    else:
        privacy_level = user_privacy or "PUBLIC_TO_EVERYONE"

    disable_comment = bool(args.get("disable_comment", False))
    disable_duet = bool(args.get("disable_duet", False))
    disable_stitch = bool(args.get("disable_stitch", False))

    payload = {
        "content": caption,
        "platforms": [
            {
                "platform": "tiktok",
                "accountId": account_id,
                "platformSpecificData": {
                    "privacyLevel": privacy_level,
                    "disableComment": disable_comment,
                    "disableDuet": disable_duet,
                    "disableStitch": disable_stitch,
                    "draft": is_draft,
                },
            }
        ],
        "mediaItems": [
            {
                "type": "video",
                "url": video_url,
            }
        ],
        "publishNow": True,
    }

    res = await _post_media(token, payload)
    if isinstance(res, dict) and res.get("__error"):
        return "ERROR: " + res["__error"]

    post_id = str(res.get("postId") or res.get("id") or "")
    post_url = str(res.get("postUrl") or res.get("url") or "")
    if not post_url and isinstance(res.get("platforms"), list) and res["platforms"]:
        post_url = str(res["platforms"][0].get("platformPostUrl") or "")
    status = str(res.get("status") or "published")

    return json.dumps({
        "ok": True,
        "postpeer_id": post_id,
        "tiktok_url": post_url,
        "status": status,
        "draft": is_draft,
        "credit_note": "Trừ 1 credit PostPeer",
    }, ensure_ascii=False)


async def _handle_tiktok_photos(args: dict[str, Any], ctx: Any) -> str:
    """Đăng carousel ảnh 9:16 + nhạc auto (autoAddMusic) — na ná album Fanpage."""
    token = _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    account_id = str(args.get("account_id") or "").strip()
    caption = str(args.get("caption") or "").strip()
    raw = args.get("images") or args.get("photos") or []
    if isinstance(raw, str):
        images = [x.strip() for x in re.split(r"[\s,]+", raw) if x.strip()]
    elif isinstance(raw, list):
        images = [str(x).strip() for x in raw if str(x).strip()]
    else:
        images = []
    if not account_id:
        return "ERROR: thiếu 'account_id'."
    if len(images) < 1:
        return "ERROR: thiếu 'images' (1–10 URL https ảnh 9:16)."
    if len(images) > 10:
        images = images[:10]
    bad = [u for u in images if not u.startswith("http://") and not u.startswith("https://")]
    if bad:
        return "ERROR: mỗi ảnh phải là URL https công khai. File trong vault chưa public thì chưa đăng được."
    if not caption:
        return "ERROR: thiếu caption."

    creator_res = await _get_creator_info(token, account_id)
    privacy_opts: list[str] = []
    if isinstance(creator_res, dict) and not creator_res.get("__error"):
        opts = creator_res.get("privacyLevelOptions") or creator_res.get("privacy_level_options")
        if isinstance(opts, list):
            privacy_opts = [str(x) for x in opts]
    user_privacy = str(args.get("privacy_level") or "").strip()
    is_draft = bool(args.get("draft", False))
    if user_privacy and user_privacy in privacy_opts:
        privacy_level = user_privacy
    elif "PUBLIC_TO_EVERYONE" in privacy_opts:
        privacy_level = "PUBLIC_TO_EVERYONE"
    elif privacy_opts:
        privacy_level = privacy_opts[0]
        is_draft = True
    else:
        privacy_level = user_privacy or "PUBLIC_TO_EVERYONE"

    auto_music = args.get("auto_add_music")
    if auto_music is None:
        auto_music = True

    payload = {
        "content": caption,
        "platforms": [{
            "platform": "tiktok",
            "accountId": account_id,
            "platformSpecificData": {
                "privacyLevel": privacy_level,
                "disableComment": bool(args.get("disable_comment", False)),
                "disableDuet": bool(args.get("disable_duet", True)),
                "disableStitch": bool(args.get("disable_stitch", True)),
                "draft": is_draft,
                "autoAddMusic": bool(auto_music),
                "isAigc": True,
            },
        }],
        "mediaItems": [{"type": "image", "url": u} for u in images],
        "publishNow": True,
    }
    res = await _post_media(token, payload)
    if isinstance(res, dict) and res.get("__error"):
        return "ERROR: " + str(res["__error"])
    post_id = str(res.get("postId") or res.get("id") or "")
    post_url = str(res.get("postUrl") or res.get("url") or "")
    if not post_url and isinstance(res.get("platforms"), list) and res["platforms"]:
        post_url = str(res["platforms"][0].get("platformPostUrl") or "")
    return json.dumps({
        "ok": True,
        "postpeer_id": post_id,
        "tiktok_url": post_url,
        "status": str(res.get("status") or "published"),
        "draft": is_draft,
        "auto_add_music": bool(auto_music),
        "images": len(images),
        "credit_note": "Trừ credit PostPeer (ảnh/carousel)",
    }, ensure_ascii=False)


def register(ctx: Any) -> None:
    ctx.register_tool(
        name="postpeer_accounts",
        min_mode="readonly",
        check_fn=_check,
        handler=_handle_accounts,
        description=(
            "Liệt kê các tài khoản mạng xã hội (đặc biệt là TikTok) đã liên kết qua PostPeer. "
            "Trả về accountId, platform, username để chọn tài khoản đăng video. Không lộ API key."
        ),
        schema={"type": "object", "properties": {}},
    )

    ctx.register_tool(
        name="postpeer_tiktok_creator",
        min_mode="readonly",
        check_fn=_check,
        handler=_handle_creator,
        description=(
            "Lấy thông tin Creator Info của tài khoản TikTok qua PostPeer trước khi đăng. "
            "Trả về privacyLevelOptions, quyền comment/duet/stitch. account_id = ID tài khoản TikTok."
        ),
        schema={
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "ID tài khoản TikTok trên PostPeer"},
            },
            "required": ["account_id"],
        },
    )

    ctx.register_tool(
        name="postpeer_post_get",
        min_mode="readonly",
        check_fn=_check,
        handler=_handle_post_get,
        description="Tra cứu trạng thái xử lý bài đăng trên PostPeer qua post ID.",
        schema={
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "ID bài đăng PostPeer"},
            },
            "required": ["id"],
        },
    )

    ctx.register_tool(
        name="postpeer_tiktok_post",
        min_mode="full",
        check_fn=_check,
        handler=_handle_tiktok_post,
        description=(
            "Đăng video dọc (9:16) lên TikTok qua PostPeer. Yêu cầu quyền Toàn quyền (full mode). "
            "account_id = ID tài khoản TikTok; video = URL https công khai của file video mp4; "
            "caption = nội dung bài đăng kèm hashtag. Tốn 1 credit PostPeer."
        ),
        schema={
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "ID tài khoản TikTok trên PostPeer"},
                "video": {"type": "string", "description": "URL HTTPS công khai của video mp4 (9:16)"},
                "caption": {"type": "string", "description": "Nội dung caption TikTok kèm hashtag"},
                "privacy_level": {"type": "string", "description": "Mức hiển thị: PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, SELF_ONLY"},
                "draft": {"type": "boolean", "description": "Đăng vào mục Bản nháp (inbox TikTok) thay vì công khai ngay"},
                "disable_comment": {"type": "boolean", "description": "Tắt bình luận trên video"},
                "disable_duet": {"type": "boolean", "description": "Tắt tính năng Duet"},
                "disable_stitch": {"type": "boolean", "description": "Tắt tính năng Stitch"},
            },
            "required": ["account_id", "video", "caption"],
        },
    )
    ctx.register_tool(
        name="postpeer_tiktok_photos",
        min_mode="full",
        check_fn=_check,
        handler=_handle_tiktok_photos,
        description=(
            "Đăng carousel ảnh dọc 9:16 lên TikTok (na ná album Fanpage). "
            "images = URL https công khai. auto_add_music=true để TikTok gắn nhạc gợi ý (không chọn được 1 bài trend cụ thể qua API). "
            "Ảnh AI: javis_generate_image aspect_ratio=portrait rồi đưa URL public. Tốn credit PostPeer."
        ),
        schema={
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "images": {"description": "Danh sách URL https ảnh 9:16 (1–10)"},
                "caption": {"type": "string"},
                "auto_add_music": {"type": "boolean", "description": "Mặc định true — TikTok tự gắn nhạc"},
                "privacy_level": {"type": "string"},
                "draft": {"type": "boolean"},
                "disable_comment": {"type": "boolean"},
                "disable_duet": {"type": "boolean"},
                "disable_stitch": {"type": "boolean"},
            },
            "required": ["account_id", "images", "caption"],
        },
    )
