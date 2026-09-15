"""
skill_usage.py - Sidecar TELEMETRY cho skill: đo skill nào THẬT SỰ được dùng.

Vị trí: <brain>/Javis/skill-usage.json. Đặt cạnh Javis/loop-state.json theo đúng quy ước
đã có của Javis ("STATE runtime tách riêng, server sở hữu" - xem self_improve.py). KHÔNG
nhét vào frontmatter SKILL.md: brain là git repo, mỗi lần dùng skill sẽ đẻ một commit rác
và tạo áp lực xung đột lên file do người viết.

TÍN HIỆU DƯƠNG MỘT CHIỀU. Bộ đếm chỉ bump ở tool javis_use_skill (mcp_hub). Claude Code
nạp skill NATIVE qua bản mirror <brain>/.claude/skills KHÔNG đi qua đó, nên:
  - use_count > 0  → skill CHẮC CHẮN có dùng.
  - use_count == 0 → KHÔNG có bằng chứng. TUYỆT ĐỐI không suy ra "vô dụng", không tự tắt,
    không tự archive. Nhãn stale chỉ để hiển thị tham khảo cho người, người tự quyết.

Mọi hàm BEST-EFFORT: sidecar thiếu/hỏng/không ghi được thì trả rỗng và đi tiếp. Sidecar
hỏng KHÔNG BAO GIỜ được làm gãy lời gọi skill.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

# Skill chưa có tín hiệu dùng nào và đã quá ngần này ngày thì gắn nhãn "chưa thấy dùng".
# Ngưỡng rộng tay có chủ đích: skill mới đơn giản là chưa gặp trigger (luật của Hermes).
SKILL_STALE_AFTER_DAYS = 30

_LOCK = threading.Lock()   # serialize read-modify-write trong process


def usage_path(brain_root) -> Path:
    return Path(brain_root) / "Javis" / "skill-usage.json"


def read_usage(brain_root) -> dict:
    """{slug: {...}}. Thiếu file / JSON hỏng / lỗi đọc → {} (không raise)."""
    try:
        p = usage_path(brain_root)
        if not p.is_file():
            return {}
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_atomic(p: Path, text: str) -> None:
    """Ghi atomic: .tmp cạnh đích rồi os.replace (cùng ổ đĩa → rename nguyên tử)."""
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=".skill-usage-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, p)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def bump(brain_root, slug: str, created_by: str = "") -> None:
    """Đếm 1 lần dùng skill. BEST-EFFORT: nuốt mọi lỗi, chỉ log stderr.
    Gọi ở ĐIỂM THÀNH CÔNG của handler _skill (mcp_hub) - không gọi khi slug sai.

    ⚠ HÀM NÀY CHẶN (blocking): giữ _LOCK trong lúc đọc + ghi đĩa + os.fsync. Gọi thẳng từ
    handler async sẽ chẹn event loop. Bên gọi async nên đẩy qua thread (vd
    asyncio.to_thread / run_in_executor).
    """
    slug = str(slug or "").strip()
    if not slug:
        return
    try:
        now = time.time()
        with _LOCK:
            data = read_usage(brain_root)
            rec = data.get(slug)
            if not isinstance(rec, dict):
                rec = {"use_count": 0, "created_at": now, "created_by": created_by,
                       "first_used_at": None, "last_used_at": None, "pinned": False}
            try:
                cur_count = int(rec.get("use_count", 0) or 0)
            except (TypeError, ValueError):
                # use_count hỏng (vd chuỗi "abc") -> coi như 0 và GHI ĐÈ ngay dưới đây, tự lành
                # bản ghi hỏng ở lần bump kế tiếp thay vì hỏng vĩnh viễn.
                cur_count = 0
            rec["use_count"] = cur_count + 1
            rec["last_used_at"] = now
            if not rec.get("first_used_at"):
                rec["first_used_at"] = now
            if not rec.get("created_at"):
                rec["created_at"] = now
            data[slug] = rec
            _write_atomic(usage_path(brain_root),
                          json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[skill usage] bump {slug}: {type(e).__name__}: {e}", file=sys.stderr)


def is_stale(rec: dict, skill_md_mtime: Optional[float], now: Optional[float] = None) -> bool:
    """Hàm THUẦN. True = "chưa thấy dùng và đã đủ già" - CHỈ để hiển thị, KHÔNG để tự tắt.

    Luật:
      - pinned → không bao giờ stale.
      - use_count > 0 → không bao giờ stale, BẤT KỂ last_used_at cũ đến đâu (điểm mù native
        khiến last_used_at không đủ tin làm căn cứ phủ định).
      - Không có created_at (skill có từ trước khi có tính năng này) → fallback mtime của
        SKILL.md. Không có cả mtime → False (không đủ căn cứ thì không phán).
    """
    now = time.time() if now is None else now
    rec = rec if isinstance(rec, dict) else {}
    if rec.get("pinned"):
        return False
    try:
        use_count = int(rec.get("use_count", 0) or 0)
    except (TypeError, ValueError):
        # use_count hỏng (vd chuỗi "abc") -> không đủ căn cứ coi là "có dùng", nhưng cũng
        # không sập: coi như 0 rồi đi tiếp xét theo tuổi bản ghi.
        use_count = 0
    if use_count > 0:
        return False
    born = rec.get("created_at") or skill_md_mtime
    if not born:
        return False
    return (now - float(born)) > SKILL_STALE_AFTER_DAYS * 86400
