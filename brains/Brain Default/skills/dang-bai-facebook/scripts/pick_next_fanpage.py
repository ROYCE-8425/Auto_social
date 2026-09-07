# -*- coding: utf-8 -*-
"""Chọn ĐÚNG 1 Fanpage + 1 thẻ khoá học cho vòng đăng hôm nay.

Luật:
- 1 ngày / 1 page / tối đa 1 bài OK.
- Fail: ghi skip, thử lại 1 lần sau >= 2 giờ; lần 2 fail thì bỏ page đó tới ngày mai.
- Không chọn page đã OK hôm nay.
- Thẻ lấy ngẫu nhiên trong Thẻ khoá học của kit (all = mọi id trong `_the-khoa-hoc.md`).

In ra khối NEXT=... để loop đọc. Không gọi Facebook.
"""
from __future__ import annotations

import json
import random
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TZ = ZoneInfo("Asia/Ho_Chi_Minh")
VAULT = Path(__file__).resolve().parents[3]
if VAULT.name != "Brain Default" and not (VAULT / "wiki" / "brand-kits").is_dir():
    VAULT = Path(__file__).resolve().parents[4]
KITS = VAULT / "wiki" / "brand-kits"
STATE = VAULT / "Javis" / "dang-hang-ngay.json"
SKIP_FILES = {"royce-shop.md"}  # test page: không vào hàng ngày trừ khi --include-royce


def registry_tags():
    """Mọi id trong wiki/brand-kits/_the-khoa-hoc.md — thêm ngành = thêm dòng bảng + folder."""
    p = KITS / "_the-khoa-hoc.md"
    ids = []
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|", line)
            if not m:
                continue
            tid = m.group(1).strip()
            if not tid or tid.lower() in ("id", "---") or set(tid) <= {"-"}:
                continue
            ids.append(tid)
    return ids or ["tin-hoc _ai", "do-hoa", "ke-toan", "ve-ky-thuat"]


def field(md, *labels):
    for lab in labels:
        m = re.search(r"^[ \t]*[-*][ \t]*" + re.escape(lab) + r":[ \t]*(.*)$", md, re.M)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def parse_tags(raw):
    raw = (raw or "").strip()
    if not raw or re.match(r"^(all|\*|full)$", raw, re.I):
        return list(registry_tags())
    parts = [p.strip() for p in re.split(r"[,;|/]+", raw) if p.strip()]
    out = []
    for p in parts:
        if re.match(r"^ve[\s_-]*ky[\s_-]*thuat$", p, re.I) or p == "VE KY THUAT":
            p = "ve-ky-thuat"
        if p not in out:
            out.append(p)
    return out or list(registry_tags())


def load_pages(include_royce=False):
    rows = []
    if not KITS.is_dir():
        return rows
    for p in sorted(KITS.glob("*.md")):
        if p.name.startswith("_"):
            continue
        if p.name in SKIP_FILES and not include_royce:
            continue
        md = p.read_text(encoding="utf-8")
        pid = field(md, "Page ID", "page_id")
        if not re.fullmatch(r"\d+", pid or ""):
            continue
        rows.append({
            "file": p.name,
            "slug": field(md, "slug") or p.stem,
            "name": field(md, "Tên Fanpage") or p.stem,
            "page_id": pid,
            "tags": parse_tags(field(md, "Thẻ khoá học")),
            "address": field(md, "Cơ sở / địa chỉ"),
            "hotline": field(md, "Hotline / Zalo", "Hotline riêng", "Hotline"),
            "email": field(md, "Email Fanpage", "Email"),
            "web": field(md, "Web Fanpage", "Web"),
            "logo": field(md, "Logo chính") or "attachments/dataset/chung/thsv-logo-2025.png",
            "logo_white": field(md, "Logo trắng") or "",
            "color_pri": field(md, "Màu chính") or "#6C3BFF",
            "color_sec": field(md, "Màu phụ") or "#00D4FF",
            "fonts": field(md, "Font") or "",
            "voice": field(md, "Tone of voice") or "",
            "layout": field(md, "Quy tắc bố cục") or "",
            "image_style": field(md, "Phong cách hình ảnh") or "",
            "donts": field(md, "Điều không được làm") or "",
        })
    return rows


def load_state(today):
    st = {"date": today, "ok": [], "skip": [], "cursor": 0}
    if STATE.exists():
        try:
            raw = json.loads(STATE.read_text(encoding="utf-8"))
            if raw.get("date") == today:
                st.update(raw)
                st["date"] = today
        except Exception:
            pass
    return st


def save_state(st):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv):
    now = datetime.now(TZ)
    today = now.strftime("%Y-%m-%d")
    include_royce = "--include-royce" in argv
    specific_page = None
    if "--page" in argv:
        i = argv.index("--page")
        specific_page = argv[i + 1] if i + 1 < len(argv) else ""

    mark_ok = None
    mark_fail = None
    reason = ""
    if "--ok" in argv:
        i = argv.index("--ok")
        mark_ok = argv[i + 1] if i + 1 < len(argv) else ""
    if "--fail" in argv:
        i = argv.index("--fail")
        mark_fail = argv[i + 1] if i + 1 < len(argv) else ""
        reason = " ".join(argv[i + 2 :]) if i + 2 < len(argv) else "POST_SKIP"

    if specific_page:
        all_pages = load_pages(include_royce=True)
        row = None
        try:
            sys.path.insert(0, str(Path(VAULT) / "scratch"))
            import kit_tim
            best = kit_tim.resolve_kit(specific_page)
            if best:
                row = next((p for p in all_pages if p["file"] == best["filename"]), None)
        except Exception:
            pass
        if not row:
            q_clean = specific_page.lower().strip()
            row = next((p for p in all_pages if q_clean in p["name"].lower() or q_clean in p["slug"].lower() or q_clean in p["file"].lower() or q_clean == p["page_id"]), None)
        if not row:
            print(f"ERROR: khong-tim-thay-page query={specific_page}")
            return 1
        tag = random.choice(row["tags"]) if row.get("tags") else "tin-hoc _ai"
        print("NEXT=1")
        print("page_id=" + row["page_id"])
        print("ten=" + row["name"])
        print("slug=" + row["slug"])
        print("kit=" + row["file"])
        print("the=" + tag)
        print("hotline=" + (row["hotline"] or ""))
        print("email=" + (row["email"] or ""))
        print("web=" + (row["web"] or ""))
        print("dia_chi=" + (row["address"] or ""))
        print("folder=attachments/dataset/" + tag + "/")
        print("luat_anh=album 5-8 anh neu du dataset: photos[0]=cover AI moi, photos[1..]=anh that dung folder; chi fb_page_photo khi khong du anh")
        print("doc_he_thong=FAST_PATH:skills/dang-bai-facebook/SKILL.md + đúng 1 brand kit; không đọc _y-chu/_quy-trinh/_the-khoa-hoc nếu không thiếu dữ liệu")
        print("logo=" + (row.get("logo") or ""))
        print("logo_white=" + (row.get("logo_white") or ""))
        print("mau_chinh=" + (row.get("color_pri") or ""))
        print("mau_phu=" + (row.get("color_sec") or ""))
        print("font=" + (row.get("fonts") or ""))
        print("giong=" + (row.get("voice") or ""))
        print("bo_cuc=" + (row.get("layout") or ""))
        print("phong_cach_anh=" + (row.get("image_style") or ""))
        print("cam=" + (row.get("donts") or ""))
        print("KIT_VISUAL")
        print("Dung dung logo file: " + (row.get("logo") or ""))
        print("Mau poster: " + (row.get("color_pri") or "") + " + " + (row.get("color_sec") or ""))
        print("Font: " + (row.get("fonts") or ""))
        print("Giong caption: " + (row.get("voice") or ""))
        print("Bo cuc: " + (row.get("layout") or ""))
        print("Phong cach anh: " + (row.get("image_style") or ""))
        print("Cam: " + (row.get("donts") or ""))
        print("HET_KIT_VISUAL")
        print("CHAN_TRANG")
        print(row["name"])
        if row.get("address"):
            for part in [p.strip() for p in row["address"].replace("|", "\n").splitlines() if p.strip()]:
                print(part)
        if row.get("hotline"):
            print("Hotline/Zalo: " + row["hotline"])
        if row.get("email"):
            print("Email: " + row["email"])
        if row.get("web"):
            print("Web: " + row["web"])
        print("HET_CHAN_TRANG")
        return 0

    pages = load_pages(include_royce=include_royce)
    st = load_state(today)

    if mark_ok:
        if mark_ok not in st["ok"]:
            st["ok"].append(mark_ok)
        if len(argv) > argv.index("--ok") + 2 and not argv[argv.index("--ok") + 2].startswith("-"):
            st["last_course"] = argv[argv.index("--ok") + 2].strip()
        st["skip"] = [x for x in st.get("skip") or [] if x.get("id") != mark_ok]
        save_state(st)
        print("MARK_OK", mark_ok)
        return 0
    if mark_fail:
        skips = list(st.get("skip") or [])
        prev = next((x for x in skips if x.get("id") == mark_fail), None)
        lan = int((prev or {}).get("lan") or 0) + 1
        hard = bool(re.search(
            r"chan-trang|khong-retry|chua-co-brand-kit|khong-dung-the",
            reason, re.I))
        retry_at = (now + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
        rec = {"id": mark_fail, "ly_do": reason[:200], "lan": lan, "retry_after": retry_at}
        skips = [x for x in skips if x.get("id") != mark_fail]
        if hard or lan >= 2:
            rec["retry_after"] = today + " 23:59"
            rec["bo_toi_mai"] = True
            rec["lan"] = max(lan, 2)
        skips.append(rec)
        st["skip"] = skips
        save_state(st)
        print("MARK_FAIL", json.dumps(rec, ensure_ascii=False))
        return 0

    ok = set(st.get("ok") or [])
    skip_map = {x.get("id"): x for x in (st.get("skip") or []) if x.get("id")}
    eligible = []
    for row in pages:
        pid = row["page_id"]
        if pid in ok:
            continue
        sk = skip_map.get(pid)
        if sk:
            if sk.get("bo_toi_mai"):
                continue
            ra = sk.get("retry_after") or ""
            try:
                ra_dt = datetime.strptime(ra, "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
            except ValueError:
                ra_dt = now
            if now < ra_dt:
                continue
        eligible.append(row)
    n_all = len(pages)
    print("HANG_NGAY date=" + today)
    print("tong_page=" + str(n_all) + " da_ok=" + str(len(ok)) + " cho=" + str(len(eligible)))
    if not eligible:
        print("NEXT=NONE het-hang-hom-nay")
        return 0
    cur = int(st.get("cursor") or 0) % len(eligible)
    row = eligible[cur]
    st["cursor"] = (cur + 1) % max(len(eligible), 1)
    save_state(st)
    last_tag = st.get("last_course") or ""
    all_tags = row.get("tags") or list(registry_tags())
    available_tags = [t for t in all_tags if t != last_tag] if len(all_tags) > 1 else all_tags
    tag = random.choice(available_tags or all_tags)
    print("NEXT=1")
    print("page_id=" + row["page_id"])
    print("ten=" + row["name"])
    print("slug=" + row["slug"])
    print("kit=" + row["file"])
    print("the=" + tag)
    print("hotline=" + (row["hotline"] or ""))
    print("email=" + (row["email"] or ""))
    print("web=" + (row["web"] or ""))
    print("dia_chi=" + (row["address"] or ""))
    print("folder=attachments/dataset/" + tag + "/")
    print("luat_anh=album 5-8 anh neu du dataset: photos[0]=cover AI moi, photos[1..]=anh that dung folder; chi fb_page_photo khi khong du anh")
    print("doc_he_thong=FAST_PATH:skills/dang-bai-facebook/SKILL.md + đúng 1 brand kit; không đọc _y-chu/_quy-trinh/_the-khoa-hoc nếu không thiếu dữ liệu")
    print("logo=" + (row.get("logo") or ""))
    print("logo_white=" + (row.get("logo_white") or ""))
    print("mau_chinh=" + (row.get("color_pri") or ""))
    print("mau_phu=" + (row.get("color_sec") or ""))
    print("font=" + (row.get("fonts") or ""))
    print("giong=" + (row.get("voice") or ""))
    print("bo_cuc=" + (row.get("layout") or ""))
    print("phong_cach_anh=" + (row.get("image_style") or ""))
    print("cam=" + (row.get("donts") or ""))
    print("KIT_VISUAL")
    print("Dung dung logo file: " + (row.get("logo") or ""))
    print("Mau poster: " + (row.get("color_pri") or "") + " + " + (row.get("color_sec") or ""))
    print("Font: " + (row.get("fonts") or ""))
    print("Giong caption: " + (row.get("voice") or ""))
    print("Bo cuc: " + (row.get("layout") or ""))
    print("Phong cach anh: " + (row.get("image_style") or ""))
    print("Cam: " + (row.get("donts") or ""))
    print("HET_KIT_VISUAL")
    print("CHAN_TRANG")
    print(row["name"])
    if row.get("address"):
        for part in [p.strip() for p in row["address"].replace("|", "\n").splitlines() if p.strip()]:
            print(part)
    if row.get("hotline"):
        print("Hotline/Zalo: " + row["hotline"])
    if row.get("email"):
        print("Email: " + row["email"])
    if row.get("web"):
        print("Web: " + row["web"])
    print("HET_CHAN_TRANG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
