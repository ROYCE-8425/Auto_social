"""Script nhập access token hàng loạt cho các Fanpage vào Javis.
Đọc từ file text hoặc tham số, gọi Graph API xác thực, tự động cập nhật:
1. brains/Brain Default/Javis/page_tokens.json
2. brains/Brain Default/wiki/brand-kits/<page>.md
"""
import sys
import os
import re
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import date

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS_DIR.parent
SKILLS_DIR = SKILL_DIR.parent
BRAIN_DEFAULT = SKILLS_DIR.parent   # brains/Brain Default
ROOT = BRAIN_DEFAULT.parent.parent  # javis-os root
TOKENS_JSON = BRAIN_DEFAULT / "Javis" / "page_tokens.json"
BRAND_KITS_DIR = BRAIN_DEFAULT / "wiki" / "brand-kits"


def verify_token(token: str) -> dict:
    """Gọi Graph API để lấy thông tin chuẩn xác của Page từ token."""
    url = f"https://graph.facebook.com/v21.0/me?access_token={token.strip()}"
    req = urllib.request.Request(url, headers={"User-Agent": "JavisOS/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return {"ok": True, "id": str(data.get("id")), "name": data.get("name")}
            return {"ok": False, "error": f"HTTP {resp.status}"}
    except urllib.error.HTTPError as e:
        try:
            err_data = json.loads(e.read().decode("utf-8"))
            msg = err_data.get("error", {}).get("message", str(e))
            return {"ok": False, "error": msg}
        except Exception:
            return {"ok": False, "error": f"HTTP Error {e.code}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def fold_text(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", s)


def find_matching_kit(page_id: str, page_name: str, hint_name: str = "") -> Path | None:
    """Tìm file brand kit phù hợp dựa trên Page ID hoặc Tên Fanpage."""
    if not BRAND_KITS_DIR.is_dir():
        return None

    # 1. Tìm chính xác theo Page ID
    for f in BRAND_KITS_DIR.glob("*.md"):
        if f.name.startswith("_"):
            continue
        try:
            content = f.read_text(encoding="utf-8")
            m = re.search(r"^[ \t]*[-*][ \t]*(?:Page ID|page_id|ID Fanpage|ID Trang)[ \t]*:[ \t]*([0-9]+)", content, re.M | re.I)
            if m and m.group(1).strip() == page_id:
                return f
        except Exception:
            pass

    # 2. Tìm theo độ khớp tên Fanpage (bỏ dấu)
    f_pname = fold_text(page_name)
    f_hint = fold_text(hint_name)
    best_match = None
    best_score = 0

    for f in BRAND_KITS_DIR.glob("*.md"):
        if f.name.startswith("_"):
            continue
        f_stem = fold_text(f.stem)
        score = 0
        if f_pname and f_pname in f_stem or f_stem in f_pname:
            score += 5
        if f_hint and (f_hint in f_stem or f_stem in f_hint):
            score += 3
        if score > best_score:
            best_score = score
            best_match = f

    return best_match if best_score >= 3 else None


def update_brand_kit(kit_path: Path, page_id: str, access_token: str, official_name: str):
    """Cập nhật Access Token và Page ID vào file brand kit."""
    try:
        content = kit_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"Không đọc được file: {e}"

    # Cập nhật hoặc thêm Access Token
    if re.search(r"^[ \t]*[-*][ \t]*(?:Access Token|access_token|Page Token|Token)[ \t]*:.*$", content, re.M):
        content = re.sub(
            r"^([ \t]*[-*][ \t]*(?:Access Token|access_token|Page Token|Token)[ \t]*:)[ \t]*.*$",
            rf"\g<1> {access_token}",
            content,
            flags=re.M
        )
    else:
        # Chèn vào dưới mục Tuỳ biến trang
        if "## Tuỳ biến trang" in content:
            content = content.replace("## Tuỳ biến trang", f"## Tuỳ biến trang\n- Access Token: {access_token}")
        else:
            content += f"\n\n## Tuỳ biến trang\n- Page ID: {page_id}\n- Access Token: {access_token}\n"

    # Cập nhật hoặc thêm Page ID
    if re.search(r"^[ \t]*[-*][ \t]*(?:Page ID|page_id|ID Fanpage|ID Trang)[ \t]*:.*$", content, re.M):
        content = re.sub(
            r"^([ \t]*[-*][ \t]*(?:Page ID|page_id|ID Fanpage|ID Trang)[ \t]*:)[ \t]*.*$",
            rf"\g<1> {page_id}",
            content,
            flags=re.M
        )

    try:
        kit_path.write_text(content, encoding="utf-8")
        return True, kit_path.name
    except Exception as e:
        return False, f"Lỗi ghi file: {e}"


def parse_and_import(raw_text: str):
    today = date.today().isoformat()
    lines = raw_text.splitlines()

    # Tìm App ID nếu có
    app_id = ""
    m_app = re.search(r"(?:ID\s*:\s*|app_id\s*[:=]\s*)(\d+)", raw_text, re.I)
    if m_app:
        app_id = m_app.group(1).strip()

    # Tách các cặp Page Hint và Token
    # Hỗ trợ dạng:
    # F1: <Tên>
    # T1: <Token>
    # hoặc từng cặp dòng
    pairs = []
    current_hint = ""
    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue
        # Check F<n>: <name>
        m_f = re.match(r"^F\d*\s*:\s*(.+)$", line_s, re.I)
        if m_f:
            current_hint = m_f.group(1).strip()
            continue

        # Check T<n>: <token>
        m_t = re.match(r"^T\d*\s*:\s*([A-Za-z0-9_]+)$", line_s, re.I)
        if m_t:
            tok = m_t.group(1).strip()
            pairs.append((current_hint, tok))
            current_hint = ""
            continue

        # Check nếu dòng chỉ chứa token EAAY... hoặc EAAV...
        if re.match(r"^(?:EAAY|EAAV|EAA)[A-Za-z0-9_]+$", line_s):
            pairs.append((current_hint, line_s))
            current_hint = ""

    if not pairs:
        print("KHÔNG tìm thấy cặp token nào trong dữ liệu nhập!")
        return

    # Đọc page_tokens.json hiện tại
    page_tokens_data = {}
    if TOKENS_JSON.is_file():
        try:
            page_tokens_data = json.loads(TOKENS_JSON.read_text(encoding="utf-8"))
        except Exception:
            page_tokens_data = {}

    results = []
    for hint, token in pairs:
        info = verify_token(token)
        if not info["ok"]:
            results.append({
                "hint": hint or "Không rõ",
                "page_id": "N/A",
                "name": "N/A",
                "status": f"❌ Lỗi: {info.get('error')}",
                "kit": "N/A",
                "json": "Bỏ qua"
            })
            continue

        pid = info["id"]
        pname = info["name"]

        # Cập nhật page_tokens.json
        page_tokens_data[pid] = {
            "name": pname,
            "page_id": pid,
            "access_token": token,
            "app_id": app_id or page_tokens_data.get(pid, {}).get("app_id", ""),
            "expires_at": "never",
            "updated_at": today
        }

        # Cập nhật brand kit markdown
        kit_file = find_matching_kit(pid, pname, hint)
        kit_status = "Chưa có kit"
        if kit_file:
            ok, msg = update_brand_kit(kit_file, pid, token, pname)
            kit_status = msg if ok else f"Lỗi: {msg}"

        results.append({
            "hint": hint or pname,
            "page_id": pid,
            "name": pname,
            "status": "✅ Live (Hợp lệ)",
            "kit": kit_status,
            "json": "✅ Đã lưu"
        })

    # Lưu lại page_tokens.json
    try:
        TOKENS_JSON.parent.mkdir(parents=True, exist_ok=True)
        TOKENS_JSON.write_text(json.dumps(page_tokens_data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"Lỗi ghi {TOKENS_JSON}: {e}")

    # In báo cáo bảng
    print(f"\n{'='*95}")
    print(f"KẾT QUẢ XỬ LÝ NẠP TOKEN FANPAGE ({len(results)} Trang)")
    print(f"{'='*95}")
    header = f"{'STT':<4} | {'Page ID':<16} | {'Tên Fanpage (Graph API)':<35} | {'Token':<18} | {'Brand Kit':<25}"
    print(header)
    print("-" * 110)
    for idx, r in enumerate(results, start=1):
        pname_disp = (r['name'][:32] + '...') if len(r['name']) > 35 else r['name']
        kit_disp = (r['kit'][:22] + '...') if len(r['kit']) > 25 else r['kit']
        print(f"{idx:<4} | {r['page_id']:<16} | {pname_disp:<35} | {r['status']:<18} | {kit_disp:<25}")
    print(f"{'='*95}")
    print(f"Đã cập nhật file: {TOKENS_JSON}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
        if target_path.is_file():
            raw = target_path.read_text(encoding="utf-8")
            parse_and_import(raw)
        else:
            parse_and_import(sys.argv[1])
    else:
        # Đọc từ stdin
        raw = sys.stdin.read()
        if raw.strip():
            parse_and_import(raw)
        else:
            print("Cách dùng: python import_tokens.py <duong_dan_file_txt>")
