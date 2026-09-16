# ============================================================
# Javis OS - Module Phân Quyền Vận Hành (Ops RBAC)
# docs/dev/2026-09-16-ops-dashboard-plan.md (Mục 3)
# Quản lý tài khoản staff / manager và bảo vệ route 403 thật.
# ============================================================
import json
import os
import secrets
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import config as cfgmod

OPS_USERS_FILE = cfgmod.STATE_DIR / "ops_users.json"
OPS_SESSIONS_FILE = cfgmod.STATE_DIR / "ops_sessions.json"
OPS_SESSION_TTL = 30 * 86400  # 30 ngày

_OPS_SESSIONS: Dict[str, Dict[str, Any]] = {}


def _load_sessions():
    global _OPS_SESSIONS
    if OPS_SESSIONS_FILE.exists():
        try:
            data = json.loads(OPS_SESSIONS_FILE.read_text(encoding="utf-8"))
            now = time.time()
            _OPS_SESSIONS = {
                k: v for k, v in data.items()
                if isinstance(v, dict) and (now - v.get("ts", 0)) < OPS_SESSION_TTL
            }
        except Exception:
            _OPS_SESSIONS = {}


def _save_sessions():
    try:
        now = time.time()
        valid = {
            k: v for k, v in _OPS_SESSIONS.items()
            if isinstance(v, dict) and (now - v.get("ts", 0)) < OPS_SESSION_TTL
        }
        OPS_SESSIONS_FILE.write_text(json.dumps(valid, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


_load_sessions()


def hash_ops_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()
    return h, salt


def verify_ops_password(password: str, stored_hash: str, salt: str) -> bool:
    h, _ = hash_ops_password(password, salt)
    return secrets.compare_digest(h, stored_hash)


def load_users() -> list[dict]:
    if not OPS_USERS_FILE.exists():
        return []
    try:
        data = json.loads(OPS_USERS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_users(users: list[dict]):
    OPS_USERS_FILE.write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")


def get_user_by_id(user_id: str) -> Optional[dict]:
    users = load_users()
    return next((u for u in users if u.get("id") == user_id), None)


def get_user_by_username(username: str) -> Optional[dict]:
    u_clean = username.strip().lower()
    users = load_users()
    return next((u for u in users if u.get("username", "").strip().lower() == u_clean), None)


def create_user(username: str, password: str, role: str = "staff", name: str = "", enabled: bool = True) -> dict:
    if role not in ("staff", "manager", "owner"):
        raise ValueError("Role không hợp lệ: " + role)
    username_clean = username.strip()
    if not username_clean:
        raise ValueError("Username không được để trống")
    if get_user_by_username(username_clean):
        raise ValueError("Tên đăng nhập đã tồn tại")
    if len(password) < 6:
        raise ValueError("Mật khẩu tối thiểu 6 ký tự")

    h, salt = hash_ops_password(password)
    user_id = "u_" + secrets.token_hex(6)
    new_user = {
        "id": user_id,
        "username": username_clean,
        "password_hash": h,
        "salt": salt,
        "role": role,
        "enabled": enabled,
        "name": name.strip() or username_clean,
        "created_at": time.time(),
    }
    users = load_users()
    users.append(new_user)
    save_users(users)
    return sanitize_user(new_user)


def update_user(user_id: str, updates: dict) -> Optional[dict]:
    users = load_users()
    idx = next((i for i, u in enumerate(users) if u.get("id") == user_id), None)
    if idx is None:
        return None
    u = users[idx]
    if "role" in updates and updates["role"] in ("staff", "manager", "owner"):
        u["role"] = updates["role"]
    if "name" in updates:
        u["name"] = updates["name"].strip()
    if "enabled" in updates:
        u["enabled"] = bool(updates["enabled"])
    if "password" in updates and updates["password"]:
        if len(updates["password"]) < 6:
            raise ValueError("Mật khẩu tối thiểu 6 ký tự")
        h, salt = hash_ops_password(updates["password"])
        u["password_hash"] = h
        u["salt"] = salt
    users[idx] = u
    save_users(users)
    return sanitize_user(u)


def delete_user(user_id: str) -> bool:
    users = load_users()
    new_users = [u for u in users if u.get("id") != user_id]
    if len(new_users) == len(users):
        return False
    save_users(new_users)
    return True


def sanitize_user(user: dict) -> dict:
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "role": user.get("role"),
        "name": user.get("name"),
        "enabled": user.get("enabled", True),
        "created_at": user.get("created_at"),
    }


def create_session(user_id: str, username: str, role: str, name: str) -> str:
    token = "ops_" + secrets.token_hex(24)
    _OPS_SESSIONS[token] = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "name": name,
        "ts": time.time(),
    }
    _save_sessions()
    return token


def get_session(token: str) -> Optional[dict]:
    if not token or token not in _OPS_SESSIONS:
        return None
    sess = _OPS_SESSIONS[token]
    if time.time() - sess.get("ts", 0) > OPS_SESSION_TTL:
        _OPS_SESSIONS.pop(token, None)
        _save_sessions()
        return None
    return sess


def drop_session(token: str):
    _OPS_SESSIONS.pop(token, None)
    _save_sessions()


def get_current_ops_user(request) -> Optional[dict]:
    """Đọc người dùng hiện tại từ request.
    Ưu tiên 1: Session admin Javis (cookie javis_session) -> luôn là role owner.
    Ưu tiên 2: Session Ops (cookie ops_session).
    """
    # 1. Kiểm tra cookie javis_session
    javis_tok = request.cookies.get("javis_session", "")
    if javis_tok and cfgmod.valid_session(javis_tok):
        cfg = cfgmod.read_settings()
        admin_uname = cfg.get("auth", {}).get("username") or "admin"
        return {
            "id": "owner",
            "username": admin_uname,
            "role": "owner",
            "name": "Chủ máy",
        }

    # 2. Kiểm tra cookie ops_session
    ops_tok = request.cookies.get("ops_session", "")
    if ops_tok:
        s = get_session(ops_tok)
        if s:
            return s

    return None


def verify_login(username: str, password: str) -> Optional[dict]:
    """Xác thực đăng nhập Ops:
    - Nếu là tài khoản admin chủ máy (settings.json) -> role owner
    - Nếu là tài khoản trong ops_users.json -> role tương ứng
    """
    u_clean = username.strip()
    cfg = cfgmod.read_settings()
    admin_uname = cfg.get("auth", {}).get("username") or "admin"

    # Kiểm tra chủ máy (Owner)
    if u_clean == admin_uname and cfgmod.verify_password(password, cfg):
        return {
            "id": "owner",
            "username": admin_uname,
            "role": "owner",
            "name": "Chủ máy",
        }

    # Kiểm tra danh sách Ops users
    user = get_user_by_username(u_clean)
    if user and user.get("enabled", True):
        if verify_ops_password(password, user.get("password_hash", ""), user.get("salt", "")):
            return sanitize_user(user)

    return None


# ============================================================
# RBAC Policy Matrix Check (Fail-closed)
# ============================================================
def check_access_permission(user: Optional[dict], path: str, method: str, payload: Optional[dict] = None) -> Tuple[bool, Optional[str]]:
    """Kiểm tra quyền truy cập theo Ma trận RBAC trong plan:
    - role == 'owner': Luôn cho phép.
    - role == 'manager':
        * Xem/gửi/bỏ nháp, xem khách, tạo việc, Messenger.
        * Gộp/xoá CRM.
        * Cấu hình Care (nhưng CẤM mode=full).
        * Quét bình luận ngay.
        * Xem xu hướng / usage token.
        * CẤM buồng lái: terminal, mcp, settings console, chat, kanban run, / (console chủ).
    - role == 'staff':
        * Chỉ xem/gửi/bỏ nháp, xem khách, tạo việc handoff, Messenger ("Javis nhận lại").
        * CẤM: gộp/xoá CRM, đổi settings Care, Quét ngay, xem usage tiền, / (console chủ).
    """
    if not user:
        return False, "Chưa đăng nhập"

    role = user.get("role")
    if role == "owner":
        return True, None

    m = method.upper()

    # Landing `/` `/chao` công khai. Console chủ máy chuyển sang `/app`.
    if path in ("/", "/chao"):
        return True, None
    if path in ("/app", "/index.html"):
        return False, "Chỉ chủ máy mới được truy cập console điều khiển"

    # Các route cấm hoàn toàn với staff và manager:
    forbidden_prefixes = (
        "/terminal",
        "/mcp",
        "/connect",
        "/settings",
        "/chat",
        "/plugins",
        "/brandkits",
    )
    if any(path == p or path.startswith(p + "/") for p in forbidden_prefixes):
        return False, f"Tài khoản {role} không có quyền truy cập tính năng buồng lái"

    if path == "/kanban/run":
        return False, "Chỉ chủ máy mới được kích hoạt chạy việc tự động"

    # Xử lý riêng cho Manager
    if role == "manager":
        # Manager được vào /ops/*
        if path.startswith("/ops"):
            # Quản lý nhân sự (/ops/users) chỉ dành cho owner
            if path.startswith("/ops/users"):
                return False, "Chỉ chủ máy mới được quản lý tài khoản nhân sự"
            return True, None

        # Manager được phép cấu hình Care nhưng cấm mode=full
        if path == "/fanpage-care/settings" and m == "POST":
            if payload and payload.get("mode") == "full":
                return False, "Chỉ chủ máy mới được kích hoạt chế độ Tự động + tin (mode full)"
            if payload and payload.get("kill_switch") is not None:
                return False, "Chỉ chủ máy mới được bật/tắt Kill Switch"
            return True, None

        # Manager được vào usage, kanban read, care
        if path.startswith("/usage") or path.startswith("/fanpage-care") or path.startswith("/kanban") or path.startswith("/inbox"):
            return True, None

    # Xử lý riêng cho Staff
    if role == "staff":
        if path.startswith("/ops"):
            if path.startswith("/ops/users"):
                return False, "Chỉ chủ máy mới được quản lý tài khoản nhân sự"
            return True, None

        # Staff cấm xem chi phí token /usage
        if path.startswith("/usage"):
            return False, "Nhân viên không có quyền xem chi phí token"

        # Staff cấm gộp/xóa CRM
        if path == "/fanpage-care/customers/merge" or (path.startswith("/fanpage-care/customers/") and m == "DELETE"):
            return False, "Nhân viên không có quyền gộp hoặc xoá dữ liệu khách hàng"

        # Staff cấm sửa settings Care và cấm bấm Quét ngay
        if path == "/fanpage-care/settings" or path == "/fanpage-care/poll-now":
            return False, "Nhân viên không có quyền thay đổi cài đặt hoặc kích hoạt quét"

        # Staff được phép các thao tác Care hàng ngày
        allowed_care_paths = (
            "/fanpage-care/state",
            "/fanpage-care/inbox",
            "/fanpage-care/customers",
            "/fanpage-care/conversations",
            "/fanpage-care/conversations/release-takeover",
            "/fanpage-care/handoff",
        )
        if any(path == p or path.startswith(p + "/") for p in allowed_care_paths):
            return True, None

        if path.startswith("/fanpage-care/drafts/") and path.endswith(("/send", "/reject")):
            return True, None

        if path == "/kanban" and m == "GET":
            return True, None

        if path == "/inbox" and m == "GET":
            return True, None

    return False, f"Tài khoản {role} không có quyền thực hiện thao tác này"
