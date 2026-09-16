# -*- coding: utf-8 -*-
"""Test PR T5: Honest TikTok empty state (no fake ingest, no crawlers)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

import fanpage_care_store as store


def test_tiktok_empty_events_in_store():
    """Bảng events không có bình luận TikTok nào bị fake hoặc crawler."""
    events = store.list_events(platform="tiktok")
    assert len(events) == 0, f"Expected 0 tiktok events, found {len(events)}"


def test_inbox_ui_empty_state_copy():
    """Kiểm tra UI Inbox.tsx chứa đúng thông điệp trung thực khi lọc TikTok."""
    inbox_tsx = ROOT / "ops" / "src" / "pages" / "Inbox.tsx"
    assert inbox_tsx.is_file(), "Inbox.tsx must exist"
    content = inbox_tsx.read_text(encoding="utf-8")

    expected_msg = "Chưa có bình luận TikTok — kênh này dùng để đăng video."
    assert expected_msg in content, f"Inbox.tsx must contain exact copy: '{expected_msg}'"


def main():
    test_tiktok_empty_events_in_store()
    test_inbox_ui_empty_state_copy()
    print("OK - test_tiktok_empty_inbox: tất cả pass")


if __name__ == "__main__":
    main()
