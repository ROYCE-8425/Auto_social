# ============================================================
# Javis OS - Module Phân Quyền Vận Hành (Ops RBAC)
# docs/dev/2026-09-16-ops-dashboard-plan.md & RBAC Multi-role Matrix
# Quản lý tài khoản đa vai trò và thiết lập quyền hạn tùy chỉnh (Fail-closed).
# ============================================================
import json
import os
import secrets
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

try:
    import config as cfgmod
except ModuleNotFoundError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    import config as cfgmod

OPS_USERS_FILE = cfgmod.STATE_DIR / "ops_users.json"
OPS_SESSIONS_FILE = cfgmod.STATE_DIR / "ops_sessions.json"
OPS_ROLE_PERMISSIONS_FILE = cfgmod.STATE_DIR / "ops_role_permissions.json"
OPS_SESSION_TTL = 30 * 86400  # 30 ngày

# ============================================================
# 1. Danh Mục Các Vai Trò (Roles Registry)
# ============================================================
ROLES_REGISTRY: Dict[str, Dict[str, Any]] = {
    "owner": {
        "title": "Chủ sở hữu / Giám đốc",
        "code": "OWN",
        "badge_color": "purple",
        "description": "Toàn quyền hệ thống: buồng lái console máy chủ, Terminal, MCP, cấu hình model AI, quản trị tài khoản và kích hoạt Kill Switch khẩn cấp.",
        "level": 100,
    },
    "manager": {
        "title": "Quản lý vận hành",
        "code": "MGR",
        "badge_color": "indigo",
        "description": "Quản lý toàn diện đội ngũ CSKH, chốt đơn và vận chuyển; xem SĐT khách đầy đủ (unmask), gộp/xoá CRM, cấu hình Care (suggest/auto), quét bình luận ngay, xem chi phí token AI.",
        "level": 80,
    },
    "cskh": {
        "title": "Chuyên viên CSKH & Tư vấn",
        "code": "CSKH",
        "badge_color": "blue",
        "description": "Trực tiếp duyệt & chỉnh sửa nháp phản hồi AI, tiếp quản hội thoại Messenger/Zalo, tạo việc handoff, tạo đơn hàng từ chat, xem CRM (SĐT che bảo mật).",
        "level": 40,
    },
    "sales": {
        "title": "Chuyên viên Kinh doanh",
        "code": "SALE",
        "badge_color": "emerald",
        "description": "Quản lý đơn hàng, trích xuất đơn hàng từ chat khách, xác nhận đơn hàng, huỷ đơn kèm lý do, tiếp cận lead tiềm năng từ bình luận/tin nhắn.",
        "level": 40,
    },
    "warehouse": {
        "title": "Nhân viên Kho & Vận chuyển",
        "code": "KHO",
        "badge_color": "amber",
        "description": "Xử lý đóng gói đơn hàng, tạo vận đơn sang GHTK/GHN/ViettelPost, in phiếu gửi hàng, tra cứu hành trình vận chuyển theo thời gian thực.",
        "level": 30,
    },
    "marketing": {
        "title": "Chuyên viên Marketing & TikTok",
        "code": "MKT",
        "badge_color": "pink",
        "description": "Lên chiến dịch tiếp thị Autopilot, xuất bản nội dung TikTok Carousel/Video, xem Radar đối thủ, phân tích nguồn chuyển đổi (Attribution).",
        "level": 40,
    },
    "technical": {
        "title": "Kỹ thuật viên Kênh nối",
        "code": "TECH",
        "badge_color": "cyan",
        "description": "Kiểm tra kết nối các kênh (Facebook Fanpage, Zalo, Telegram, TikTok), giám sát webhook, chạy kiểm thử đánh giá chất lượng QA.",
        "level": 40,
    },
    "staff": {
        "title": "Nhân viên chung (Mặc định)",
        "code": "NV",
        "badge_color": "slate",
        "description": "Vai trò tổng hợp cơ bản (tương thích ngược): Duyệt nháp Care, xem CRM che SĐT, tạo việc handoff, xử lý công việc được giao.",
        "level": 30,
    },
}

VALID_ROLES: Tuple[str, ...] = tuple(ROLES_REGISTRY.keys())

# ============================================================
# 2. Danh Mục Toàn Bộ Quyền Hạn (Permissions Catalog)
# ============================================================
ALL_PERMISSIONS_CATALOG = [
    {
        "category": "care",
        "category_title": "Hộp thư & Phản hồi CSKH",
        "permissions": [
            {"id": "care:view", "name": "Xem Hộp thư & Bình luận", "description": "Xem danh sách bình luận Fanpage, tin nhắn Messenger/Zalo và trạng thái bot Care."},
            {"id": "care:reply", "name": "Duyệt, chỉnh sửa & gửi nháp", "description": "Duyệt câu trả lời do AI soạn, sửa nội dung trước khi gửi, từ chối nháp hoặc tiếp quản chat."},
            {"id": "care:config", "name": "Cấu hình chế độ trả lời", "description": "Thay đổi chế độ Care giữa gợi ý (suggest), bán tự động (semi), tự động (auto)."},
            {"id": "care:poll_now", "name": "Kích hoạt quét bình luận tức thì", "description": "Bấm nút quét ngay trên Fanpage mà không cần chờ chu kỳ tự động."},
        ]
    },
    {
        "category": "crm",
        "category_title": "Khách hàng & CRM",
        "permissions": [
            {"id": "crm:view", "name": "Xem danh sách khách hàng", "description": "Xem danh sách khách hàng và lịch sử tương tác (Số điện thoại được che bảo mật)."},
            {"id": "crm:unmask_phone", "name": "Mở khoá xem SĐT đầy đủ", "description": "Xem đầy đủ 10 chữ số điện thoại của khách hàng để gọi điện chăm sóc."},
            {"id": "crm:edit", "name": "Ghi chú & Cập nhật khách hàng", "description": "Thêm ghi chú nội bộ, cập nhật nhu cầu, gắn tag phân loại khách hàng."},
            {"id": "crm:merge_delete", "name": "Gộp trùng & Xoá khách hàng", "description": "Gộp các hồ sơ khách hàng bị trùng lặp hoặc xoá hồ sơ rác khỏi CRM."},
        ]
    },
    {
        "category": "orders",
        "category_title": "Đơn hàng & Bán hàng",
        "permissions": [
            {"id": "orders:view", "name": "Xem danh sách đơn hàng", "description": "Xem danh sách đơn hàng, giá trị, sản phẩm và trạng thái thanh toán."},
            {"id": "orders:create_edit", "name": "Tạo & Chỉnh sửa đơn hàng", "description": "Tạo đơn hàng mới thủ công hoặc trích xuất từ đoạn chat của khách hàng."},
            {"id": "orders:confirm", "name": "Xác nhận đơn hàng", "description": "Duyệt xác nhận đơn hàng khi khách hàng đã chốt mua thành công."},
            {"id": "orders:cancel", "name": "Huỷ đơn hàng", "description": "Huỷ đơn hàng kèm lý do khi khách không nhận hàng hoặc đổi ý."},
        ]
    },
    {
        "category": "shipping",
        "category_title": "Kho vận & Giao nhận",
        "permissions": [
            {"id": "shipping:view", "name": "Xem thông tin vận chuyển", "description": "Tra cứu mã vận đơn, hành trình giao hàng và đơn vị chuyển phát."},
            {"id": "shipping:create_shipment", "name": "Tạo vận đơn giao hàng", "description": "Đóng gói và đẩy đơn sang GHTK, GHN, ViettelPost để lấy mã vận đơn."},
            {"id": "shipping:config", "name": "Cấu hình cổng vận chuyển", "description": "Cấu hình API token, kho hàng lấy hàng của các hãng vận chuyển."},
        ]
    },
    {
        "category": "marketing",
        "category_title": "Marketing & TikTok",
        "permissions": [
            {"id": "marketing:campaigns", "name": "Quản lý chiến dịch Autopilot", "description": "Tạo và theo dõi chiến dịch tiếp thị tự động, radar đối thủ cạnh tranh."},
            {"id": "marketing:social_publish", "name": "Đăng bài TikTok & Video", "description": "Soạn và xuất bản bài đăng Carousel hoặc video review lên kênh TikTok."},
        ]
    },
    {
        "category": "channels",
        "category_title": "Kênh kết nối & Kỹ thuật",
        "permissions": [
            {"id": "channels:view", "name": "Xem trạng thái kênh", "description": "Xem trạng thái kết nối Webhook Fanpage, Zalo OA, Telegram, TikTok."},
            {"id": "channels:manage", "name": "Cấu hình kết nối kênh", "description": "Thêm mới hoặc kết nối lại token mạng xã hội, webhook."},
            {"id": "qa:view_run", "name": "Kiểm thử chất lượng QA", "description": "Chạy kiểm thử tự động đánh giá độ chính xác câu trả lời của AI."},
        ]
    },
    {
        "category": "analytics",
        "category_title": "Báo cáo & Chi phí AI",
        "permissions": [
            {"id": "analytics:view_trends", "name": "Xem báo cáo xu hướng", "description": "Xem biểu đồ tương tác 7 ngày, phân tích FAQ và nguồn chuyển đổi."},
            {"id": "analytics:view_token_cost", "name": "Xem chi phí Token AI", "description": "Xem số lượng token đã dùng và ước tính chi phí tiền điện toán AI."},
        ]
    },
    {
        "category": "tasks",
        "category_title": "Công việc & Danh bạ",
        "permissions": [
            {"id": "tasks:view_manage", "name": "Quản lý việc Kanban", "description": "Xem và kéo thả cập nhật tiến độ công việc trên bảng Kanban."},
            {"id": "tasks:assign_all", "name": "Giao việc cho bất kỳ ai", "description": "Phân công công việc cho mọi nhân sự trong công ty."},
            {"id": "directory:view", "name": "Xem danh bạ nhân sự", "description": "Xem danh sách đồng nghiệp để phối hợp và giao việc."},
        ]
    },
]

# ============================================================
# 3. Ma Trận Quyền Hạn Mặc Định & Tùy Chỉnh
# ============================================================
DEFAULT_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "owner": [
        "*",  # Toàn quyền mọi tính năng
    ],
    "manager": [
        "care:view", "care:reply", "care:config", "care:poll_now",
        "crm:view", "crm:unmask_phone", "crm:edit", "crm:merge_delete",
        "orders:view", "orders:create_edit", "orders:confirm", "orders:cancel",
        "shipping:view", "shipping:create_shipment", "shipping:config",
        "marketing:campaigns", "marketing:social_publish",
        "channels:view", "channels:manage",
        "tasks:view_manage", "tasks:assign_all",
        "analytics:view_trends", "analytics:view_token_cost",
        "qa:view_run",
        "directory:view",
    ],
    "cskh": [
        "care:view", "care:reply", "care:poll_now",
        "crm:view", "crm:edit",
        "orders:view", "orders:create_edit",
        "shipping:view",
        "channels:view",
        "tasks:view_manage",
        "directory:view",
    ],
    "sales": [
        "care:view",
        "crm:view", "crm:edit",
        "orders:view", "orders:create_edit", "orders:confirm", "orders:cancel",
        "shipping:view",
        "tasks:view_manage",
        "directory:view",
    ],
    "warehouse": [
        "orders:view", "orders:confirm",
        "shipping:view", "shipping:create_shipment",
        "tasks:view_manage",
        "directory:view",
    ],
    "marketing": [
        "care:view",
        "marketing:campaigns", "marketing:social_publish",
        "channels:view",
        "analytics:view_trends",
        "tasks:view_manage",
        "directory:view",
    ],
    "technical": [
        "channels:view", "channels:manage",
        "qa:view_run",
        "tasks:view_manage",
        "directory:view",
    ],
    "staff": [
        "care:view", "care:reply", "care:poll_now",
        "crm:view", "crm:edit",
        "orders:view", "orders:create_edit",
        "shipping:view",
        "tasks:view_manage",
        "directory:view",
    ],
}


def load_role_permissions() -> Dict[str, List[str]]:
    """Tải ma trận phân quyền từ file tùy chỉnh (nếu có) hoặc dùng mặc định."""
    if OPS_ROLE_PERMISSIONS_FILE.exists():
        try:
            data = json.loads(OPS_ROLE_PERMISSIONS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                merged = {k: list(v) for k, v in DEFAULT_ROLE_PERMISSIONS.items()}
                for r, perms in data.items():
                    if r in VALID_ROLES and isinstance(perms, list):
                        merged[r] = perms
                merged["owner"] = ["*"]
                return merged
        except Exception:
            pass
    return {k: list(v) for k, v in DEFAULT_ROLE_PERMISSIONS.items()}


def save_role_permissions(permissions_dict: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Lưu ma trận phân quyền tùy chỉnh vào file."""
    permissions_dict["owner"] = ["*"]
    cleaned: Dict[str, List[str]] = {}
    for r in VALID_ROLES:
        if r == "owner":
            cleaned["owner"] = ["*"]
        else:
            perms = permissions_dict.get(r, DEFAULT_ROLE_PERMISSIONS.get(r, []))
            cleaned[r] = sorted(list(set(perms)))

    OPS_ROLE_PERMISSIONS_FILE.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False), encoding="utf-8")
    global ROLE_PERMISSIONS
    ROLE_PERMISSIONS = cleaned
    return cleaned


def reset_role_permissions() -> Dict[str, List[str]]:
    """Khôi phục ma trận phân quyền về mặc định ban đầu."""
    if OPS_ROLE_PERMISSIONS_FILE.exists():
        try:
            OPS_ROLE_PERMISSIONS_FILE.unlink()
        except Exception:
            pass
    global ROLE_PERMISSIONS
    ROLE_PERMISSIONS = {k: list(v) for k, v in DEFAULT_ROLE_PERMISSIONS.items()}
    return ROLE_PERMISSIONS


ROLE_PERMISSIONS: Dict[str, List[str]] = load_role_permissions()


def get_user_permissions(role: str) -> List[str]:
    """Lấy danh sách các quyền hạn được cấp cho một vai trò."""
    if role == "owner":
        return ["*"]
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS.get("staff", []))


def user_has_permission(user: Optional[dict], permission: str) -> bool:
    """Kiểm tra xem người dùng có quyền cụ thể hay không."""
    if not user:
        return False
    role = user.get("role", "")
    if role == "owner":
        return True
    perms = get_user_permissions(role)
    return "*" in perms or permission in perms


# ============================================================
# 4. Quản lý Session lưu trữ
# ============================================================
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


def create_user(username: str, password: str, role: str = "staff", name: str = "", enabled: bool = True, code: str = "") -> dict:
    if role not in VALID_ROLES:
        raise ValueError(f"Role không hợp lệ: {role}. Các role hợp lệ: {', '.join(VALID_ROLES)}")
    username_clean = username.strip()
    if not username_clean:
        raise ValueError("Username không được để trống")
    if get_user_by_username(username_clean):
        raise ValueError("Tên đăng nhập đã tồn tại")
    if len(password) < 6:
        raise ValueError("Mật khẩu tối thiểu 6 ký tự")

    h, salt = hash_ops_password(password)
    user_id = "u_" + secrets.token_hex(6)
    if not code:
        code = ROLES_REGISTRY.get(role, {}).get("code", "NV")

    new_user = {
        "id": user_id,
        "username": username_clean,
        "password_hash": h,
        "salt": salt,
        "role": role,
        "code": code,
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
    if "role" in updates:
        new_role = updates["role"]
        if new_role not in VALID_ROLES:
            raise ValueError(f"Role không hợp lệ: {new_role}. Các role hợp lệ: {', '.join(VALID_ROLES)}")
        u["role"] = new_role
        if "code" not in updates and not u.get("code"):
            u["code"] = ROLES_REGISTRY.get(new_role, {}).get("code", "NV")
    if "code" in updates:
        u["code"] = updates["code"].strip().upper()
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
    role = user.get("role", "staff")
    role_cfg = ROLES_REGISTRY.get(role, {})
    code = user.get("code")
    if not code:
        code = role_cfg.get("code", "NV")
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "role": role,
        "role_title": role_cfg.get("title", role),
        "name": user.get("name"),
        "code": code,
        "enabled": user.get("enabled", True),
        "created_at": user.get("created_at"),
        "permissions": get_user_permissions(role),
    }


def create_session(user_id: str, username: str, role: str, name: str, code: str = "") -> str:
    token = "ops_" + secrets.token_hex(24)
    if not code:
        u = get_user_by_id(user_id) or get_user_by_username(username)
        if u:
            code = u.get("code", "")
    if not code:
        code = ROLES_REGISTRY.get(role, {}).get("code", "NV")

    _OPS_SESSIONS[token] = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "role_title": ROLES_REGISTRY.get(role, {}).get("title", role),
        "name": name,
        "code": code,
        "permissions": get_user_permissions(role),
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


def is_demo_auto_owner() -> bool:
    """Kiểm tra xem hệ thống có đang bật chế độ demo tự động nhận owner hay không."""
    if os.getenv("JAVIS_OPS_DEMO_AUTO_OWNER", "").strip().lower() in ("1", "true", "yes"):
        return True
    if os.getenv("JAVIS_REQUIRE_LOGIN", "").strip().lower() in ("0", "false", "no"):
        return True
    return False


def get_current_ops_user(request) -> Optional[dict]:
    """Đọc người dùng hiện tại từ request.
    Ưu tiên 1: Session admin Javis (cookie javis_session) -> luôn là role owner.
    Ưu tiên 2: Session Ops (cookie ops_session).
    Ưu tiên 3: Authorization header (Bearer ops_...).
    Ưu tiên 4: Chế độ demo (chỉ khi JAVIS_OPS_DEMO_AUTO_OWNER=1 hoặc JAVIS_REQUIRE_LOGIN=0).
    Mặc định production: Trả về None nếu chưa đăng nhập.
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
            "role_title": "Chủ sở hữu / Giám đốc",
            "name": "Chủ máy",
            "code": "OWN",
            "permissions": ["*"],
        }

    # 2. Kiểm tra cookie ops_session
    ops_tok = request.cookies.get("ops_session", "")
    if ops_tok:
        s = get_session(ops_tok)
        if s:
            role = s.get("role", "staff")
            if not s.get("code"):
                u = get_user_by_username(s.get("username", ""))
                s["code"] = u.get("code", "") if u else ROLES_REGISTRY.get(role, {}).get("code", "NV")
            s["permissions"] = get_user_permissions(role)
            if "role_title" not in s:
                s["role_title"] = ROLES_REGISTRY.get(role, {}).get("title", role)
            return s

    # 3. Kiểm tra Authorization header
    auth_hdr = request.headers.get("Authorization", "")
    if auth_hdr.startswith("Bearer "):
        tok = auth_hdr[7:].strip()
        s = get_session(tok)
        if s:
            role = s.get("role", "staff")
            if not s.get("code"):
                u = get_user_by_username(s.get("username", ""))
                s["code"] = u.get("code", "") if u else ROLES_REGISTRY.get(role, {}).get("code", "NV")
            s["permissions"] = get_user_permissions(role)
            if "role_title" not in s:
                s["role_title"] = ROLES_REGISTRY.get(role, {}).get("title", role)
            return s

    # 4. Chế độ demo auto-owner (chỉ khi có biến môi trường chỉ định)
    if is_demo_auto_owner():
        cfg = cfgmod.read_settings()
        admin_uname = cfg.get("auth", {}).get("username") or "admin"
        return {
            "id": "owner",
            "username": admin_uname,
            "role": "owner",
            "role_title": "Chủ sở hữu / Giám đốc",
            "name": "Chủ máy (Demo)",
            "code": "OWN",
            "permissions": ["*"],
            "is_demo": True,
        }

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
            "role_title": "Chủ sở hữu / Giám đốc",
            "name": "Chủ máy",
            "code": "OWN",
            "permissions": ["*"],
        }

    # Kiểm tra danh sách Ops users
    user = get_user_by_username(u_clean)
    if user and user.get("enabled", True):
        if verify_ops_password(password, user.get("password_hash", ""), user.get("salt", "")):
            return sanitize_user(user)

    return None


# ============================================================
# 5. RBAC Policy Matrix Check (Fail-closed)
# ============================================================
def check_access_permission(user: Optional[dict], path: str, method: str, payload: Optional[dict] = None) -> Tuple[bool, Optional[str]]:
    """Kiểm tra quyền truy cập theo Ma trận RBAC đa vai trò (Fail-closed):
    - role == 'owner': Luôn cho phép toàn quyền.
    - Không có user: 401/403 Chưa đăng nhập.
    - CÁC VAI TRÒ KHÁC:
        * CẤM buồng lái kỹ thuật: terminal, mcp, settings console, chat bot lõi, kanban run, /app, /index.html.
        * CẤM quản lý tài khoản (/ops/users): chỉ dành riêng cho Owner.
        * Quyền theo từng chức năng được kiểm tra năng động qua user_has_permission().
    """
    if not user:
        return False, "Chưa đăng nhập"

    role = user.get("role")
    if role == "owner":
        return True, None

    m = method.upper()

    # 1. Các route công khai hoặc cho phép mọi người dùng đã đăng nhập:
    if path in ("/", "/chao"):
        return True, None
    if path.startswith("/tiktok-media"):
        return True, None
    if path == "/tiktok/status" and m == "GET":
        return True, None
    if path in ("/ops/directory", "/ops/rbac/roles"):
        return True, None
    if path == "/ops/rbac/permissions" and m == "GET":
        return True, None

    # 2. Các route buồng lái kỹ thuật CẤM TUYỆT ĐỐI với mọi role khác Owner:
    if path in ("/app", "/index.html"):
        return False, "Chỉ chủ máy mới được truy cập console điều khiển"

    forbidden_cockpit_prefixes = (
        "/terminal",
        "/mcp",
        "/connect",
        "/settings",
        "/chat",
        "/plugins",
        "/brandkits",
    )
    if any(path == p or path.startswith(p + "/") for p in forbidden_cockpit_prefixes):
        return False, f"Tài khoản {role} không có quyền truy cập tính năng buồng lái"

    if path == "/kanban/run":
        return False, "Chỉ chủ máy mới được kích hoạt chạy việc tự động"

    # 3. Quản trị tài khoản nhân sự (/ops/users) & Cấu hình phân quyền (/ops/rbac/permissions POST): Chỉ Owner
    if path == "/ops/users" or path.startswith("/ops/users/"):
        return False, "Chỉ chủ máy mới được quản lý tài khoản nhân sự"
    if path.startswith("/ops/rbac/permissions") and m in ("POST", "PUT", "DELETE"):
        return False, "Chỉ chủ máy mới có quyền thiết lập ma trận phân quyền"

    # 4. Bảo vệ cài đặt Care đặc biệt & Kill Switch (Chỉ Owner):
    if path == "/fanpage-care/settings" and m == "POST":
        if payload and payload.get("mode") == "full":
            return False, "Chỉ chủ máy mới được kích hoạt chế độ Tự động + tin (mode full)"
        if payload and payload.get("kill_switch") is not None:
            return False, "Chỉ chủ máy mới được bật/tắt Kill Switch"

    if path.startswith("/ops/automation/kill-switch"):
        return False, "Chỉ chủ máy mới được bật/tắt Kill Switch"

    # 5. Chi phí Token AI (/usage): Kiểm tra quyền analytics:view_token_cost
    if path.startswith("/usage"):
        if user_has_permission(user, "analytics:view_token_cost"):
            return True, None
        return False, f"Tài khoản {role} không có quyền xem chi phí token"

    # 6. Thao tác nhạy cảm CRM: Gộp hồ sơ trùng, xoá khách hàng, backfill lịch sử
    if path in ("/fanpage-care/customers/merge", "/fanpage-care/customers/backfill") or (path.startswith("/fanpage-care/customers/") and m == "DELETE"):
        if user_has_permission(user, "crm:merge_delete"):
            return True, None
        return False, f"Tài khoản {role} không có quyền gộp, xoá hoặc đồng bộ lại dữ liệu khách hàng"

    # 7. Cài đặt Fanpage Care & Quét ngay (poll-now):
    if path == "/fanpage-care/settings":
        if user_has_permission(user, "care:config"):
            return True, None
        return False, f"Tài khoản {role} không có quyền thay đổi cài đặt Care"

    if path == "/fanpage-care/poll-now":
        if user_has_permission(user, "care:poll_now") or user_has_permission(user, "care:view"):
            return True, None
        return False, f"Tài khoản {role} không có quyền kích hoạt quét bình luận"

    # 8. Phân hệ TikTok:
    if path.startswith("/tiktok"):
        if path in ("/tiktok/loop-toggle", "/tiktok/kit-account"):
            return False, "Chỉ chủ máy mới có quyền cấu hình tài khoản TikTok"
        if user_has_permission(user, "marketing:social_publish"):
            return True, None
        return False, "Chỉ chủ máy mới có quyền thực hiện thao tác đăng hoặc cấu hình TikTok"

    # 9. Cài đặt Vận chuyển (/ops/shipping/settings):
    if path == "/ops/shipping/settings" and m in ("POST", "PUT", "PATCH", "DELETE"):
        if user_has_permission(user, "shipping:config"):
            return True, None
        return False, "Nhân viên không có quyền thay đổi cài đặt vận chuyển"

    # 10. Tạo vận đơn giao hàng (/create-shipment):
    if path.endswith("/create-shipment") and m == "POST":
        if user_has_permission(user, "shipping:create_shipment"):
            return True, None
        return False, f"Tài khoản {role} không có quyền tạo vận đơn giao hàng"

    # 11. Xác nhận và huỷ đơn hàng:
    if path.endswith("/confirm") and m == "POST":
        if user_has_permission(user, "orders:confirm"):
            return True, None
        return False, f"Tài khoản {role} không có quyền xác nhận đơn hàng"

    if path.endswith("/cancel") and m == "POST":
        if user_has_permission(user, "orders:cancel"):
            return True, None
        return False, f"Tài khoản {role} không có quyền huỷ đơn hàng"

    # 12. Chiến dịch tiếp thị & Phân tích tiếp thị (Campaigns, Competitor Radar, Attribution):
    if path.startswith(("/ops/campaigns", "/ops/competitor", "/ops/attribution")):
        if user_has_permission(user, "marketing:campaigns"):
            return True, None
        return False, f"Tài khoản {role} không có quyền quản lý chiến dịch tiếp thị"

    # 13. Kỹ thuật kênh nối (/ops/channels) & Đánh giá QA benchmark (/ops/qa/run, /ops/qa/eval):
    # Lưu ý: /ops/qa là Trợ lý ca làm việc (Ops Q&A Assistant) cho mọi nhân sự (Staff, CSKH, Sales, Quản lý)
    if path == "/ops/qa":
        return True, None
    if path.startswith(("/ops/qa/run", "/ops/qa/eval", "/ops/qa/benchmark")):
        if user_has_permission(user, "qa:view_run"):
            return True, None
        return False, f"Tài khoản {role} không có quyền thực hiện kiểm thử QA"


    if path.startswith("/ops/channels"):
        if m in ("POST", "PUT", "PATCH", "DELETE"):
            if user_has_permission(user, "channels:manage"):
                return True, None
            return False, f"Tài khoản {role} không có quyền cấu hình kết nối kênh"
        return True, None

    # 14. Duyệt câu trả lời Care hàng ngày (Duyệt nháp, Gửi, Bỏ qua, Handoff, Release takeover):
    care_action_suffixes = ("/send", "/reject", "/handoff", "/release-takeover")
    if any(path.endswith(s) for s in care_action_suffixes) or path.startswith("/fanpage-care/drafts/"):
        if user_has_permission(user, "care:reply"):
            return True, None
        return False, f"Tài khoản {role} không có quyền duyệt phản hồi khách hàng"

    # 14b. Xuất bản mạng xã hội qua Social Provider Adapter (/ops/social/publish):
    if path == "/ops/social/publish" and m == "POST":
        if user_has_permission(user, "marketing:social_publish"):
            return True, None
        return False, f"Tài khoản {role} không có quyền xuất bản bài đăng mạng xã hội"

    # 15. Xem dữ liệu hàng ngày trong /ops:
    if path.startswith("/ops"):
        return True, None

    # 16. Xem dữ liệu Care (state, inbox, customers, conversations, stats):
    allowed_care_paths = (
        "/fanpage-care/state",
        "/fanpage-care/inbox",
        "/fanpage-care/customers",
        "/fanpage-care/conversations",
        "/fanpage-care/stats",
    )
    if any(path == p or path.startswith(p + "/") for p in allowed_care_paths):
        return True, None

    # 17. Xem bảng Kanban và Hộp thư tổng hợp:
    if path == "/kanban" and m == "GET":
        return True, None
    if path == "/inbox" and m == "GET":
        return True, None

    return False, f"Tài khoản {role} không có quyền thực hiện thao tác này"
