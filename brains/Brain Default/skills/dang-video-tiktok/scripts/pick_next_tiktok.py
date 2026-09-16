#!/usr/bin/env python3
"""Script điều phối hàng đợi đăng video TikTok qua PostPeer (1 bài/ngày).

Sử dụng:
    python pick_next_tiktok.py                  # Lấy video tiếp theo
    python pick_next_tiktok.py --ok "<url>"     # Ghi nhận đăng thành công
    python pick_next_tiktok.py --fail "<url>" "lý do" # Ghi nhận lỗi
"""
import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

# Tìm vault root
CWD = Path.cwd().resolve()
if (CWD / "wiki" / "brand-kits").is_dir():
    VAULT = CWD
elif (CWD / "brains" / "Brain Default" / "wiki" / "brand-kits").is_dir():
    VAULT = CWD / "brains" / "Brain Default"
else:
    # fallback
    VAULT = Path(__file__).resolve().parents[3]

STATE_FILE = VAULT / "Javis" / "tiktok-queue.json"
MAX_PER_DAY = 1

# Danh sách video CDN mẫu sẵn sàng (9:16 dọc)
DEFAULT_VIDEOS = [
    {
        "url": "https://laptrinhpython.tinhocsaoviet.com/storage/videos/ready/rendered_tin_hoc_ai_01.mp4",
        "the": "tin-hoc_ai",
        "title": "Mẹo Excel AI tự động điền dữ liệu",
    },
    {
        "url": "https://laptrinhpython.tinhocsaoviet.com/storage/videos/ready/rendered_tin_hoc_ai_02.mp4",
        "the": "tin-hoc_ai",
        "title": "3 Phím tắt thần thánh trong Word và PowerPoint",
    },
    {
        "url": "https://laptrinhpython.tinhocsaoviet.com/storage/videos/ready/rendered_tin_hoc_ai_03.mp4",
        "the": "tin-hoc_ai",
        "title": "Cách tạo báo cáo tự động bằng ChatGPT và Excel",
    },
]


def load_state() -> dict:
    if STATE_FILE.is_file():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"history": [], "last_date": "", "today_count": 0}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def find_tiktok_account() -> tuple[str, str, str, str]:
    """Tìm accountId và hotline từ brand kit."""
    bk_dir = VAULT / "wiki" / "brand-kits"
    if not bk_dir.is_dir():
        return "", "", "", ""

    for p in sorted(bk_dir.glob("*.md")):
        if p.name.startswith("_"):
            continue
        try:
            md = p.read_text(encoding="utf-8")
        except OSError:
            continue
        m_id = re.search(r"^[ \t]*[-*][ \t]*(?:TikTok accountId|tiktok_account_id|TikTok Account ID)[ \t]*:[ \t]*(.+)$", md, re.M | re.I)
        if m_id:
            acc_id = m_id.group(1).strip()
            m_user = re.search(r"^[ \t]*[-*][ \t]*(?:TikTok username|tiktok_username|TikTok User)[ \t]*:[ \t]*(.+)$", md, re.M | re.I)
            username = m_user.group(1).strip() if m_user else "@tinhocsaoviet"
            m_hotline = re.search(r"^[ \t]*[-*][ \t]*(?:Hotline|Hotline / Zalo)[ \t]*:[ \t]*(.+)$", md, re.M | re.I)
            hotline = m_hotline.group(1).strip() if m_hotline else "0823 552 558"
            return acc_id, username, hotline, p.name

    # Fallback to _mac-dinh.md
    mac_dinh = bk_dir / "_mac-dinh.md"
    if mac_dinh.is_file():
        md = mac_dinh.read_text(encoding="utf-8")
        m_id = re.search(r"^[ \t]*[-*][ \t]*(?:TikTok accountId|tiktok_account_id|TikTok Account ID)[ \t]*:[ \t]*(.+)$", md, re.M | re.I)
        if m_id:
            acc_id = m_id.group(1).strip()
            return acc_id, "@tinhocsaoviet", "0823 552 558", "_mac-dinh.md"

    return "", "", "", ""


def main():
    parser = argparse.ArgumentParser(description="Điều phối đăng video TikTok")
    parser.add_argument("--ok", type=str, help="Ghi nhận đăng thành công cho video URL")
    parser.add_argument("--fail", type=str, help="Ghi nhận đăng thất bại cho video URL")
    parser.add_argument("reason", nargs="?", default="", help="Lý do lỗi nếu dùng --fail")
    args = parser.parse_args()

    today_str = datetime.date.today().isoformat()
    state = load_state()

    # Reset counter nếu sang ngày mới
    if state.get("last_date") != today_str:
        state["last_date"] = today_str
        state["today_count"] = 0

    if args.ok:
        state["today_count"] = state.get("today_count", 0) + 1
        state.setdefault("history", []).append({
            "url": args.ok,
            "status": "ok",
            "time": datetime.datetime.now().isoformat(),
        })
        save_state(state)
        print(f"OK: đã ghi nhận video {args.ok}")
        return

    if args.fail:
        state.setdefault("history", []).append({
            "url": args.fail,
            "status": "fail",
            "reason": args.reason,
            "time": datetime.datetime.now().isoformat(),
        })
        save_state(state)
        print(f"FAIL: đã ghi nhận lỗi cho video {args.fail}: {args.reason}")
        return

    # Kiểm tra quota ngày
    if state.get("today_count", 0) >= MAX_PER_DAY:
        print(f"NEXT=NONE da-du-quota-hom-nay ({state['today_count']}/{MAX_PER_DAY})")
        return

    # Tìm accountId
    acc_id, username, hotline, kit_file = find_tiktok_account()
    if not acc_id:
        print("NEXT=NONE chua-cau-hinh-tiktok-account-id-trong-brand-kit")
        return

    # Lấy danh sách video từ file nếu có
    videos_file = VAULT / "Javis" / "tiktok-videos.json"
    videos = DEFAULT_VIDEOS
    if videos_file.is_file():
        try:
            custom_vids = json.loads(videos_file.read_text(encoding="utf-8"))
            if isinstance(custom_vids, list) and custom_vids:
                videos = custom_vids
        except Exception:
            pass

    # Lọc video chưa đăng thành công
    posted_urls = {h.get("url") for h in state.get("history", []) if h.get("status") == "ok"}
    unposted = [v for v in videos if v.get("url") not in posted_urls]

    if not unposted:
        # Nếu đã đăng hết, xoay tua lại
        unposted = videos

    if not unposted:
        print("NEXT=NONE het-video-san-sang")
        return

    selected = unposted[0]
    print("NEXT=1")
    print(f"account_id={acc_id}")
    print(f"username={username}")
    print(f"video_url={selected['url']}")
    print(f"the={selected.get('the', 'tin-hoc_ai')}")
    print(f"title={selected.get('title', '')}")
    print(f"kit_file={kit_file}")
    print(f"hotline={hotline}")


if __name__ == "__main__":
    main()
