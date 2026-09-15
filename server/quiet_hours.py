"""Module xác định khung giờ im lặng (Quiet Hours) - không gửi tin/thông báo.

Hỗ trợ cả format ngắn '21-7' (cho loop self_improve) và '21:00-07:00' (cho fanpage_care).
Không dùng cron_util để giữ code nhẹ và an toàn trên VPS.
"""
from __future__ import annotations

import datetime
import re
from typing import Any

# Match '21-7' hoặc '21:00-07:00'
_QH_RE = re.compile(r"^\s*(\d{1,2})(?::\d{2})?\s*-\s*(\d{1,2})(?::\d{2})?\s*$")


def _in_quiet_hours(spec: str, hour: int) -> bool:
    """Kiểm tra một giờ cụ thể (0-23) có nằm trong spec '21-7' hoặc '23-07' không.

    '23-07' = im lặng 23h..7h (giờ VN). Sai format / rỗng / a==b → không im lặng.
    """
    m = _QH_RE.match(spec or "")
    if not m:
        return False
    a, b = int(m.group(1)) % 24, int(m.group(2)) % 24
    if a == b:
        return False
    return (a <= hour < b) if a < b else (hour >= a or hour < b)


def parse_time_to_minutes(t_str: str) -> int:
    """Chuyển chuỗi 'HH:MM' hoặc 'HH' thành số phút từ 00:00 (0-1439)."""
    s = (t_str or "").strip()
    if ":" in s:
        parts = s.split(":")
        h = int(parts[0]) % 24
        m = int(parts[1]) % 60
        return h * 60 + m
    else:
        h = int(s) % 24
        return h * 60


def in_quiet_hours(
    start: str = "21:00",
    end: str = "07:00",
    now_dt: datetime.datetime | None = None,
    spec: str | None = None,
    timezone_str: str = "Asia/Ho_Chi_Minh",
) -> bool:
    """Kiểm tra thời điểm hiện tại (hoặc now_dt) có thuộc giờ im lặng không.

    Mặc định 21h-7h sáng hôm sau theo giờ Việt Nam (UTC+7).
    """
    target_spec = spec or (start if "-" in str(start) else None)
    if target_spec:
        m = _QH_RE.match(target_spec.strip())
        if m:
            start = m.group(1)
            end = m.group(2)
        else:
            return False

    try:
        start_min = parse_time_to_minutes(start)
        end_min = parse_time_to_minutes(end)
    except (ValueError, TypeError):
        return False

    if start_min == end_min:
        return False

    if now_dt is None:
        # Giờ VN = UTC + 7
        tz_vn = datetime.timezone(datetime.timedelta(hours=7))
        now_dt = datetime.datetime.now(tz_vn)

    curr_min = now_dt.hour * 60 + now_dt.minute

    if start_min < end_min:
        return start_min <= curr_min < end_min
    else:
        # Qua đêm (vd: 21:00 -> 07:00)
        return curr_min >= start_min or curr_min < end_min
