"""Tầng thuần dùng chung cho cập nhật: so sánh phiên bản + đọc/ghi update_state.json +
quyết định rollback. Không phụ thuộc FastAPI/main - import được từ cả main.py lẫn updater.py."""
import json
import re

import config as cfgmod

STATE_DIR = cfgmod.STATE_DIR
STATE_FILE = STATE_DIR / "update_state.json"


def ver_tuple(s):
    try:
        parts = [int(x) for x in re.split(r"[.\-]", (s or "").strip().lstrip("vV"))[:3] if x.isdigit()]
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts[:3])
    except Exception:
        return None


def ver_newer(latest, cur) -> bool:
    """So sánh semver: latest MỚI HƠN cur? (tránh báo nhầm khi local ahead / lệch định dạng)."""
    lt, ct = ver_tuple(latest), ver_tuple(cur)
    if lt is None or ct is None:
        return False
    return lt > ct


def read_state() -> dict:
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def write_state(patch: dict) -> dict:
    """Merge patch vào state hiện có rồi ghi. Trả state sau khi ghi."""
    st = read_state()
    st.update(patch)
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    return st


def record_boot_version(current: str) -> dict:
    """Chạy mỗi lần khởi động: duy trì last_good_version + previous_version để mọi mode biết
    'lùi về đâu'. Vừa lên bản mới hơn thì previous = last_good cũ."""
    st = read_state()
    last_good = st.get("last_good_version")
    patch = {}
    if last_good and last_good != current and ver_newer(current, last_good):
        patch["previous_version"] = last_good
    patch["last_good_version"] = current
    return write_state(patch)


def update_outcome(health_ok: bool, current: str, old: str, target=None) -> str:
    """Kết quả sau khi thử bật bản mới. Tách riêng để test được (poll health nằm ở updater)."""
    if not health_ok:
        return "need_rollback"
    ct, tt = ver_tuple(current), ver_tuple(target)
    if target and ct and tt and ct >= tt:
        return "success"
    if ver_newer(current, old):
        return "success"
    return "version_mismatch"
