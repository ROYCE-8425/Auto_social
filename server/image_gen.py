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
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import httpx

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


def _resolve_vault(vault_root: Optional[str]) -> Path:
    if vault_root and os.path.isdir(vault_root):
        return Path(vault_root)
    return Path(_default_vault())


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


def save_png_b64(b64: str, vault_root: Optional[str], prefix: str = "javis-img") -> dict:
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
    adir = _attachments_dir(vault)
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
                           images: Optional[list] = None) -> dict:
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

    saved = save_png_b64(b64, vault_root, prefix="javis-img")
    if not saved.get("ok"):
        return saved
    return {"ok": True, "rel_path": saved["rel_path"], "abs_path": saved["abs_path"],
            "file": saved["file"], "size": size, "quality": quality, "aspect": aspect,
            "provider": "openai-codex", "prompt": prompt, "refs": len(data_urls)}


# ---------------------------------------------------------------------------
# Google Gemini / Imagen + Nano Banana (generateContent)
# ---------------------------------------------------------------------------
# Imagen (:predict) và Gemini image (:generateContent) dùng CÙNG API key Gemini.
# Chọn model ở trang Models (model.gemini_image_model) hoặc tham số tool.
GEMINI_IMAGE_MODELS = [
    {"id": "imagen-4.0-generate-001", "label": "Imagen 4", "kind": "predict"},
    {"id": "imagen-4.0-fast-generate-001", "label": "Imagen 4 Fast", "kind": "predict"},
    {"id": "imagen-4.0-ultra-generate-001", "label": "Imagen 4 Ultra", "kind": "predict"},
    {"id": "imagen-3.0-generate-002", "label": "Imagen 3", "kind": "predict"},
    {"id": "gemini-2.5-flash-image", "label": "Nano Banana (2.5 Flash Image)", "kind": "generateContent"},
    {"id": "gemini-3.1-flash-image", "label": "Nano Banana 2 (3.1 Flash Image)", "kind": "generateContent"},
    {"id": "gemini-3-pro-image", "label": "Nano Banana Pro (3 Pro Image)", "kind": "generateContent"},
]
_IMAGE_KIND = {m["id"]: m["kind"] for m in GEMINI_IMAGE_MODELS}
GEMINI_IMAGEN_MODEL = os.getenv("JAVIS_GEMINI_IMAGEN_MODEL", "imagen-4.0-generate-001")
GEMINI_IMAGEN_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={key}"
GEMINI_GENCONTENT_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"


def list_gemini_image_models():
    return list(GEMINI_IMAGE_MODELS)


def resolve_gemini_image_model(explicit: Optional[str] = None) -> str:
    raw = (explicit or "").strip()
    if not raw:
        try:
            import config
            raw = str(((config.read_settings().get("model") or {}).get("gemini_image_model") or "")).strip()
        except Exception:
            raw = ""
    if not raw:
        raw = GEMINI_IMAGEN_MODEL
    if raw not in _IMAGE_KIND:
        raw = GEMINI_IMAGEN_MODEL if GEMINI_IMAGEN_MODEL in _IMAGE_KIND else GEMINI_IMAGE_MODELS[0]["id"]
    return raw


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


def _extract_gencontent_image_b64(data: dict) -> Optional[str]:
    for cand in (data.get("candidates") or []):
        parts = ((cand.get("content") or {}).get("parts") or [])
        for part in parts:
            inline = part.get("inlineData") or part.get("inline_data") or {}
            b64 = inline.get("data")
            if b64:
                return b64
    return None


def _gemini_ref_parts(paths, vault_root) -> tuple[list, Optional[str]]:
    """parts inlineData từ file trong vault. Lỗi -> (None, msg)."""
    parts = []
    for raw in (paths or [])[:MAX_REF_IMAGES]:
        rec = read_reference_image(str(raw), vault_root)
        if not rec.get("ok"):
            return [], rec.get("error") or "ảnh tham chiếu lỗi"
        url = rec.get("data_url") or ""
        if not url.startswith("data:") or "," not in url:
            return [], "ảnh tham chiếu không đọc được"
        head, b64 = url.split(",", 1)
        mime = "image/png"
        if "image/jpeg" in head:
            mime = "image/jpeg"
        elif "image/webp" in head:
            mime = "image/webp"
        parts.append({"inline_data": {"mime_type": mime, "data": b64}})
    return parts, None


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
) -> dict:
    """Tạo 1 ảnh bằng Imagen (:predict) hoặc Gemini image / Nano Banana (:generateContent).
    Có reference_images (logo + ảnh lớp) thì luôn generateContent, dán pixel logo, cấm vẽ path."""
    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "error": "Thieu mo ta anh (prompt)."}

    key = get_gemini_api_key(api_key)
    if not key:
        return {
            "ok": False,
            "error": "Chua co API key Gemini. Hay luu key vao Cai dat > Models hoac dat bien moi truong GEMINI_API_KEY."
        }

    aspect = _resolve_gemini_aspect(aspect_ratio)
    model = resolve_gemini_image_model(model)
    kind = _IMAGE_KIND.get(model, "predict")
    refs = [p for p in (reference_images or []) if str(p).strip()]
    if refs:
        kind = "generateContent"
        if "image" not in (model or "").lower():
            model = "gemini-2.5-flash-image"
        prompt += (
            "\n\nCRITICAL CREATIVE & BRAND INSTRUCTIONS:\n"
            "1. STRICTLY NO ENGLISH TEXT: All typography and badges MUST be in Vietnamese with proper diacritics (e.g. 'TIN HỌC VĂN PHÒNG', 'ƯU ĐÃI 30% HỌC PHÍ', 'DẠY KÈM 1-1'). NEVER generate English words like 'Enroll now', 'Professional Office IT', 'Register now', 'Course'.\n"
            "2. GROUNDED IN DATASET: Take direct inspiration from the real Vietnamese students and modern classroom in the attached reference image(s). Maintain authentic Asian/Vietnamese subjects in a professional, friendly learning environment. NEVER invent Caucasian/Western stock faces.\n"
            "3. EYE-CATCHING & VIBRANT (BẮT MẮT THU HÚT): Create a premium commercial education poster. Bright, clean studio lighting, high contrast, vivid Royal Blue and Golden Yellow brand colors, glossy 3D floating software icons with soft drop shadows, and sharp clean typography that pops on the mobile newsfeed.\n"
            "4. CLEAN LAYOUT: Logo placed naturally in top corner. NEVER draw file paths (attachments/...) or empty buttons. Absolutely NO dark sci-fi neon circuit boards or murky backgrounds."
        )

    try:
        timeout = httpx.Timeout(timeout_s, connect=20.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            if kind == "generateContent":
                url = GEMINI_GENCONTENT_URL.format(model=model, key=key)
                parts = [{"text": prompt}]
                extra, err = _gemini_ref_parts(refs, vault_root)
                if err:
                    return {"ok": False, "error": err}
                parts.extend(extra)
                payload = {
                    "contents": [{"parts": parts}],
                    "generationConfig": {
                        "responseModalities": ["IMAGE", "TEXT"],
                        "imageConfig": {"aspectRatio": aspect},
                    },
                }
                resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                if resp.status_code != 200:
                    body = resp.text[:500]
                    return {"ok": False, "error": f"Google image API {resp.status_code}: {body}"}
                b64 = _extract_gencontent_image_b64(resp.json())
                if not b64:
                    return {"ok": False, "error": "Gemini không trả bytes ảnh (generateContent)."}
            else:
                url = GEMINI_IMAGEN_URL.format(model=model, key=key)
                payload = {
                    "instances": [{"prompt": prompt}],
                    "parameters": {
                        "sampleCount": 1,
                        "aspectRatio": aspect,
                        "outputMimeType": "image/jpeg",
                    },
                }
                resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                if resp.status_code != 200:
                    body = resp.text[:500]
                    return {"ok": False, "error": f"Google Imagen API {resp.status_code}: {body}"}
                data = resp.json()
                predictions = data.get("predictions") or []
                if not predictions:
                    return {"ok": False, "error": f"Google Imagen không trả ảnh: {data}"}
                b64 = predictions[0].get("bytesBase64Encoded")
                if not b64:
                    return {"ok": False, "error": "Không thấy bytesBase64Encoded trong phản hồi Imagen."}

            raw_bytes = base64.b64decode(b64)
            saved = save_image_bytes(
                raw_bytes, vault_root, prefix=prefix, ext=".jpg",
                subdir=save_under or "attachments/dataset/_xuat",
            )
            if not saved.get("ok"):
                return saved
            return {
                "ok": True,
                "rel_path": saved["rel_path"],
                "abs_path": saved["abs_path"],
                "file": saved["file"],
                "aspect": aspect,
                "provider": "google-imagen" if kind == "predict" else "google-gemini-image",
                "model": model,
                "prompt": prompt,
            }
    except Exception as e:
        return {"ok": False, "error": f"Goi Google Imagen that bai: {type(e).__name__}: {e}"}

