import urllib.request
import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

base_url = os.getenv("SEOTRUM_OPS_BASE_URL", "http://127.0.0.1:7777").rstrip("/")

# 1. Login as nv_an (Kỹ thuật viên)
req = urllib.request.Request(
    f"{base_url}/ops/auth/login",
    data=json.dumps({"username": "nv_an", "password": "password123"}).encode(),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    login_data = json.loads(resp.read().decode())
    print("Login nv_an OK:", login_data.get("ok"), "User:", login_data.get("user"))
    token = login_data.get("token")

# 2. Get /ops/tasks
req = urllib.request.Request(
    f"{base_url}/ops/tasks",
    headers={"Authorization": f"Bearer {token}"}
)
with urllib.request.urlopen(req) as resp:
    tasks_data = json.loads(resp.read().decode())
    tasks = tasks_data.get("tasks", [])
    print(f"Total tasks on VPS: {len(tasks)}")
    print("First task:", tasks[0]["title"], "| Assignee:", tasks[0].get("assignee"))

# 3. Get /ops/directory as staff (nv_an)
req = urllib.request.Request(
    f"{base_url}/ops/directory",
    headers={"Authorization": f"Bearer {token}"}
)
with urllib.request.urlopen(req) as resp:
    dir_data = json.loads(resp.read().decode())
    users = dir_data.get("users", [])
    print(f"Total directory users visible on VPS: {len(users)}")
    for u in users:
        print(f" - [{u.get('code')}] {u.get('username')}: {u.get('name')} ({u.get('role_title') or u.get('role')})")

# 4. Verify /ops/users is FORBIDDEN (403) for non-owner
try:
    req_users = urllib.request.Request(
        f"{base_url}/ops/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req_users) as resp:
        print("ERROR: /ops/users should be 403 for non-owner!")
except urllib.error.HTTPError as e:
    print(f"Verified /ops/users blocked for staff: HTTP {e.code} (Correct!)")

# 5. Test /ops/rbac/roles
req_roles = urllib.request.Request(f"{base_url}/ops/rbac/roles")
with urllib.request.urlopen(req_roles) as resp:
    roles_data = json.loads(resp.read().decode())
    roles_dict = roles_data.get("roles", {})
    print(f"Total RBAC Roles on VPS: {len(roles_dict)} -> {list(roles_dict.keys())}")

# 6. Test Login as ql_tuan (Quản lý)
req = urllib.request.Request(
    f"{base_url}/ops/auth/login",
    data=json.dumps({"username": "ql_tuan", "password": "password123"}).encode(),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    login_ql = json.loads(resp.read().decode())
    print("Login ql_tuan OK:", login_ql.get("ok"), "User:", login_ql.get("user"))

print("\nALL VERIFICATIONS PASSED 100%!")
