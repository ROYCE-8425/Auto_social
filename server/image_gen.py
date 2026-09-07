"""
image_gen.py - Tạo ảnh bằng GÓI ChatGPT (OAuth device-code) - KHÔNG cần OpenAI API key.

Cơ chế (port từ plugin image_gen/openai-codex của nousresearch/hermes-agent): gọi Codex Responses
API (https://chatgpt.com/backend-api/codex/responses - CÙNG endpoint Javis đã dùng cho chat ChatGPT)
với builtin tool 'image_generation' (model gpt-image-2) + tool_choice=required, stream SSE, lấy ảnh
base64 trong 'image_generation_call.result'. Token OAuth lấy từ openai_oauth.valid_creds() (tự refresh).

Vì sao Javis trước đây KHÔNG tạo ảnh trực tiếp: đường chat ChatGPT (engine.responses_with_mcp) chỉ
gửi function tool, chưa từng gửi builtin tool 'image_generation'. Module này bổ sung đúng chỗ đó.

Ảnh lưu vào <vault>/attachments/ để nhúng thẳng vào chat: ![](attachments/<tên>.png)
(dashboard phục vụ qua /files/raw). Các hàm build_payload / extract_image_b64 / resolve_size /
save_png_b64 là THUẦN → test được không cần mạng.
"""
from __future__ import annotations

import base64
import io
import json
import os
import random
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx

_CUR_DIR = Path(__file__).resolve().parent
if str(_CUR_DIR) not in sys.path:
    sys.path.insert(0, str(_CUR_DIR))

import openai_oauth

CODEX_RESPONSES_URL = "https://chatgpt.com/backend-api/codex/responses"
# Model chat 'chủ' chỉ để gọi tool; ảnh do IMAGE_MODEL sinh. Override qua env nếu gói đổi tên model.
HOST_MODEL = os.getenv("JAVIS_IMAGE_HOST_MODEL", "gpt-5.5")
IMAGE_MODEL = os.getenv("JAVIS_IMAGE_MODEL", "gpt-image-2")
INSTRUCTIONS = ("You are an assistant that must fulfill image generation and image editing "
                "requests by using the image_generation tool when provided.")

_SIZES = {"landscape": "1536x1024", "square": "1024x1024", "portrait": "1024x1536"}
_QUALITIES = {"low", "medium", "high"}
_ATTACH_RE = r"^(\d+\s*[-_.]\s*)?attachments$"


# ---------------------------------------------------------------------------
# Helpers thuần (test được)
# ---------------------------------------------------------------------------
def resolve_size(aspect_ratio: Optional[str]) -> str:
    return _SIZES.get((aspect_ratio or "square").strip().lower(), _SIZES["square"])


# Ảnh MẪU gửi kèm: trần dung lượng và số lượng. Ảnh đi trong thân request dưới dạng base64
# nên một tấm 4000px chụp từ điện thoại đủ làm request phình gấp mấy lần và bị backend từ
# chối - hỏng ở đó thì người dùng chỉ thấy "ChatGPT 413", không lần ra được vì sao.
MAX_REF_IMAGES = 4
MAX_REF_BYTES = 12 * 1024 * 1024
_IMG_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
             ".webp": "image/webp", ".gif": "image/gif"}


def fix_dataset_path(rel: str) -> str:
    """Model hay đổi 'tin-hoc _ai' thành tin-hoc/_ai hoặc tin-hoc/."""
    s = (rel or "").replace("\\", "/").strip()
    s = s.replace("tin-hoc/_ai", "tin-hoc _ai")
    s = s.replace("tin-hoc_ai", "tin-hoc _ai")
    if "/dataset/tin-hoc/" in s and "/dataset/tin-hoc _ai/" not in s:
        s = s.replace("/dataset/tin-hoc/", "/dataset/tin-hoc _ai/")
    return s


def first_dataset_photo(vault_root: Optional[str], folder: str = "tin-hoc _ai") -> str:
    """Path tương đối 1 jpg raw trong folder ngành (bỏ file (1))."""
    vault = _resolve_vault(vault_root)
    folder = fix_dataset_path("attachments/dataset/" + folder).split("dataset/")[-1]
    d = vault / "attachments" / "dataset" / folder
    if not d.is_dir():
        return ""
    for p in sorted(d.iterdir(), key=lambda x: x.name.lower()):
        if p.is_file() and p.suffix.lower() in _IMG_MIME and " (1)" not in p.name:
            return str(p.relative_to(vault)).replace("\\", "/")
    return ""


def pick_dataset_photo(
    vault_root: Optional[str],
    folder: str = "tin-hoc _ai",
    random_choice: bool = True,
    prefer_premade: bool = True,
) -> str:
    """Path tương đối 1 ảnh chất lượng trong folder ngành hoặc _mau.
    Nếu prefer_premade=True, ưu tiên chọn các poster đồ họa marketing có sẵn (khai giảng, ưu đãi, poster)
    để đạt chất lượng thương mại cao nhất."""
    vault = _resolve_vault(vault_root)
    clean_folder = fix_dataset_path("attachments/dataset/" + folder).split("dataset/")[-1]
    d = vault / "attachments" / "dataset" / clean_folder
    mau_dir = vault / "attachments" / "dataset" / "_mau"

    premade_kws = ("khai-giang", "uu-dai", "poster", "banner", "thong-bao", "looker-studio", "trung-tam-dao-tao", "hoc-ung-dung")

    candidates = []
    premade_candidates = []

    # 1. Quét trong folder ngành
    if d.is_dir():
        for p in d.iterdir():
            if p.is_file() and p.suffix.lower() in _IMG_MIME and " (1)" not in p.name:
                # Bỏ các ảnh chụp màn hình/lưng ghế thô không đạt chuẩn thẩm mỹ
                if p.name.startswith("Tin-hoc-00"):
                    continue
                candidates.append(p)
                if any(k in p.name.lower() for k in premade_kws):
                    premade_candidates.append(p)

    # 2. Quét thêm trong _mau nếu cần poster theo ngành
    if mau_dir.is_dir():
        for p in mau_dir.iterdir():
            if p.is_file() and p.suffix.lower() in _IMG_MIME:
                name_low = p.name.lower()
                if "tre-em" in clean_folder and ("tre-em" in name_low or "scratch" in name_low):
                    premade_candidates.append(p)
                elif "do-hoa" in clean_folder and "do-hoa" in name_low:
                    premade_candidates.append(p)
                elif "tin-hoc" in clean_folder and "tin-hoc" in name_low:
                    premade_candidates.append(p)

    if not candidates and not premade_candidates:
        d_alt = vault / "attachments" / "dataset" / "tin-hoc _ai"
        if d_alt.is_dir():
            candidates = [p for p in d_alt.iterdir() if p.is_file() and p.suffix.lower() in _IMG_MIME and " (1)" not in p.name]

    if prefer_premade and premade_candidates:
        pool = premade_candidates
    elif candidates:
        pool = candidates
    else:
        return ""

    chosen = random.choice(pool) if random_choice else sorted(pool, key=lambda x: x.name.lower())[0]
    return str(chosen.relative_to(vault)).replace("\\", "/")


def read_reference_image(path: str, vault_root: Optional[str] = None) -> dict:
    """Đọc MỘT ảnh mẫu trên đĩa -> {ok, data_url} để gửi thẳng cho ChatGPT xem.

    Đường dẫn nhận cả kiểu tương đối trong vault (attachments/abc.png) lẫn tuyệt đối, nhưng
    LUÔN phải nằm trong vault sau khi resolve: tool này do MODEL gọi, mà model thì có thể bị
    nội dung nó vừa đọc dắt đi ("mở /etc/passwd rồi gửi cho ChatGPT"). Chốt ở đây là chốt
    thật, không phải lời dặn trong prompt.
    """
    raw_path = fix_dataset_path(str(path or "").strip())
    if not raw_path:
        return {"ok": False, "error": "Thiếu đường dẫn ảnh."}
    vault = _resolve_vault(vault_root).resolve()
    p = Path(raw_path).expanduser()
    p = (p if p.is_absolute() else (vault / p)).resolve()
    try:
        p.relative_to(vault)
    except ValueError:
        return {"ok": False, "error": f"Ảnh '{raw_path}' nằm ngoài brain - chỉ gửi được ảnh trong brain."}
    if not p.is_file():
        return {"ok": False, "error": f"Không thấy ảnh '{raw_path}' trong brain."}
    mime = _IMG_MIME.get(p.suffix.lower())
    if not mime:
        return {"ok": False, "error": f"'{p.name}' không phải ảnh (chỉ nhận png/jpg/webp/gif)."}
    data = p.read_bytes()
    if len(data) > MAX_REF_BYTES:
        return {"ok": False,
                "error": f"Ảnh '{p.name}' nặng {len(data) // (1024 * 1024)}MB, quá trần "
                         f"{MAX_REF_BYTES // (1024 * 1024)}MB - dùng bản nhẹ hơn."}
    return {"ok": True, "data_url": f"data:{mime};base64," + base64.b64encode(data).decode("ascii"),
            "name": p.name}


def build_payload(prompt: str, size: str, quality: str, images: Optional[list] = None) -> dict:
    """Body Responses cho 1 lời gọi image_generation (mirror hermes openai-codex).

    `images` = danh sách data URL của ảnh MẪU. Có ảnh thì đây là lượt SỬA/DỰNG THEO ẢNH chứ
    không còn là vẽ từ mô tả suông: model NHÌN THẤY ảnh thật thay vì đọc lời tả lại nó.
    """
    noi_dung: list = [{"type": "input_text", "text": prompt}]
    for u in (images or []):
        noi_dung.append({"type": "input_image", "image_url": u})
    return {
        "model": HOST_MODEL,
        "store": False,
        "instructions": INSTRUCTIONS,
        "input": [{"type": "message", "role": "user", "content": noi_dung}],
        "tools": [{"type": "image_generation", "model": IMAGE_MODEL, "size": size,
                   "quality": quality, "output_format": "png", "background": "opaque",
                   "partial_images": 1}],
        "tool_choice": {"type": "allowed_tools", "mode": "required",
                        "tools": [{"type": "image_generation"}]},
        "stream": True,
    }


def extract_image_b64(value: Any) -> Optional[str]:
    """Bới đệ quy 1 payload sự kiện SSE, trả b64 ảnh MỚI nhất (image_generation_call.result
    hoặc partial_image_b64). Bới đệ quy để chịu được thay đổi hình dạng sự kiện của backend."""
    found: Optional[str] = None
    if isinstance(value, dict):
        if value.get("type") == "image_generation_call":
            r = value.get("result")
            if isinstance(r, str) and r:
                found = r
        p = value.get("partial_image_b64")
        if isinstance(p, str) and p:
            found = p
        for v in value.values():
            n = extract_image_b64(v)
            if n:
                found = n
    elif isinstance(value, list):
        for v in value:
            n = extract_image_b64(v)
            if n:
                found = n
    return found


def _default_vault() -> str:
    return str(Path(os.getenv("BRAINS_DIR", str(Path(__file__).parent.parent / "brains"))) / "Brain Default")


def _resolve_vault(vault_root: Optional[Union[str, Path]]) -> Path:
    if vault_root and os.path.isdir(str(vault_root)):
        p = Path(vault_root).resolve()
        if (p / "brains" / "Brain Default").is_dir() and not (p / "wiki").is_dir():
            return (p / "brains" / "Brain Default").resolve()
        return p
    return Path(_default_vault()).resolve()


def _attachments_dir(vault: Path) -> Path:
    """Thư mục attachments của vault (khớp 'attachments'/'Attachments'/'NN - attachments'), tạo nếu thiếu."""
    try:
        for name in os.listdir(vault):
            if os.path.isdir(vault / name) and re.match(_ATTACH_RE, name.strip(), re.IGNORECASE):
                return vault / name
    except Exception:
        pass
    d = vault / "attachments"
    d.mkdir(parents=True, exist_ok=True)
    return d


BRAND_SOFTWARE = "Javis OS"
BRAND_SOURCE = "https://javisos.com"


def _strip_c2pa_on() -> bool:
    """Chủ workspace có tự bật gỡ Content Credentials không. Mặc định KHÔNG."""
    try:
        import config
        return bool((config.read_settings().get("image") or {}).get("strip_c2pa"))
    except Exception:
        return False                      # đọc cài đặt lỗi → giữ dấu nguồn gốc, đừng gỡ nhầm


def _png_text_chunk(key: str, value: str) -> bytes:
    """Một chunk tEXt PNG: len + 'tEXt' + key\\0value + CRC32(type+data). tEXt là
    Latin-1 nên chỉ truyền chuỗi ASCII vào đây."""
    import zlib
    data = key.encode("latin-1") + b"\x00" + value.encode("latin-1")
    body = b"tEXt" + data
    return len(data).to_bytes(4, "big") + body + zlib.crc32(body).to_bytes(4, "big")


def _iter_png_chunks(raw: bytes):
    """Duyệt chunk PNG, sinh (type, start, end). Gặp byte hỏng thì dừng im lặng."""
    i = 8
    while i + 8 <= len(raw):
        ln = int.from_bytes(raw[i:i + 4], "big")
        typ = raw[i + 4:i + 8]
        end = i + 12 + ln
        if ln < 0 or end > len(raw):
            return
        yield typ, i, end
        if typ == b"IEND":
            return
        i = end


def strip_c2pa_png(raw: bytes) -> bytes:
    """Gỡ chunk caBX (Content Credentials / C2PA) khỏi PNG.

    caBX là nơi nhà cung cấp ảnh nhúng bản ghi nguồn gốc có chữ ký, nói rõ ảnh do AI
    sinh ra; nền tảng như Facebook đọc nó để gắn nhãn "Nội dung do AI tạo".

    CHỈ chạy khi chủ workspace tự bật `image.strip_c2pa` trong Cài đặt - mặc định TẮT.
    Gỡ dấu này KHÔNG xoá nghĩa vụ công bố nội dung AI của người đăng; đó là việc của họ.
    """
    try:
        if raw[:8] != b"\x89PNG\r\n\x1a\n":
            return raw
        parts, last, found = [], 0, False
        for typ, start, end in _iter_png_chunks(raw):
            if typ == b"caBX":
                parts.append(raw[last:start])
                last = end
                found = True
        if not found:
            return raw
        parts.append(raw[last:])
        return b"".join(parts)
    except Exception:
        return raw


def brand_png(raw: bytes) -> bytes:
    """Gắn thông tin tác giả (Javis OS / javisos.com) vào PNG, chèn ngay sau IHDR.

    CHỈ THÊM, không gỡ chunk nào - phần Content Credentials (C2PA) mà nhà cung cấp
    ảnh nhúng sẵn vẫn nằm nguyên trong file. Lưu ý: vì thêm chunk làm đổi byte của
    file, chữ ký C2PA cũ có thể không còn khớp khi đem đi kiểm; đó là hệ quả kỹ
    thuật của việc ghi metadata, không phải chủ đích gỡ nguồn gốc.

    File không phải PNG hợp lệ thì trả nguyên xi, không làm hỏng ảnh.
    """
    try:
        if raw[:8] != b"\x89PNG\r\n\x1a\n":
            return raw
        ihdr_len = int.from_bytes(raw[8:12], "big")
        end = 8 + 12 + ihdr_len                      # hết chunk IHDR
        if raw[12:16] != b"IHDR" or end > len(raw):
            return raw
        block = (_png_text_chunk("Software", BRAND_SOFTWARE)
                 + _png_text_chunk("Source", BRAND_SOURCE)
                 + _png_text_chunk("Creation Time", time.strftime("%Y-%m-%dT%H:%M:%S%z")))
        return raw[:end] + block + raw[end:]
    except Exception:
        return raw                                    # gắn nhãn hỏng thì thà mất nhãn còn hơn mất ảnh


def save_png_b64(b64: str, vault_root: Optional[str], prefix: str = "javis-img",
                 subdir: Optional[str] = None) -> dict:
    """Giải mã b64 → lưu PNG vào <vault>/attachments. Trả {ok, rel_path, abs_path, file}."""
    try:
        raw = base64.b64decode(b64)
    except Exception as e:
        return {"ok": False, "error": f"Ảnh base64 hỏng: {e}"}
    if not raw:
        return {"ok": False, "error": "Ảnh rỗng."}
    if _strip_c2pa_on():
        raw = strip_c2pa_png(raw)
    raw = brand_png(raw)
    vault = _resolve_vault(vault_root)
    adir = (vault / subdir) if subdir else _attachments_dir(vault)
    try:
        adir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    fname = f"{prefix}-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}.png"
    fpath = adir / fname
    try:
        fpath.write_bytes(raw)
    except Exception as e:
        return {"ok": False, "error": f"Lưu ảnh lỗi: {e}"}
    rel = os.path.relpath(fpath, vault).replace(os.sep, "/")
    return {"ok": True, "rel_path": rel, "abs_path": str(fpath), "file": fname}


def save_image_bytes(raw: bytes, vault_root: Optional[str], prefix: str = "javis-img",
                     ext: str = ".jpg", subdir: Optional[str] = None) -> dict:
    """Luu bytes anh vao vault (mac dinh attachments/). Tra {ok, rel_path, abs_path, file}."""
    if not raw:
        return {"ok": False, "error": "Du lieu anh rong."}
    vault = _resolve_vault(vault_root)
    adir = (vault / subdir) if subdir else _attachments_dir(vault)
    try:
        adir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    fname = f"{prefix}-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}{ext}"
    fpath = adir / fname
    try:
        fpath.write_bytes(raw)
    except Exception as e:
        return {"ok": False, "error": f"Luu anh loi: {e}"}
    rel = os.path.relpath(fpath, vault).replace(os.sep, "/")
    return {"ok": True, "rel_path": rel, "abs_path": str(fpath), "file": fname}



def _headers(token: str, account_id: str) -> dict:
    # KHỚP đúng bộ header engine.responses_with_mcp đã chạy được (qua Cloudflare backend Codex).
    return {
        "Authorization": f"Bearer {token}", "chatgpt-account-id": account_id or "",
        "OpenAI-Beta": "responses=experimental", "originator": "codex_cli_rs",
        "session_id": str(uuid.uuid4()), "Content-Type": "application/json",
        "Accept": "text/event-stream", "User-Agent": "javis-os/0.3 (codex)",
    }


# ---------------------------------------------------------------------------
# Gọi thật
# ---------------------------------------------------------------------------
async def generate_chatgpt(prompt: str, aspect_ratio: str = "square", quality: str = "medium",
                           vault_root: Optional[str] = None, timeout_s: float = 300.0,
                           images: Optional[list] = None, page_id: Optional[str] = None,
                           brand_kit: Optional[dict] = None,
                           save_under: Optional[str] = None) -> dict:
    """Tạo 1 ảnh bằng gói ChatGPT. Trả {ok, rel_path, abs_path, size, quality, aspect} hoặc {ok:False, error}.

    `images` = danh sách đường dẫn ảnh MẪU trong brain. Có ảnh thì ChatGPT NHÌN THẤY ảnh thật
    (gửi kèm dạng input_image) rồi sửa/dựng theo, thay vì đọc một đoạn tả lại ảnh - đó là khác
    biệt giữa "giống hệt cái chai này" và "vẽ một cái chai nghe mô tả na ná".
    """
    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "error": "Thiếu mô tả ảnh (prompt)."}
    aspect = (aspect_ratio or "square").strip().lower()
    if aspect not in _SIZES:
        aspect = "square"
    quality = (quality or "medium").strip().lower()
    if quality not in _QUALITIES:
        quality = "medium"

    vault = _resolve_vault(vault_root)
    kit = brand_kit if isinstance(brand_kit, dict) else load_brand_kit_info(page_id, vault_root=vault)
    prompt = apply_brand_guidelines(prompt, kit, provider="openai")

    creds = openai_oauth.valid_creds()
    if not creds or not creds.get("access_token"):
        return {"ok": False, "error": "Chưa kết nối ChatGPT (OAuth). Vào trang Model đăng nhập ChatGPT rồi thử lại."}

    # Đọc ảnh mẫu TRƯỚC khi gọi mạng: ảnh sai đường dẫn thì báo ngay và nói rõ ảnh nào,
    # thay vì đốt một lượt gọi rồi trả về một tấm vẽ từ mô tả suông mà người dùng tưởng là
    # đã dựng theo ảnh của mình.
    ds_anh = [x for x in (images or []) if str(x or "").strip()]
    if len(ds_anh) > MAX_REF_IMAGES:
        return {"ok": False, "error": f"Gửi tối đa {MAX_REF_IMAGES} ảnh mẫu một lượt (đang gửi {len(ds_anh)})."}
    data_urls = []
    for x in ds_anh:
        r = read_reference_image(x, vault_root)
        if not r.get("ok"):
            return {"ok": False, "error": r.get("error") or f"Không đọc được ảnh '{x}'."}
        data_urls.append(r["data_url"])

    size = resolve_size(aspect)
    payload = build_payload(prompt, size, quality, data_urls)
    headers = _headers(creds["access_token"], creds.get("account_id") or "")

    b64: Optional[str] = None
    err: Optional[str] = None
    try:
        timeout = httpx.Timeout(timeout_s, connect=20)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", CODEX_RESPONSES_URL, headers=headers, json=payload) as r:
                if r.status_code != 200:
                    body = await r.aread()
                    return {"ok": False, "error": f"ChatGPT {r.status_code}: {body.decode('utf-8', 'replace')[:300]}"}
                async for line in r.aiter_lines():
                    line = (line or "").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        obj = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    if obj.get("type") in ("response.failed", "error", "response.error"):
                        e = (obj.get("response") or {}).get("error") or obj.get("error") or {}
                        err = e.get("message") if isinstance(e, dict) else str(e)
                        continue
                    got = extract_image_b64(obj)
                    if got:
                        b64 = got
    except Exception as e:
        return {"ok": False, "error": f"Gọi ChatGPT lỗi: {type(e).__name__}: {e}"}

    if not b64:
        return {"ok": False, "error": err or "ChatGPT không trả ảnh (gói ChatGPT có thể chưa hỗ trợ tạo ảnh qua Codex)."}

    should_overlay_cover = bool(
        save_under or page_id or re.search(r"cover|bìa|bia|facebook|fanpage|khóa học|khoa hoc", prompt, re.I)
    )
    if should_overlay_cover:
        try:
            import banner_templates
        except ImportError:
            try:
                from server import banner_templates
            except ImportError:
                banner_templates = None
        if banner_templates is not None:
            try:
                from PIL import Image
                raw_bytes = base64.b64decode(b64)
                bg_img = Image.open(io.BytesIO(raw_bytes))
                content = parse_banner_content(prompt, vault_root=vault)
                logo_file = None
                if kit and kit.get("logo_path"):
                    cand = vault / str(kit["logo_path"])
                    if cand.is_file():
                        logo_file = cand
                if not logo_file:
                    for ref in ds_anh:
                        s_ref = str(ref).replace("\\", "/").lower()
                        if "logo" in s_ref:
                            cand = Path(ref)
                            cand = cand if cand.is_absolute() else (vault / ref)
                            if cand.is_file():
                                logo_file = cand
                                break
                if not logo_file:
                    for cand_rel in (
                        "attachments/dataset/chung/thsv-logo-2025.png",
                        "attachments/dataset/chung/thsv-logo-big.png",
                    ):
                        cand = vault / cand_rel
                        if cand.is_file():
                            logo_file = cand
                            break
                enhanced = banner_templates.render_ai_enhanced_banner(
                    ai_background_img=bg_img,
                    logo_path=logo_file,
                    title=content.get("title") or "TIN HỌC VĂN PHÒNG & ỨNG DỤNG AI",
                    subtitle=content.get("subtitle"),
                    highlights=content.get("highlights"),
                    badge_text=content.get("badge_text"),
                    footer_text=(kit.get("brand_name") if kit else None) or (kit.get("name") if kit else None),
                    hotline=(kit.get("hotline") if kit else None),
                )
                out = io.BytesIO()
                enhanced.save(out, format="JPEG", quality=95)
                saved = save_image_bytes(
                    out.getvalue(), vault_root, prefix="javis-img-cover", ext=".jpg",
                    subdir=save_under or "attachments/dataset/_xuat",
                )
                if saved.get("ok"):
                    return {"ok": True, "rel_path": saved["rel_path"], "abs_path": saved["abs_path"],
                            "file": saved["file"], "size": size, "quality": quality, "aspect": aspect,
                            "provider": "openai-codex", "model": IMAGE_MODEL,
                            "prompt": prompt, "refs": len(data_urls), "overlay": "brand_cover"}
            except Exception:
                pass

    saved = save_png_b64(b64, vault_root, prefix="javis-img", subdir=save_under)
    if not saved.get("ok"):
        return saved
    return {"ok": True, "rel_path": saved["rel_path"], "abs_path": saved["abs_path"],
            "file": saved["file"], "size": size, "quality": quality, "aspect": aspect,
            "provider": "openai-codex", "model": IMAGE_MODEL, "prompt": prompt, "refs": len(data_urls)}


# ---------------------------------------------------------------------------
# Google Gemini / Imagen + Nano Banana (generateContent)
# ---------------------------------------------------------------------------
# Imagen (:predict) và Gemini image (:generateContent) dùng CÙNG API key Gemini.
# Chọn model ở trang Models (model.gemini_image_model) hoặc tham số tool.
GEMINI_IMAGE_MODELS = [
    {"id": "imagen-3.0-generate-002", "label": "Imagen 3 (Tối ưu nhất - Đề xuất)", "kind": "predict"},
    {"id": "imagen-3.0-fast-generate-001", "label": "Imagen 3 Fast (Tốc độ cao)", "kind": "predict"},
    {"id": "imagen-4.0-generate-001", "label": "Imagen 4 (Google Imagen 4 - Mới nhất)", "kind": "predict"},
]
_IMAGE_KIND = {m["id"]: m["kind"] for m in GEMINI_IMAGE_MODELS}
GEMINI_DEFAULT_IMAGE_MODEL = "imagen-3.0-generate-002"
GEMINI_IMAGEN_MODEL = os.getenv("JAVIS_GEMINI_IMAGEN_MODEL", GEMINI_DEFAULT_IMAGE_MODEL)
if GEMINI_IMAGEN_MODEL not in _IMAGE_KIND:
    GEMINI_IMAGEN_MODEL = GEMINI_DEFAULT_IMAGE_MODEL
GEMINI_IMAGEN_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={key}"


KNOWN_INVALID_IMAGE_MODELS = {
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image",
    "gemini-3-pro-image",
}


def list_gemini_image_models():
    return list(GEMINI_IMAGE_MODELS)


def resolve_gemini_image_model(explicit: Optional[str] = None) -> str:
    """Xác định model ảnh Gemini: luôn tuân thủ triệt để model bạn đang chọn.
    - Nếu bạn chọn model trong danh sách (imagen-3.0-generate-002 hoặc fast) -> dùng đúng model đó.
    - Nếu bạn thử nghiệm bất kỳ model Imagen nào mới trong tương lai (imagen-*) -> cho phép chạy.
    - Nếu model lưu trong Cài đặt là model ảo cũ -> tự động dọn sạch về imagen-3.0-generate-002.
    - Nếu model mới gặp lỗi trên Google API, hệ thống sẽ tự động fallback về imagen-3.0-generate-002."""
    saved = ""
    try:
        import config
        s = config.read_settings()
        saved = str(((s.get("model") or {}).get("gemini_image_model") or "")).strip()
    except Exception:
        saved = ""

    if saved:
        if saved in _IMAGE_KIND:
            return saved
        if saved in KNOWN_INVALID_IMAGE_MODELS:
            # Dọn sạch model ảo cũ về model chuẩn
            try:
                import config
                s = config.read_settings()
                m = s.setdefault("model", {})
                m["gemini_image_model"] = GEMINI_DEFAULT_IMAGE_MODEL
                config.write_settings(s)
            except Exception:
                pass
            return GEMINI_DEFAULT_IMAGE_MODEL
        # Cho phép bất kỳ model Imagen hợp lệ nào mà người dùng muốn đổi/thử nghiệm
        if saved.startswith("imagen-"):
            return saved
        return GEMINI_DEFAULT_IMAGE_MODEL

    # Nếu settings chưa có, xét đối số explicit
    exp = (explicit or "").strip()
    if exp and (exp in _IMAGE_KIND or (exp.startswith("imagen-") and exp not in KNOWN_INVALID_IMAGE_MODELS)):
        return exp

    return GEMINI_IMAGEN_MODEL if GEMINI_IMAGEN_MODEL in _IMAGE_KIND else GEMINI_DEFAULT_IMAGE_MODEL


def get_gemini_api_key(explicit_key: Optional[str] = None) -> str:
    """Lay API key Gemini tu doi so, settings.json hoac bien moi truong."""
    if explicit_key and str(explicit_key).strip():
        return str(explicit_key).strip()
    try:
        import config
        s = config.read_settings()
        k = (s.get("model") or {}).get("gemini_api_key") or ""
        if k and not k.startswith("••••"):
            return str(k).strip()
    except Exception:
        pass
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_KEY"):
        val = os.getenv(var, "").strip()
        if val:
            return val
    return ""


def _resolve_gemini_aspect(aspect_ratio: Optional[str]) -> str:
    a = (aspect_ratio or "square").strip().lower()
    mapping = {
        "square": "1:1",
        "1:1": "1:1",
        "landscape": "16:9",
        "16:9": "16:9",
        "4:3": "4:3",
        "portrait": "9:16",
        "9:16": "9:16",
        "3:4": "3:4",
    }
    return mapping.get(a, "1:1")


def overlay_logo(
    image_bytes: bytes,
    logo_path: str,
    vault_root: Optional[str] = None,
    position: str = "top-left",
    scale_ratio: float = 0.22,
    margin_px: int = 36,
) -> bytes:
    """Dán logo thật (PNG trong suốt) từ dataset lên ảnh cover đã tạo.
    Đảm bảo logo chuẩn nhận diện thương hiệu, không méo, không ảo tưởng chữ.
    Nếu logo_path không hợp lệ hoặc PIL lỗi -> trả về nguyên image_bytes an toàn."""
    try:
        from PIL import Image
        import io
        vault = _resolve_vault(vault_root)
        lp = Path(logo_path).expanduser()
        lp = lp if lp.is_absolute() else (vault / lp)
        if not lp.is_file():
            return image_bytes

        base_img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        logo_img = Image.open(lp).convert("RGBA")

        bw, bh = base_img.size
        lw, lh = logo_img.size
        if lw <= 0 or lh <= 0:
            return image_bytes

        from PIL import ImageDraw
        target_w = max(140, int(bw * scale_ratio))
        target_h = max(40, int(lh * (target_w / float(lw))))
        logo_resized = logo_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

        pad_x = 16
        pad_y = 10
        card_w = target_w + pad_x * 2
        card_h = target_h + pad_y * 2

        if position == "top-right":
            x = max(10, bw - card_w - margin_px)
            y = margin_px
        else:
            x = margin_px
            y = margin_px

        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        # Thẻ nền trắng bo góc viền vàng kim bảo vệ logo sắc nét 100% trên mọi nền ảnh
        draw_ov.rounded_rectangle([x, y, x + card_w, y + card_h], radius=16, fill=(255, 255, 255, 250), outline=(255, 215, 0, 220), width=2)
        overlay.paste(logo_resized, (x + pad_x, y + pad_y), logo_resized)
        composed = Image.alpha_composite(base_img, overlay).convert("RGB")

        out_io = io.BytesIO()
        composed.save(out_io, format="JPEG", quality=95)
        return out_io.getvalue()
    except Exception:
        return image_bytes


def _extract_generate_images_b64(data: dict) -> Optional[str]:
    for img_obj in (data.get("generatedImages") or []):
        img_info = img_obj.get("image") or {}
        b64 = img_info.get("imageBytes") or img_info.get("data")
        if b64:
            return b64
    for img_obj in (data.get("images") or []):
        if isinstance(img_obj, str):
            return img_obj
        b64 = img_obj.get("imageBytes") or img_obj.get("bytesBase64Encoded")
        if b64:
            return b64
    return None


def _extract_gencontent_image_b64(data: dict) -> Optional[str]:
    for cand in (data.get("candidates") or []):
        parts = ((cand.get("content") or {}).get("parts") or [])
        for part in parts:
            inline = part.get("inlineData") or part.get("inline_data") or {}
            b64 = inline.get("data")
            if b64:
                return b64
    return None


def generate_antigravity_cli_image(
    prompt: str,
    aspect_ratio: str = "square",
    vault_root: Optional[str] = None,
    prefix: str = "agy-img",
    save_under: Optional[str] = None,
    logo_path: Optional[str] = None,
    course_id: Optional[str] = None,
    hotline: Optional[str] = None,
    footer_text: Optional[str] = None,
    timeout_s: float = 120.0,
) -> Optional[dict]:
    """Tận dụng trực tiếp Antigravity CLI (binary `agy`) đã kết nối trên VPS để tạo ảnh AI miễn phí 100%.
    Chạy lệnh `agy --dangerously-skip-permissions -p` gọi tool `generate_image` của Google Imagen."""
    try:
        s_dir = str(Path(__file__).resolve().parent)
        if s_dir not in sys.path:
            sys.path.insert(0, s_dir)
        from antigravity_cli import find_antigravity_cli
    except Exception:
        try:
            from server.antigravity_cli import find_antigravity_cli
        except Exception:
            find_antigravity_cli = None

    if not find_antigravity_cli:
        return None

    cli = find_antigravity_cli()
    if not cli or not Path(cli).is_file():
        return None

    import subprocess, time, os, io

    v_root = _resolve_vault(vault_root)
    clean_p = " ".join(prompt.replace('"', '').replace("'", "").split())
    if len(clean_p) > 400:
        clean_p = clean_p[:400]
    art_prompt = (
        f"Commercial advertising photography, professional tech education: {clean_p}. "
        "Modern computer lab, confident Vietnamese students, bright studio key lighting, 8k resolution, photorealistic, realistic skin texture, cinematic composition, absolutely no text, no watermark, no logo."
    )

    t0 = time.time()
    prompt_text = (
        f"Use the tool generate_image now with:\n"
        f"Prompt: {art_prompt}\n"
        f"ImageName: sao_viet_cover\n"
    )
    cmd = [
        cli,
        "--dangerously-skip-permissions",
        "-p",
        prompt_text,
    ]

    effective_timeout = max(timeout_s or 90.0, 120.0)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=effective_timeout)
    except Exception as e:
        print(f"[image_gen] Lỗi chạy agy generate_image: {e}", file=sys.stderr)
        return None

    home = Path.home()
    cand_dirs = [
        home / ".gemini" / "antigravity-cli" / "brain",
        home / ".gemini" / "antigravity-ide" / "brain",
        home / ".gemini" / "brain",
        home / ".gemini",
        Path.cwd() / ".gemini" / "brain",
    ]
    files = []
    for cd in cand_dirs:
        if cd.is_dir():
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                files.extend(list(cd.rglob(ext)))
    files = [str(f) for f in files if os.path.getmtime(str(f)) >= t0 - 5]

    if not files:
        return None

    latest_file = max(files, key=os.path.getmtime)
    with open(latest_file, "rb") as rf:
        raw_bytes = rf.read()

    # Dán logo thương hiệu Sao Việt nếu có
    if logo_path:
        raw_bytes = overlay_logo(raw_bytes, logo_path, vault_root=vault_root)

    # Thêm dải chân trang sang trọng (Hotline & Tên cơ sở) nếu có
    if hotline or footer_text:
        try:
            from PIL import Image, ImageDraw
            try:
                import banner_templates
            except ImportError:
                from server import banner_templates
            ai_img = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
            iw, ih = ai_img.size
            f_h = max(70, int(ih * 0.065))
            f_bar = Image.new("RGBA", (iw, f_h), (11, 35, 65, 235))
            f_draw = ImageDraw.Draw(f_bar)
            f_draw.line([(0, 0), (iw, 0)], fill=(255, 215, 0, 220), width=3)

            f_txt_l = f"📍 {footer_text.upper()}" if footer_text else "🌐 www.tinhocsaoviet.edu.vn"
            f_txt_r = f"📞 Hotline: {hotline}" if hotline else "ĐÀO TẠO THỰC CHIẾN KÈM 1-1"

            font_f = banner_templates.get_font(max(20, int(f_h * 0.36)), bold=True)
            f_draw.text((int(iw * 0.04), int(f_h * 0.28)), f_txt_l, font=font_f, fill="#E2E8F0")

            bb_r = f_draw.textbbox((0, 0), f_txt_r, font=font_f)
            rw_w = bb_r[2] - bb_r[0]
            f_draw.text((iw - rw_w - int(iw * 0.04), int(f_h * 0.28)), f_txt_r, font=font_f, fill="#FFD54F")

            ai_img.paste(f_bar, (0, ih - f_h), f_bar)
            out_b = io.BytesIO()
            ai_img.convert("RGB").save(out_b, format="JPEG", quality=95)
            raw_bytes = out_b.getvalue()
        except Exception:
            pass

    saved = save_image_bytes(
        raw_bytes, vault_root, prefix=prefix, ext=".jpg",
        subdir=save_under or "attachments/dataset/_xuat",
    )
    if not saved.get("ok"):
        return None

    return {
        "ok": True,
        "rel_path": saved["rel_path"],
        "abs_path": saved["abs_path"],
        "file": saved["file"],
        "aspect": aspect_ratio or "1:1",
        "provider": "antigravity-cli-imagen",
        "model": "google-imagen-via-agy",
        "prompt": prompt,
        "hotline": hotline,
        "footer_text": footer_text,
        "course_id": course_id,
    }



def _kit_field(md: str, *labels: str) -> str:
    """Trích xuất giá trị trường trong file markdown dạng '- Nhãn: Giá trị'."""
    for lab in labels:
        m = re.search(r"^[ \t]*[-*][ \t]*" + re.escape(lab) + r":[ \t]*(.*)$", md, re.M)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def _extract_frontmatter_field(text: str, field_name: str) -> str:
    """Trích xuất trường YAML frontmatter đơn giản."""
    m = re.search(r"^" + re.escape(field_name) + r":\s*(.*)$", text, re.M)
    return m.group(1).strip() if m else ""


def _clean_kit_value(value: Any, limit: int = 260) -> str:
    """Normalize a Brand Kit value before injecting it into an image prompt."""
    s = re.sub(r"\s+", " ", str(value or "")).strip()
    if not s:
        return ""
    if len(s) > limit:
        return s[:limit].rsplit(" ", 1)[0].strip()
    return s


def build_brand_guideline_prompt(kit: Optional[dict], provider: str = "") -> str:
    """Build a compact mandatory prompt block from wiki/brand-kits/*.md."""
    if not isinstance(kit, dict) or not kit:
        return ""

    fields = [
        ("Brand/page", kit.get("name")),
        ("Business name", kit.get("brand_name")),
        ("Primary color", kit.get("brand_color")),
        ("Secondary color", kit.get("secondary_color")),
        ("Fonts", kit.get("font")),
        ("Image style", kit.get("image_style")),
        ("Voice/tone", kit.get("tone")),
        ("Layout rules", kit.get("layout_rules")),
        ("Do not do", kit.get("donts")),
    ]
    lines = ["BRAND KIT RULES - follow these as mandatory visual constraints:"]
    for label, value in fields:
        val = _clean_kit_value(value)
        if val:
            lines.append(f"- {label}: {val}")

    logo = _clean_kit_value(kit.get("logo_path"))
    if logo:
        lines.append(f"- Official logo/reference asset: {logo}. Do not alter, recolor, distort, or invent a replacement logo.")

    lines.extend([
        "- Keep safe margins around all important subjects; never cover faces, hands, screens, or the main learning activity.",
        "- Use the brand palette and a premium modern education advertising look; avoid random colors, fake brands, clutter, and gimmicky stock-photo effects.",
        "- Do not render Vietnamese text inside the AI image. Leave clean copy space; Javis will overlay final Vietnamese text, logo, hotline, and badges by code.",
    ])
    if provider == "google":
        lines.append("- If generating a full AI poster/background, make it realistic and usable as an ad cover background, not a fantasy illustration.")
    elif provider == "openai":
        lines.append("- Use GPT Image for high-fidelity image generation/editing, while keeping brand assets and layout rules consistent.")
    return "\n".join(lines)


def apply_brand_guidelines(prompt: str, kit: Optional[dict], provider: str = "") -> str:
    """Append Brand Kit rules to an image prompt without changing the user's core brief."""
    base = (prompt or "").strip()
    guide = build_brand_guideline_prompt(kit, provider=provider)
    if not guide:
        return base
    return (base + "\n\n" + guide).strip()


def load_course_info(course_id_or_tag: str, vault_root: Optional[Union[str, Path]] = None) -> Optional[dict]:
    """Tải hồ sơ tri thức khóa học từ wiki/courses/<id>.md.
    Đảm bảo 100% dữ liệu chuyên môn (title, subtitle, highlights, tools, v.v.) chuẩn xác,
    chống tuyệt đối hiện tượng AI bịa đặt nội dung khóa học."""
    vault = _resolve_vault(vault_root)
    courses_dir = vault / "wiki" / "courses"
    if not courses_dir.is_dir():
        courses_dir = vault / "brains" / "Brain Default" / "wiki" / "courses"
        if not courses_dir.is_dir():
            return None

    target = (course_id_or_tag or "").strip().lower()
    if not target:
        return None

    matched_file = None
    for md_file in courses_dir.glob("*.md"):
        if md_file.name.startswith("_"):
            continue
        stem = md_file.stem.lower()
        if stem == target or stem.replace(" ", "") == target.replace(" ", "") or stem.replace("-", "") == target.replace("-", ""):
            matched_file = md_file
            break
        try:
            txt = md_file.read_text(encoding="utf-8")
        except OSError:
            continue
        m_id = re.search(r"^id:\s*(.*)$", txt, re.M)
        if m_id and m_id.group(1).strip().lower() == target:
            matched_file = md_file
            break
        m_aliases = re.search(r"^aliases:\s*\[(.*?)\]", txt, re.M)
        if m_aliases:
            aliases = [a.strip().lower() for a in m_aliases.group(1).split(",")]
            if target in aliases or any(target in a or a in target for a in aliases):
                matched_file = md_file
                break

    if not matched_file:
        return None

    try:
        content = matched_file.read_text(encoding="utf-8")
    except OSError:
        return None

    def _extract_list_items(header_regex: str, text: str) -> List[str]:
        items = []
        m = re.search(header_regex, text, re.I)
        if not m:
            return items
        start = m.end()
        lines = text[start:].splitlines()
        for l in lines:
            l_strip = l.strip()
            if not l_strip:
                continue
            if l_strip.startswith("##") or (l_strip.startswith("- **") and not l_strip.startswith("- **" + header_regex)):
                break
            if l_strip.startswith(("*", "-", "•")):
                val = re.sub(r"^[*•-]\s*", "", l_strip).strip()
                if val:
                    items.append(val)
            elif re.match(r"^\d+\.\s*", l_strip):
                val = re.sub(r"^\d+\.\s*", "", l_strip).strip()
                if val:
                    items.append(val)
        return items

    folder = matched_file.stem
    m_folder = re.search(r"^dataset_folder:\s*(?:attachments/dataset/)?([^/\n\r]+)", content, re.M)
    if m_folder:
        folder = m_folder.group(1).strip()

    titles = _extract_list_items(r"Tiêu đề gợi ý|Title Hooks", content)
    subtitles = _extract_list_items(r"Phụ đề gợi ý|Subtitle", content)
    highlights = _extract_list_items(r"Kho Highlights chuẩn|Highlights", content)
    badges = _extract_list_items(r"Huy hiệu gợi ý|Badge Text", content)

    layouts = []
    m_lay = re.search(r"Layout banner phù hợp[:\s]+([^\n\r]+)", content, re.I)
    if m_lay:
        layouts = [x.strip() for x in m_lay.group(1).split(",") if x.strip()]

    return {
        "id": matched_file.stem,
        "name": _extract_frontmatter_field(content, "name") or matched_file.stem,
        "folder": folder,
        "titles": titles,
        "subtitles": subtitles,
        "highlights": highlights,
        "badges": badges,
        "recommended_layouts": layouts,
        "raw_md": content,
    }


def load_brand_kit_info(page_identifier: Optional[str] = None, vault_root: Optional[Union[str, Path]] = None) -> Optional[dict]:
    """Tải Brand Kit của Fanpage từ wiki/brand-kits/<page>.md.
    Lấy đúng Hotline riêng của Fanpage, Tên giao dịch, Logo và Màu thương hiệu."""
    vault = _resolve_vault(vault_root)
    kit_dir = vault / "wiki" / "brand-kits"
    if not kit_dir.is_dir():
        kit_dir = vault / "brains" / "Brain Default" / "wiki" / "brand-kits"
        if not kit_dir.is_dir():
            return None

    target = str(page_identifier or "").strip().lower()
    matched_file = None

    if target in ("thsv-page-chinh", "page-chinh", "pagechinh", "chinh", "default", "_mac-dinh"):
        f = kit_dir / "_mac-dinh.md"
        if f.is_file():
            matched_file = f

    if not matched_file and target:
        for md_file in kit_dir.glob("*.md"):
            if md_file.name.startswith("_"):
                continue
            stem = md_file.stem.lower()
            if stem == target or stem.replace("-", "") == target.replace("-", ""):
                matched_file = md_file
                break
            try:
                txt = md_file.read_text(encoding="utf-8")
            except OSError:
                continue
            pid = _kit_field(txt, "Page ID", "page_id", "ID Fanpage", "ID Trang")
            if pid and pid.lower() == target:
                matched_file = md_file
                break
            pname = (_kit_field(txt, "Tên Fanpage") or "").lower()
            if pname and len(pname) >= 4 and (target == pname or target in pname or (len(target) >= 4 and pname in target)):
                matched_file = md_file
                break

    if not matched_file:
        for cand in ("royce-shop.md", "_mac-dinh.md"):
            f = kit_dir / cand
            if f.is_file():
                matched_file = f
                break

    if not matched_file:
        for md_file in kit_dir.glob("*.md"):
            if not md_file.name.startswith("_"):
                matched_file = md_file
                break

    if not matched_file:
        return None

    try:
        md = matched_file.read_text(encoding="utf-8")
    except OSError:
        return None

    stem = matched_file.stem
    name = _kit_field(md, "Tên Fanpage") or stem
    brand_name = _kit_field(md, "Tên giao dịch", "Tên thương hiệu") or "TRUNG TÂM TIN HỌC SAO VIỆT"
    hotline = _kit_field(md, "Hotline / Zalo", "Hotline riêng", "Hotline", "Hotline mặc định")
    if not hotline:
        def_file = kit_dir / "_mac-dinh.md"
        if def_file.is_file():
            try:
                def_md = def_file.read_text(encoding="utf-8")
                hotline = _kit_field(def_md, "Hotline mặc định", "Hotline / Zalo", "Hotline")
            except OSError:
                pass
    logo_path = _kit_field(md, "Logo chính", "Logo")
    logo_white = _kit_field(md, "Logo trắng")
    brand_color = _kit_field(md, "Màu chính")
    secondary_color = _kit_field(md, "Màu phụ")
    font = _kit_field(md, "Font", "Fonts")
    image_style = _kit_field(md, "Phong cách hình ảnh", "Phong cach hinh anh", "Image style")
    tone = _kit_field(md, "Tone of voice", "Giọng văn", "Giong van", "Tone")
    layout_rules = _kit_field(md, "Quy tắc bố cục", "Quy tac bo cuc", "Layout rules")
    donts = _kit_field(md, "Điều không được làm", "Dieu khong duoc lam", "Không được làm", "Khong duoc lam", "Do not do")
    address = _kit_field(md, "Cơ sở / địa chỉ", "Địa chỉ")

    return {
        "file": matched_file.name,
        "name": name,
        "brand_name": brand_name,
        "hotline": hotline or None,
        "logo_path": logo_path or None,
        "logo_white": logo_white or None,
        "brand_color": brand_color or None,
        "secondary_color": secondary_color or None,
        "font": font or None,
        "image_style": image_style or None,
        "tone": tone or None,
        "layout_rules": layout_rules or None,
        "donts": donts or None,
        "address": address or None,
        "raw_md": md,
    }


def parse_banner_content(
    prompt: str,
    course_id: Optional[str] = None,
    vault_root: Optional[Union[str, Path]] = None,
) -> dict:
    """Trích xuất tiêu đề, phụ đề, điểm nổi bật, huy hiệu và thư mục ảnh.
    Ưu tiên tải từ Hồ sơ tri thức chuẩn wiki/courses/<course_id>.md, chống bịa đặt nội dung.
    Đồng thời hỗ trợ nạp/ghi đè linh hoạt qua prompt."""
    p_lower = (prompt or "").lower()

    # 1. Xác định course_id
    detected_course = course_id
    if not detected_course:
        m_course = re.search(r"(?:khóa học|khoa hoc|chủ đề|chu de|môn học|mon hoc|course)\s*:\s*([^\n\r,.;]+)", prompt, re.IGNORECASE)
        if m_course:
            detected_course = m_course.group(1).strip()
        else:
            if any(k in p_lower for k in ("kế toán", "ke toan", "thuế", "thue", "misa", "báo cáo tài chính", "bctc", "accounting")):
                detected_course = "ke-toan"
            elif any(k in p_lower for k in ("đồ họa", "do hoa", "photoshop", "illustrator", "corel", "indesign", "graphic design")):
                detected_course = "do-hoa"
            elif any(k in p_lower for k in ("autocad", "cad", "bản vẽ", "ban ve", "cơ khí", "xây dựng", "solidworks")):
                detected_course = "ve-ky-thuat"
            elif any(k in p_lower for k in ("trẻ em", "tre em", "bé", "scratch", "khóa hè", "mua he", "kids")):
                detected_course = "tre-em"
            elif any(k in p_lower for k in ("ai", "chatgpt", "copilot", "vibe coding", "n8n", "tự động hóa", "tu dong hoa")):
                detected_course = "tin-hoc _ai"
            elif any(k in p_lower for k in ("tin học", "tin hoc", "excel", "word", "powerpoint", "office")):
                detected_course = "tin-hoc _ai"

    course_data = load_course_info(detected_course or "tin-hoc _ai", vault_root=vault_root)

    # 2. Dữ liệu nền tảng từ Course Kit (Chuẩn xác, chống bịa đặt)
    if course_data:
        folder = course_data.get("folder", "tin-hoc _ai")
        title = course_data["titles"][0] if course_data.get("titles") else "TIN HỌC VĂN PHÒNG"
        subtitle = course_data["subtitles"][0] if course_data.get("subtitles") else None
        highlights = course_data["highlights"][:3] if course_data.get("highlights") else None
        badge_text = course_data["badges"][0] if course_data.get("badges") else None
        recommended_layouts = course_data.get("recommended_layouts", [])
    else:
        folder = "tin-hoc _ai"
        title = "TIN HỌC VĂN PHÒNG CHUYÊN NGHIỆP"
        subtitle = None
        highlights = None
        badge_text = None
        recommended_layouts = []

    # 3. Ghi đè có chủ đích từ Prompt
    m_title = re.search(r"(?:tiêu đề|title)\s*:\s*([^\n\r,.;]+)", prompt, re.IGNORECASE)
    if m_title:
        val = m_title.group(1).strip().strip('"\'')
        if len(val) >= 4:
            title = val.upper()

    m_sub = re.search(r"(?:phụ đề|subtitle)\s*:\s*([^\n\r,.;]+)", prompt, re.IGNORECASE)
    if m_sub:
        val = m_sub.group(1).strip().strip('"\'')
        if len(val) >= 4:
            subtitle = val

    # Badge text
    if any(k in p_lower for k in ("không badge", "khong badge", "bỏ badge", "bo badge", "không huy hiệu", "khong huy hieu", "no badge")):
        badge_text = None
    else:
        m_badge = re.search(r"(?:huy hiệu|badge|ưu đãi|uu dai)\s*:\s*([^\n\r,.;]+)", prompt, re.IGNORECASE)
        if m_badge:
            val = m_badge.group(1).strip().strip('"\'')
            if len(val) >= 2:
                badge_text = val.upper()

    # Highlights
    if any(k in p_lower for k in ("tối giản", "toi gian", "minimalist", "không bullet", "khong bullet", "không gạch đầu dòng", "no bullet")):
        highlights = None
    else:
        bullet_items = re.findall(r"^[ \t]*[-*•]\s*([^\n\r]+)", prompt, re.M)
        if bullet_items:
            highlights = [b.strip() for b in bullet_items[:3] if b.strip()]

    # Template
    tpl = None
    if any(k in p_lower for k in ("cinematic", "photo_first", "ảnh thật", "anh that", "nguyên bản", "nguyen ban", "tự nhiên", "tu nhien")):
        tpl = "photo_first_cinematic"
    elif "bauhaus" in p_lower:
        tpl = "bauhaus_grid"
    else:
        for cand in (
            "modern_ribbon_wave",
            "photo_first_cinematic",
            "bento_box",
            "curved_window",
            "floating_card",
            "bottom_bar",
            "bauhaus_grid",
        ):
            if cand in p_lower:
                tpl = cand
                break

    if not tpl and recommended_layouts:
        tpl = random.choice(recommended_layouts)

    palette_name = None
    pal_map = {
        "sapphire": "royal_sapphire",
        "navy": "royal_sapphire",
        "ruby": "ruby_urgency",
        "wine": "ruby_urgency",
        "do": "ruby_urgency",
        "đỏ": "ruby_urgency",
        "violet": "cosmic_violet",
        "purple": "cosmic_violet",
        "tim": "cosmic_violet",
        "tím": "cosmic_violet",
        "emerald": "emerald_growth",
        "green": "emerald_growth",
        "xanh la": "emerald_growth",
        "xanh lá": "emerald_growth",
        "editorial": "warm_editorial",
        "mocha": "warm_editorial",
        "nau": "warm_editorial",
        "nâu": "warm_editorial",
    }
    for kw, p_id in pal_map.items():
        if kw in p_lower:
            palette_name = p_id
            break

    return {
        "title": title,
        "subtitle": subtitle,
        "highlights": highlights,
        "badge_text": badge_text,
        "folder": folder,
        "template_name": tpl,
        "palette_name": palette_name,
        "course_id": detected_course,
    }


def generate_authentic_banner_cover(
    vault_root: Optional[str] = None,
    page_id: Optional[str] = None,
    course_id: Optional[str] = None,
    brand_kit: Optional[dict] = None,
    logo_path: Optional[str] = None,
    raw_path: Optional[str] = None,
    prompt: str = "",
    template_name: Optional[str] = None,
    save_under: Optional[str] = None,
    prefix: str = "banner-cover",
    hotline: Optional[str] = None,
    footer_text: Optional[str] = None,
    badge_text: Optional[str] = None,
    highlights: Optional[List[str]] = None,
) -> Optional[dict]:
    """Tạo cover Kiểu 2: Ảnh thật lớp học từ dataset kết hợp layout đồ họa Agency 2026.
    Tự động liên kết Brand Kit (Hotline, Logo, Tên Fanpage) và Course Kit (Dữ liệu khóa học chuẩn xác).
    Thích ứng linh hoạt: Khi không có hotline, badge, hoặc highlights, layout tự co giãn hoàn hảo."""
    try:
        try:
            import banner_templates
        except ImportError:
            try:
                from server import banner_templates
            except ImportError:
                sys.path.insert(0, str(Path(__file__).resolve().parent))
                import banner_templates
        vault = _resolve_vault(vault_root)

        # 1. Tải Brand Kit theo Fanpage
        kit = brand_kit if isinstance(brand_kit, dict) else load_brand_kit_info(page_id, vault_root=vault)

        # Trích xuất Hotline và Footer chuẩn từ Brand Kit (Không hardcode!)
        final_hotline = hotline if hotline is not None else (kit.get("hotline") if kit else None)
        final_footer = footer_text if footer_text is not None else (
            (kit.get("brand_name") if kit else None) or (kit.get("name") if kit else None)
        )

        # 2. Phân tích nội dung khóa học
        content = parse_banner_content(prompt, course_id=course_id, vault_root=vault)
        if badge_text is not None:
            content["badge_text"] = badge_text
        if highlights is not None:
            content["highlights"] = highlights

        # 3. Xác định ảnh thật lớp học
        raw_file = None
        if raw_path:
            rp = Path(raw_path).expanduser()
            rp = rp if rp.is_absolute() else (vault / rp)
            if rp.is_file():
                raw_file = rp

        if not raw_file:
            chosen_rel = pick_dataset_photo(str(vault), folder=content["folder"], random_choice=True)
            if chosen_rel:
                raw_file = vault / chosen_rel

        if not raw_file or not raw_file.is_file():
            for fld in (content["folder"], "tin-hoc _ai", "ke-toan", "do-hoa", "ve-ky-thuat"):
                d_set = vault / "attachments" / "dataset" / fld
                if d_set.is_dir():
                    for f in d_set.iterdir():
                        if f.is_file() and f.suffix.lower() in _IMG_MIME and " (1)" not in f.name:
                            raw_file = f
                            break
                if raw_file:
                    break

        if not raw_file or not raw_file.is_file():
            return None

        # 4. Xác định logo thương hiệu (Ưu tiên Logo trong Brand Kit)
        logo_file = None
        if logo_path:
            lp = Path(logo_path).expanduser()
            lp = lp if lp.is_absolute() else (vault / lp)
            if lp.is_file():
                logo_file = lp

        if not logo_file and kit and kit.get("logo_path"):
            lp = vault / kit["logo_path"]
            if lp.is_file():
                logo_file = lp

        if not logo_file:
            for def_l in [
                vault / "attachments" / "dataset" / "chung" / "thsv-logo-2025.png",
                vault / "attachments" / "dataset" / "chung" / "thsv-logo-big.png",
            ]:
                if def_l.is_file():
                    logo_file = def_l
                    break

        # 5. Chuẩn bị đường dẫn lưu
        sub = save_under or "attachments/dataset/_xuat"
        target_dir = (vault / sub).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{prefix}-{int(time.time())}-{uuid.uuid4().hex[:6]}.jpg"
        out_file = target_dir / fname

        # Production Facebook covers keep the dataset photo as the visual truth,
        # but rotate among safe creative layouts so posts do not look cloned.
        safe_templates = getattr(banner_templates, "REAL_PHOTO_TEMPLATE_CHOICES", ("bottom_bar",))
        chosen_template = template_name or random.choice(tuple(safe_templates))

        res_path = banner_templates.generate_authentic_banner(
            classroom_img_path=raw_file,
            out_path=out_file,
            logo_path=logo_file,
            title=content["title"],
            subtitle=content["subtitle"],
            highlights=content["highlights"],
            badge_text=content["badge_text"],
            footer_text=final_footer,
            hotline=final_hotline,
            template_name=chosen_template,
            palette_name=content.get("palette_name"),
        )

        if not res_path or not out_file.is_file():
            return None

        rel_path = str(out_file.relative_to(vault)).replace("\\", "/")
        return {
            "ok": True,
            "rel_path": rel_path,
            "abs_path": str(out_file),
            "file": fname,
            "aspect": "1:1",
            "provider": "authentic-classroom-banner",
            "model": f"banner-layout-{chosen_template or 'random'}",
            "prompt": prompt or content["title"],
            "hotline": final_hotline,
            "footer_text": final_footer,
            "course_id": content.get("course_id"),
        }
    except Exception as e:
        print(f"[image_gen] Lỗi tạo authentic banner: {e}", file=sys.stderr)
        return None


def create_dataset_fallback_cover(
    vault_root: Optional[str] = None,
    page_id: Optional[str] = None,
    course_id: Optional[str] = None,
    brand_kit: Optional[dict] = None,
    logo_path: Optional[str] = None,
    raw_path: Optional[str] = None,
    save_under: Optional[str] = None,
    prefix: str = "gemini-img",
    prompt: str = "",
    template_name: Optional[str] = None,
    hotline: Optional[str] = None,
    footer_text: Optional[str] = None,
) -> Optional[dict]:
    """Tạo cover Kiểu 2 từ ảnh thật lớp học trong dataset + dán layout đồ họa thương hiệu chuẩn.
    Dùng khi Google Image API không khả dụng (404/quota), đảm bảo luôn có ảnh cover chuẩn 1:1 để đăng Facebook."""
    # Ưu tiên tạo banner đồ họa hoàn chỉnh với 8 layouts chuẩn Agency
    res = generate_authentic_banner_cover(
        vault_root=vault_root,
        page_id=page_id,
        course_id=course_id,
        brand_kit=brand_kit,
        logo_path=logo_path,
        raw_path=raw_path,
        prompt=prompt,
        template_name=template_name,
        save_under=save_under,
        prefix=prefix,
        hotline=hotline,
        footer_text=footer_text,
    )
    if res and res.get("ok"):
        return res

    # Fallback tối hậu nếu vì lý do gì đó banner_templates không sinh được
    try:
        from PIL import Image
        import io
        vault = _resolve_vault(vault_root)

        raw_file = None
        if raw_path:
            rp = Path(raw_path).expanduser()
            rp = rp if rp.is_absolute() else (vault / rp)
            if rp.is_file():
                raw_file = rp
        if not raw_file:
            raw_rel = first_dataset_photo(str(vault), "tin-hoc _ai")
            if raw_rel:
                raw_file = vault / raw_rel

        if not raw_file or not raw_file.is_file():
            d_set = vault / "attachments" / "dataset"
            for sub in ("tin-hoc _ai", "ke-toan", "do-hoa", "ve-ky-thuat"):
                s_dir = d_set / sub
                if s_dir.is_dir():
                    for f in s_dir.iterdir():
                        if f.is_file() and f.suffix.lower() in _IMG_MIME and " (1)" not in f.name:
                            raw_file = f
                            break
                if raw_file:
                    break

        if not raw_file or not raw_file.is_file():
            return None

        img = Image.open(raw_file).convert("RGB")
        w, h = img.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        cropped = img.crop((left, top, left + min_dim, top + min_dim))
        resized = cropped.resize((1200, 1200), Image.Resampling.LANCZOS)

        logo_file = None
        if logo_path:
            lp = Path(logo_path).expanduser()
            lp = lp if lp.is_absolute() else (vault / lp)
            if lp.is_file():
                logo_file = lp
        if not logo_file:
            def_logo = vault / "attachments/dataset/chung/thsv-logo-2025.png"
            if def_logo.is_file():
                logo_file = def_logo

        if logo_file and logo_file.is_file():
            logo_img = Image.open(logo_file).convert("RGBA")
            lw, lh = logo_img.size
            target_w = int(1200 * 0.22)
            target_h = int(lh * (target_w / float(lw)))
            logo_resized = logo_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            overlay = Image.new("RGBA", (1200, 1200), (0, 0, 0, 0))
            overlay.paste(logo_resized, (36, 36), logo_resized)
            composed = Image.alpha_composite(resized.convert("RGBA"), overlay).convert("RGB")
        else:
            composed = resized

        out_io = io.BytesIO()
        composed.save(out_io, format="JPEG", quality=95)
        raw_bytes = out_io.getvalue()

        saved = save_image_bytes(
            raw_bytes, vault_root, prefix=prefix, ext=".jpg",
            subdir=save_under or "attachments/dataset/_xuat",
        )
        if not saved.get("ok"):
            return None

        return {
            "ok": True,
            "rel_path": saved["rel_path"],
            "abs_path": saved["abs_path"],
            "file": saved["file"],
            "aspect": "1:1",
            "provider": "dataset-brand-cover",
            "model": "dataset-real-photo-with-brand-logo",
            "prompt": prompt or "Cover Kiểu 2 từ ảnh lớp học thật dataset và logo thương hiệu Sao Việt",
        }
    except Exception:
        return None


async def generate_gemini(
    prompt: str,
    aspect_ratio: str = "square",
    vault_root: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout_s: float = 90.0,
    prefix: str = "gemini-img",
    model: Optional[str] = None,
    reference_images: Optional[list] = None,
    save_under: Optional[str] = None,
    style_preference: Optional[str] = None,
    page_id: Optional[str] = None,
    course_id: Optional[str] = None,
    brand_kit: Optional[dict] = None,
    hotline: Optional[str] = None,
    footer_text: Optional[str] = None,
) -> dict:
    """Tạo 1 ảnh cover Fanpage chuẩn Facebook với tỷ lệ 7/3:
    1. 70% Tỷ lệ: Sinh Kiểu 2 (Ảnh thật lớp học dataset + Layout đồ họa Agency 2026).
    2. 30% Tỷ lệ: Sinh Kiểu 1 (AI 3D Poster sinh từ prompt qua Google Imagen / Gemini).
    3. Tự động liên kết Brand Kit (Hotline, Logo, Tên Fanpage) và Course Kit (Chống bịa đặt nội dung).
    4. Thích ứng hoàn hảo khi thiếu thông tin, layout tự co giãn chuẩn xác."""
    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "error": "Thiếu mô tả ảnh (prompt)."}

    aspect = _resolve_gemini_aspect(aspect_ratio)
    chosen_model = resolve_gemini_image_model(model)

    v_root = _resolve_vault(vault_root)
    kit = brand_kit if isinstance(brand_kit, dict) else load_brand_kit_info(page_id, vault_root=v_root)
    resolved_hotline = hotline if hotline is not None else (kit.get("hotline") if kit else None)
    resolved_footer = footer_text if footer_text is not None else (
        (kit.get("brand_name") if kit else None) or (kit.get("name") if kit else None)
    )

    logo_file = None
    raw_photo_file = None
    for p in (reference_images or []):
        s_p = str(p).replace("\\", "/").strip()
        if "logo" in s_p.lower():
            logo_file = s_p
        elif not raw_photo_file and s_p.endswith((".jpg", ".png", ".jpeg", ".webp")):
            raw_photo_file = s_p

    if not raw_photo_file:
        content = parse_banner_content(prompt, course_id=course_id, vault_root=v_root)
        chosen_rel = pick_dataset_photo(str(v_root), folder=content.get("folder", "tin-hoc _ai"), random_choice=True)
        if chosen_rel:
            raw_photo_file = chosen_rel

    if not logo_file and kit and kit.get("logo_path"):
        lp = v_root / kit["logo_path"]
        if lp.is_file():
            logo_file = str(kit["logo_path"])

    if not logo_file:
        for cand in [
            "attachments/dataset/chung/thsv-logo-2025.png",
            "attachments/dataset/chung/thsv-logo-big.png",
        ]:
            if (v_root / cand).is_file():
                logo_file = cand
                break

    p_lower = prompt.lower()
    allow_ai_full = (
        style_preference in ("ai_full", "pure_ai", "generated_poster") or
        any(k in p_lower for k in (
            "ai_full", "pure_ai", "generated_poster", "full ai", "ai poster",
            "poster ai toan phan", "poster ai toàn phần", "tao moi bang ai", "tạo mới bằng ai",
        ))
    )
    force_dataset_photo = (
        style_preference != "ai_full" and
        not allow_ai_full and
        (
            style_preference in (None, "", "authentic_photo", "facebook_cover", "real_photo_cover") or
            bool(raw_photo_file) or
            any(k in p_lower for k in (
                "chỉ dùng ảnh thật", "chi dung anh that", "ảnh thật dataset", "anh that dataset",
                "không dùng ai", "khong dung ai", "dùng ảnh có sẵn", "dung anh co san",
                "không tạo ai", "khong tao ai", "không gen ai", "khong gen ai",
                "cover facebook", "fanpage", "ảnh đầu", "anh dau", "bài đăng", "bai dang",
            ))
        )
    )

    if force_dataset_photo:
        banner_res = generate_authentic_banner_cover(
            vault_root=vault_root,
            page_id=page_id,
            course_id=course_id,
            brand_kit=kit,
            logo_path=logo_file,
            raw_path=raw_photo_file,
            prompt=prompt,
            save_under=save_under,
            prefix=prefix,
            hotline=resolved_hotline,
            footer_text=resolved_footer,
        )
        if banner_res and banner_res.get("ok"):
            return banner_res


    # tuyệt đối không để AI tự vẽ chữ dẫn đến lỗi chính tả ("PHỞNG", "ŨNG", "THỰC HẢN").
    clean_prompt = re.sub(r'["“][^"”]+["”]', '', prompt)
    for kw in ("hiển thị chữ", "vẽ chữ", "ghi chữ", "with text", "featuring text"):
        clean_prompt = re.sub(re.escape(kw), '', clean_prompt, flags=re.IGNORECASE)
    clean_prompt = " ".join(clean_prompt.split())
    if not clean_prompt:
        clean_prompt = "Commercial advertising photography, professional tech classroom, confident Vietnamese learner working on laptop, modern corporate office"

    block_5 = (
        "[BLOCK 5 - STRICT NEGATIVE]: Absolutely NO text, NO words, NO letters, NO numbers, NO alphabet, NO typography, NO watermark, NO logo, NO banner, NO buttons, NO distorted hands, NO duplicate faces, NO dark neon circuit lines, clean smooth empty left side reserved as copy space."
    )

    creative_instructions = (
        "\n\nCRITICAL CREATIVE DIRECTOR & BRAND RULES:\n"
        "[BLOCK 1 - SUBJECT]: Authentic Vietnamese/Asian learner or professional in a modern, well-lit tech classroom or corporate office, confident and focused expression, grounded in the attached reference dataset.\n"
        "[BLOCK 2 - COMPOSITION]: Square 1:1 framing (2000x2000 px). Position subject at lower-third or golden ratio. Leave generous, clean negative space at the top third or left side for official brand logo and graphic overlay.\n"
        "[BLOCK 3 - LIGHTING & BRAND COLORS]: Commercial advertising studio key lighting, warm and bright atmosphere. Deep Royal Navy Blue palette with vibrant Golden Yellow accents.\n"
        "[BLOCK 4 - STYLE]: Commercial education advertising photography, 8k resolution, crisp focus, natural skin texture, realistic, no uncanny valley.\n"
        + block_5
    )
    full_prompt = clean_prompt + creative_instructions
    full_prompt = apply_brand_guidelines(full_prompt, kit, provider="google")

    key = get_gemini_api_key(api_key)

    b64 = None
    err = None

    if key:
        async def _call_generate_images(m_id: str, p_text: str) -> tuple[Optional[str], Optional[str]]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_id}:generateImages?key={key}"
                payload = {"prompt": p_text, "numberOfImages": 1, "aspectRatio": aspect}
                resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                if resp.status_code == 200:
                    img_data = _extract_generate_images_b64(resp.json())
                    if img_data:
                        return img_data, None
                return None, f"generateImages {resp.status_code}: {resp.text[:300]}"
            except Exception as e:
                return None, str(e)

        async def _call_generate_content(m_id: str, p_text: str) -> tuple[Optional[str], Optional[str]]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_id}:generateContent?key={key}"
                parts = []
                # Đính kèm ảnh thật từ dataset làm ảnh tham chiếu (multimodal conditioning)
                if raw_photo_file:
                    rp = Path(raw_photo_file)
                    rp = rp if rp.is_absolute() else (v_root / rp)
                    if rp.is_file() and rp.suffix.lower() in _IMG_MIME:
                        try:
                            with open(rp, "rb") as rf:
                                r_bytes = rf.read()
                            parts.append({
                                "inlineData": {
                                    "mimeType": _IMG_MIME.get(rp.suffix.lower(), "image/jpeg"),
                                    "data": base64.b64encode(r_bytes).decode("utf-8"),
                                }
                            })
                        except Exception:
                            pass
                parts.append({"text": p_text})
                payload = {
                    "contents": [{"parts": parts}],
                    "generationConfig": {
                        "responseModalities": ["TEXT", "IMAGE"],
                        "imageConfig": {"aspectRatio": aspect},
                    },
                }
                resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                if resp.status_code == 200:
                    img_data = _extract_gencontent_image_b64(resp.json())
                    if img_data:
                        return img_data, None
                return None, f"generateContent {resp.status_code}: {resp.text[:300]}"
            except Exception as e:
                return None, str(e)

        async def _call_predict(m_id: str, p_text: str) -> tuple[Optional[str], Optional[str]]:
            try:
                url = GEMINI_IMAGEN_URL.format(model=m_id, key=key)
                payload = {
                    "instances": [{"prompt": p_text}],
                    "parameters": {"sampleCount": 1, "aspectRatio": aspect, "outputMimeType": "image/jpeg"},
                }
                resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                if resp.status_code == 200:
                    preds = (resp.json().get("predictions") or [])
                    if preds and preds[0].get("bytesBase64Encoded"):
                        return preds[0]["bytesBase64Encoded"], None
                return None, f"predict {resp.status_code}: {resp.text[:300]}"
            except Exception as e:
                return None, str(e)

        try:
            timeout = httpx.Timeout(timeout_s, connect=20.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                # 1. Thử theo model người dùng chọn (hỗ trợ cả Imagen 4 và Imagen 3)
                if "image" in chosen_model.lower():
                    b64, err = await _call_generate_content(chosen_model, full_prompt)
                else:
                    b64, err = await _call_generate_images(chosen_model, full_prompt)
                    if not b64:
                        b64, err = await _call_predict(chosen_model, full_prompt)

                # 2. Thử fallback sang các endpoint Gemini Image thế hệ mới nếu model chính lỗi
                if not b64:
                    b64, err = await _call_generate_content("gemini-2.5-flash-image", full_prompt)
                if not b64:
                    b64, err = await _call_generate_content("gemini-3.1-flash-image", full_prompt)

                if b64:
                    raw_bytes = base64.b64decode(b64)
                    # Ghép Logo 3D và chữ tiếng Việt Unicode chuẩn nét căng lên visual Imagen
                    try:
                        import banner_templates
                        ai_base_img = Image.open(io.BytesIO(raw_bytes))
                        content = parse_banner_content(prompt, course_id=course_id, vault_root=v_root)
                        lp = Path(logo_file) if logo_file else None
                        if lp and not lp.is_absolute():
                            lp = v_root / lp
                        enhanced_img = banner_templates.render_ai_enhanced_banner(
                            ai_background_img=ai_base_img,
                            logo_path=lp,
                            title=content["title"],
                            subtitle=content["subtitle"],
                            highlights=content["highlights"],
                            badge_text=content["badge_text"],
                            footer_text=resolved_footer,
                            hotline=resolved_hotline,
                        )
                        out_buf = io.BytesIO()
                        enhanced_img.save(out_buf, format="JPEG", quality=95)
                        raw_bytes = out_buf.getvalue()
                    except Exception as e:
                        if logo_file:
                            raw_bytes = overlay_logo(raw_bytes, logo_file, vault_root=vault_root)

                    saved = save_image_bytes(
                        raw_bytes, vault_root, prefix=prefix, ext=".jpg",
                        subdir=save_under or "attachments/dataset/_xuat",
                    )
                    if saved.get("ok"):
                        return {
                            "ok": True,
                            "rel_path": saved["rel_path"],
                            "abs_path": saved["abs_path"],
                            "file": saved["file"],
                            "aspect": aspect,
                            "provider": "google-imagen",
                            "model": chosen_model,
                            "prompt": prompt,
                            "hotline": resolved_hotline,
                            "footer_text": resolved_footer,
                            "course_id": content.get("course_id"),
                        }
        except Exception as e:
            err = str(e)

    # Nếu không có Google AI Studio API Key hoặc API lỗi: TẬN DỤNG TRỰC TIẾP ANTIGRAVITY CLI ĐANG KẾT NỐI TRÊN VPS!
    if not b64:
        agy_res = generate_antigravity_cli_image(
            prompt=full_prompt,
            aspect_ratio=aspect,
            vault_root=vault_root,
            prefix=prefix,
            save_under=save_under,
            logo_path=logo_file,
            course_id=course_id,
            hotline=resolved_hotline,
            footer_text=resolved_footer,
            timeout_s=timeout_s,
        )
        if agy_res and agy_res.get("ok"):
            return agy_res


    # 3. TỰ ĐỘNG CỨU HỘ: Tạo Cover Kiểu 2 từ ảnh thật lớp học dataset + logo Sao Việt chuẩn
    fallback_res = create_dataset_fallback_cover(
        vault_root=vault_root,
        page_id=page_id,
        course_id=course_id,
        brand_kit=kit,
        logo_path=logo_file,
        raw_path=raw_photo_file,
        save_under=save_under,
        prefix=prefix,
        prompt=prompt,
        hotline=resolved_hotline,
        footer_text=resolved_footer,
    )
    if fallback_res and fallback_res.get("ok"):
        return fallback_res

    return {"ok": False, "error": err or "Không thể tạo ảnh (cả Google API và dataset fallback đều thất bại)."}
