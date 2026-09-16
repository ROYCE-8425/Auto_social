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

# Tìm server directory và nạp module brand_kit
current = Path(__file__).resolve()
server_dir = None
for parent in [current] + list(current.parents):
    if (parent / "server" / "brand_kit.py").is_file():
        server_dir = parent / "server"
        break

if server_dir and str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))

try:
    from brand_kit import parse_brand_kit_channels, ParsedBrandKit, detect_brand_from_kit
except ImportError:
    parse_brand_kit_channels = None
    detect_brand_from_kit = lambda stem: "bsn" if "bsn" in str(stem).lower() else "saoviet"

STATE_FILE = VAULT / "Javis" / "tiktok-queue.json"
MAX_PER_DAY = 1

# Danh sách video CDN mẫu sẵn sàng (9:16 dọc) cho Sao Việt
DEFAULT_SAOVIET_VIDEOS = [
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

# Danh sách video CDN mẫu cho Game Giá Rẻ BSN (cấm dùng tin-hoc)
DEFAULT_BSN_VIDEOS = [
    {
        "url": "https://laptrinhpython.tinhocsaoviet.com/storage/videos/ready/rendered_game_bsn_01.mp4",
        "the": "game-bsn",
        "title": "Top 3 Game Steam Offline Đáng Mua Nhất 2026",
    },
    {
        "url": "https://laptrinhpython.tinhocsaoviet.com/storage/videos/ready/rendered_game_bsn_02.mp4",
        "the": "game-bsn",
        "title": "Cách kích hoạt Key Steam bản quyền và cài đặt nhanh",
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


def find_tiktok_account() -> dict | None:
    """Tìm kit có kênh TikTok được bật và accountId hợp lệ qua parse_brand_kit_channels."""
    bk_dir = VAULT / "wiki" / "brand-kits"
    if not bk_dir.is_dir():
        return None

    candidates = []
    # Quét các kit cụ thể
    for p in sorted(bk_dir.glob("*.md")):
        if p.name.startswith("_"):
            continue
        if parse_brand_kit_channels:
            candidates.append(parse_brand_kit_channels(p))
        else:
            candidates.append(p)

    # Thêm fallback _mac-dinh.md
    mac_dinh = bk_dir / "_mac-dinh.md"
    if mac_dinh.is_file():
        if parse_brand_kit_channels:
            candidates.append(parse_brand_kit_channels(mac_dinh))
        else:
            candidates.append(mac_dinh)

    for item in candidates:
        if parse_brand_kit_channels and isinstance(item, ParsedBrandKit):
            tt = item.tiktok
            acc_id = (tt.ids.get("account_id") or tt.ids.get("accountId") or "").strip()
            # Bắt buộc: Kênh TikTok Bật: true VÀ accountId không rỗng, không phải CHƯA_NỐI
            if tt.enabled and acc_id and acc_id not in ("CHƯA_NỐI", "CHUA_NOI", "CHƯA_CÓ", ""):
                return {
                    "account_id": acc_id,
                    "username": tt.ids.get("username", "@tinhocsaoviet" if item.brand == "saoviet" else "@gamegiarebsn"),
                    "brand": item.brand,
                    "kit_file": item.filename,
                    "caption_mode": tt.caption_mode,
                    "hashtag": tt.extras.get("hashtag", ""),
                    "disable_duet": tt.extras.get("disable_duet", True),
                    "disable_stitch": tt.extras.get("disable_stitch", True),
                    "video_cdn": tt.extras.get("video_cdn", ""),
                }
        elif isinstance(item, Path):
            # Fallback regex nếu không có module brand_kit
            try:
                md = item.read_text(encoding="utf-8")
                m_id = re.search(r"^[ \t]*[-*][ \t]*(?:accountId|TikTok accountId)[ \t]*:[ \t]*(.+)$", md, re.M | re.I)
                if m_id:
                    acc_id = m_id.group(1).strip()
                    if acc_id and acc_id not in ("CHƯA_NỐI", "CHUA_NOI", ""):
                        return {
                            "account_id": acc_id,
                            "username": "@tinhocsaoviet",
                            "brand": "bsn" if "bsn" in item.name.lower() else "saoviet",
                            "kit_file": item.name,
                            "caption_mode": "short",
                            "hashtag": "",
                            "disable_duet": True,
                            "disable_stitch": True,
                            "video_cdn": "",
                        }
            except OSError:
                pass

    return None


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

    # Tìm accountId qua Brand Kit kênh TikTok
    kit_info = find_tiktok_account()
    if not kit_info:
        # Khi chưa có kit nào bật kênh TikTok hoặc accountId còn là CHƯA_NỐI
        print("NEXT=NONE chua-noi-tiktok")
        return

    brand = kit_info.get("brand", "saoviet")
    if brand == "bsn":
        videos = DEFAULT_BSN_VIDEOS
        default_hashtag = "#GameGiaRe #SteamGame #SteamVN #GamingPC #GameOffline"
    else:
        videos = DEFAULT_SAOVIET_VIDEOS
        default_hashtag = "#TinhocSaoViet #HocExcel #KienthucTinhoctonghop"

    # Lấy danh sách video từ file nếu có
    videos_file = VAULT / "Javis" / "tiktok-videos.json"
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
    hashtag = kit_info.get("hashtag") or default_hashtag

    print("NEXT=1")
    print(f"account_id={kit_info['account_id']}")
    print(f"username={kit_info['username']}")
    print(f"brand={brand}")
    print(f"video_url={selected['url']}")
    print(f"the={selected.get('the', 'game-bsn' if brand == 'bsn' else 'tin-hoc_ai')}")
    print(f"title={selected.get('title', '')}")
    print(f"kit_file={kit_info['kit_file']}")
    print(f"hashtag={hashtag}")
    print(f"disable_duet={str(kit_info.get('disable_duet', True)).lower()}")
    print(f"disable_stitch={str(kit_info.get('disable_stitch', True)).lower()}")


if __name__ == "__main__":
    main()
