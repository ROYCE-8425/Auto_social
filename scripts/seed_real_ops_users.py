"""
Seed real staff & manager user accounts into ops_users.json
"""
import sys
from pathlib import Path

# Add server directory to path
server_dir = Path(__file__).resolve().parent.parent / "server"
sys.path.insert(0, str(server_dir))

import ops_rbac

REAL_USERS = [
    {
        "username": "ql_tuan",
        "name": "Lê Tuấn (Quản lý vận hành)",
        "role": "manager",
        "password": "password123",
        "code": "LT",
    },
    {
        "username": "nv_thao",
        "name": "Lê Thảo (Chuyên viên CSKH)",
        "role": "cskh",
        "password": "password123",
        "code": "LT",
    },
    {
        "username": "sale_huy",
        "name": "Võ Huy (Chuyên viên Kinh doanh)",
        "role": "sales",
        "password": "password123",
        "code": "VH",
    },
    {
        "username": "kho_phong",
        "name": "Phạm Phong (Kho & Vận chuyển)",
        "role": "warehouse",
        "password": "password123",
        "code": "PP",
    },
    {
        "username": "mkt_linh",
        "name": "Nguyễn Linh (Marketing & TikTok)",
        "role": "marketing",
        "password": "password123",
        "code": "NL",
    },
    {
        "username": "nv_an",
        "name": "Nguyễn Văn An (Kỹ thuật viên Kênh)",
        "role": "technical",
        "password": "password123",
        "code": "NV",
    },
    {
        "username": "nv_minh",
        "name": "Trần Minh (Tư vấn viên chung)",
        "role": "staff",
        "password": "password123",
        "code": "TM",
    },
]

def seed():
    existing = ops_rbac.load_users()
    existing_unames = {u.get("username", "").lower(): u for u in existing}
    
    updated = False
    for ru in REAL_USERS:
        uname = ru["username"].lower()
        if uname in existing_unames:
            # Update password and role to ensure login works
            u = existing_unames[uname]
            h, salt = ops_rbac.hash_ops_password(ru["password"])
            u["password_hash"] = h
            u["salt"] = salt
            u["name"] = ru["name"]
            u["role"] = ru["role"]
            u["code"] = ru["code"]
            u["enabled"] = True
            print(f"Updated existing user: {ru['username']} ({ru['role']})")
            updated = True
        else:
            h, salt = ops_rbac.hash_ops_password(ru["password"])
            uid = "u_" + uname
            new_u = {
                "id": uid,
                "username": ru["username"],
                "password_hash": h,
                "salt": salt,
                "role": ru["role"],
                "code": ru["code"],
                "enabled": True,
                "name": ru["name"],
                "created_at": 1790700000.0,
            }
            existing.append(new_u)
            print(f"Created new user: {ru['username']} ({ru['role']})")
            updated = True

    if updated:
        ops_rbac.save_users(existing)
        print("Successfully saved users to ops_users.json!")

if __name__ == "__main__":
    seed()
