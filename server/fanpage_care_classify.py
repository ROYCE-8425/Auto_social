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
) -> dict[str, Any]:
    """Phân loại bình luận theo thứ tự fail-closed (0 token, pure Python)."""
    if parent_id and not is_reply_to_page:
        is_reply_to_page = True
    raw_text = (text or "").strip()
    folded = fold_text(raw_text)
    phones = extract_vn_phones(raw_text)
    course_hints = detect_course_hints(folded)
    wants_zalo = "zalo" in folded
    reasons = []

    # 1. ignore — trống, chỉ sticker/emoji, comment của chính Page
    if from_id and page_id and str(from_id) == str(page_id):
        return {
            "class": "ignore",
            "faq_intent": None,
            "confidence": 1.0,
            "phones": [],
            "course_hints": course_hints,
            "wants_zalo": wants_zalo,
            "reasons": ["from_page_itself"],
        }

    if not raw_text or not re.search(r"\w", raw_text):
        # Kiểm tra xem có emoji khen không trước khi coi là ignore
        if any(em in raw_text for em in PRAISE_EMOJIS) and not any(c.isalnum() for c in raw_text):
            return {
                "class": "khen",
                "faq_intent": None,
                "confidence": 0.8,
                "phones": [],
                "course_hints": course_hints,
                "wants_zalo": False,
                "reasons": ["emoji_praise_only"],
            }
        return {
            "class": "ignore",
            "faq_intent": None,
            "confidence": 1.0,
            "phones": [],
            "course_hints": course_hints,
            "wants_zalo": wants_zalo,
            "reasons": ["empty_or_no_alphanumeric"],
        }

    # 2. toxic — chửi tục, lừa đảo
    for kw in TOXIC_KEYWORDS:
        if kw in folded:
            return {
                "class": "toxic",
                "faq_intent": None,
                "confidence": 0.95,
                "phones": phones,
                "course_hints": course_hints,
                "wants_zalo": wants_zalo,
                "reasons": [f"toxic_kw:{kw}"],
            }

    # 2. spam — URL rút gọn, crypto/forex/viagra, lặp ký tự, user patterns
    if SHORT_URL_RE.search(raw_text):
        return {
            "class": "spam",
            "faq_intent": None,
            "confidence": 0.95,
            "phones": phones,
            "course_hints": course_hints,
            "wants_zalo": wants_zalo,
            "reasons": ["short_url"],
        }

    for kw in SPAM_KEYWORDS:
        if kw in folded:
            return {
                "class": "spam",
                "faq_intent": None,
                "confidence": 0.9,
                "phones": phones,
                "course_hints": course_hints,
                "wants_zalo": wants_zalo,
                "reasons": [f"spam_kw:{kw}"],
            }

    if REPEATED_CHAR_RE.search(raw_text):
        return {
            "class": "spam",
            "faq_intent": None,
            "confidence": 0.85,
            "phones": phones,
            "course_hints": course_hints,
            "wants_zalo": wants_zalo,
            "reasons": ["repeated_chars"],
        }

    if ("ib minh" in folded or "inbox minh" in folded) and ("http" in folded or ".com" in folded or ".ly" in folded):
        return {
            "class": "spam",
            "faq_intent": None,
            "confidence": 0.9,
            "phones": phones,
            "course_hints": course_hints,
            "wants_zalo": wants_zalo,
            "reasons": ["ib_minh_with_link"],
        }

    if spam_patterns:
        for p in spam_patterns:
            if p and (p in raw_text or p in folded):
                return {
                    "class": "spam",
                    "faq_intent": None,
                    "confidence": 0.9,
                    "phones": phones,
                    "course_hints": course_hints,
                    "wants_zalo": wants_zalo,
                    "reasons": [f"custom_spam:{p}"],
                }

    # 3. lead — có SĐT VN (luôn thắng mọi intent khác)
    if phones:
        reasons.append("has_vn_phone")
        return {
            "class": "lead",
            "faq_intent": None,
            "confidence": 0.95,
            "phones": phones,
            "course_hints": course_hints,
            "wants_zalo": wants_zalo,
            "reasons": reasons,
        }

    # 3b. FAQ Zalo — khách xin Zalo của Page (không để lại SĐT)
    if wants_zalo:
        zalo_kws = ["zalo", "ib zalo", "alo zalo", "qua zalo", "so zalo", "xin so zalo"]
        if any(k in folded for k in zalo_kws):
            return {
                "class": "faq",
                "faq_intent": "zalo",
                "confidence": 0.9,
                "phones": [],
                "course_hints": course_hints,
                "wants_zalo": True,
                "reasons": ["faq:zalo"],
            }

    # 3c. FAQ Khai giảng — hỏi lịch mở lớp
    open_kws = ["khi nao khai giang", "lich khai giang", "con cho", "khi nao mo lop", "bao gio mo lop", "bao gio khai giang"]
    if any(k in folded for k in open_kws):
        return {
            "class": "faq",
            "faq_intent": "khai_giang",
            "confidence": 0.9,
            "phones": [],
            "course_hints": course_hints,
            "wants_zalo": wants_zalo,
            "reasons": ["faq:khai_giang"],
        }

    # 3d. Cụm xin học / đăng ký (khi không để lại SĐT)
    for kw in LEAD_KEYWORDS:
        if kw in folded:
            return {
                "class": "lead",
                "faq_intent": None,
                "confidence": 0.9,
                "phones": phones,
                "course_hints": course_hints,
                "wants_zalo": wants_zalo,
                "reasons": [f"lead_kw:{kw}"],
            }

    # 4. faq — các intent còn lại (không có SĐT)
    # 4a. hoc_phi
    fee_kws = ["hoc phi", "bao nhieu tien", "gia khoa", "gia bao nhieu", "chi phi", "phi bao nhieu", "ton bao nhieu", "nhiu tien", "bao nhieu a", "bao nhieu vay"]
    if any(k in folded for k in fee_kws):
        return {
            "class": "faq",
            "faq_intent": "hoc_phi",
            "confidence": 0.9,
            "phones": phones,
            "course_hints": course_hints,
            "wants_zalo": wants_zalo,
            "reasons": ["faq:hoc_phi"],
        }

    # 4b. dia_chi
    addr_kws = ["dia chi", "o dau", "co so", "quan 7", "thu dau mot", "bien hoa", "di an", "thuan an", "tan uyen", "chi nhanh", "dia diem"]
    if any(k in folded for k in addr_kws):
        return {
            "class": "faq",
            "faq_intent": "dia_chi",
            "confidence": 0.9,
            "phones": phones,
            "course_hints": course_hints,
            "wants_zalo": wants_zalo,
            "reasons": ["faq:dia_chi"],
        }

    # 4c. lich_hoc
    schedule_kws = ["lich hoc", "ca toi", "ca sang", "ca chieu", "thu 7", "chu nhat", "gio hoc", "thoi gian hoc", "hoc luc nao"]
    if any(k in folded for k in schedule_kws):
        return {
            "class": "faq",
            "faq_intent": "lich_hoc",
            "confidence": 0.9,
            "phones": phones,
            "course_hints": course_hints,
            "wants_zalo": wants_zalo,
            "reasons": ["faq:lich_hoc"],
        }

    # 4d. khai_giang chung (nếu còn sót)
    if "khai giang" in folded:
        return {
            "class": "faq",
            "faq_intent": "khai_giang",
            "confidence": 0.9,
            "phones": phones,
            "course_hints": course_hints,
            "wants_zalo": wants_zalo,
            "reasons": ["faq:khai_giang"],
        }

    # 5. khen — khen ngợi, cảm ơn (không có câu hỏi)
    is_q = is_question_text(raw_text, folded)
    if not is_q and (any(k in folded for k in PRAISE_KEYWORDS) or any(em in raw_text for em in PRAISE_EMOJIS)):
        return {
            "class": "khen",
            "faq_intent": None,
            "confidence": 0.85,
            "phones": phones,
            "course_hints": course_hints,
            "wants_zalo": wants_zalo,
            "reasons": ["praise_kw_or_emoji"],
        }

    # 6. ky_thuat — công cụ / hàm / lỗi + có câu hỏi hoặc vấn đề
    has_tech_subject = any(s in folded for s in TECH_SUBJECTS)
    has_tech_problem = any(p in folded for p in TECH_PROBLEM_INDICATORS) or "?" in raw_text
    if has_tech_subject and has_tech_problem:
        return {
            "class": "ky_thuat",
            "faq_intent": None,
            "confidence": 0.85,
            "phones": phones,
            "course_hints": course_hints,
            "wants_zalo": wants_zalo,
            "reasons": ["tech_subject_and_problem"],
        }

    # 7. ambiguous — còn lại
    return {
        "class": "ambiguous",
        "faq_intent": None,
        "confidence": 0.5,
        "phones": phones,
        "course_hints": course_hints,
        "wants_zalo": wants_zalo,
        "reasons": ["unmatched_rule"],
    }
