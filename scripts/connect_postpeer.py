#!/usr/bin/env python3
"""Lưu PostPeer access key vào mcp_store (STATE_DIR, đã mã hoá). KHÔNG commit key.

Trên VPS:
  POSTPEER_API_KEY='...' python scripts/connect_postpeer.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

import mcp_store  # noqa: E402


def main() -> int:
    key = (os.environ.get("POSTPEER_API_KEY") or "").strip()
    if not key:
        print("ERROR: đặt env POSTPEER_API_KEY rồi chạy lại. Không dán key vào brand kit.")
        return 1
    # Tránh trùng: xóa connection postpeer cũ rồi thêm
    for c in list(mcp_store.list_connections()):
        if c.get("connector_id") == "postpeer":
            mcp_store.delete_connection(c["id"])
    cid, err = mcp_store.add_connection(
        "postpeer",
        {
            "label": "TikTok PostPeer",
            "fields": {"postpeer_key": key},
            "perm": "full",
        },
    )
    if err:
        print("ERROR:", err)
        return 1
    print("OK connection_id=", cid, "perm=full (key không in ra).")
    print("Kit chỉ giữ accountId TikTok, không giữ access key.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
