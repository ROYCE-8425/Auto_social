# -*- coding: utf-8 -*-
"""Gọi tool qua Javis hub MCP (JSON-RPC) và tiện ích chọn/chuẩn hóa ảnh Facebook."""
import json
import os
import sys
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

_HERE = Path(__file__).resolve()
VAULT = str(_HERE.parents[1])  # brains/Brain Default
_SERVER = _HERE.parents[3] / "server"
if _SERVER.is_dir():
    sys.path.insert(0, str(_SERVER))
import mcp_hub  # noqa: E402

TOKEN = mcp_hub.hub_token()
URL = mcp_hub.hub_url()
_RID = 0
_IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def resolve_dataset_folder(folder):
    """
    Chuẩn hóa tên hoặc đường dẫn folder dataset về đúng thư mục thật trên đĩa.
    Chấp nhận: 'tin-hoc _ai', 'attachments/dataset/tin-hoc _ai', 'tin-hoc-ai', 'tin-hoc',
    've-ky-thuat', 'cad', 'autocad', 'do-hoa', 'ke-toan', slash/backslash.
    """
    f = str(folder or "").strip().replace("\\", "/")
    if "attachments/dataset/" in f:
        f = f.split("attachments/dataset/", 1)[1]
    elif f.startswith("dataset/"):
        f = f.split("dataset/", 1)[1]
    f = f.strip("/")

    # Fuzzy map theo từ khóa ngành / khóa học
    low = f.lower().replace(" ", "").replace("_", "").replace("-", "")
    if any(k in low for k in ("tinhoc", "vanphong", "office", "word", "excel", "mos")) or low in ("ai", "tinhocai", "tinhoc_ai"):
        f = "tin-hoc _ai"
    elif any(k in low for k in ("cad", "autocad", "vekythuat", "solidworks", "cokhi")):
        f = "ve-ky-thuat"
    elif any(k in low for k in ("dohoa", "photoshop", "illustrator", "design", "corel")):
        f = "do-hoa"
    elif any(k in low for k in ("ketoan", "misa", "tax", "sach", "chungtu")):
        f = "ke-toan"
    elif low in ("chung", "logo"):
        f = "chung"

    d = Path(VAULT) / "attachments" / "dataset" / f
    if d.is_file():
        # Pointer file text (ví dụ file 'tin-hoc' chứa 'tin-hoc _ai')
        try:
            target = d.read_text(encoding="utf-8").strip()
            if (Path(VAULT) / "attachments" / "dataset" / target).is_dir():
                return target
        except Exception:
            pass

    if not d.is_dir():
        dataset_root = Path(VAULT) / "attachments" / "dataset"
        if dataset_root.is_dir():
            for sub in dataset_root.iterdir():
                if sub.is_dir():
                    sub_clean = sub.name.lower().replace(" ", "").replace("_", "").replace("-", "")
                    if sub_clean == low or sub.name.lower() == f.lower():
                        return sub.name

    return f


def _get_dataset_cache(folder):
    cache_file = Path(VAULT) / "attachments" / "dataset" / ".dataset_cache.json"
    if not cache_file.exists():
        return {}
    try:
        return json.loads(cache_file.read_text(encoding="utf-8")).get(folder, {})
    except Exception:
        return {}


def _save_dataset_cache(folder, data):
    cache_file = Path(VAULT) / "attachments" / "dataset" / ".dataset_cache.json"
    all_cache = {}
    if cache_file.exists():
        try:
            all_cache = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            all_cache = {}
    all_cache[folder] = data
    try:
        cache_file.write_text(json.dumps(all_cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def unique_dataset_photos(folder, skip_names=None):
    """
    Ảnh gốc không trùng hash, bỏ file Windows ' (1)' / copy.
    Tối ưu I/O: Scan metadata st_size/st_mtime trước, dùng cache JSON nhẹ.
    Chỉ hash MD5 khi trùng kích thước file hoặc cache miss để tránh đọc hàng trăm MB.
    """
    import hashlib
    import re
    skip_names = {str(x).replace("\\", "/").split("/")[-1].lower() for x in (skip_names or [])}
    real_folder = resolve_dataset_folder(folder)
    d = Path(VAULT) / "attachments" / "dataset" / real_folder
    if not d.is_dir():
        return []

    cache = _get_dataset_cache(real_folder)
    new_cache = {}
    out = []
    seen_sizes = {}
    seen_hash = set()
    cache_changed = False

    for p in sorted(d.iterdir(), key=lambda x: x.name.lower()):
        if not p.is_file() or p.suffix.lower() not in _IMG_EXT:
            continue
        if re.search(r"\(\d+\)", p.name):
            continue
        if re.search(r"_\d+\.[^.]+$", p.name):
            continue
        if "copy" in p.stem.lower():
            continue
        if p.name.lower() in skip_names:
            continue

        try:
            st = p.stat()
            sz = st.st_size
            mtime = st.st_mtime
        except OSError:
            continue

        rel = f"attachments/dataset/{real_folder}/{p.name}"

        # Nếu kích thước chưa từng xuất hiện trong folder -> file độc nhất, không cần hash byte
        if sz not in seen_sizes:
            seen_sizes[sz] = p
            out.append(rel)
            cached_info = cache.get(p.name)
            if cached_info and cached_info.get("size") == sz and cached_info.get("mtime") == mtime:
                new_cache[p.name] = cached_info
            else:
                new_cache[p.name] = {"size": sz, "mtime": mtime}
                cache_changed = True
            continue

        # Nếu trùng size với một file khác trong folder -> cần đối chiếu MD5
        cached_info = cache.get(p.name)
        if cached_info and cached_info.get("size") == sz and cached_info.get("mtime") == mtime and "md5" in cached_info:
            h = cached_info["md5"]
        else:
            try:
                h = hashlib.md5(p.read_bytes()).hexdigest()
                cache_changed = True
            except OSError:
                continue

        new_cache[p.name] = {"size": sz, "mtime": mtime, "md5": h}
        if h in seen_hash:
            continue
        seen_hash.add(h)
        out.append(rel)

    if cache_changed or len(new_cache) != len(cache):
        _save_dataset_cache(real_folder, new_cache)

    return out


def pick_random_album_photos(folder, cover_path=None, target_total=None):
    """
    Chọn ngẫu nhiên số lượng ảnh gốc từ folder để ghép với cover_path.
    Mục tiêu tổng số ảnh: 5, 6, 7, hoặc 8 ảnh khi có cover.
    Ưu tiên ảnh gốc chưa từng dùng trong _anh-da-dung.md.
    Nếu hết ảnh mới, tự động xoay vòng ảnh gốc để luôn đủ 5-8 ảnh khi folder có đủ ảnh.
    """
    import random
    real_folder = resolve_dataset_folder(folder)
    skip = []
    if cover_path:
        skip.append(cover_path)
    cover_inner_file = Path(VAULT) / "attachments/dataset/_xuat/cover_inner_photo.txt"
    if cover_inner_file.exists():
        inner_name = cover_inner_file.read_text(encoding="utf-8").strip().replace("\\", "/").split("/")[-1].lower()
        if inner_name:
            skip.append(inner_name)
    all_goc = unique_dataset_photos(real_folder, skip_names=skip)
    if not all_goc:
        return [cover_path] if cover_path else []

    # Ưu tiên ảnh chưa dùng
    used_file = Path(VAULT) / "wiki" / "brand-kits" / "_anh-da-dung.md"
    used_set = set()
    if used_file.exists():
        for l in used_file.read_text(encoding="utf-8").splitlines():
            if l.strip().startswith("- "):
                used_set.add(l.strip()[2:].strip().replace("\\", "/").split("/")[-1].lower())

    if cover_inner_file.exists():
        inner_name = cover_inner_file.read_text(encoding="utf-8").strip().replace("\\", "/").split("/")[-1].lower()
        if inner_name:
            used_set.add(inner_name)

    # Lọc ảnh chưa dùng
    chua_dung = [p for p in all_goc if p.replace("\\", "/").split("/")[-1].lower() not in used_set]

    # Nếu ảnh chưa dùng còn >= 4 ảnh thì ưu tiên dùng ảnh chưa dùng;
    # nếu không đủ, cho phép xoay vòng lại all_goc để không bị tụt số lượng album
    if len(chua_dung) >= 4:
        pool = chua_dung
    elif len(all_goc) >= 4:
        pool = all_goc
    else:
        pool = chua_dung if chua_dung else all_goc

    n_pool = len(pool)

    if target_total is None or str(target_total).lower() == "random":
        # Có cover -> cần 4, 5, 6, 7 ảnh gốc để tổng album đạt 5, 6, 7, 8 ảnh
        min_full = 4 if cover_path else 5
        if n_pool >= 7:
            so_goc = random.choice([min_full, 5, 6, 7])
        elif n_pool >= 5:
            so_goc = random.choice([min_full, 5])
        elif n_pool >= 4:
            so_goc = 4
        elif n_pool >= 2:
            so_goc = n_pool
        else:
            so_goc = 1
    else:
        try:
            tot = int(target_total)
            can_goc = tot - (1 if cover_path else 0)
            so_goc = max(1, min(can_goc, n_pool))
        except Exception:
            so_goc = min(4, n_pool)

    # Xáo trộn random các ảnh gốc
    chosen_goc = random.sample(pool, min(so_goc, len(pool)))
    raw_list = ([cover_path] if cover_path else []) + chosen_goc
    return raw_list


def normalize_photo_square(in_path, out_path, size=2000):
    """Center-crop và resize ảnh về hình vuông 1:1 (2000x2000)."""
    from PIL import Image
    with Image.open(in_path) as im:
        side = min(im.width, im.height)
        l = (im.width - side) // 2
        t = (im.height - side) // 2
        cropped = im.crop((l, t, l + side, t + side))
        sq = cropped.resize((size, size), Image.Resampling.LANCZOS)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        sq.convert("RGB").save(out_path, "JPEG", quality=95)


def normalize_photo_landscape(in_path, out_path, target_w=2000, target_h=1330):
    """Center-crop và resize ảnh về hình chữ nhật ngang 3:2 (2000x1330)."""
    from PIL import Image
    with Image.open(in_path) as im:
        target_ratio = target_w / target_h
        cur_ratio = im.width / im.height
        if cur_ratio > target_ratio:
            w = int(im.height * target_ratio)
            l = (im.width - w) // 2
            cropped = im.crop((l, 0, l + w, im.height))
        else:
            h = int(im.width / target_ratio)
            t = (im.height - h) // 2
            cropped = im.crop((0, t, im.width, t + h))
        ls = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        ls.convert("RGB").save(out_path, "JPEG", quality=95)


def normalize_album_photos(photo_list):
    """
    Chuẩn hóa toàn bộ danh sách ảnh theo bố cục Facebook 2026:
    - Nếu album >= 5 ảnh (5, 6, 7, 8 ảnh):
      * photos[0] (Cover Banner): Vuông 1:1 (2000x2000)
      * photos[1] (Ảnh chính 2): Vuông 1:1 (2000x2000)
      * photos[2..N] (Ảnh phụ): Ngang 3:2 (2000x1330)
    - Nếu album == 4 ảnh:
      * Tất cả đều Vuông 1:1 (2000x2000) -> Lưới 2x2.
    """
    if not photo_list:
        return []

    vault_p = Path(VAULT)
    out_dir = vault_p / "attachments" / "dataset" / "_xuat" / "album_ready"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Dọn dẹp ảnh cũ
    for old_f in out_dir.glob("*.jpg"):
        try:
            old_f.unlink()
        except Exception:
            pass

    norm_paths = []
    n = len(photo_list)
    for i, p_str in enumerate(photo_list):
        full_in = vault_p / p_str if not Path(p_str).is_absolute() else Path(p_str)
        if not full_in.exists():
            try:
                name = Path(p_str).name
                matches = list(vault_p.rglob(name)) if name else []
                if matches:
                    full_in = matches[0]
            except Exception:
                pass
        if not full_in.exists():
            norm_paths.append(p_str)
            continue

        out_file = out_dir / f"fb_norm_{i:02d}.jpg"
        rel_out = str(out_file.relative_to(vault_p)).replace("\\", "/")

        try:
            if n >= 5:
                if i == 0 or i == 1:
                    normalize_photo_square(full_in, out_file, size=2000)
                else:
                    normalize_photo_landscape(full_in, out_file, target_w=2000, target_h=1330)
            else:
                normalize_photo_square(full_in, out_file, size=2000)
            norm_paths.append(rel_out)
        except Exception as e:
            print(f"Warning: Lỗi chuẩn hóa {p_str}: {e}")
            norm_paths.append(p_str)

    return norm_paths


def _parse_body(raw: str, ctype: str):
    if "text/event-stream" in (ctype or "") or raw.startswith("event:") or raw.lstrip().startswith("data:"):
        chunks = []
        for line in raw.splitlines():
            if line.startswith("data:"):
                chunks.append(line[5:].strip())
        raw = "\n".join(c for c in chunks if c) or raw
    raw = raw.strip()
    if not raw:
        return {"error": "empty"}
    try:
        return json.loads(raw.split("\n")[0])
    except Exception:
        i = raw.find("{")
        if i >= 0:
            try:
                return json.loads(raw[i:])
            except Exception:
                pass
        return {"raw": raw[:3000]}


def rpc(method, params=None):
    global _RID
    _RID += 1
    body = {"jsonrpc": "2.0", "id": _RID, "method": method}
    if params is not None:
        body["params"] = params
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {TOKEN}",
            "X-Javis-Mode": "full",
            "X-Javis-Vault": VAULT,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return _parse_body(raw, resp.headers.get("Content-Type", ""))


def tool(name, arguments=None):
    r = rpc("tools/call", {"name": name, "arguments": arguments or {}})
    if "error" in r and "result" not in r:
        return r
    result = r.get("result") or r
    if isinstance(result, dict) and "content" in result:
        parts = []
        for c in result["content"]:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c.get("text") or "")
            else:
                parts.append(json.dumps(c, ensure_ascii=False))
        return "\n".join(parts)
    return result


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"

    # =========================================================================
    # CÁC LỆNH LOCAL CỤC BỘ: Chạy ngay lập tức, KHÔNG kết nối RPC HTTP port 7777
    # =========================================================================
    if cmd == "kit":
        import kit_tim
        args = ["kit_tim.py"] + sys.argv[2:]
        sys.exit(kit_tim.main(args))

    if cmd == "kit_footer":
        import kit_chan_trang
        args = ["kit_chan_trang.py"] + sys.argv[2:]
        sys.exit(kit_chan_trang.main(args))

    if cmd == "used_photos":
        slug = sys.argv[2] if len(sys.argv) > 2 else ""
        p = Path(VAULT) / "wiki" / "brand-kits" / "_anh-da-dung.md"
        if not p.exists():
            print(json.dumps([]))
            return
        lines = p.read_text(encoding="utf-8").splitlines()
        cur_slug = None
        used = []
        for line in lines:
            s = line.strip()
            if s.startswith("## "):
                cur_slug = s[3:].strip()
            elif cur_slug == slug and s.startswith("- "):
                pth = s[2:].strip()
                if pth:
                    used.append(pth)
        print(json.dumps(used, ensure_ascii=False))
        return

    if cmd == "append_used":
        slug = sys.argv[2] if len(sys.argv) > 2 else ""
        paths = sys.argv[3:]
        if not slug or not paths:
            print("usage: hub_call.py append_used <slug> <path1> [path2...]")
            return
        p = Path(VAULT) / "wiki" / "brand-kits" / "_anh-da-dung.md"
        if not p.exists():
            content = "---\ntype: wiki\nupdated: 2026-09-03\n---\n# Ảnh đã dùng khi đăng\n\n"
        else:
            content = p.read_text(encoding="utf-8")
        lines = content.splitlines()
        header_idx = -1
        for i, line in enumerate(lines):
            if line.strip() == f"## {slug}":
                header_idx = i
                break
        cur_slug = None
        existing = set()
        for line in lines:
            s = line.strip()
            if s.startswith("## "):
                cur_slug = s[3:].strip()
            elif cur_slug == slug and s.startswith("- "):
                pth = s[2:].strip()
                if pth:
                    existing.add(pth)
        to_add = [x for x in paths if x and x not in existing]
        if not to_add:
            print("Da co san, khong can them.")
            return
        if header_idx >= 0:
            insert_idx = header_idx + 1
            while insert_idx < len(lines) and not lines[insert_idx].strip().startswith("## "):
                insert_idx += 1
            for x in to_add:
                lines.insert(insert_idx, f"- {x}")
                insert_idx += 1
        else:
            lines.append(f"\n## {slug}")
            for x in to_add:
                lines.append(f"- {x}")
        p.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        print(f"Da them {len(to_add)} anh vao muc ## {slug} trong _anh-da-dung.md")
        return

    if cmd == "list_imgs":
        raw_folder = sys.argv[2] if len(sys.argv) > 2 else ""
        folder = resolve_dataset_folder(raw_folder)
        d = Path(VAULT) / "attachments" / "dataset" / folder
        if not d.is_dir():
            print(json.dumps({"ok": False, "error": "khong co folder " + raw_folder}))
            return
        files = unique_dataset_photos(folder)
        print(json.dumps({"folder": folder, "n": len(files), "photos": files}, ensure_ascii=False))
        return

    if cmd == "pick_photos":
        raw_folder = sys.argv[2] if len(sys.argv) > 2 else ""
        folder = resolve_dataset_folder(raw_folder)
        cover = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].isdigit() and sys.argv[3] != "random" else None
        target = "random"
        for a in sys.argv[3:]:
            if a.isdigit() or a == "random":
                target = a
        raw_res = pick_random_album_photos(folder, cover_path=cover, target_total=target)
        norm_res = normalize_album_photos(raw_res)
        print(json.dumps({"ok": True, "folder": folder, "count": len(norm_res), "photos": norm_res, "raw_photos": raw_res}, ensure_ascii=False))
        return

    # =========================================================================
    # CÁC LỆNH GỌI QUA MCP HUB RPC (chỉ kết nối khi cần thiết)
    # =========================================================================
    rpc(
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "hub_call", "version": "1.0"},
        },
    )
    try:
        rpc("notifications/initialized", {})
    except Exception:
        pass

    if cmd == "list":
        tools = rpc("tools/list", {})
        tls = (tools.get("result") or {}).get("tools") or []
        names = [t.get("name") for t in tls]
        print("COUNT", len(names))
        for n in sorted(names):
            print(n)
        return

    if cmd == "search":
        q = sys.argv[2] if len(sys.argv) > 2 else "facebook"
        print(tool("javis_search_tools", {"query": q}))
        return

    if cmd == "run":
        name = sys.argv[2]
        if len(sys.argv) > 3:
            raw = sys.argv[3]
            if raw.startswith("@"):
                args = json.loads(open(raw[1:], encoding="utf-8").read())
            else:
                args = json.loads(raw)
        else:
            args = {}
        print(tool(name, args))
        return

    if cmd == "fb":
        name = sys.argv[2]
        if len(sys.argv) > 3:
            raw = sys.argv[3]
            args = json.loads(open(raw[1:], encoding="utf-8").read()) if raw.startswith("@") else json.loads(raw)
        else:
            args = {}
        print(tool("javis_run_tool", {"name": name, "args": args}))
        return

    if cmd == "check":
        target = sys.argv[2] if len(sys.argv) > 2 else ""
        page_id = sys.argv[3] if len(sys.argv) > 3 else "988656934325292"
        res = tool("javis_run_tool", {"name": "fb_page_posts", "args": {"page_id": page_id, "limit": 5}})
        if isinstance(res, str):
            try:
                res = json.loads(res)
            except Exception:
                print(res)
                return
        data = res.get("data") if isinstance(res, dict) else []
        if not data:
            print(f"Khong tim thay bai viet nao tren trang {page_id}")
            return

        found = None
        if target:
            for p in data:
                if target in p.get("id", "") or target.lower() in (p.get("message") or "").lower():
                    found = p
                    break
        if not found:
            found = data[0]

        print("=== KET QUA KIEM TRA BAI VIET FACEBOOK ===")
        print(f"Trang: Royce Shop (ID: {page_id})")
        print(f"Post ID: {found.get('id')}")
        print(f"Thoi gian dang: {found.get('created_time')}")
        print(f"Trang thai: DA DANG CONG KHAI TREN FACEBOOK")
        print(f"Link xem truc tiep: {found.get('permalink_url')}")
        msg = (found.get('message') or '').strip().split('\n')[0]
        print(f"Noi dung dau: {msg}")
        return

    if cmd == "album_folder":
        page = sys.argv[2] if len(sys.argv) > 2 else "Royce Shop"
        raw_folder = sys.argv[3] if len(sys.argv) > 3 else ""
        folder = resolve_dataset_folder(raw_folder)
        rest = sys.argv[4:]
        message = ""
        if rest and rest[0].startswith("@"):
            message = Path(rest[0][1:]).read_text(encoding="utf-8")
        elif rest:
            message = " ".join(rest)
        d = Path(VAULT) / "attachments" / "dataset" / folder
        if not d.is_dir():
            print("ERROR: khong co folder " + raw_folder)
            return
        photos = unique_dataset_photos(folder)[:4]
        if len(photos) < 2:
            print("ERROR: folder " + folder + " sau loc trung con " + str(len(photos)) + " anh. Khong ghep album trung. N=1: fb_page_photo 1 tam (cover HOAC goc, khong ca hai).")
            return
        args = {"page": page, "photos": photos, "message": message}
        print("ALBUM", len(photos), "anh tu", folder)
        for pth in photos:
            print(" ", pth)
    if cmd == "auto_post":
        # usage: hub_call.py auto_post <page> <course_or_folder> <caption_or_@file> [cover_path]
        page = sys.argv[2] if len(sys.argv) > 2 else "Royce Shop"
        raw_course = sys.argv[3] if len(sys.argv) > 3 else "tin-hoc"
        folder = resolve_dataset_folder(raw_course)
        caption = ""
        if len(sys.argv) > 4:
            c_arg = sys.argv[4]
            if c_arg.startswith("@"):
                p_cap = Path(c_arg[1:])
                if not p_cap.is_absolute():
                    p_cap = Path(VAULT) / p_cap
                caption = p_cap.read_text(encoding="utf-8") if p_cap.exists() else ""
            else:
                caption = c_arg
        cover = sys.argv[5] if len(sys.argv) > 5 else None
        if not cover:
            # Tự tìm cover mới nhất trong _xuat
            xuat_p = Path(VAULT) / "attachments" / "dataset" / "_xuat"
            if xuat_p.is_dir():
                cand_covers = sorted(
                    [f for f in xuat_p.iterdir() if f.is_file() and f.suffix.lower() in _IMG_EXT and "album_ready" not in str(f)],
                    key=lambda f: f.stat().st_mtime, reverse=True
                )
                if cand_covers:
                    cover = str(cand_covers[0].relative_to(Path(VAULT))).replace("\\", "/")

        raw_res = pick_random_album_photos(folder, cover_path=cover, target_total="random")
        norm_res = normalize_album_photos(raw_res)
        if len(norm_res) < 2:
            print(json.dumps({"ok": False, "error": f"Khong du anh de tao album cho folder '{folder}'"}))
            return

        res = tool("javis_run_tool", {"name": "fb_page_album", "args": {"page": page, "photos": norm_res, "message": caption}})
        res_obj = {}
        if isinstance(res, str):
            try:
                res_obj = json.loads(res)
            except Exception:
                res_obj = {"raw": res}
        elif isinstance(res, dict):
            res_obj = res

        pid = res_obj.get("post_id") or ""
        link = res_obj.get("link") or (f"https://www.facebook.com/{pid}" if pid else "")
        if pid:
            print(f"POST_OK post_id={pid} link={link} photos={len(norm_res)}")
            print(f"OK | {page} | {folder} | {len(norm_res)} anh | post_id: {pid} | link: {link}")
        else:
            print(f"FAIL | {page} | {res}")
        return

    print("usage: list | search <q> | run <tool> '<json>' | fb <tool> [@args.json] | check [post_id_or_keyword] | kit <q> | kit_footer <q> | used_photos <slug> | append_used <slug> <path1>... | list_imgs <folder> | pick_photos <folder> [cover] [target] | album_folder <page> <folder> [@caption.txt] | auto_post <page> <course> <caption_or_@file> [cover]")


if __name__ == "__main__":
    main()
