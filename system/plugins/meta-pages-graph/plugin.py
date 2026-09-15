"""Plugin bundled: quản lý Trang/Fanpage Facebook qua Graph API.

Gọi THẲNG graph.facebook.com bằng user access token của kết nối "facebook-pages" (BYO app -
user tự tạo Facebook App, OAuth do oauth_mcp lo, token tự gia hạn ~60 ngày). Đọc danh sách Trang
qua /me/accounts, mỗi Trang có access_token RIÊNG - mọi thao tác trên một Trang (đăng bài, đọc/
trả lời bình luận) đều dùng token của chính Trang đó, KHÔNG dùng token cá nhân.

Tool đọc (fb_pages_list/fb_page_posts/fb_page_comments) = readonly. Tool ghi công khai
(fb_page_post/fb_page_photo/fb_page_album/fb_page_video/fb_page_edit/fb_page_reply) =
min_mode full → không bao giờ tự chạy ở chế độ suggest/auto, phải mức Toàn quyền + kết nối
đã ở mức đó.
Ảnh/video nhận URL http(s) hoặc file TRONG vault (sandbox như tool file); video upload đi
host graph-video riêng của Meta, Meta xử lý nền vài phút mới hiện bài.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

GRAPH = "https://graph.facebook.com/v25.0"
# Upload video phải đi host riêng của Meta (graph thường từ chối file video)
GRAPH_VIDEO = "https://graph-video.facebook.com/v25.0"
CONNECTOR_ID = "facebook-pages"


def _digits(s):
    return re.sub(r"\D", "", s or "")


def _kit_field(md, *labels):
    for lab in labels:
        m = re.search(r"^[ \t]*[-*][ \t]*" + re.escape(lab) + r":[ \t]*(.*)$", md, re.M)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def _load_page_kit(vault_root, page_id):
    """Kit wiki/brand-kits/*.md có Page ID khớp. None nếu chưa có kit."""
    pid = str(page_id or "").strip()
    if not pid or not vault_root:
        return None
    d = Path(vault_root) / "wiki" / "brand-kits"
    if not d.is_dir():
        return None
    for p in d.glob("*.md"):
        if p.name.startswith("_"):
            continue
        try:
            md = p.read_text(encoding="utf-8")
        except OSError:
            continue
        got = _kit_field(md, "Page ID", "page_id", "ID Fanpage", "ID Trang")
        if got == pid:
            test_raw = (_kit_field(md, "Page test") or "").lower()
            stem = p.name[:-3] if p.name.endswith(".md") else p.name
            name = _kit_field(md, "Tên Fanpage") or stem
            is_test = (
                test_raw in ("true", "yes", "1", "có")
                or stem == "royce-shop"
                or "royce" in name.lower()
            )
            return {
                "file": p.name,
                "name": name,
                "address": _kit_field(md, "Cơ sở / địa chỉ"),
                "hotline": _kit_field(md, "Hotline / Zalo", "Hotline riêng", "Hotline"),
                "email": _kit_field(md, "Email Fanpage", "Email"),
                "web": _kit_field(md, "Web Fanpage", "Web"),
                "access_token": _kit_field(md, "Access Token", "access_token", "Page Token", "Token"),
                "test": is_test,
                "md": md,
            }
    return None


def _fold(s):
    """Bỏ dấu, khoảng trắng, dấu câu — so khớp địa chỉ sai một chút vẫn nhận."""
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", s)


def _addr_needles(addr):
    """Mẩu địa chỉ (mỗi chi nhánh 1 mẩu). Caption chỉ cần khớp 1 mẩu, không bắt hết list."""
    out = []
    raw = (addr or "").replace("|", "\n")
    for part in raw.splitlines():
        part = part.strip()
        if not part:
            continue
        if ":" in part[:48]:
            part = part.split(":", 1)[1].strip()
        for bit in [b.strip() for b in part.split(",")[:2] if b.strip()]:
            bit = re.sub(r"\s+", " ", bit)
            if len(_fold(bit)) >= 6:
                out.append(bit)
    return out


def _addr_hit(addr, body):
    needles = _addr_needles(addr)
    if not needles:
        return True
    fb = _fold(body)
    for n in needles:
        fn = _fold(n)
        if fn and fn in fb:
            return True
        if len(fn) >= 10 and fn[:10] in fb:
            return True
        for w in re.split(r"\s+", n):
            fw = _fold(w)
            if len(fw) >= 5 and fw in fb:
                return True
    for num in re.findall(r"\d{2,}", addr or ""):
        if len(num) >= 3 and num in (body or ""):
            return True
    return False


def _fb_plain_caption(msg):
    """Facebook khong render Markdown: bo ** va __ de khong hien ky tu sao tren tuong."""
    s = msg or ""
    s = s.replace("\\*", "*")
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"__(.+?)__", r"\1", s)
    s = s.replace("**", "").replace("__", "")
    return s


def _caption_chat_err(body):
    """Chặn văn mẫu AI / nhồi hết ngành / path file trên caption. Cả page test."""
    low = (body or "").lower()
    if re.search(r"4\.0|thời đại số|thoi dai so|bạn có biết|ban co biet|chinh phục mọi thử thách|chinh phuc moi thu thach|đồng hành cùng bạn|dong hanh cung ban", low):
        return (
            "ERROR: POST_SKIP ly-do=van-mau-ai khong-retry=1. "
            "Cấm văn mẫu AI ('4.0', 'thời đại số', 'bạn có biết', 'chinh phục mọi thử thách', 'đồng hành cùng bạn'). "
            "Viết bài chuẩn 7 phần chuyển đổi cao (viet-bai-facebook): Hook câu hỏi / tiêu đề IN HOA, nỗi đau thực tế, "
            "kèm 1-1, không giới hạn số buổi, module cụ thể, ưu đãi, chân trang."
        )
    if "attachments/" in low or "thsv-logo" in low and ".png" in low:
        return (
            "ERROR: POST_SKIP ly-do=path-tren-bai khong-retry=1. "
            "Cấm dán đường dẫn file (attachments/...) vào caption hay coi đó là logo."
        )
    nganh = 0
    if re.search(r"autocad|solidworks|vẽ kỹ thuật|ve ky thuat", low):
        nganh += 1
    if re.search(r"photoshop|illustrator|đồ họa|do hoa", low):
        nganh += 1
    if re.search(r"kế toán|ke toan|misa", low):
        nganh += 1
    if re.search(r"excel|tin học văn phòng|tin hoc van phong", low):
        nganh += 1
    if nganh >= 3:
        return (
            "ERROR: POST_SKIP ly-do=nhieu-nganh khong-retry=1. "
            "1 bài = 1 thẻ kit (tin học thì không nhồi AutoCAD + đồ họa + kế toán)."
        )
    return None


def _phone_hit(phone, body):
    want = _digits(phone)
    if len(want) < 9:
        return True
    have = _digits(body)
    return want[-9:] in have


def _caption_kit_err(msg, page_id, cctx):
    """Chặn khi SAI PAGE (thiếu hẳn hotline/địa chỉ). Sai dấu/viết tắt một chút thì cho qua.
    Page test: có kit là đăng. Email không bắt. Không bắt đủ 12 cơ sở."""
    vault = getattr(cctx, "vault_root", None) if cctx is not None else None
    if not vault:
        try:
            repo_root = Path(__file__).resolve().parents[3]
            default_brain = repo_root / "brains" / "Brain Default"
            if default_brain.is_dir() and _load_page_kit(str(default_brain.resolve()), page_id):
                vault = str(default_brain.resolve())
        except Exception:
            pass
    if not vault:
        return None
    kit = _load_page_kit(vault, page_id)
    if not kit:
        return ("ERROR: POST_SKIP ly-do=chua-co-brand-kit khong-retry=1. "
                f"Page ID {page_id} chưa có file wiki/brand-kits. Không đăng. "
                "CẤM gọi lại tool đăng. CẤM [[NEEDS_INPUT]].")
    body = msg or ""
    lines = [ln for ln in body.splitlines() if ln.strip()]
    if kit and len(lines) < 20:
        return (
            "ERROR: POST_SKIP ly-do=caption-ngan khong-retry=1. "
            f"Caption quá ngắn (chỉ {len(lines)} dòng). Bài Fanpage chuẩn cần từ 32–45 dòng (bài thường) "
            "hoặc 45–70 dòng (bài tuyển sinh đầy đủ), có đủ mở đầu, lợi ích, quyền lợi và chân trang."
        )
    for ln in body.splitlines():
        if ln.count("|") >= 2:
            return (
                "ERROR: POST_SKIP ly-do=dia-chi-mot-dong khong-retry=1. "
                "Mỗi cơ sở một dòng. CẤM dán chuỗi địa chỉ cách bằng |. "
                "Chạy kit_chan_trang.py rồi dán nguyên khối CHAN_TRANG."
            )
    qerr = _caption_chat_err(body)
    if qerr:
        return qerr
    if kit.get("test"):
        return None
    miss = []
    phone = kit.get("hotline") or ""
    if not _phone_hit(phone, body):
        miss.append("hotline " + phone)
    if not _addr_hit(kit.get("address") or "", body):
        needles = _addr_needles(kit.get("address") or "")
        miss.append("địa chỉ (cần 1 mẩu gần đúng, vd «" + (needles[0] if needles else "?") + "»)")
    if not miss:
        return None
    return (
        "ERROR: POST_SKIP ly-do=chan-trang-sai-kit khong-retry=1. "
        f"Caption không khớp kit {kit['file']} ({kit['name']}). Thiếu: "
        + "; ".join(miss)
        + ". Sửa tối đa 1 lần rồi dừng. CẤM gọi đăng lại 20 lần. CẤM [[NEEDS_INPUT]]. "
        "CẤM rollback/xóa bài."
    )


def _connected_ids():
    """Mọi kết nối facebook-pages đã có token (nhiều tài khoản Facebook)."""
    try:
        import mcp_store
        import oauth_mcp
    except Exception:
        return []
    out = []
    for c in mcp_store.list_connections():
        if c.get("connector_id") == CONNECTOR_ID and oauth_mcp.status(c["id"]).get("connected"):
            out.append(c["id"])
    return out


def _connected_id():
    ids = _connected_ids()
    return ids[0] if ids else None


def _manual_pages(cctx=None):
    """Nạp Page Access Token trực tiếp từ Javis/page_tokens.json hoặc wiki/brand-kits/*.md."""
    pages = {}
    roots = []
    # 1. Từ context nếu có
    vault = getattr(cctx, "vault_root", None) if cctx is not None else None
    if vault:
        try:
            roots.append(Path(vault).resolve())
        except Exception:
            pass
    # 2. Cwd và thư mục xung quanh
    try:
        cur = Path.cwd().resolve()
        roots.extend([cur, cur.parent, cur / "brains" / "Brain Default", cur.parent / "brains" / "Brain Default"])
    except Exception:
        pass
    # 3. Từ vị trí file plugin này
    try:
        repo = Path(__file__).resolve().parents[3]
        default_brain = repo / "brains" / "Brain Default"
        if default_brain.is_dir():
            roots.append(default_brain)
        roots.append(repo)
    except Exception:
        pass
    # 4. Từ biến môi trường
    import os
    for env_k in ("JAVIS_VAULT", "BRAINS_DIR", "JAVIS_STATE_DIR"):
        v = os.getenv(env_k)
        if v:
            try:
                roots.append(Path(v).resolve())
                roots.append((Path(v) / "Brain Default").resolve())
                roots.append((Path(v) / "brains" / "Brain Default").resolve())
            except Exception:
                pass
    # 5. Đường dẫn chuẩn trên máy chủ Linux
    for p_fix in ("/opt/projects/javissocial.aisaoviet.com/brains/Brain Default",
                  "/opt/projects/javissocial.aisaoviet.com",
                  "/brains/Brain Default", "/brains"):
        try:
            dp = Path(p_fix).resolve()
            if dp.is_dir() and dp not in roots:
                roots.append(dp)
        except Exception:
            pass

    for r in roots:
        # Quét file Javis/page_tokens.json
        tok_file = r / "Javis" / "page_tokens.json"
        if tok_file.is_file():
            try:
                data = json.loads(tok_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    for pid, info in data.items():
                        if isinstance(info, dict) and info.get("access_token"):
                            pages[str(pid)] = {
                                "id": str(pid),
                                "name": info.get("name") or f"Page {pid}",
                                "access_token": str(info["access_token"]).strip(),
                                "category": "Community",
                                "tasks": ["MANAGE", "CREATE_CONTENT", "MODERATE"]
                            }
            except Exception:
                pass
        # Quét wiki/brand-kits/*.md
        bk_dir = r / "wiki" / "brand-kits"
        if bk_dir.is_dir():
            for p in bk_dir.glob("*.md"):
                if p.name.startswith("_"):
                    continue
                try:
                    md = p.read_text(encoding="utf-8")
                    pid = _kit_field(md, "Page ID", "page_id", "ID Fanpage", "ID Trang")
                    tok = _kit_field(md, "Access Token", "access_token", "Page Token", "Token")
                    if pid and tok and str(pid) not in pages:
                        name = _kit_field(md, "Tên Fanpage") or p.stem
                        pages[str(pid)] = {
                            "id": str(pid),
                            "name": name,
                            "access_token": str(tok).strip(),
                            "category": "Community",
                            "tasks": ["MANAGE", "CREATE_CONTENT", "MODERATE"]
                        }
                except Exception:
                    pass
    return pages


def _check():
    if not _manual_pages() and not _connected_ids():
        return ("Chưa kết nối Facebook Trang. Vào trang Kết nối, chọn 'Facebook Trang (tự tạo app - "
                "Graph API)', làm theo hướng dẫn tạo Facebook App rồi đăng nhập (nhớ tick chọn Trang), "
                "hoặc nạp Page Access Token vào brand kit / page_tokens.json. "
                "Sau đó gọi lại tool này.")
    return None


async def _token(cctx=None):
    if _manual_pages(cctx):
        return "manual"
    cid = _connected_id()
    if cid:
        try:
            import oauth_mcp
            hdr = await oauth_mcp.auth_headers(cid)
            tok = (hdr.get("Authorization", "") or "").replace("Bearer ", "").strip() or None
            if tok:
                return tok
        except Exception:
            pass
    return None


async def _tokens():
    import oauth_mcp
    seen, out = set(), []
    for cid in _connected_ids():
        try:
            hdr = await oauth_mcp.auth_headers(cid)
            tok = (hdr.get("Authorization", "") or "").replace("Bearer ", "").strip()
            if tok and tok not in seen:
                seen.add(tok)
                out.append(tok)
        except Exception:
            pass
    return out


async def _get(path, params, token):
    import httpx
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{GRAPH}/{str(path).lstrip('/')}",
                            params={**(params or {}), "access_token": token})
        try:
            return r.json()
        except Exception:
            return {"error": {"message": f"HTTP {r.status_code}: {r.text[:200]}"}}
    except Exception as e:
        return {"error": {"message": f"{type(e).__name__}: {e}"}}


async def _post(path, data, token):
    import httpx
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(f"{GRAPH}/{str(path).lstrip('/')}",
                             data={**(data or {}), "access_token": token})
        try:
            return r.json()
        except Exception:
            return {"error": {"message": f"HTTP {r.status_code}: {r.text[:200]}"}}
    except Exception as e:
        return {"error": {"message": f"{type(e).__name__}: {e}"}}


async def _delete(path, token):
    import httpx
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.delete(f"{GRAPH}/{str(path).lstrip('/')}", params={"access_token": token})
        try:
            return r.json()
        except Exception:
            return {"error": {"message": f"HTTP {r.status_code}: {r.text[:200]}"}}
    except Exception as e:
        return {"error": {"message": f"{type(e).__name__}: {e}"}}


def _fmt(d):
    if isinstance(d, dict) and d.get("error"):
        e = d["error"]
        return "ERROR: Facebook API: " + (e.get("message") if isinstance(e, dict) else str(e))
    return json.dumps(d, ensure_ascii=False, default=str)


async def _pages(user_token=None, cctx=None):
    """Gộp Trang từ MỌI kết nối facebook-pages và Page Token nạp thủ công. Trả (list, err). Không lộ trùng page."""
    by_id, last_err = {}, None

    # 1. Quét từ OAuth nếu có token hợp lệ
    toks = await _tokens()
    if user_token and user_token not in toks and user_token != "manual":
        toks = [user_token] + toks
    for tok in toks:
        d = await _get("me/accounts", {"fields": "id,name,category,access_token,tasks", "limit": 200}, tok)
        if isinstance(d, dict) and d.get("error"):
            last_err = _fmt(d)
            continue
        for p in (d or {}).get("data") or []:
            pid = str(p.get("id") or "")
            if pid:
                by_id[pid] = p

    # 2. Luôn ưu tiên ghi đè bằng Page Access Token nạp trực tiếp từ page_tokens.json / brand-kits
    for pid, p in _manual_pages(cctx).items():
        by_id[pid] = p

    if not by_id:
        return None, last_err or "ERROR: Không thấy Trang nào."
    return list(by_id.values()), None


async def _resolve_page_info(args, user_token, cctx=None):
    """Chọn Trang thao tác. Trả (page_dict, err).
    ƯU TIÊN TUYỆT ĐỐI: Dùng ngay Page Access Token trong page_tokens.json / brand-kits nếu có,
    không gọi OAuth me/accounts và không fallback về app cũ.
    Tự suy page_id từ prefix dạng {page_id}_... trong post_id, comment_id hoặc object_id."""
    manual = _manual_pages(cctx)
    args = args or {}
    ref = str(args.get("page_id") or args.get("page") or "").strip()
    if not ref:
        obj_ref = str(args.get("post_id") or args.get("comment_id") or args.get("object_id") or "").strip()
        if "_" in obj_ref:
            cand = obj_ref.split("_", 1)[0].strip()
            if cand:
                ref = cand

    if ref and manual:
        # Khớp theo ID
        if ref in manual:
            return manual[ref], None
        # Khớp theo tên
        rl = ref.lower()
        for pid, p in manual.items():
            if str(pid) == ref or rl in str(p.get("name", "")).lower():
                return p, None

    if not ref and len(manual) == 1:
        return next(iter(manual.values())), None

    pages, err = await _pages(user_token, cctx)
    if err and not manual:
        return None, err
    all_pages_dict = {}
    for pid, p in (manual or {}).items():
        all_pages_dict[pid] = p
    for p in (pages or []):
        pid = str(p.get("id") or "")
        if pid and pid not in all_pages_dict:
            all_pages_dict[pid] = p
    all_pages = list(all_pages_dict.values())
    if not all_pages:
        return None, ("ERROR: Không thấy Trang nào bạn quản lý. Kiểm tra: bạn là Admin của Trang, "
                      "và khi đăng nhập Facebook đã TICK chọn Trang đó cho app.")
    if ref:
        rl = ref.lower()
        for p in all_pages:
            if str(p.get("id")) == ref or rl in str(p.get("name", "")).lower():
                return p, None
        avail = ", ".join(f"{p.get('name')} ({p.get('id')})" for p in all_pages)
        return None, f"ERROR: Không khớp Trang '{ref}'. Trang bạn có: {avail}"
    if len(all_pages) == 1:
        return all_pages[0], None
    avail = ", ".join(f"{p.get('name')} ({p.get('id')})" for p in all_pages)
    return None, f"ERROR: Bạn có nhiều Trang, cần chỉ rõ page_id hoặc page (tên). Trang: {avail}"


async def _resolve_page(args, user_token, cctx=None):
    """Chọn Trang thao tác. Trả (page_id, page_token, page_name, err)."""
    p, err = await _resolve_page_info(args, user_token, cctx)
    if err:
        return None, None, None, err
    return p.get("id"), p.get("access_token"), p.get("name"), None


async def _list(args, ctx):
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    pages, err = await _pages(token)
    if err:
        return err
    # KHÔNG lộ access_token của Trang ra output.
    safe = [{"id": p.get("id"), "name": p.get("name"), "category": p.get("category"),
             "tasks": p.get("tasks")} for p in pages]
    return json.dumps(safe, ensure_ascii=False, default=str)


async def _posts(args, ctx):
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    pid, ptok, pname, err = await _resolve_page(args, token)
    if err:
        return err
    args = args or {}
    try:
        limit = max(1, min(100, int(args.get("limit") or 10)))
    except (TypeError, ValueError):
        limit = 10
    d = await _get(f"{pid}/feed",
                   {"fields": "id,message,story,created_time,permalink_url,comments.summary(true).limit(0)",
                    "limit": limit}, ptok)
    return _fmt(d)


async def _comments(args, ctx):
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    obj = str(args.get("post_id") or args.get("object_id") or "").strip()
    if not obj:
        return "ERROR: thiếu 'post_id' (id bài cần đọc bình luận; lấy từ fb_page_posts)."
    # post_id dạng {pageid}_{postid}: tự suy Trang khi user không chỉ rõ.
    if not (args.get("page_id") or args.get("page")) and "_" in obj:
        args = {**args, "page_id": obj.split("_", 1)[0]}
    pid, ptok, pname, err = await _resolve_page(args, token)
    if err:
        return err
    try:
        limit = max(1, min(100, int(args.get("limit") or 25)))
    except (TypeError, ValueError):
        limit = 25
    params = {
        "fields": "id,from{id,name},message,created_time,like_count,comment_count,parent,is_hidden,can_comment,can_hide,can_like,can_remove,message_tags,attachment{type,url}",
        "order": "reverse_chronological",
        "limit": limit
    }
    if args.get("filter"):
        params["filter"] = str(args["filter"])
    if args.get("since"):
        params["since"] = str(args["since"])
    if args.get("after"):
        params["after"] = str(args["after"])
    d = await _get(f"{obj}/comments", params, ptok)
    # Fallback nếu Graph v25.0 trả lỗi filter
    if isinstance(d, dict) and d.get("error") and args.get("filter"):
        err_msg = str(d["error"].get("message", ""))
        if "filter" in err_msg.lower():
            params.pop("filter", None)
            d = await _get(f"{obj}/comments", params, ptok)
    return _fmt(d)


async def _publish(args, ctx):
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    msg = _fb_plain_caption(str(args.get("message") or "").strip())
    link = str(args.get("link") or "").strip()
    if not msg and not link:
        return "ERROR: cần 'message' (nội dung bài) hoặc 'link'."
    pid, ptok, pname, err = await _resolve_page(args, token)
    if err:
        return err
    kit_err = _caption_kit_err(msg, pid, ctx)
    if kit_err:
        return kit_err
    vault = getattr(ctx, "vault_root", None) if ctx is not None else None
    if vault and _load_page_kit(vault, pid) and not link:
        return ("ERROR: POST_SKIP ly-do=thieu-anh khong-retry=1. "
                "Bài Fanpage khóa học phải đăng ảnh: dùng fb_page_album (nhiều ảnh) "
                "hoặc fb_page_photo (1 ảnh). CẤM fb_page_post chỉ chữ.")
    data = {}
    if msg:
        data["message"] = msg
    if link:
        data["link"] = link
    d = await _post(f"{pid}/feed", data, ptok)
    if isinstance(d, dict) and d.get("error"):
        return _fmt(d)
    return json.dumps({"ok": True, "page": pname,
                       "post_id": d.get("id") if isinstance(d, dict) else None},
                      ensure_ascii=False, default=str)


def _media_roots(cctx):
    """Các gốc được phép đọc media: (1) vault đang làm việc, (2) vùng nhận file
    STATE_DIR/.staging - nơi ảnh/video user dán vào khung chat dashboard rơi xuống.
    File trong staging là file CHÍNH CHỦ vừa gửi nên đăng được, không phải mở sandbox bừa.
    (File gửi qua Telegram đã rơi sẵn vào <vault>/inbox/telegram nên thuộc gốc 1.)
    Nếu cctx thiếu vault_root, tự động fallback về vault mặc định, volume Docker và repo root."""
    from pathlib import Path
    import os
    roots = []
    root = getattr(cctx, "vault_root", None)
    if root:
        try:
            roots.append(Path(root).resolve())
        except OSError:
            pass

    # Luôn bao gồm /brains/Brain Default và /brains trên Docker / VPS
    for dv in ("/brains/Brain Default", "/brains", "/data/vaults", "/data/brains", "/data/vaults/default"):
        try:
            dp = Path(dv).resolve()
            if dp.is_dir() and dp not in roots:
                roots.append(dp)
        except Exception:
            pass

    # Thư mục vault mà image_gen sử dụng
    try:
        import image_gen
        iv = image_gen._resolve_vault(None)
        if iv and Path(iv).is_dir() and Path(iv).resolve() not in roots:
            roots.append(Path(iv).resolve())
    except Exception:
        pass

    # Fallback vault root khi cctx thiếu vault_root hoặc chạy trên Docker volume
    try:
        import config
        st = config.read_settings()
        cur_brain = st.get("brain") or "Brain Default"
        b_dir = getattr(config, "BRAINS_DIR", None) or os.getenv("BRAINS_DIR")
        if b_dir:
            cand = (Path(b_dir) / cur_brain).resolve()
            if cand.is_dir() and cand not in roots:
                roots.append(cand)
            for sub in Path(b_dir).iterdir():
                if sub.is_dir() and sub.resolve() not in roots:
                    roots.append(sub.resolve())
        v_env = os.getenv("JAVIS_VAULT")
        if v_env and Path(v_env).is_dir() and Path(v_env).resolve() not in roots:
            roots.append(Path(v_env).resolve())
    except Exception:
        pass

    try:
        repo_root = Path(__file__).resolve().parents[3]
        for cand in (repo_root / "brains" / "Brain Default", repo_root / "brains", repo_root):
            if cand.is_dir() and cand.resolve() not in roots:
                roots.append(cand.resolve())
    except Exception:
        pass

    try:
        cwd = Path.cwd().resolve()
        for cand in (cwd / "brains" / "Brain Default", cwd / "brains", cwd):
            if cand.is_dir() and cand not in roots:
                roots.append(cand)
    except Exception:
        pass

    try:
        from config import STATE_DIR
        stg = (Path(STATE_DIR) / ".staging").resolve()
        if stg.is_dir() and stg not in roots:
            roots.append(stg)
    except Exception:
        pass
    return roots


def _resolve_media(ref, cctx):
    """'photo'/'video' nhận URL http(s) HOẶC đường dẫn file trong vault / vùng nhận file
    của chat (tương đối thử lần lượt từng gốc). Trả (url, path, err) - đúng một trong
    url/path có giá trị. File NGOÀI các gốc cho phép thì từ chối - plugin chạy full quyền
    nhưng không vì thế mà cho đăng file tuỳ ý trên máy lên mạng."""
    from pathlib import Path
    ref = str(ref or "").strip().strip('"').strip("'")
    if not ref:
        return None, None, "ERROR: thiếu đường dẫn file hoặc URL http(s) của media."
    if ref.startswith("http://") or ref.startswith("https://"):
        return ref, None, None
    roots = _media_roots(cctx)
    if not roots:
        return None, None, "ERROR: không xác định được vault/vùng nhận file để tìm media."
    try:
        pref = Path(ref)
        if pref.is_absolute() and pref.is_file():
            rp = pref.resolve()
            if any(str(rp).startswith(str(r)) for r in roots) or str(rp).startswith(("/brains", "/data", "/app")):
                return None, rp, None
            for r in roots:
                try:
                    rp.relative_to(r)
                    return None, rp, None
                except ValueError:
                    pass
            # Nếu file tồn tại tuyệt đối và là file ảnh an toàn
            if rp.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                return None, rp, None
        
        clean_ref = str(ref).replace("\\", "/").lstrip("/")
        for r in roots:
            cand = (r / clean_ref).resolve()
            if cand.is_file():
                return None, cand, None
            for marker in ("attachments/", "dataset/", "_xuat/", "album_ready/"):
                if marker in clean_ref:
                    sub_ref = clean_ref[clean_ref.find(marker):]
                    cand2 = (r / sub_ref).resolve()
                    if cand2.is_file():
                        return None, cand2, None
                    cand3 = (r / "attachments" / sub_ref).resolve()
                    if cand3.is_file():
                        return None, cand3, None
            # Quét tìm trực tiếp trong thư mục _xuat và album_ready nếu truyền tên file
            fname = Path(clean_ref).name
            if fname.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                for r in roots:
                    for sub in ("attachments/dataset/_xuat/album_ready", "attachments/dataset/_xuat", "attachments"):
                        cand_ar = (r / sub / fname).resolve()
                        if cand_ar.is_file():
                            return None, cand_ar, None
    except OSError as e:
        return None, None, f"ERROR: không đọc được đường dẫn ({type(e).__name__})."
    return None, None, (f"ERROR: không thấy '{ref}' trong vault hay vùng nhận file của chat. "
                        "File phải nằm trong vault, hoặc là file vừa gửi qua khung chat/Telegram.")


def _cover_gen_err(ref):
    """Ảnh 1 (cover) phải nằm _xuat/ (đã gen poster). Cấm file lớp trần trong folder ngành."""
    s = str(ref or "").replace("\\", "/").lower()
    if not s or s.startswith("http://") or s.startswith("https://"):
        return None
    if "/attachments/dataset/_xuat/" in s or "/dataset/_xuat/" in s:
        return None
    if "/attachments/dataset/_mau/" in s:
        return ("ERROR: POST_SKIP ly-do=anh-mau. File _mau/ chỉ là mẫu, không đăng lên tường. "
                "Gen cover mới vào _xuat/.")
    if "/attachments/dataset/" in s:
        return ("ERROR: POST_SKIP ly-do=anh-goc-chua-gen khong-retry=1. "
                "Ảnh đầu bài phải là poster/banner vừa gen (Imagen/Nano Banana), "
                "lưu attachments/dataset/_xuat/. CẤM đăng ảnh lớp học trần trong "
                "do-hoa / ke-toan / tin-hoc _ai / ve-ky-thuat / chung.")
    return None


def _extra_ai_err(photos):
    """Tỷ lệ 7/3: photos[0] banner gen; tối đa 3 file _xuat (không kể crop album_ready)."""
    extra = []
    for ref in (photos or [])[1:]:
        s = str(ref or "").replace("\\", "/").lower()
        if "/_xuat/" in s and "/album_ready/" not in s:
            extra.append(str(ref))
    n_gen = 1 + len(extra)  # cover + extra banners
    n = len(photos or [])
    if n_gen > 3:
        return (
            "ERROR: POST_SKIP ly-do=gen-thua khong-retry=1. "
            "Album 7/3: tối đa 3 ảnh gen (ảnh 1 = banner). "
            f"Đang {n_gen} file _xuat. Thừa: {extra[0][:120]}"
        )
    if n >= 4 and (n - n_gen) < 2:
        return (
            "ERROR: POST_SKIP ly-do=thieu-anh-goc khong-retry=1. "
            "Album 7/3 cần phần lớn ảnh raw dataset, không gần như toàn gen."
        )
    return None


async def _post_file(path_in_graph, file_path, data, token, base=GRAPH, timeout=900):
    """POST multipart (upload file thật). Video đi base GRAPH_VIDEO, timeout dài."""
    import mimetypes
    import httpx
    from pathlib import Path
    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    try:
        with open(file_path, "rb") as f:
            files = {"source": (Path(file_path).name, f, mime)}
            async with httpx.AsyncClient(timeout=timeout) as c:
                r = await c.post(f"{base}/{str(path_in_graph).lstrip('/')}",
                                 data={**(data or {}), "access_token": token}, files=files)
        try:
            return r.json()
        except Exception:
            return {"error": {"message": f"HTTP {r.status_code}: {r.text[:200]}"}}
    except Exception as e:
        return {"error": {"message": f"{type(e).__name__}: {e}"}}


async def _publish_photo(args, cctx):
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    photo_ref = args.get("photo") or args.get("image") or ""
    cov = _cover_gen_err(photo_ref)
    if cov:
        return cov
    url, path, err = _resolve_media(photo_ref, cctx)
    if err:
        return err
    pid, ptok, pname, perr = await _resolve_page(args, token)
    if perr:
        return perr
    caption = _fb_plain_caption(str(args.get("message") or args.get("caption") or "").strip())
    if caption.endswith((".txt", ".md")) and cctx and getattr(cctx, "vault_root", None):
        try:
            from pathlib import Path
            cp = Path(cctx.vault_root) / caption
            if cp.is_file():
                caption = _fb_plain_caption(cp.read_text(encoding="utf-8", errors="replace").strip())
        except Exception:
            pass
    kit_err = _caption_kit_err(caption, pid, cctx)
    if kit_err:
        return kit_err
    data = {"caption": caption} if caption else {}
    if url:
        d = await _post(f"{pid}/photos", {**data, "url": url}, ptok)
    else:
        d = await _post_file(f"{pid}/photos", path, data, ptok)
    if isinstance(d, dict) and d.get("error"):
        return _fmt(d)
    return json.dumps({"ok": True, "page": pname,
                       "photo_id": d.get("id") if isinstance(d, dict) else None,
                       "post_id": d.get("post_id") if isinstance(d, dict) else None},
                      ensure_ascii=False, default=str)


async def _publish_video(args, cctx):
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    url, path, err = _resolve_media(args.get("video") or "", cctx)
    if err:
        return err
    pid, ptok, pname, perr = await _resolve_page(args, token)
    if perr:
        return perr
    data = {}
    desc = str(args.get("message") or args.get("description") or "").strip()
    title = str(args.get("title") or "").strip()
    if desc:
        data["description"] = desc
    if title:
        data["title"] = title
    if url:
        d = await _post(f"{pid}/videos", {**data, "file_url": url}, ptok)
    else:
        d = await _post_file(f"{pid}/videos", path, data, ptok, base=GRAPH_VIDEO)
    if isinstance(d, dict) and d.get("error"):
        return _fmt(d)
    return json.dumps({"ok": True, "page": pname,
                       "video_id": d.get("id") if isinstance(d, dict) else None,
                       "note": "Video Facebook xử lý nền vài phút rồi mới hiện trên Trang."},
                      ensure_ascii=False, default=str)


COURSE_SPECS = {
    "tin-hoc": {
        "folder": "tin-hoc _ai",
        "aliases": ["tinhoc", "tin-hoc", "tin_hoc", "vanphong", "van-phong", "van_phong", "office", "word", "excel", "powerpoint", "mos", "ic3", "ai-van-phong", "ai_van_phong", "tinhocai", "tinhoc_ai"],
        "forbidden": ["dohoa", "do-hoa", "do_hoa", "photoshop", "illustrator", "autocad", "cad", "vekythuat", "ve-ky-thuat", "ve_ky_thuat", "solidworks", "ketoan", "ke-toan", "ke_toan", "misa", "tax"],
        "display": "Tin học văn phòng & AI",
    },
    "ve-ky-thuat": {
        "folder": "ve-ky-thuat",
        "aliases": ["cad", "autocad", "vekythuat", "ve-ky-thuat", "ve_ky_thuat", "solidworks", "cokhi", "banve", "ban-ve"],
        "forbidden": ["dohoa", "do-hoa", "do_hoa", "photoshop", "illustrator", "ketoan", "ke-toan", "ke_toan", "misa", "tax", "tinhoc", "tin-hoc", "vanphong", "office", "word", "excel"],
        "display": "Vẽ kỹ thuật & AutoCAD",
    },
    "do-hoa": {
        "folder": "do-hoa",
        "aliases": ["dohoa", "do-hoa", "do_hoa", "photoshop", "illustrator", "design", "corel", "premiere"],
        "forbidden": ["autocad", "cad", "vekythuat", "ve-ky-thuat", "solidworks", "ketoan", "ke-toan", "ke_toan", "misa", "tax", "tinhoc", "tin-hoc", "vanphong", "office", "word", "excel"],
        "display": "Thiết kế đồ họa",
    },
    "ke-toan": {
        "folder": "ke-toan",
        "aliases": ["ketoan", "ke-toan", "ke_toan", "misa", "tax", "sach", "chungtu", "thue"],
        "forbidden": ["dohoa", "do-hoa", "do_hoa", "photoshop", "illustrator", "autocad", "cad", "vekythuat", "ve-ky-thuat", "solidworks", "tinhoc", "tin-hoc", "vanphong", "office", "word", "excel"],
        "display": "Kế toán thực hành",
    },
    "tre-em": {
        "folder": "tin-hoc _ai",
        "aliases": ["treem", "tre-em", "tre_em", "scratch", "python-junior", "lap-trinh-nhi", "tinhoc-treem", "kid", "kids"],
        "forbidden": ["autocad", "cad", "vekythuat", "ve-ky-thuat", "solidworks", "ketoan", "ke-toan", "ke_toan", "misa", "tax"],
        "display": "Tin học & Lập trình Trẻ em",
    },
}


def _clean_vn(text):
    import unicodedata
    s = unicodedata.normalize("NFD", str(text or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "d")
    for ch in " _-&/|\\":
        s = s.replace(ch, "")
    return s


def _detect_course(course_str):
    c = _clean_vn(course_str)
    for ckey, spec in COURSE_SPECS.items():
        for al in spec["aliases"]:
            al_clean = _clean_vn(al)
            if al_clean in c or c in al_clean:
                return ckey, spec
    return None, None


def _auto_prepare_album(course, cover_ref, cctx):
    """Tự động chọn 5-8 ảnh từ dataset và chuẩn hóa tỷ lệ 7/3 (0 token LLM).
    Bảo đảm 100% đúng khóa học qua Strict Asset Guard."""
    from pathlib import Path
    import random
    roots = _media_roots(cctx)
    ckey, spec = _detect_course(course)

    cover_path = None
    if cover_ref and str(cover_ref).strip().lower() != "auto":
        _, cp, _ = _resolve_media(cover_ref, cctx)
        if cp and Path(cp).is_file():
            c_stem = Path(cp).stem.lower().replace(" ", "").replace("_", "").replace("-", "")
            if spec and any(forb in c_stem for forb in spec["forbidden"]):
                return None, (f"ERROR: VIOLATION_ASSET_GUARD: File cover '{Path(cp).name}' chứa từ khóa cấm của ngành khác, "
                              f"không thuộc khóa học '{course}'. Dừng đăng để bảo vệ trang.")
            cover_path = Path(cp)

    if not cover_path:
        return None, ("ERROR: POST_SKIP ly-do=thieu-cover-ai khong-retry=1. "
                      "BẮT BUỘC phải gọi javis_generate_image (GPT Image) hoặc gemini_generate_image (Imagen 3) "
                      "để tạo ảnh cover vuông 1:1 mới tinh trước, rồi truyền rõ đường dẫn vào 'cover'. "
                      "TUYỆT ĐỐI CẤM để trống cover, TUYỆT ĐỐI CẤM tự bốc cover cũ trong _xuat hoặc poster trong dataset.")

    dataset_dir = None
    target_folder_name = spec["folder"] if spec else ""
    for r in roots:
        base_ds = r / "attachments" / "dataset"
        if not base_ds.is_dir():
            continue
        if target_folder_name:
            cand = base_ds / target_folder_name
            if cand.is_dir():
                dataset_dir = cand
                break
        if not dataset_dir:
            clean_c = str(course or "").strip().lower().replace(" ", "").replace("_", "").replace("-", "")
            for sub in base_ds.iterdir():
                if sub.is_dir():
                    sub_clean = sub.name.lower().replace(" ", "").replace("_", "").replace("-", "")
                    if clean_c in sub_clean or sub_clean in clean_c:
                        dataset_dir = sub
                        break
        if dataset_dir:
            break

    if not dataset_dir or not dataset_dir.is_dir():
        return None, f"ERROR: Không tìm thấy thư mục dataset cho khóa học '{course}'."

    # Lọc pool ảnh từ folder dataset: loại trừ copy, trùng, và đặc biệt loại trừ forbidden keywords!
    pool = []
    cover_name = cover_path.name.lower()
    for f in sorted(dataset_dir.iterdir(), key=lambda x: x.name.lower()):
        if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            if f.name.lower() == cover_name:
                continue
            f_stem = f.stem.lower().replace(" ", "").replace("_", "").replace("-", "")
            if "copy" in f_stem or "(" in f.stem:
                continue
            if spec and any(forb in f_stem for forb in spec["forbidden"]):
                continue
            pool.append(f)

    if len(pool) < 2:
        return None, f"ERROR: Thư mục dataset '{dataset_dir.name}' không đủ ảnh đạt chuẩn để tạo album (cần ít nhất 2 ảnh)."

    # Chọn ngẫu nhiên 5, 6 hoặc 7 ảnh raw để tổng album đạt đúng 6, 7 hoặc 8 ảnh (1 cover + 5..7 ảnh thật)
    n_raw = min(len(pool), random.choice([5, 6, 7]))
    chosen_raw = random.sample(pool, n_raw)

    final_photos = [str(cover_path.resolve())] + [str(cr.resolve()) for cr in chosen_raw]

    # Chuẩn hóa ảnh sang album_ready (fb_norm_00..07.jpg) theo Tỷ Lệ Vàng Facebook 2026
    try:
        from PIL import Image
        out_dir = None
        for r in roots:
            od = r / "attachments" / "dataset" / "_xuat" / "album_ready"
            try:
                od.mkdir(parents=True, exist_ok=True)
                out_dir = od
                break
            except Exception:
                pass
        if not out_dir:
            return final_photos, None

        norm_list = []
        for idx, p_in in enumerate(final_photos):
            out_file = out_dir / f"fb_norm_{idx:02d}.jpg"
            with Image.open(p_in) as im:
                # Tỷ Lệ Vàng Facebook Album 2026: Đồng bộ 100% tỷ lệ vuông 1:1 (2000x2000px)
                # Cho toàn bộ ảnh trong album (1 cover AI + 5..7 ảnh thật).
                # Giúp lưới hiển thị 4 ô vuông trên mobile/desktop hoàn hảo tuyệt đối,
                # không bị co kéo hay cắt mép, ô thứ 4 hiển thị badge (+2, +3, +4) kích thích tương tác cao nhất.
                side = min(im.width, im.height)
                l = (im.width - side) // 2
                t = (im.height - side) // 2
                c = im.crop((l, t, l + side, t + side)).resize((2000, 2000), Image.Resampling.LANCZOS)
                c.convert("RGB").save(out_file, "JPEG", quality=95)
            norm_list.append(str(out_file.resolve()))
        return norm_list, None
    except Exception:
        return final_photos, None


async def _publish_album(args, cctx):
    """Đăng NHIỀU ảnh thành một bài (album): up từng ảnh published=false lấy id,
    rồi gom vào MỘT bài /feed qua attached_media. Meta cho tối đa 10 ảnh một bài.
    Hỗ trợ deterministic: nếu photos rỗng hoặc 'auto', tự động chọn ảnh từ dataset theo 'course'."""
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    photos = args.get("photos") or []
    course = args.get("course") or args.get("khoa_hoc") or args.get("folder")
    if isinstance(photos, str):   # model hay đưa chuỗi cách nhau dấu phẩy hoặc chuỗi JSON array
        p_str = photos.strip()
        if p_str.startswith("[") and p_str.endswith("]"):
            try:
                parsed = json.loads(p_str)
                if isinstance(parsed, list):
                    photos = parsed
            except Exception:
                pass
        if isinstance(photos, str):
            if photos.strip().lower() == "auto":
                photos = []
            else:
                photos = [p.strip() for p in photos.split(",") if p.strip()]

    # Tự động chuẩn bị album deterministic nếu photos rỗng mà có course
    if (not photos or len(photos) < 2) and course:
        auto_p, err_prep = _auto_prepare_album(course, args.get("cover") or (photos[0] if photos else None), cctx)
        if err_prep:
            return err_prep
        if auto_p and len(auto_p) >= 2:
            photos = auto_p

    # Strict Asset Guard: kiểm tra mọi ảnh xem có dính từ khóa cấm của khóa học không
    from pathlib import Path
    ckey, spec = _detect_course(course)
    if spec and photos:
        for idx, p in enumerate(photos):
            p_stem = Path(p).stem.lower().replace(" ", "").replace("_", "").replace("-", "")
            for forb in spec["forbidden"]:
                if forb in p_stem:
                    return (f"ERROR: VIOLATION_ASSET_GUARD: Ảnh #{idx} ('{Path(p).name}') chứa từ khóa cấm '{forb}' "
                            f"không thuộc khóa học '{course}'. Dừng đăng để bảo vệ fanpage.")

    if len(photos) < 2:
        return "ERROR: album cần ít nhất 2 ảnh trong 'photos' (1 ảnh thì dùng fb_page_photo)."
    if len(photos) > 10:
        return f"ERROR: Meta cho tối đa 10 ảnh một bài, đang có {len(photos)}. Bớt lại hoặc chia 2 bài."
    cov = _cover_gen_err(photos[0])
    if cov:
        return cov
    extra = _extra_ai_err(photos)
    if extra:
        return extra
    pid, ptok, pname, perr = await _resolve_page(args, token, cctx)
    if perr:
        return perr
    msg = _fb_plain_caption(str(args.get("message") or "").strip())
    if msg.endswith((".txt", ".md")) and cctx and getattr(cctx, "vault_root", None):
        try:
            from pathlib import Path
            cp = Path(cctx.vault_root) / msg
            if cp.is_file():
                msg = _fb_plain_caption(cp.read_text(encoding="utf-8", errors="replace").strip())
        except Exception:
            pass
    kit_err = _caption_kit_err(msg, pid, cctx)
    if kit_err:
        return kit_err
    media_ids = []
    for i, ref in enumerate(photos):
        url, path, err = _resolve_media(ref, cctx)
        if err:
            return f"{err} (ảnh thứ {i + 1}: {str(ref)[:80]})"
        if url:
            d = await _post(f"{pid}/photos", {"url": url, "published": "false"}, ptok)
        else:
            d = await _post_file(f"{pid}/photos", path, {"published": "false"}, ptok)
        if isinstance(d, dict) and d.get("error"):
            return _fmt(d) + f" (ảnh thứ {i + 1})"
        mid = (d or {}).get("id") if isinstance(d, dict) else None
        if not mid:
            return f"ERROR: Facebook không trả id cho ảnh thứ {i + 1}."
        media_ids.append(mid)
    data = {}
    if msg:
        data["message"] = msg
    for i, mid in enumerate(media_ids):
        data[f"attached_media[{i}]"] = json.dumps({"media_fbid": mid})
    d = await _post(f"{pid}/feed", data, ptok)
    if isinstance(d, dict) and d.get("error"):
        return _fmt(d)
    post_id = d.get("id") if isinstance(d, dict) else None
    link = f"https://www.facebook.com/{post_id}" if post_id else ""
    return json.dumps({
        "ok": True,
        "page": pname,
        "photos": len(media_ids),
        "post_id": post_id,
        "link": link,
        "status": "verified"
    }, ensure_ascii=False, default=str)


async def _edit_post(args, cctx):
    """Sửa NỘI DUNG CHỮ của bài đã đăng. Meta chỉ cho đổi message - không đổi được
    ảnh/video đã đính kèm (muốn đổi media thì xoá đăng lại, Javis không tự xoá)."""
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    post_id = str(args.get("post_id") or "").strip()
    msg = str(args.get("message") or "").strip()
    if not post_id:
        return "ERROR: thiếu 'post_id' (id bài cần sửa, lấy từ fb_page_posts)."
    if not msg:
        return "ERROR: thiếu 'message' (nội dung MỚI thay cho nội dung cũ)."
    # post_id dạng {pageid}_{postid}: tự suy Trang như fb_page_comments
    if not (args.get("page_id") or args.get("page")) and "_" in post_id:
        args = {**args, "page_id": post_id.split("_", 1)[0]}
    pid, ptok, pname, err = await _resolve_page(args, token)
    if err:
        return err
    kit_err = _caption_kit_err(msg, pid, cctx)
    if kit_err:
        return kit_err
    d = await _post(post_id, {"message": msg}, ptok)
    if isinstance(d, dict) and d.get("error"):
        return _fmt(d)
    ok = bool(isinstance(d, dict) and (d.get("success") is True or d.get("id")))
    return json.dumps({"ok": ok, "page": pname, "post_id": post_id,
                       "note": "" if ok else "Facebook trả về khác thường: " + str(d)[:120]},
                      ensure_ascii=False, default=str)


async def _delete_post(args, cctx):
    """XOÁ HẲN một bài đã đăng trên Trang. Meta không có thùng rác cho bài Trang nên
    KHÔNG khôi phục được. Trước khi xoá có đọc lại bài, vừa để chắc đúng bài vừa giữ
    lại nội dung trả về cho người dùng đối chiếu (và có cái dán lại nếu lỡ tay)."""
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    post_id = str(args.get("post_id") or "").strip()
    if not post_id:
        return "ERROR: thiếu 'post_id' (id bài cần xoá, lấy từ fb_page_posts)."
    # post_id dạng {pageid}_{postid}: tự suy Trang như fb_page_edit
    if not (args.get("page_id") or args.get("page")) and "_" in post_id:
        args = {**args, "page_id": post_id.split("_", 1)[0]}
    pid, ptok, pname, err = await _resolve_page(args, token)
    if err:
        return err
    snap = await _get(post_id, {"fields": "id,message,created_time,permalink_url"}, ptok)
    if isinstance(snap, dict) and snap.get("error"):
        return _fmt(snap)                      # bài không tồn tại / không thuộc Trang này → dừng, chưa xoá gì
    d = await _delete(post_id, ptok)
    if isinstance(d, dict) and d.get("error"):
        return _fmt(d)
    ok = bool(isinstance(d, dict) and d.get("success") is True)
    cu = str((snap or {}).get("message") or "")
    return json.dumps({"ok": ok, "page": pname, "post_id": post_id,
                       "noi_dung_da_xoa": (cu[:300] + "…") if len(cu) > 300 else cu,
                       "created_time": (snap or {}).get("created_time"),
                       "note": "Đã xoá hẳn, KHÔNG khôi phục được." if ok
                               else "Facebook trả về khác thường: " + str(d)[:120]},
                      ensure_ascii=False, default=str)


async def _reply(args, ctx):
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    target = str(args.get("comment_id") or args.get("object_id") or args.get("post_id") or "").strip()
    raw_msg = str(args.get("message") or "").strip()
    msg = _fb_plain_caption(raw_msg)
    if not target:
        return "ERROR: thiếu 'comment_id' (bình luận cần trả lời) hoặc 'post_id' (để bình luận vào bài)."
    if not msg:
        return "ERROR: thiếu 'message' (nội dung trả lời)."
    if not (args.get("page_id") or args.get("page")) and "_" in target:
        args = {**args, "page_id": target.split("_", 1)[0]}
    pid, ptok, pname, err = await _resolve_page(args, token)
    if err:
        return err
    d = await _post(f"{target}/comments", {"message": msg}, ptok)
    if isinstance(d, dict) and d.get("error"):
        return _fmt(d)
    return json.dumps({"ok": True, "page": pname,
                       "reply_id": d.get("id") if isinstance(d, dict) else None},
                      ensure_ascii=False, default=str)


async def _inbox_comments(args, ctx):
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    p, err = await _resolve_page_info(args, token)
    if err:
        return err
    pid = p.get("id")
    ptok = p.get("access_token")
    pname = p.get("name")
    args = args or {}
    try:
        posts_limit = max(1, min(15, int(args.get("posts_limit") or 5)))
    except (TypeError, ValueError):
        posts_limit = 5
    try:
        comments_per_post = max(1, min(50, int(args.get("comments_per_post") or 25)))
    except (TypeError, ValueError):
        comments_per_post = 25
    filter_mode = str(args.get("filter") or "stream").strip()
    since = str(args.get("since") or "").strip()

    feed_params = {
        "fields": "id,created_time,comments.summary(true).limit(0)",
        "limit": posts_limit,
    }
    if since:
        feed_params["since"] = since
    feed_res = await _get(f"{pid}/feed", feed_params, ptok)
    if isinstance(feed_res, dict) and feed_res.get("error"):
        return _fmt(feed_res)

    posts = (feed_res or {}).get("data") or []
    items = []
    scanned_posts = 0
    skipped_unchanged = 0

    for post in posts:
        post_id = str(post.get("id") or "")
        if not post_id:
            continue
        scanned_posts += 1
        summary = (post.get("comments") or {}).get("summary") or {}
        total_count = summary.get("total_count", 0)
        if total_count == 0:
            skipped_unchanged += 1
            continue

        c_params = {
            "fields": "id,from{id,name},message,created_time,like_count,parent,is_hidden",
            "order": "chronological",
            "limit": comments_per_post,
        }
        if filter_mode:
            c_params["filter"] = filter_mode
        if since:
            c_params["since"] = since

        c_res = await _get(f"{post_id}/comments", c_params, ptok)
        if isinstance(c_res, dict) and c_res.get("error"):
            err_msg = str(c_res["error"].get("message", ""))
            if "filter" in err_msg.lower():
                c_params.pop("filter", None)
                c_res = await _get(f"{post_id}/comments", c_params, ptok)

        if isinstance(c_res, dict) and not c_res.get("error"):
            for c in (c_res.get("data") or []):
                from_info = c.get("from") or {}
                parent = c.get("parent") or {}
                items.append({
                    "comment_id": c.get("id"),
                    "post_id": post_id,
                    "parent_id": parent.get("id"),
                    "from_id": from_info.get("id"),
                    "from_name": from_info.get("name") or "Ẩn danh",
                    "message": c.get("message") or "",
                    "created_time": c.get("created_time"),
                    "is_hidden": bool(c.get("is_hidden", False)),
                    "like_count": c.get("like_count", 0),
                })

    return json.dumps({
        "ok": True,
        "page_id": pid,
        "page_name": pname,
        "items": items,
        "scanned_posts": scanned_posts,
        "skipped_unchanged": skipped_unchanged,
    }, ensure_ascii=False, default=str)


async def _comment_hide(args, ctx):
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    cid = str(args.get("comment_id") or "").strip()
    if not cid:
        return "ERROR: thiếu 'comment_id'."
    p, err = await _resolve_page_info(args, token)
    if err:
        return err
    tasks = [t.upper() for t in (p.get("tasks") or [])]
    if tasks and "MODERATE" not in tasks:
        return "ERROR: Page không có quyền MODERATE để ẩn bình luận."
    is_hidden = args.get("is_hidden")
    if is_hidden is None:
        is_hidden = True
    else:
        is_hidden = bool(is_hidden)
    ptok = p.get("access_token")
    d = await _post(f"{cid}", {"is_hidden": str(is_hidden).lower()}, ptok)
    if isinstance(d, dict) and d.get("error"):
        return _fmt(d)
    return json.dumps({"ok": True, "comment_id": cid, "is_hidden": is_hidden, "page": p.get("name")}, ensure_ascii=False, default=str)


async def _comment_like(args, ctx):
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    cid = str(args.get("comment_id") or "").strip()
    if not cid:
        return "ERROR: thiếu 'comment_id'."
    p, err = await _resolve_page_info(args, token)
    if err:
        return err
    tasks = [t.upper() for t in (p.get("tasks") or [])]
    if tasks and "MODERATE" not in tasks and "CREATE_CONTENT" not in tasks:
        return "ERROR: Page không có quyền like bình luận."
    unlike = bool(args.get("unlike", False))
    ptok = p.get("access_token")
    if unlike:
        d = await _delete(f"{cid}/likes", ptok)
    else:
        d = await _post(f"{cid}/likes", {}, ptok)
    if isinstance(d, dict) and d.get("error"):
        return _fmt(d)
    return json.dumps({"ok": True, "comment_id": cid, "liked": not unlike, "page": p.get("name")}, ensure_ascii=False, default=str)


async def _comment_delete(args, ctx):
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    cid = str(args.get("comment_id") or "").strip()
    if not cid:
        return "ERROR: thiếu 'comment_id'."
    p, err = await _resolve_page_info(args, token)
    if err:
        return err
    tasks = [t.upper() for t in (p.get("tasks") or [])]
    if tasks and "MODERATE" not in tasks:
        return "ERROR: Page không có quyền MODERATE để xoá bình luận."
    ptok = p.get("access_token")
    d = await _delete(f"{cid}", ptok)
    if isinstance(d, dict) and d.get("error"):
        return _fmt(d)
    return json.dumps({"ok": True, "comment_id": cid, "deleted": True, "page": p.get("name")}, ensure_ascii=False, default=str)


async def _conversations(args, ctx):
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    pid, ptok, pname, err = await _resolve_page(args, token)
    if err:
        return err
    args = args or {}
    try:
        limit = max(1, min(100, int(args.get("limit") or 20)))
    except (TypeError, ValueError):
        limit = 20
    d = await _get(
        f"{pid}/conversations",
        {
            "fields": "id,updated_time,message_count,unread_count,participants,snippet",
            "limit": limit,
        },
        ptok,
    )
    return _fmt(d)


async def _conversation_thread(args, ctx):
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    cid = str(args.get("conversation_id") or "").strip()
    if not cid:
        return "ERROR: thiếu 'conversation_id' (id hội thoại cần đọc tin nhắn; lấy từ fb_conversations)."
    pid, ptok, pname, err = await _resolve_page(args, token)
    if err:
        return err
    try:
        limit = max(1, min(100, int(args.get("limit") or 25)))
    except (TypeError, ValueError):
        limit = 25
    d = await _get(
        f"{cid}/messages",
        {
            "fields": "id,from,to,message,created_time,attachments",
            "limit": limit,
        },
        ptok,
    )
    return _fmt(d)


async def _message_send(args, ctx):
    token = await _token()
    if not token:
        return "ERROR: " + (_check() or "chưa kết nối")
    args = args or {}
    recipient_id = str(args.get("recipient_id") or "").strip()
    if not recipient_id:
        return "ERROR: thiếu 'recipient_id' (PSID người nhận tin nhắn)."
    msg = str(args.get("message") or "").strip()
    if not msg:
        return "ERROR: thiếu 'message' (nội dung tin nhắn cần gửi)."
    pid, ptok, pname, err = await _resolve_page(args, token)
    if err:
        return err
    clean_msg = _fb_plain_caption(msg)
    mtype = str(args.get("messaging_type") or "RESPONSE").strip()
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": clean_msg},
        "messaging_type": mtype,
    }
    d = await _post(f"{pid}/messages", payload, ptok)
    if isinstance(d, dict) and d.get("error"):
        return _fmt(d)
    return json.dumps({"ok": True, "recipient_id": recipient_id, "message_id": (d or {}).get("message_id")}, ensure_ascii=False, default=str)


def register(ctx):
    ctx.register_tool(
        name="fb_pages_list", min_mode="readonly", check_fn=_check, handler=_list,
        description=("Liệt kê các Trang/Fanpage Facebook bạn quản lý (id, tên, hạng mục, quyền). Gọi đầu "
                     "tiên để lấy id/tên Trang cho các tool khác. KHÔNG lộ token của Trang."),
        schema={"type": "object", "properties": {
            "query": {"type": "string", "description": "Từ khoá lọc tên hoặc id Trang (tuỳ chọn)"}
        }},
    )
    ctx.register_tool(
        name="fb_page_posts", min_mode="readonly", check_fn=_check, handler=_posts,
        description=("Đọc các bài GẦN ĐÂY trên một Trang của bạn (id bài, nội dung, thời gian, link, số bình "
                     "luận). Bỏ trống page nếu chỉ có 1 Trang; nhiều Trang thì truyền page_id hoặc page (tên)."),
        schema={"type": "object", "properties": {
            "page_id": {"type": "string", "description": "id Trang (bỏ trống nếu chỉ có 1 Trang)"},
            "page": {"type": "string", "description": "tên Trang (thay cho page_id)"},
            "limit": {"type": "integer", "description": "Số bài tối đa (mặc định 10)"}}},
    )
    ctx.register_tool(
        name="fb_page_comments", min_mode="readonly", check_fn=_check, handler=_comments,
        description=("Đọc bình luận của MỘT bài trên Trang (người bình luận, nội dung, thời gian). Cần post_id "
                     "lấy từ fb_page_posts. Trang tự suy từ post_id; nhiều Trang thì truyền thêm page_id/page nếu cần."),
        schema={"type": "object", "properties": {
            "post_id": {"type": "string", "description": "id bài cần đọc bình luận (từ fb_page_posts)"},
            "page_id": {"type": "string", "description": "id Trang (thường không cần, suy từ post_id)"},
            "page": {"type": "string", "description": "tên Trang (tuỳ chọn)"},
            "limit": {"type": "integer", "description": "Số bình luận tối đa (mặc định 25)"}},
            "required": ["post_id"]},
    )
    ctx.register_tool(
        name="fb_page_inbox_comments", min_mode="readonly", check_fn=_check, handler=_inbox_comments,
        description=("Quét bình luận mới trên N bài gần nhất của một Trang (hỗ trợ cả reply lồng filter=stream). "
                     "Primitive cho vòng lặp chăm sóc Fanpage. Bỏ trống page nếu chỉ có 1 Trang."),
        schema={"type": "object", "properties": {
            "page_id": {"type": "string", "description": "id Trang (bỏ trống nếu chỉ có 1 Trang)"},
            "page": {"type": "string", "description": "tên Trang (thay cho page_id)"},
            "posts_limit": {"type": "integer", "description": "Số bài quét, mặc định 5, max 15"},
            "comments_per_post": {"type": "integer", "description": "Số bình luận mỗi bài, mặc định 25, max 50"},
            "since": {"type": "string", "description": "ISO8601; bỏ trống = 24h"},
            "filter": {"type": "string", "description": "Mặc định stream (cả reply lồng)"}}},
    )
    ctx.register_tool(
        name="fb_page_post", min_mode="full", check_fn=_check, handler=_publish,
        description=("ĐĂNG một bài lên Trang của bạn - hành động THẬT, công khai. Cần message (nội dung) và/hoặc "
                     "link. Bỏ trống page nếu chỉ có 1 Trang; nhiều Trang thì truyền page_id/page."),
        schema={"type": "object", "properties": {
            "message": {"type": "string", "description": "Nội dung bài đăng"},
            "link": {"type": "string", "description": "Link đính kèm (tuỳ chọn)"},
            "page_id": {"type": "string", "description": "id Trang (bỏ trống nếu chỉ có 1 Trang)"},
            "page": {"type": "string", "description": "tên Trang (thay cho page_id)"}}},
    )
    ctx.register_tool(
        name="fb_page_photo", min_mode="full", check_fn=_check, handler=_publish_photo,
        description=("ĐĂNG ẢNH lên Trang của bạn - hành động THẬT, công khai. photo = đường dẫn file ảnh "
                     "trong vault (vd attachments/anh.jpg) hoặc URL http(s). message = caption tuỳ chọn. "
                     "Bỏ trống page nếu chỉ có 1 Trang."),
        schema={"type": "object", "properties": {
            "photo": {"type": "string", "description": "Đường dẫn ảnh trong vault hoặc URL http(s)"},
            "message": {"type": "string", "description": "Caption cho ảnh (tuỳ chọn)"},
            "page_id": {"type": "string", "description": "id Trang (bỏ trống nếu chỉ có 1 Trang)"},
            "page": {"type": "string", "description": "tên Trang (thay cho page_id)"}},
            "required": ["photo"]},
    )
    ctx.register_tool(
        name="fb_page_album", min_mode="full", check_fn=_check, handler=_publish_album,
        description=("ĐĂNG ALBUM: nhiều ảnh (2-10) gom vào MỘT bài trên Trang - hành động THẬT, công khai. "
                     "Khi photos='auto': BẮT BUỘC truyền cover do AI vừa tạo (javis_generate_image/gemini_generate_image) "
                     "và tên course để hệ thống tự động chuẩn bị album chuẩn 100% đúng ngành."),
        schema={"type": "object", "properties": {
            "photos": {"description": "Danh sách 2-10 ảnh trong vault hoặc URL http(s), hoặc 'auto'"},
            "course": {"type": "string", "description": "Tên khóa học hoặc ngành (vd: 'tin-hoc', 've-ky-thuat', 'do-hoa', 'ke-toan') để tự động chuẩn bị album"},
            "cover": {"type": "string", "description": "BẮT BUỘC khi photos='auto': Đường dẫn ảnh cover vuông 1:1 do AI vừa tạo mới (GPT Image / Imagen 3) lưu trong _xuat. TUYỆT ĐỐI CẤM để trống, CẤM bốc cover cũ."},
            "message": {"type": "string", "description": "Caption chung của album (tuỳ chọn)"},
            "page_id": {"type": "string", "description": "id Trang (bỏ trống nếu chỉ có 1 Trang)"},
            "page": {"type": "string", "description": "tên Trang (thay cho page_id)"}},
            "required": ["photos"]},
    )
    ctx.register_tool(
        name="fb_page_edit", min_mode="full", check_fn=_check, handler=_edit_post,
        description=("SỬA nội dung chữ của một bài ĐÃ ĐĂNG trên Trang - hành động THẬT. Cần post_id (từ "
                     "fb_page_posts) và message MỚI thay toàn bộ nội dung cũ. Meta không cho đổi ảnh/video "
                     "đã đính kèm, chỉ đổi được chữ - muốn đổi ảnh thì đăng bài mới rồi fb_page_delete bài cũ."),
        schema={"type": "object", "properties": {
            "post_id": {"type": "string", "description": "id bài cần sửa (từ fb_page_posts)"},
            "message": {"type": "string", "description": "Nội dung MỚI thay cho nội dung cũ"},
            "page_id": {"type": "string", "description": "id Trang (thường tự suy từ post_id)"},
            "page": {"type": "string", "description": "tên Trang (tuỳ chọn)"}},
            "required": ["post_id", "message"]},
    )
    ctx.register_tool(
        name="fb_page_video", min_mode="full", check_fn=_check, handler=_publish_video,
        description=("ĐĂNG VIDEO lên Trang của bạn - hành động THẬT, công khai. video = đường dẫn file "
                     "video trong vault hoặc URL http(s) (tối đa cỡ 1GB). message = mô tả, title = tiêu đề, "
                     "đều tuỳ chọn. Facebook xử lý nền vài phút mới hiện bài. Bỏ trống page nếu chỉ có 1 Trang."),
        schema={"type": "object", "properties": {
            "video": {"type": "string", "description": "Đường dẫn video trong vault hoặc URL http(s)"},
            "message": {"type": "string", "description": "Mô tả video (tuỳ chọn)"},
            "title": {"type": "string", "description": "Tiêu đề video (tuỳ chọn)"},
            "page_id": {"type": "string", "description": "id Trang (bỏ trống nếu chỉ có 1 Trang)"},
            "page": {"type": "string", "description": "tên Trang (thay cho page_id)"}},
            "required": ["video"]},
    )
    ctx.register_tool(
        name="fb_page_delete", min_mode="full", check_fn=_check, handler=_delete_post,
        description=("XOÁ HẲN một bài đã đăng trên Trang - hành động THẬT, KHÔNG HOÀN TÁC ĐƯỢC (Trang không "
                     "có thùng rác). Cần post_id từ fb_page_posts. CHỈ gọi khi người dùng nói rõ muốn xoá "
                     "đúng bài đó; đừng tự xoá để 'dọn dẹp'. Xoá xong trả lại đoạn nội dung vừa xoá để đối chiếu."),
        schema={"type": "object", "properties": {
            "post_id": {"type": "string", "description": "id bài cần xoá (từ fb_page_posts)"},
            "page_id": {"type": "string", "description": "id Trang (thường tự suy từ post_id)"},
            "page": {"type": "string", "description": "tên Trang (tuỳ chọn)"}},
            "required": ["post_id"]},
    )
    ctx.register_tool(
        name="fb_page_reply", min_mode="full", check_fn=_check, handler=_reply,
        description=("TRẢ LỜI một bình luận, hoặc bình luận vào một bài - hành động THẬT, công khai. Cần message "
                     "và comment_id (trả lời bình luận) HOẶC post_id (bình luận vào bài). Nhiều Trang thì truyền "
                     "page_id/page."),
        schema={"type": "object", "properties": {
            "message": {"type": "string", "description": "Nội dung trả lời"},
            "comment_id": {"type": "string", "description": "id bình luận cần trả lời"},
            "post_id": {"type": "string", "description": "id bài (bình luận thẳng vào bài thay vì trả lời 1 comment)"},
            "page_id": {"type": "string", "description": "id Trang (khi có nhiều Trang)"},
            "page": {"type": "string", "description": "tên Trang (khi có nhiều Trang)"}},
            "required": ["message"]},
    )
    ctx.register_tool(
        name="fb_page_comment_hide", min_mode="full", check_fn=_check, handler=_comment_hide,
        description=("ẨN hoặc HIỆN LẠI một bình luận trên Trang - hành động THẬT, cần quyền MODERATE trên Trang. "
                     "Cần comment_id. is_hidden=true (ẩn, mặc định) hoặc false (hiện lại)."),
        schema={"type": "object", "required": ["comment_id"], "properties": {
            "comment_id": {"type": "string", "description": "id bình luận cần ẩn hoặc hiện lại"},
            "is_hidden": {"type": "boolean", "description": "true ẩn, false hiện lại. Mặc định true"},
            "page_id": {"type": "string", "description": "id Trang (suy được từ comment_id)"},
            "page": {"type": "string", "description": "tên Trang"},
            "post_id": {"type": "string", "description": "id bài chứa bình luận"}}},
    )
    ctx.register_tool(
        name="fb_page_comment_like", min_mode="full", check_fn=_check, handler=_comment_like,
        description=("LIKE hoặc BỎ LIKE một bình luận trên Trang bằng tư cách Trang - hành động THẬT. "
                     "Cần comment_id. unlike=true để bỏ like."),
        schema={"type": "object", "required": ["comment_id"], "properties": {
            "comment_id": {"type": "string", "description": "id bình luận cần like hoặc bỏ like"},
            "unlike": {"type": "boolean", "description": "true bỏ like, false like. Mặc định false"},
            "page_id": {"type": "string", "description": "id Trang (suy được từ comment_id)"},
            "page": {"type": "string", "description": "tên Trang"},
            "post_id": {"type": "string", "description": "id bài chứa bình luận"}}},
    )
    ctx.register_tool(
        name="fb_page_comment_delete", min_mode="full", check_fn=_check, handler=_comment_delete,
        description=("XOÁ HẲN một bình luận trên Trang - hành động THẬT, KHÔNG HOÀN TÁC ĐƯỢC. Cần comment_id "
                     "và quyền MODERATE."),
        schema={"type": "object", "required": ["comment_id"], "properties": {
            "comment_id": {"type": "string", "description": "id bình luận cần xoá hẳn"},
            "page_id": {"type": "string", "description": "id Trang (suy được từ comment_id)"},
            "page": {"type": "string", "description": "tên Trang"},
            "post_id": {"type": "string", "description": "id bài chứa bình luận"}}},
    )
    ctx.register_tool(
        name="fb_conversations", min_mode="readonly", check_fn=_check, handler=_conversations,
        description=("Đọc danh sách các hội thoại Messenger trên Trang của bạn (id hội thoại, số tin chưa đọc, "
                     "người tham gia, tin nhắn gần nhất). Bỏ trống page nếu chỉ có 1 Trang."),
        schema={"type": "object", "properties": {
            "page_id": {"type": "string", "description": "id Trang (bỏ trống nếu chỉ có 1 Trang)"},
            "page": {"type": "string", "description": "tên Trang (thay cho page_id)"},
            "limit": {"type": "integer", "description": "Số hội thoại tối đa, mặc định 20"}}},
    )
    ctx.register_tool(
        name="fb_conversation_thread", min_mode="readonly", check_fn=_check, handler=_conversation_thread,
        description=("Đọc chi tiết các tin nhắn trong một hội thoại Messenger trên Trang. Cần conversation_id "
                     "lấy từ fb_conversations."),
        schema={"type": "object", "properties": {
            "conversation_id": {"type": "string", "description": "id hội thoại (từ fb_conversations)"},
            "page_id": {"type": "string", "description": "id Trang (bỏ trống nếu chỉ có 1 Trang)"},
            "page": {"type": "string", "description": "tên Trang"},
            "limit": {"type": "integer", "description": "Số tin nhắn tối đa, mặc định 25"}},
            "required": ["conversation_id"]},
    )
    ctx.register_tool(
        name="fb_message_send", min_mode="full", check_fn=_check, handler=_message_send,
        description=("GỬI TIN NHẮN Messenger đến người dùng (PSID) từ Trang của bạn - hành động THẬT. "
                     "Cần recipient_id (PSID) và message. Tuân thủ cửa sổ chuẩn 24 giờ của Meta."),
        schema={"type": "object", "properties": {
            "recipient_id": {"type": "string", "description": "PSID người nhận tin nhắn"},
            "message": {"type": "string", "description": "Nội dung tin nhắn cần gửi"},
            "page_id": {"type": "string", "description": "id Trang (bỏ trống nếu chỉ có 1 Trang)"},
            "page": {"type": "string", "description": "tên Trang"},
            "messaging_type": {"type": "string", "enum": ["RESPONSE", "UPDATE"], "description": "Mặc định RESPONSE"}},
            "required": ["recipient_id", "message"]},
    )

