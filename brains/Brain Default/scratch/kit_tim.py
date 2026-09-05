# -*- coding: utf-8 -*-
"""Công cụ tìm kiếm và khớp mờ thông minh Brand Kit Fanpage.

Tự động tìm ra file Brand Kit phù hợp nhất từ bất kỳ từ khóa, tên rút gọn,
tên cơ sở, slug, ngành học hoặc Page ID.

Ví dụ:
  python "brains/Brain Default/scratch/kit_tim.py" "royce"
  python "brains/Brain Default/scratch/kit_tim.py" "thủ đức"
  python "brains/Brain Default/scratch/kit_tim.py" "cad biên hòa"
  python "brains/Brain Default/scratch/kit_tim.py" "kế toán quận 7"
  python "brains/Brain Default/scratch/kit_tim.py" 988656934325292
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

VAULT = Path(__file__).resolve().parents[1]
KITS_DIR = VAULT / "wiki" / "brand-kits"

# Bảng bí danh thường gặp để tìm siêu tốc
ALIASES = {
    "royce": "royce-shop.md",
    "royceshop": "royce-shop.md",
    "royce shop": "royce-shop.md",
    "page royce": "royce-shop.md",
    "thsv": "trung-tam-tin-hoc-sao-viet-tp-thu-uc-tphcm.md",
    "sao viet": "_mac-dinh.md",
}

# Các nhóm ngành chính
SUBJECT_MAP = {
    "cad": ["autocad", "co-khi", "solidworks", "cad"],
    "autocad": ["autocad", "co-khi", "cad"],
    "ke toan": ["ke-toan", "ketoan", "misa", "thue"],
    "tin hoc": ["tin-hoc", "tinhoc", "van-phong", "excel", "word", "mos"],
    "do hoa": ["do-hoa", "thiet-ke", "photoshop", "illustrator"],
    "ai": ["ai", "tri-tue-nhan-tao", "agent"],
}

# Các địa danh cơ sở
LOCATIONS = [
    "quan 7", "q7", "quan 6", "q6", "quan 12", "q12",
    "tan binh", "binh thanh", "thu duc", "quan 9", "q9",
    "di an", "thuan an", "thu dau mot", "tdm", "tan uyen",
    "bien hoa", "long thanh", "dong nai", "binh duong",
    "vung tau", "ba ria",
]


def remove_accents(text: str) -> str:
    """Loại bỏ dấu tiếng Việt và chuẩn hóa về chữ thường."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[àáảãạâầấẩẫậăằắẳẵặ]", "a", text)
    text = re.sub(r"[èéẻẽẹêềếểễệ]", "e", text)
    text = re.sub(r"[ìíỉĩị]", "i", text)
    text = re.sub(r"[òóỏõọôồốổỗộơờớởỡợ]", "o", text)
    text = re.sub(r"[ùúủũụưừứửữự]", "u", text)
    text = re.sub(r"[ỳýỷỹỵ]", "y", text)
    text = re.sub(r"[đ]", "d", text)
    # Loại bỏ dấu kết hợp nếu còn
    nfkd = unicodedata.normalize("NFKD", text)
    text = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return text


def clean_tokens(text: str) -> list[str]:
    """Tách từ khóa sạch từ văn bản."""
    norm = remove_accents(text)
    words = re.findall(r"[a-z0-9]+", norm)
    # Loại bỏ các từ chung chung không mang ý nghĩa nhận diện
    stop_words = {"trung", "tam", "dao", "tao", "sao", "viet", "fanpage", "page", "bai", "viet", "khoa", "hoc", "cho", "tren", "cua", "tphcm", "tp", "hcm"}
    return [w for w in words if w not in stop_words]


def get_field(md: str, *labels: str) -> str:
    """Lấy giá trị trường từ markdown."""
    for lab in labels:
        m = re.search(r"^[ \t]*[-*][ \t]*" + re.escape(lab) + r":[ \t]*(.*)$", md, re.M)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def build_footer(md: str, name: str) -> str:
    """Tạo khối chân trang từ thông tin trong kit."""
    addr = get_field(md, "Cơ sở / địa chỉ")
    parts = [a.strip() for a in addr.split("|") if a.strip()] if addr else []
    hot = get_field(md, "Hotline / Zalo", "Hotline riêng", "Hotline")
    email = get_field(md, "Email Fanpage", "Email")
    web = get_field(md, "Web Fanpage", "Web")
    lines = [name] if name else []
    lines.extend(parts)
    if hot:
        lines.append("Hotline/Zalo: " + hot)
    if email:
        lines.append("Email: " + email)
    if web:
        lines.append("Web: " + web)
    return "\n".join(lines)


def load_all_kits() -> list[dict]:
    """Đọc toàn bộ brand kits hiện có trong vault."""
    kits = []
    if not KITS_DIR.is_dir():
        return kits
    for p in sorted(KITS_DIR.glob("*.md")):
        if p.name.startswith("_"):
            continue
        try:
            md = p.read_text(encoding="utf-8")
        except Exception:
            continue
        page_id = get_field(md, "Page ID", "page_id", "ID Fanpage", "ID Trang")
        page_name = get_field(md, "Tên Fanpage") or p.stem
        slug = get_field(md, "slug") or p.stem
        address = get_field(md, "Cơ sở / địa chỉ")
        tags = get_field(md, "Thẻ khoá học") or "all"
        hotline = get_field(md, "Hotline / Zalo", "Hotline riêng", "Hotline")
        email = get_field(md, "Email Fanpage", "Email")
        web = get_field(md, "Web Fanpage", "Web")

        kits.append({
            "path": p,
            "filename": p.name,
            "stem": p.stem,
            "page_id": page_id,
            "page_name": page_name,
            "slug": slug,
            "address": address,
            "tags": tags,
            "hotline": hotline,
            "email": email,
            "web": web,
            "md": md,
            "norm_stem": remove_accents(p.stem),
            "norm_name": remove_accents(page_name),
            "norm_addr": remove_accents(address),
            "tokens": set(clean_tokens(p.stem + " " + page_name + " " + address)),
        })
    return kits


def search_kits(query: str, kits: list[dict] | None = None) -> list[dict]:
    """Tìm và xếp hạng các brand kits theo độ khớp với câu truy vấn."""
    if kits is None:
        kits = load_all_kits()

    raw_q = str(query or "").strip()
    norm_q = remove_accents(raw_q)
    q_tokens = set(clean_tokens(raw_q))

    # Kiểm tra tra cứu nhanh theo ALIASES
    alias_target = ALIASES.get(norm_q)
    if not alias_target and norm_q.replace("-", " ") in ALIASES:
        alias_target = ALIASES[norm_q.replace("-", " ")]

    scored = []
    for k in kits:
        score = 0
        reasons = []

        # 1. Khớp Page ID chính xác
        if raw_q.isdigit() and k["page_id"] == raw_q:
            score += 1000
            reasons.append("Chính xác Page ID")

        # 2. Khớp Alias
        if alias_target and (k["filename"] == alias_target or k["stem"] == alias_target.replace(".md", "")):
            score += 950
            reasons.append(f"Khớp bí danh '{norm_q}'")

        # 3. Khớp chính xác tên file/slug hoặc tên page
        if norm_q == k["norm_stem"] or norm_q == k["slug"]:
            score += 800
            reasons.append("Chính xác slug/tên file")
        elif norm_q == k["norm_name"]:
            score += 750
            reasons.append("Chính xác Tên Fanpage")

        # 4. Truy vấn nằm trong tên file hoặc ngược lại
        if norm_q and (norm_q in k["norm_stem"] or k["norm_stem"] in norm_q):
            score += 350
            reasons.append("Chuỗi con tên file")
        if norm_q and (norm_q in k["norm_name"] or k["norm_name"] in norm_q):
            score += 300
            reasons.append("Chuỗi con tên Fanpage")

        # 5. Khớp địa danh (Location matching)
        for loc in LOCATIONS:
            if loc in norm_q:
                # Nếu truy vấn có địa danh này, kiểm tra kit có chứa không
                if loc in k["norm_stem"] or loc in k["norm_name"] or loc in k["norm_addr"]:
                    score += 180
                    reasons.append(f"Khớp địa danh: {loc}")

        # 6. Khớp ngành học (Subject matching)
        for subj, keywords in SUBJECT_MAP.items():
            subj_in_q = any(kw in norm_q for kw in keywords)
            if subj_in_q:
                subj_in_kit = any(kw in k["norm_stem"] or kw in k["norm_name"] or kw in k["tags"] for kw in keywords)
                if subj_in_kit:
                    score += 160
                    reasons.append(f"Khớp ngành: {subj}")
                else:
                    # Truy vấn rõ ngành mà kit khác ngành thì trừ điểm nhẹ để không chọn nhầm
                    score -= 40

        # 7. Khớp từ khóa lẻ (Token overlap)
        overlap = q_tokens.intersection(k["tokens"])
        if overlap:
            token_score = len(overlap) * 40
            score += token_score
            reasons.append(f"Trùng {len(overlap)} từ: {', '.join(overlap)}")

        if score > 0:
            scored.append({
                **k,
                "score": score,
                "reasons": reasons,
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def resolve_kit(query: str) -> dict | None:
    """Trả về Brand Kit khớp nhất. None nếu không tìm thấy gì."""
    results = search_kits(query)
    if results:
        return results[0]
    return None


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Cú pháp: kit_tim.py <từ_khóa_hoặc_page_id> [--json]", file=sys.stderr)
        return 2

    query = argv[1]
    is_json = "--json" in argv

    results = search_kits(query)
    if not results:
        if is_json:
            print(json.dumps({"ok": False, "error": f"Không tìm thấy kit phù hợp cho '{query}'"}, ensure_ascii=False))
        else:
            print(f"ERROR: Không tìm thấy Brand Kit nào phù hợp với từ khóa: '{query}'")
        return 1

    top = results[0]
    footer = build_footer(top["md"], top["page_name"])

    if is_json:
        data = {
            "ok": True,
            "query": query,
            "best_match": {
                "file": top["filename"],
                "path": str(top["path"]),
                "page_id": top["page_id"],
                "page_name": top["page_name"],
                "slug": top["slug"],
                "tags": top["tags"],
                "score": top["score"],
                "reasons": top["reasons"],
                "hotline": top["hotline"],
                "email": top["email"],
                "web": top["web"],
            },
            "footer": footer,
            "candidates_count": len(results),
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    print("KIT_MATCH")
    print(f"file={top['filename']}")
    print(f"page_id={top['page_id']}")
    print(f"page_name={top['page_name']}")
    print(f"slug={top['slug']}")
    print(f"tags={top['tags']}")
    print(f"score={top['score']} ({'; '.join(top['reasons'])})")
    print("CHAN_TRANG")
    print(footer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
