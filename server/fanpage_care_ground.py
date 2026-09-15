"""Grounding và trích xuất thông tin brand kit / course cho Fanpage Care.

Nguyên tắc:
1. address_short: lấy đúng 1 địa chỉ cơ sở khớp page, không bao giờ để chuỗi '|'. Nếu không khớp hoặc mơ hồ -> fail-closed (trả "").
2. get_course_fee: Chỉ trích xuất học phí khi có bảng giá trong file wiki/courses/*.md hoặc brand kit khớp cơ sở. CẤM BỊA SỐ.
3. Templates: đọc từ kit override (## Care templates) hoặc fallback system/fanpage_care/templates.md.
4. Bảo mật: Tuyệt đối không để lộ access_token, EAA... trong kết quả hay prompt.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

_SYSTEM_TEMPLATES_PATH = Path(__file__).resolve().parent.parent / "system" / "fanpage_care" / "templates.md"


def _fold(s: str | None) -> str:
    """Bỏ dấu, khoảng trắng, dấu câu — so khớp địa chỉ, từ khóa."""
    if not s:
        return ""
    norm = unicodedata.normalize("NFD", str(s).lower())
    clean = "".join(c for c in norm if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", clean)


def _one_line(s: str | None) -> str:
    """Gộp thành 1 dòng, loại bỏ ký tự pipe (|) và khoảng trắng thừa."""
    if not s:
        return ""
    res = str(s).replace("|", " ").replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", res).strip()


def sanitize_kit(kit: dict[str, Any] | None) -> dict[str, Any]:
    """Loại bỏ access_token và mọi chuỗi EAA khỏi kit dictionary."""
    if not kit:
        return {}
    out = dict(kit)
    out.pop("access_token", None)
    # Loại bỏ token dạng EAA nếu có trong bất kỳ field nào
    for k, v in list(out.items()):
        if isinstance(v, str) and "EAA" in v:
            out[k] = re.sub(r"EAA[A-Za-z0-9]+", "[REDACTED_TOKEN]", v)
    return out


def _campus_needles(kit: dict[str, Any]) -> list[str]:
    """Sinh danh sách các từ khóa nhận diện cơ sở / chi nhánh từ kit."""
    needles: set[str] = set()
    name = str(kit.get("name") or "")
    fname = str(kit.get("file") or "")
    stem = fname[:-3] if fname.endswith(".md") else fname

    if name:
        needles.add(_fold(name))
    if stem:
        needles.add(_fold(stem))
        needles.add(_fold(stem.replace("-", " ")))

    md = str(kit.get("md") or "")
    # Tìm Góc địa phương trong md
    m_loc = re.search(r"(?:Góc địa phương|Địa phương|Khu vực):\s*([^\n]+)", md, re.I)
    if m_loc:
        needles.add(_fold(m_loc.group(1)))

    # Các alias cơ sở phổ biến của Sao Việt
    alias_map = {
        "thudautmot": ["thudaumot", "tdm", "thu dau mot", "d5", "phuhoa", "phu hoa"],
        "dian": ["dian", "di an", "donghoa", "dong hoa", "le hong phong"],
        "thuanan": ["thuanan", "thuan an", "an phu"],
        "tanuyen": ["tanuyen", "tan uyen"],
        "quan7": ["quan7", "quan 7", "florita", "himlam", "him lam", "dung dung"],
        "bienhoa": ["bienhoa", "bien hoa", "dong nai"],
        "govap": ["govap", "go vap", "quang trung"],
        "binhthanh": ["binhthanh", "binh thanh", "bach dang"],
        "tanbinh": ["tanbinh", "tan binh"],
        "thuduc": ["thuduc", "thu duc", "tp thu duc"],
    }

    combined_text = _fold(name + " " + stem + " " + md)
    for key, aliases in alias_map.items():
        if key in combined_text or any(_fold(al) in combined_text for al in aliases):
            for al in aliases:
                needles.add(_fold(al))

    return [n for n in needles if len(n) >= 4]


def address_short(kit: dict[str, Any] | None) -> str:
    """Trích xuất địa chỉ 1 cơ sở duy nhất khớp với Fanpage.
    
    Quy tắc:
    - Nếu có 1 địa chỉ duy nhất -> trả 1 dòng (không có '|').
    - Nếu là danh sách nhiều cơ sở -> tìm cơ sở khớp needle dài >= 5.
    - Nếu khớp duy nhất 1 cơ sở -> trả cơ sở đó.
    - Nếu không khớp hoặc khớp > 1 cơ sở -> fail-closed, trả "" (để người xử lý).
    """
    if not kit:
        return ""
    raw = kit.get("address") or ""
    parts = [p.strip() for p in re.split(r"[|\n]", str(raw)) if p.strip()]
    if not parts:
        return ""

    if len(parts) == 1:
        return _one_line(parts[0])

    needles = _campus_needles(kit)
    # Lọc những needle dài >= 5 để so khớp chính xác
    strong_needles = [n for n in needles if len(n) >= 5]
    hits = [p for p in parts if any(n in _fold(p) for n in strong_needles)]

    if len(hits) == 1:
        return _one_line(hits[0])

    # Nếu không khớp với strong_needles, thử với các needle còn lại
    if not hits:
        hits = [p for p in parts if any(n in _fold(p) for n in needles)]
        if len(hits) == 1:
            return _one_line(hits[0])

    return ""  # 0 hoặc > 1 hit -> fail-closed


def get_course_fee(
    course_hint: str | None,
    kit: dict[str, Any] | None,
    vault_root: str | Path | None = None,
) -> str | None:
    """Tìm học phí được ghi rõ trong file brand kit hoặc wiki/courses/*.md.
    
    CẤM BỊA SỐ. Chỉ trả về chuỗi học phí nếu tìm thấy số cụ thể khớp với khóa học và cơ sở.
    Nếu không tìm thấy -> trả về None (để fallback về template không có số).
    """
    if not kit:
        return None

    course_tokens = [t for t in _fold(course_hint or "").split() if t] if course_hint else []
    needles = _campus_needles(kit)

    # 1. Tìm trong kit markdown
    md = str(kit.get("md") or "")
    fee_from_kit = _extract_fee_from_text(md, course_tokens, needles)
    if fee_from_kit:
        return fee_from_kit

    # 2. Tìm trong wiki/courses/*.md nếu có vault_root
    if vault_root:
        courses_dir = Path(vault_root) / "wiki" / "courses"
        if courses_dir.is_dir():
            for cfile in courses_dir.glob("*.md"):
                if cfile.name.startswith("_"):
                    continue
                try:
                    ccontent = cfile.read_text(encoding="utf-8")
                except OSError:
                    continue
                fee = _extract_fee_from_text(ccontent, course_tokens, needles)
                if fee:
                    return fee

    return None


def _extract_fee_from_text(text: str, course_tokens: list[str], campus_needles: list[str]) -> str | None:
    """Phân tích văn bản markdown (bảng, danh sách) để tìm học phí đã ghi rõ."""
    if not text:
        return None

    # Mẫu tìm giá tiền: e.g. 3.500.000, 3.500.000đ, 2.800.000 VND, 1.200.000đ
    fee_re = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d+(?:[.,]\d+)?\s*(?:tr|triệu|k))\s*(?:đ|vnd|đồng)?", re.I)

    lines = text.splitlines()
    for line in lines:
        f_line = _fold(line)
        # Nếu có chỉ định khóa học, dòng phải nhắc đến khóa học đó
        if course_tokens and not any(t in f_line for t in course_tokens):
            continue
        # Dòng phải có nhắc đến cơ sở nếu có nhiều cơ sở trong bảng
        # (nếu text chỉ nói riêng về 1 cơ sở hoặc line khớp needle)
        m = fee_re.search(line)
        if m:
            matched_fee = m.group(0).strip()
            # Kiểm tra xem có phải hotline hoặc MST không (loại trừ)
            digits_only = re.sub(r"\D", "", matched_fee)
            if len(digits_only) in (10, 11) and digits_only.startswith(("0", "84")):
                continue  # SĐT
            # Nếu dòng khớp cơ sở của Page, ưu tiên tuyệt đối
            if campus_needles and any(n in f_line for n in campus_needles):
                return matched_fee

            # Hoặc kiểm tra dòng có từ khóa học phí / giá / fee và không nhắc cơ sở khác
            if any(kw in f_line for kw in ["hocphi", "gia", "phi", "vnd", "dong", "tr", "k"]):
                if not any(other in f_line for other in ["quan7", "bienhoa", "thudaumot", "dian", "tanuyen", "thuanan"]):
                    return matched_fee

    return None


def parse_templates_markdown(md_text: str) -> dict[str, str]:
    """Parse khối templates từ markdown text."""
    templates = {}
    in_templates = False
    for line in md_text.splitlines():
        line_s = line.strip()
        if line_s.startswith("## Care templates") or line_s.startswith("## Templates"):
            in_templates = True
            continue
        if in_templates:
            if line_s.startswith("## ") and not line_s.startswith("## Care templates"):
                break
            # Dạng `- intent: "nội dung"` hoặc `- intent: nội dung`
            m = re.match(r"^[-\*]\s*([a-zA-Z0-9_]+)\s*:\s*[\"']?(.*?)[\"']?$", line_s)
            if m:
                intent_key = m.group(1).strip()
                content = m.group(2).strip()
                templates[intent_key] = content
    return templates


def load_templates(kit: dict[str, Any] | None = None) -> dict[str, str]:
    """Tải templates kết hợp: mặc định hệ thống + kit override."""
    templates: dict[str, str] = {}
    if _SYSTEM_TEMPLATES_PATH.exists():
        try:
            sys_md = _SYSTEM_TEMPLATES_PATH.read_text(encoding="utf-8")
            templates.update(parse_templates_markdown(sys_md))
        except OSError:
            pass

    if kit and kit.get("md"):
        kit_override = parse_templates_markdown(str(kit.get("md")))
        templates.update(kit_override)

    return templates


def render_template(
    intent_or_key: str,
    kit: dict[str, Any] | None,
    *,
    course_hint: str | None = None,
    vault_root: str | Path | None = None,
) -> str | None:
    """Render template câu trả lời tự động cho FAQ/Lead/Khen.
    
    Tuân thủ tuyệt đối:
    - Bảng giá chỉ xuất hiện khi get_course_fee có kết quả.
    - Không có giá -> dùng template hotline mặc định không chứa số tiền.
    - address_short không có -> trả None (để đưa vào draft cho người xử lý).
    """
    if not kit:
        return None

    clean_kit = sanitize_kit(kit)
    templates = load_templates(clean_kit)

    key = str(intent_or_key or "").strip().lower()
    tpl = templates.get(key)
    if not tpl:
        return None

    page_name = clean_kit.get("name") or "Trung tâm"
    hotline = clean_kit.get("hotline") or ""
    addr = address_short(clean_kit)
    course_or_nganh = course_hint or "Tin học"

    # Với intent hoc_phi: kiểm tra xem có bảng giá trong file không
    if key == "hoc_phi":
        fee = get_course_fee(course_hint, clean_kit, vault_root=vault_root)
        if fee:
            # Có số trong file: quote đúng số
            tpl = f"Dạ học phí {course_or_nganh} tại cơ sở {page_name} là {fee}. Anh/chị inbox hoặc liên hệ Hotline/Zalo {hotline} để nhận lịch học chi tiết nhé ạ."
            return _one_line(tpl)
        # Chưa có số trong file: giữ nguyên template hotline mặc định (CẤM BỊA SỐ)

    if "{address_short}" in tpl:
        if not addr:
            # Thiếu địa chỉ cơ sở cụ thể -> không tự gửi
            return None
        tpl = tpl.replace("{address_short}", addr)

    tpl = tpl.replace("{page_name}", page_name)
    tpl = tpl.replace("{hotline}", hotline or "hotline trên Trang")
    tpl = tpl.replace("{course_or_nganh}", course_or_nganh)

    return _one_line(tpl)


_BO_QUA_DIRS = {"inbox", "attachments", "javis", ".git", ".obsidian", ".trash", "node_modules", "memory", "skills", "plugins", ".claude", ".agents"}
_BO_QUA_FILES = {"claude.md", "agents.md", "readme.md", "index.md", "log.md", "_open-questions.md", "_session-handoff.md", "memory.md"}


def build_care_llm_prompt(
    page_id: str,
    kit: dict[str, Any] | None,
    comment_text: str,
    *,
    thread_comments: list[dict[str, Any]] | None = None,
    vault_root: str | Path | None = None,
) -> tuple[str, str]:
    """Tạo cặp (system_prompt, user_prompt) cho complete_json.
    
    Quy tắc an toàn:
    - KHÔNG chứa CLAUDE.md, AGENTS.md, pancake, fb_page_album.
    - KHÔNG chứa token access_token / EAA.
    - Chỉ đưa kit và course files của đúng page_id vào context.
    - Yêu cầu model trả về JSON object có cite_files.
    """
    clean_kit = sanitize_kit(kit)
    page_name = clean_kit.get("name") or "Trung tâm Sao Việt"
    hotline = clean_kit.get("hotline") or ""
    addr = address_short(clean_kit)

    # 1. Thu thập Context
    context_blocks = []
    kit_fname = clean_kit.get("file") or f"{page_id}.md"
    kit_summary = [
        f"### File: {kit_fname}",
        f"- Tên Fanpage / Cơ sở: {page_name}",
        f"- Địa chỉ: {addr or 'Xem trên trang'}",
        f"- Hotline/Zalo: {hotline}",
    ]
    if clean_kit.get("md"):
        # Cắt bớt phần md dài, lọc token
        sanitized_md = re.sub(r"EAA[A-Za-z0-9]+", "", str(clean_kit.get("md")))
        kit_summary.append(sanitized_md[:1500])
    context_blocks.append("\n".join(kit_summary))

    # Đọc course files nếu có vault_root
    if vault_root:
        courses_dir = Path(vault_root) / "wiki" / "courses"
        if courses_dir.is_dir():
            count = 0
            for cfile in courses_dir.glob("*.md"):
                if cfile.name.lower() in _BO_QUA_FILES or cfile.name.startswith("_"):
                    continue
                try:
                    content = cfile.read_text(encoding="utf-8")
                    content = re.sub(r"EAA[A-Za-z0-9]+", "", content)
                    context_blocks.append(f"### File: {cfile.name}\n{content[:1500]}")
                    count += 1
                    if count >= 3:
                        break
                except OSError:
                    continue

    context_str = "\n\n".join(context_blocks)

    system_prompt = (
        f"Bạn là trợ lý Chăm sóc Fanpage cho '{page_name}'. Nhiệm vụ: trả lời bình luận của học viên một cách lịch sự, chính xác.\n\n"
        "QUY TẮC BẮT BUỘC:\n"
        "1. CHỈ sử dụng thông tin có trong phần 'Context' bên dưới. CẤM tự bịa học phí, lịch học, hoặc địa chỉ nếu trong file không có số liệu cụ thể. Nếu không chắc chắn, bạn PHẢI đặt `\"refuse\": true`.\n"
        "2. BẮT BUỘC trích dẫn tên file đã sử dụng trong mảng `\"cite_files\"`. Nếu không trích dẫn được file nào trong context, bạn PHẢI đặt `\"refuse\": true`.\n"
        "3. Câu trả lời (`reply`) tối đa 400 ký tự, ngắn gọn, xưng hô Dạ/Em với khách.\n"
        "4. ĐỊNH DẠNG ĐẦU RA: BẮT BUỘC là 1 JSON object duy nhất, không thêm markdown ngoài JSON:\n"
        '{\n  "reply": "Nội dung trả lời",\n  "refuse": false,\n  "cite_files": ["tên_file.md"]\n}\n'
        "Nếu từ chối trả lời:\n"
        '{\n  "reply": "",\n  "refuse": true,\n  "cite_files": []\n}\n\n'
        f"--- CONTEXT ---\n{context_str}"
    )

    user_parts = []
    if thread_comments:
        user_parts.append("Lịch sử trao đổi gần nhất:")
        for tc in thread_comments[-5:]:
            sender = tc.get("from_name") or "Khách"
            msg = tc.get("message") or ""
            user_parts.append(f"- {sender}: {msg}")
        user_parts.append("")

    user_parts.append(f"Bình luận mới từ học viên: {comment_text}")
    user_prompt = "\n".join(user_parts)

    return system_prompt, user_prompt

