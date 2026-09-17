"""Module phân loại bình luận Fanpage (deterministic, pure Python).

0-token preflight: phân loại hoàn toàn bằng Python (regex + keyword rules),
không gọi LLM, không I/O mạng.
Trả về: {
  "class": "faq|lead|spam|toxic|khen|ky_thuat|ambiguous|ignore",
  "faq_intent": "hoc_phi|lich_hoc|dia_chi|khai_giang|zalo|null",
  "confidence": 0.0-1.0,
  "phones": ["0901234567"],
  "course_hints": ["tin-hoc"],
  "wants_zalo": bool,
  "reasons": ["phone_regex", "kw:hoc_phi"]
}
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

# Regex chuẩn số điện thoại Việt Nam 10 số (0[35789]xxxxxxxx)
# Loại trừ dãy số nằm giữa các chữ số khác (MST, Page ID, dãy số dài)
VN_PHONE_RE = re.compile(
    r'(?<!\d)(?:(?:\+?84)|0)\s*[3-9](?:[\s.\-]*\d){8}(?!\d)'
)

# URL rút gọn thường dùng trong spam
SHORT_URL_RE = re.compile(
    r'(?:https?://)?(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|fb\.me|cutt\.ly|shorturl\.at)/\S+',
    re.IGNORECASE
)

# Ký tự lặp spam: 7 ký tự liên tiếp giống nhau
REPEATED_CHAR_RE = re.compile(r'(.)\1{6,}')

# Toxic keywords (chửi tục, lừa đảo vu khống nặng)
TOXIC_KEYWORDS = [
    "đm", "dm", "dcm", "vcl", "đmm", "dmm", "clmm",
    "lua dao", "lừa đảo", "lua dao trang tron", "cho de", "chó đẻ",
    "suc sinh", "súc sinh", "mat day", "mất dạy", "luon leo", "lươn lẹo"
]

# Spam keywords (tài chính đen, 18+, cờ bạc, crypto)
SPAM_KEYWORDS = [
    "forex", "crypto", "bitcoin", "casino", "viagra",
    "keo bong", "kèo bóng", "tai xiu", "tài xỉu", "nap rut", "nạp rút",
    "danh bac", "đánh bạc", "gai goi", "gái gọi", "vay tien", "cho vay nang lai"
]

# Lead keywords (muốn học / đăng ký / tư vấn)
LEAD_KEYWORDS = [
    "muon hoc", "muốn học", "dang ky", "đăng ký", "dk hoc", "đk học",
    "xin sdt", "xin sđt", "xin so", "xin số", "nhan tu van", "nhận tư vấn",
    "hoc thu", "học thử", "khai giang lop", "khai giảng lớp",
    "tu van giup", "tư vấn giúp", "tu van cho minh", "tư vấn cho mình",
    "tu van cho em", "tư vấn cho em", "inbox em dang ky", "inbox em đăng ký",
    "em can tu van", "em cần tư vấn", "minh can tu van", "mình cần tư vấn"
]

# Course hints mapping
COURSE_KEYWORDS = {
    "tin-hoc": ["tin hoc", "van phong", "excel", "word", "powerpoint", "mos", "ic3", "vba", "macro"],
    "ke-toan": ["ke toan", "misa", "thue", "bao cao tai chinh", "bctc"],
    "do-hoa": ["do hoa", "photoshop", "illustrator", "pts", "corel", "indesign", "canva", "premiere"],
    "ve-ky-thuat": ["autocad", "cad", "solidworks", "sketchup", "revit", "3ds max", "ve ky thuat", "2d", "3d"]
}

# Technical keywords for class ky_thuat
TECH_SUBJECTS = [
    "excel", "vlookup", "hlookup", "xlookup", "index", "match", "sumif", "countif",
    "autocad", "cad", "misa", "photoshop", "illustrator", "solidworks", "sketchup",
    "ham", "hàm", "lenh", "lệnh", "cong thuc", "công thức", "phim tat", "phím tắt"
]

TECH_PROBLEM_INDICATORS = [
    "?", "loi", "lỗi", "lam sao", "làm sao", "the nao", "thế nào",
    "tai sao", "tại sao", "sua the nao", "sửa thế nào", "khong duoc", "không được",
    "bi giat", "bị giật", "khong chay", "không chạy", "khong hien", "không hiện", "#n/a", "#value"
]

# BSN Game keywords mapping
BSN_PRODUCT_KEYWORDS = {
    "key-steam": ["steam", "key steam", "steam key", "key", "game steam", "wukong", "elden ring", "gta", "fifa", "fc24", "fc25", "rdr2", "cyberpunk"],
    "tai-khoan": ["tai khoan", "acc", "account", "offline", "share acc", "family share", "family"],
    "bao-hanh": ["bao hanh", "bh", "doi pass", "mat pass", "loi pass", "bao hanh tron doi"],
    "viet-hoa": ["viet hoa", "tieng viet", "sub viet", "patch viet hoa"],
}

BSN_LEAD_KEYWORDS = [
    "mua key", "mua game", "inbox mua", "ib mua", "muon mua", "order game", "lay game",
    "mua acc", "mua tai khoan", "lay acc", "muon lay game", "lay ban nay", "inbox em mua",
    "ib em mua", "can mua", "cho em mua", "con key khong", "con game khong", "lay game nay",
    "check ib", "ib minh", "inbox minh", "ib em", "inbox em", "ib nhe", "inbox nhe",
]

BSN_FAQ_BAO_HANH_KEYWORDS = [
    "bao hanh", "bh the nao", "bh bao lau", "loi key", "loi pass", "bi vang", "loi game",
    "khong vao duoc game", "doi pass", "mat pass", "bao hanh tron doi", "chinh sach bao hanh"
]

BSN_FAQ_KEY_STEAM_KEYWORDS = [
    "key steam", "steam key", "steam", "tai khoan steam", "acc steam", "offline",
    "share acc", "family share", "choi offline", "choi online", "kich hoat steam", "kich hoat"
]

BSN_FAQ_VIET_HOA_KEYWORDS = [
    "viet hoa", "tieng viet", "patch viet hoa", "co viet hoa khong", "cai viet hoa", "sub viet"
]

BSN_FAQ_CAI_DAT_KEYWORDS = [
    "cai the nao", "huong dan cai", "link tai", "drive", "dung luong", "tai qua dau",
    "tai game the nao", "cai dat the nao"
]

BSN_FAQ_GIA_KEYWORDS = [
    "gia ca", "gia sao", "bao nhieu tien", "bao nhieu k", "gia the nao", "uy tin",
    "gia bn", "gia bao nhieu", "bao nhieu shop", "nhiu tien", "gia sao", "nhieu tien",
    "gia the nao", "bao nhieu a", "bao nhieu vay", "bao gia", "gia sao shop"
]

BSN_TECH_KEYWORDS = [
    "crash", "vang game", "man hinh den", "directx", "card man hinh", "cau hinh",
    "ram", "fps drop", "lag", "loi dll", "khong vao duoc", "fix loi"
]

SAOVIET_TT_LEAD_KEYWORDS = [
    "ib bio", "inbox bio", "link bio", "check bio", "xem bio", "vao bio", "ib em",
    "inbox em", "tu van em", "nhan tin bio", "qua bio", "link o dau", "bio o dau"
]


def detect_bsn_hints(text_folded: str) -> list[str]:
    """Nhận diện thể loại / sản phẩm game BSN được nhắc đến."""
    hints = []
    for cat, kws in BSN_PRODUCT_KEYWORDS.items():
        if any(kw in text_folded for kw in kws):
            hints.append(cat)
    return hints


# Praise keywords
PRAISE_KEYWORDS = [
    "hay qua", "hay quá", "cam on", "cảm ơn", "tuyet voi", "tuyệt vời",
    "bai viet hay", "bài viết hay", "huu ich", "hữu ích", "thanks", "thx",
    "tuyet", "tuyệt", "xuat sac", "xuất sắc", "qua hay", "quá hay"
]

PRAISE_EMOJIS = ["👍", "👏", "❤️", "👌", "💯", "🎉", "🔥", "🙏"]


def normalize_vn_phone(raw: str) -> str:
    """Rút gọn số điện thoại VN về chuẩn 10 chữ số bắt đầu bằng 0."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("84") and len(digits) == 11:
        digits = "0" + digits[2:]
    elif digits.startswith("+84") and len(digits) == 12:
        digits = "0" + digits[3:]
    return digits


def extract_vn_phones(text: str) -> list[str]:
    """Tìm tất cả số điện thoại VN hợp lệ trong văn bản."""
    if not text:
        return []
    matches = VN_PHONE_RE.findall(text)
    phones = []
    seen = set()
    for m in matches:
        p = normalize_vn_phone(m)
        if len(p) == 10 and p.startswith("0") and p not in seen:
            seen.add(p)
            phones.append(p)
    return phones


def fold_text(s: str) -> str:
    """Bỏ dấu tiếng Việt, đưa về chữ thường để so khớp keyword."""
    s = unicodedata.normalize("NFD", s or "").lower()
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    return re.sub(r"\s+", " ", s).strip()


def detect_course_hints(text_folded: str) -> list[str]:
    """Nhận diện ngành / khóa học được nhắc đến."""
    hints = []
    for course, kws in COURSE_KEYWORDS.items():
        if any(kw in text_folded for kw in kws):
            hints.append(course)
    return hints


# Question word patterns with word boundaries to prevent substring matching
QUESTION_WORDS_RE = re.compile(
    r'(?:\?|\b(khong|the nao|lam sao|tai sao|ra sao|o dau|nhu the nao|co duoc khong|co khong|khi nao|bao gio|may gio|bao nhieu|nhieu tien)\b)',
    re.IGNORECASE
)


def is_question_text(raw_text: str, folded_text: str) -> bool:
    """Kiểm tra câu có phải câu hỏi không (có dấu ? hoặc từ để hỏi có ranh giới từ)."""
    if "?" in raw_text:
        return True
    return bool(QUESTION_WORDS_RE.search(folded_text))


def classify_comment(
    text: str,
    *,
    page_id: str | None = None,
    from_id: str | None = None,
    parent_id: str | None = None,
    is_reply_to_page: bool = False,
    has_attachment: bool = False,
    spam_patterns: list[str] | None = None,
    platform: str = "facebook",
    brand: str = "saoviet",
) -> dict[str, Any]:
    """Phân loại bình luận theo thứ tự fail-closed (0 token, pure Python).
    
    Packs:
    - core: ignore / toxic / spam / lead qua SĐT (mọi kênh và brand)
    - bsn: mua key / game steam / offline / bao hanh / viet hoa
    - saoviet_tt: link bio / ib bio / 1 cơ sở / online
    - saoviet_fb: hoc_phi / dia_chi (13 cơ sở) / lich_hoc / khai_giang / kỹ thuật (Excel, AutoCAD...)
    """
    if parent_id and not is_reply_to_page:
        is_reply_to_page = True
    raw_text = (text or "").strip()
    folded = fold_text(raw_text)
    phones = extract_vn_phones(raw_text)
    wants_zalo = "zalo" in folded
    reasons = []

    p_norm = (platform or "facebook").strip().lower()
    if p_norm not in ("facebook", "tiktok", "messenger"):
        p_norm = "facebook"
    b_norm = (brand or "saoviet").strip().lower()
    if "bsn" in b_norm or "game" in b_norm:
        b_norm = "bsn"
    else:
        b_norm = "saoviet"

    if b_norm == "bsn":
        course_hints = detect_bsn_hints(folded)
    else:
        course_hints = detect_course_hints(folded)

    def _res(cls: str, faq: str | None, conf: float, r: list[str]) -> dict[str, Any]:
        return {
            "class": cls,
            "faq_intent": faq,
            "confidence": conf,
            "phones": phones,
            "course_hints": course_hints,
            "wants_zalo": wants_zalo,
            "reasons": r,
            "platform": p_norm,
            "brand": b_norm,
        }

    # =========================================================================
    # PACK 1: CORE (Áp dụng cho mọi thương hiệu và nền tảng)
    # =========================================================================
    # 1. ignore — trống, chỉ sticker/emoji, comment của chính Page
    if from_id and page_id and str(from_id) == str(page_id):
        return _res("ignore", None, 1.0, ["from_page_itself"])

    if not raw_text or not re.search(r"\w", raw_text):
        if any(em in raw_text for em in PRAISE_EMOJIS) and not any(c.isalnum() for c in raw_text):
            return _res("khen", None, 0.8, ["emoji_praise_only"])
        return _res("ignore", None, 1.0, ["empty_or_no_alphanumeric"])

    # 2. toxic — chửi tục, lừa đảo
    for kw in TOXIC_KEYWORDS:
        if kw in folded:
            return _res("toxic", None, 0.95, [f"toxic_kw:{kw}"])

    # 3. spam — URL rút gọn, crypto/forex/viagra, lặp ký tự, user patterns
    if SHORT_URL_RE.search(raw_text):
        return _res("spam", None, 0.95, ["short_url"])

    for kw in SPAM_KEYWORDS:
        if kw in folded:
            return _res("spam", None, 0.9, [f"spam_kw:{kw}"])

    if REPEATED_CHAR_RE.search(raw_text):
        return _res("spam", None, 0.85, ["repeated_chars"])

    if ("ib minh" in folded or "inbox minh" in folded) and ("http" in folded or ".com" in folded or ".ly" in folded):
        return _res("spam", None, 0.9, ["ib_minh_with_link"])

    if spam_patterns:
        for p in spam_patterns:
            if p and (p in raw_text or p in folded):
                return _res("spam", None, 0.9, [f"custom_spam:{p}"])

    # 4. lead — có SĐT VN (luôn thắng mọi intent khác)
    if phones:
        reasons.append("has_vn_phone")
        return _res("lead", None, 0.95, reasons)

    # =========================================================================
    # PACK 2: BRAND BSN (Game Giá Rẻ BSN — Steam / Key / Bảo hành / Cài đặt)
    # =========================================================================
    if b_norm == "bsn":
        # 2a. BSN Lead: Mua key, mua game, đặt game
        for kw in BSN_LEAD_KEYWORDS:
            if kw in folded:
                return _res("lead", None, 0.9, [f"bsn_lead:{kw}"])

        # 2b. BSN FAQ: Bảo hành
        if any(k in folded for k in BSN_FAQ_BAO_HANH_KEYWORDS):
            return _res("faq", "bao_hanh", 0.9, ["bsn_faq:bao_hanh"])

        # 2c. BSN FAQ: Key Steam / Offline
        if any(k in folded for k in BSN_FAQ_KEY_STEAM_KEYWORDS):
            return _res("faq", "key_steam", 0.9, ["bsn_faq:key_steam"])

        # 2d. BSN FAQ: Việt hóa
        if any(k in folded for k in BSN_FAQ_VIET_HOA_KEYWORDS):
            return _res("faq", "viet_hoa", 0.9, ["bsn_faq:viet_hoa"])

        # 2e. BSN FAQ: Cài đặt / Link tải
        if any(k in folded for k in BSN_FAQ_CAI_DAT_KEYWORDS):
            return _res("faq", "cai_dat", 0.9, ["bsn_faq:cai_dat"])

        # 2f. BSN FAQ: Giá game
        if any(k in folded for k in BSN_FAQ_GIA_KEYWORDS):
            return _res("faq", "gia_game", 0.9, ["bsn_faq:gia_game"])

        # 2g. Zalo
        if wants_zalo:
            return _res("faq", "zalo", 0.9, ["bsn_faq:zalo"])

        # 2h. Khen
        is_q = is_question_text(raw_text, folded)
        if not is_q and (any(k in folded for k in PRAISE_KEYWORDS) or any(em in raw_text for em in PRAISE_EMOJIS)):
            return _res("khen", None, 0.85, ["praise_kw_or_emoji"])

        # 2i. Kỹ thuật (crash, văng game, lỗi dll...)
        if any(s in folded for s in BSN_TECH_KEYWORDS) or ("loi" in folded and ("game" in folded or "steam" in folded or "key" in folded or "pass" in folded)):
            return _res("ky_thuat", None, 0.85, ["bsn_tech_problem"])

        return _res("ambiguous", None, 0.5, ["bsn:unmatched_rule"])

    # =========================================================================
    # PACK 3: SAO VIỆT TIKTOK (saoviet_tt: Bio lead / 1 cơ sở / Online)
    # =========================================================================
    if p_norm == "tiktok":
        # 3a. Lead qua Bio / đăng ký học
        for kw in SAOVIET_TT_LEAD_KEYWORDS:
            if kw in folded:
                return _res("lead", None, 0.9, [f"saoviet_tt:lead:{kw}"])

        for kw in LEAD_KEYWORDS:
            if kw in folded:
                return _res("lead", None, 0.9, [f"saoviet_tt:lead_kw:{kw}"])

        # 3b. FAQ Zalo
        if wants_zalo:
            return _res("faq", "zalo", 0.9, ["saoviet_tt:faq:zalo"])

        # 3c. FAQ Khai giảng
        open_kws = ["khi nao khai giang", "lich khai giang", "con cho", "khi nao mo lop", "bao gio mo lop", "bao gio khai giang", "khai giang"]
        if any(k in folded for k in open_kws):
            return _res("faq", "khai_giang", 0.9, ["saoviet_tt:faq:khai_giang"])

        # 3d. FAQ Học phí
        fee_kws = ["hoc phi", "bao nhieu tien", "gia khoa", "gia bao nhieu", "chi phi", "phi bao nhieu", "ton bao nhieu", "nhiu tien", "bao nhieu a", "bao nhieu vay"]
        if any(k in folded for k in fee_kws):
            return _res("faq", "hoc_phi", 0.9, ["saoviet_tt:faq:hoc_phi"])

        # 3e. FAQ Địa chỉ (TikTok: chỉ cơ sở video hoặc dẫn xem link bio, không nhồi 13 cơ sở)
        addr_kws = ["dia chi", "o dau", "co so", "chi nhanh", "hoc o dau", "dia diem"]
        if any(k in folded for k in addr_kws):
            return _res("faq", "dia_chi", 0.9, ["saoviet_tt:faq:dia_chi"])

        # 3f. FAQ Lịch học
        schedule_kws = ["lich hoc", "ca toi", "ca sang", "ca chieu", "thu 7", "chu nhat", "gio hoc", "thoi gian hoc", "hoc luc nao"]
        if any(k in folded for k in schedule_kws):
            return _res("faq", "lich_hoc", 0.9, ["saoviet_tt:faq:lich_hoc"])

        # 3g. FAQ Học Online
        if "hoc online" in folded or "lop online" in folded or "dao tao online" in folded:
            return _res("faq", "online", 0.9, ["saoviet_tt:faq:online"])

        # 3h. Khen
        is_q = is_question_text(raw_text, folded)
        if not is_q and (any(k in folded for k in PRAISE_KEYWORDS) or any(em in raw_text for em in PRAISE_EMOJIS)):
            return _res("khen", None, 0.85, ["praise_kw_or_emoji"])

        # 3i. Kỹ thuật
        has_tech_subject = any(s in folded for s in TECH_SUBJECTS)
        has_tech_problem = any(p in folded for p in TECH_PROBLEM_INDICATORS) or "?" in raw_text
        if has_tech_subject and has_tech_problem:
            return _res("ky_thuat", None, 0.85, ["tech_subject_and_problem"])

        return _res("ambiguous", None, 0.5, ["saoviet_tt:unmatched_rule"])

    # =========================================================================
    # PACK 4: SAO VIỆT FACEBOOK / MESSENGER (saoviet_fb: 13 cơ sở, giáo trình...)
    # =========================================================================
    # 4a. FAQ Zalo
    if wants_zalo:
        zalo_kws = ["zalo", "ib zalo", "alo zalo", "qua zalo", "so zalo", "xin so zalo"]
        if any(k in folded for k in zalo_kws):
            return _res("faq", "zalo", 0.9, ["faq:zalo"])

    # 4b. FAQ Khai giảng
    open_kws = ["khi nao khai giang", "lich khai giang", "con cho", "khi nao mo lop", "bao gio mo lop", "bao gio khai giang"]
    if any(k in folded for k in open_kws):
        return _res("faq", "khai_giang", 0.9, ["faq:khai_giang"])

    # 4c. Cụm xin học / đăng ký (khi không để lại SĐT)
    for kw in LEAD_KEYWORDS:
        if kw in folded:
            return _res("lead", None, 0.9, [f"lead_kw:{kw}"])

    # 4d. FAQ hoc_phi
    fee_kws = ["hoc phi", "bao nhieu tien", "gia khoa", "gia bao nhieu", "chi phi", "phi bao nhieu", "ton bao nhieu", "nhiu tien", "bao nhieu a", "bao nhieu vay"]
    if any(k in folded for k in fee_kws):
        return _res("faq", "hoc_phi", 0.9, ["faq:hoc_phi"])

    # 4e. FAQ dia_chi (13 cơ sở)
    addr_kws = ["dia chi", "o dau", "co so", "quan 7", "thu dau mot", "bien hoa", "di an", "thuan an", "tan uyen", "chi nhanh", "dia diem"]
    if any(k in folded for k in addr_kws):
        return _res("faq", "dia_chi", 0.9, ["faq:dia_chi"])

    # 4f. FAQ lich_hoc
    schedule_kws = ["lich hoc", "ca toi", "ca sang", "ca chieu", "thu 7", "chu nhat", "gio hoc", "thoi gian hoc", "hoc luc nao"]
    if any(k in folded for k in schedule_kws):
        return _res("faq", "lich_hoc", 0.9, ["faq:lich_hoc"])

    # 4g. FAQ khai_giang chung
    if "khai giang" in folded:
        return _res("faq", "khai_giang", 0.9, ["faq:khai_giang"])

    # 4h. Khen
    is_q = is_question_text(raw_text, folded)
    if not is_q and (any(k in folded for k in PRAISE_KEYWORDS) or any(em in raw_text for em in PRAISE_EMOJIS)):
        return _res("khen", None, 0.85, ["praise_kw_or_emoji"])

    # 4i. Kỹ thuật
    has_tech_subject = any(s in folded for s in TECH_SUBJECTS)
    has_tech_problem = any(p in folded for p in TECH_PROBLEM_INDICATORS) or "?" in raw_text
    if has_tech_subject and has_tech_problem:
        return _res("ky_thuat", None, 0.85, ["tech_subject_and_problem"])

    # 4j. ambiguous
    return _res("ambiguous", None, 0.5, ["unmatched_rule"])
