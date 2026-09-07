# -*- coding: utf-8 -*-
"""Gọi tool qua Javis hub MCP (JSON-RPC)."""
import json
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


def unique_dataset_photos(folder, skip_names=None):
    """Anh goc khong trung hash, bo file Windows ' (1)' / copy."""
    import hashlib
    import re
    skip_names = {str(x).replace("\\", "/").split("/")[-1].lower() for x in (skip_names or [])}
    folder = str(folder or "").replace("tin-hoc/_ai", "tin-hoc _ai").replace("tin-hoc_ai", "tin-hoc _ai")
    if folder.strip("/") in ("tin-hoc",):
        folder = "tin-hoc _ai"
    d = Path(VAULT) / "attachments" / "dataset" / folder
    if not d.is_dir():
        return []
    seen_hash = set()
    out = []
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
        h = hashlib.md5(p.read_bytes()).hexdigest()
        if h in seen_hash:
            continue
        seen_hash.add(h)
        out.append(f"attachments/dataset/{folder}/{p.name}")
    return out


def pick_random_album_photos(folder, cover_path=None, target_total=None):
    """
    Chon ngau nhien so luong anh goc tu folder de ghep voi cover_path.
    Muc tieu tong so anh: 5, 6, 7, hoac 8 anh khi co cover.
    Uu tien anh goc chua tung dung trong _anh-da-dung.md.
    """
    import random
    skip = []
    if cover_path:
        skip.append(cover_path)
    cover_inner_file = Path(VAULT) / "attachments/dataset/_xuat/cover_inner_photo.txt"
    if cover_inner_file.exists():
        inner_name = cover_inner_file.read_text(encoding="utf-8").strip().replace("\\", "/").split("/")[-1].lower()
        if inner_name:
            skip.append(inner_name)
    all_goc = unique_dataset_photos(folder, skip_names=skip)
    if not all_goc:
        return [cover_path] if cover_path else []

    # Uu tien anh chua dung
    used_file = Path(VAULT) / "wiki" / "brand-kits" / "_anh-da-dung.md"
    used_set = set()
    if used_file.exists():
        for l in used_file.read_text(encoding="utf-8").splitlines():
            if l.strip().startswith("- "):
                used_set.add(l.strip()[2:].strip().replace("\\", "/").split("/")[-1].lower())

    # Kiem tra anh da ghep vao cover (neu co) de tranh trung lap
    cover_inner_file = Path(VAULT) / "attachments/dataset/_xuat/cover_inner_photo.txt"
    if cover_inner_file.exists():
        inner_name = cover_inner_file.read_text(encoding="utf-8").strip().replace("\\", "/").split("/")[-1].lower()
        if inner_name:
            used_set.add(inner_name)

    # Bo qua anh da dung (neu du anh moi)
    chua_dung = [p for p in all_goc if p.replace("\\", "/").split("/")[-1].lower() not in used_set]

    n_goc = len(chua_dung) if len(chua_dung) >= 3 else len(all_goc)
    pool = chua_dung if len(chua_dung) >= 3 else all_goc

    if target_total is None or str(target_total).lower() == "random":
        # Neu co cover, so_goc 4/5/6/7 -> tong album 5/6/7/8 anh.
        # Neu khong co cover, giu album raw tuong ung 5/6/7/8 neu du anh.
        min_full = 4 if cover_path else 5
        if n_goc >= 7:
            so_goc = random.choice([min_full, 5, 6, 7])
        elif n_goc >= 5:
            so_goc = random.choice([min_full, 5])
        elif n_goc >= 4:
            so_goc = 4
        elif n_goc >= 2:
            so_goc = n_goc
        else:
            so_goc = 1
    else:
        try:
            tot = int(target_total)
            can_goc = tot - (1 if cover_path else 0)
            so_goc = max(1, min(can_goc, n_goc))
        except Exception:
            so_goc = min(3, n_goc)

    # Xao tron random cac anh goc de moi bai la mot tap anh khac nhau
    chosen_goc = random.sample(pool, min(so_goc, len(pool)))
    raw_list = ([cover_path] if cover_path else []) + chosen_goc
    return raw_list


def normalize_photo_square(in_path, out_path, size=2000):
    """Center-crop va resize anh ve hinh vuong 1:1 (2000x2000)."""
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
    """Center-crop va resize anh ve hinh chu nhat ngang 3:2 (2000x1330)."""
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
    Chuan hoa toan bo danh sach anh theo dung bo cuc Facebook 2026:
    - Neu album >= 5 anh (5, 6, 7, 8 anh):
      * photos[0] (Cover Banner): Vuong 1:1 (2000x2000)
      * photos[1] (Anh chinh 2): Vuong 1:1 (2000x2000)
      * photos[2..N] (Anh phu): Ngang 3:2 (2000x1330)
      -> Ket qua hien thi tren Facebook: Cot trai 2 anh vuong, cot phai 3 anh ngang khit cao!
    - Neu album == 4 anh (fallback khi dataset it anh):
      * Tat ca deu Vuong 1:1 (2000x2000) -> Facebook hien thi luoi 2x2 vuong deu hoan hao.
    """
    from pathlib import Path
    if not photo_list:
        return []

    vault_p = Path(VAULT)
    out_dir = vault_p / "attachments" / "dataset" / "_xuat" / "album_ready"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Don dep anh cu
    for old_f in out_dir.glob("*.jpg"):
        try:
            old_f.unlink()
        except Exception:
            pass

    norm_paths = []
    n = len(photo_list)
    for i, p_str in enumerate(photo_list):
        full_in = vault_p / p_str if not Path(p_str).is_absolute() else Path(p_str)
        # Một số tool trả về đường dẫn tương đối theo brain/workdir thay vì
        # theo gốc vault. Thử tìm lại đúng file theo basename để không truyền
        # đường dẫn "ma" sang fb_page_album.
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
            print(f"Warning: Loi chuan hoa {p_str}: {e}")
            norm_paths.append(p_str)

    return norm_paths


def _parse_body(raw: str, ctype: str):
    if "text/event-stream" in (ctype or "") or raw.startswith("event:") or raw.lstrip().startswith("data:"):
        chunks = []
        for line in raw.splitlines():
            if line.startswith("data:"):
                chunks.append(line[5:].strip())
        raw = "\n".join(c for c in chunks if c) or raw
    # lấy object JSON đầu
    raw = raw.strip()
    if not raw:
        return {"error": "empty"}
    try:
        return json.loads(raw.split("\n")[0])
    except Exception:
        # thử tìm { ... }
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
    # MCP wraps content
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

    if cmd == "kit":
        import kit_tim
        args = ["kit_tim.py"] + sys.argv[2:]
        sys.exit(kit_tim.main(args))

    if cmd == "kit_footer":
        import kit_chan_trang
        args = ["kit_chan_trang.py"] + sys.argv[2:]
        sys.exit(kit_chan_trang.main(args))

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
        # shortcut: fb <tool> [@args.json | inline json]
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
        # Lấy các bài gần đây để kiểm tra
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
        folder = sys.argv[2] if len(sys.argv) > 2 else ""
        d = Path(VAULT) / "attachments" / "dataset" / folder
        if not d.is_dir():
            print(json.dumps({"ok": False, "error": "khong co folder " + folder}))
            return
        files = unique_dataset_photos(folder)
        print(json.dumps({"folder": folder, "n": len(files), "photos": files}, ensure_ascii=False))
        return

    if cmd == "pick_photos":
        folder = sys.argv[2] if len(sys.argv) > 2 else ""
        cover = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].isdigit() and sys.argv[3] != "random" else None
        target = "random"
        for a in sys.argv[3:]:
            if a.isdigit() or a == "random":
                target = a
        raw_res = pick_random_album_photos(folder, cover_path=cover, target_total=target)
        # Tu dong chuan hoa toan bo anh ve dung ti le vang Facebook 2026 (1:1 vuong cho anh 1 va 2, 3:2 ngang cho cac anh con lai)
        norm_res = normalize_album_photos(raw_res)
        print(json.dumps({"ok": True, "folder": folder, "count": len(norm_res), "photos": norm_res, "raw_photos": raw_res}, ensure_ascii=False))
        return

    if cmd == "album_folder":
        page = sys.argv[2] if len(sys.argv) > 2 else "Royce Shop"
        folder = sys.argv[3] if len(sys.argv) > 3 else ""
        rest = sys.argv[4:]
        message = ""
        if rest and rest[0].startswith("@"):
            message = Path(rest[0][1:]).read_text(encoding="utf-8")
        elif rest:
            message = " ".join(rest)
        d = Path(VAULT) / "attachments" / "dataset" / folder
        if not d.is_dir():
            print("ERROR: khong co folder " + folder)
            return
        photos = unique_dataset_photos(folder)[:4]
        if len(photos) < 2:
            print("ERROR: folder " + folder + " sau loc trung con " + str(len(photos)) + " anh. Khong ghep album trung. N=1: fb_page_photo 1 tam (cover HOAC goc, khong ca hai).")
            return
        args = {"page": page, "photos": photos, "message": message}
        print("ALBUM", len(photos), "anh tu", folder)
        for pth in photos:
            print(" ", pth)
        print(tool("javis_run_tool", {"name": "fb_page_album", "args": args}))
        return

    print("usage: list | search <q> | run <tool> '<json>' | fb <tool> [@args.json] | check [post_id_or_keyword] | kit <q> | kit_footer <q> | used_photos <slug> | append_used <slug> <path1>... | list_imgs <folder> | album_folder <page> <folder> [@caption.txt]")


if __name__ == "__main__":
    main()
