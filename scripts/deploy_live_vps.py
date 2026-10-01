import os
import sys
import paramiko
import time

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

VPS_HOST = "180.93.37.8"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "wh8bCLxIAitPOfIB"
REMOTE_ROOT = "/root/Auto_social"

def upload_file(sftp, local_path, remote_path):
    remote_dir = os.path.dirname(remote_path).replace("\\", "/")
    ensure_remote_dir(sftp, remote_dir)
    print(f"Uploading {local_path} -> {remote_path}")
    sftp.put(local_path, remote_path)

def ensure_remote_dir(sftp, remote_dir):
    parts = remote_dir.strip("/").split("/")
    cur = ""
    for p in parts:
        cur += "/" + p
        try:
            sftp.stat(cur)
        except IOError:
            try:
                sftp.mkdir(cur)
            except IOError:
                pass

def upload_dir_recursive(sftp, local_dir, remote_dir):
    ensure_remote_dir(sftp, remote_dir)
    for root, dirs, files in os.walk(local_dir):
        rel = os.path.relpath(root, local_dir).replace("\\", "/")
        target_dir = remote_dir if rel == "." else f"{remote_dir}/{rel}"
        ensure_remote_dir(sftp, target_dir)
        for f in files:
            lp = os.path.join(root, f)
            rp = f"{target_dir}/{f}"
            print(f"Uploading {lp} -> {rp}")
            sftp.put(lp, rp)

def main():
    print(f"Connecting to VPS {VPS_HOST}:{VPS_PORT}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("Connected.")
    sftp = ssh.open_sftp()

    # Files to upload
    single_files = [
        ("website/index.html", f"{REMOTE_ROOT}/website/index.html"),
        ("website/logo.png", f"{REMOTE_ROOT}/website/logo.png"),
        ("dashboard/logo.png", f"{REMOTE_ROOT}/dashboard/logo.png"),
        ("server/main.py", f"{REMOTE_ROOT}/server/main.py"),
        ("server/fanpage_care.py", f"{REMOTE_ROOT}/server/fanpage_care.py"),
        ("server/fanpage_care_policy.py", f"{REMOTE_ROOT}/server/fanpage_care_policy.py"),
        ("server/fanpage_care_store.py", f"{REMOTE_ROOT}/server/fanpage_care_store.py"),
        ("server/ops_attribution.py", f"{REMOTE_ROOT}/server/ops_attribution.py"),
        ("server/ops_briefing.py", f"{REMOTE_ROOT}/server/ops_briefing.py"),
        ("server/ops_campaign.py", f"{REMOTE_ROOT}/server/ops_campaign.py"),
        ("server/ops_campaign_store.py", f"{REMOTE_ROOT}/server/ops_campaign_store.py"),
        ("server/ops_order_store.py", f"{REMOTE_ROOT}/server/ops_order_store.py"),
        ("server/ops_orders.py", f"{REMOTE_ROOT}/server/ops_orders.py"),
        ("server/ops_automation_engine.py", f"{REMOTE_ROOT}/server/ops_automation_engine.py"),
        ("server/ops_rbac.py", f"{REMOTE_ROOT}/server/ops_rbac.py"),
        ("server/ops_sales_extraction.py", f"{REMOTE_ROOT}/server/ops_sales_extraction.py"),
        ("server/ops_shipping.py", f"{REMOTE_ROOT}/server/ops_shipping.py"),
        ("server/ops_shipping_store.py", f"{REMOTE_ROOT}/server/ops_shipping_store.py"),
        ("server/ops_shipping_settings.json", f"{REMOTE_ROOT}/server/ops_shipping_settings.json"),
        ("server/ops_automation_kill_switch.json", f"{REMOTE_ROOT}/server/ops_automation_kill_switch.json"),
        ("server/ops_tasks_store.py", f"{REMOTE_ROOT}/server/ops_tasks_store.py"),
        ("server/ops_users.json", f"{REMOTE_ROOT}/server/ops_users.json"),
        ("server/ops_tasks.json", f"{REMOTE_ROOT}/server/ops_tasks.json"),
        ("server/ops_business_store.py", f"{REMOTE_ROOT}/server/ops_business_store.py"),
        ("server/ops_business_modules.py", f"{REMOTE_ROOT}/server/ops_business_modules.py"),
        ("server/ops_documents_store.py", f"{REMOTE_ROOT}/server/ops_documents_store.py"),
        ("server/ops_documents.py", f"{REMOTE_ROOT}/server/ops_documents.py"),
        ("server/ops_qa.py", f"{REMOTE_ROOT}/server/ops_qa.py"),
        ("server/web_security.py", f"{REMOTE_ROOT}/server/web_security.py"),
        ("scripts/seed_mock_ghn_orders.py", f"{REMOTE_ROOT}/scripts/seed_mock_ghn_orders.py"),
        ("brains/Brain Default/memory/MEMORY.md", f"{REMOTE_ROOT}/brains/Brain Default/memory/MEMORY.md"),
        ("brains/Brain Default/memory/facts/ops_documents_vault.md", f"{REMOTE_ROOT}/brains/Brain Default/memory/facts/ops_documents_vault.md"),
        ("brains/Brain Default/memory/facts/ops_business_catalog.md", f"{REMOTE_ROOT}/brains/Brain Default/memory/facts/ops_business_catalog.md"),
        ("brains/Brain Default/memory/facts/ops_shipping_and_operations.md", f"{REMOTE_ROOT}/brains/Brain Default/memory/facts/ops_shipping_and_operations.md"),
        ("tests/python/test_ops_qa.py", f"{REMOTE_ROOT}/tests/python/test_ops_qa.py"),
        ("docs/dev/2026-09-30-rbac-multi-role-architecture.md", f"{REMOTE_ROOT}/docs/dev/2026-09-30-rbac-multi-role-architecture.md"),
    ]

    for local_f, remote_f in single_files:
        if os.path.exists(local_f):
            upload_file(sftp, local_f, remote_f)
        else:
            print(f"Warning: {local_f} does not exist locally")

    # Upload system/plugins/ops-tools
    if os.path.exists("system/plugins/ops-tools"):
        print("Uploading system/plugins/ops-tools...")
        upload_dir_recursive(sftp, "system/plugins/ops-tools", f"{REMOTE_ROOT}/system/plugins/ops-tools")

    # Upload website/assets if exists
    if os.path.exists("website/assets"):
        upload_dir_recursive(sftp, "website/assets", f"{REMOTE_ROOT}/website/assets")

    # Upload branding dir if exists
    if os.path.exists("server/branding"):
        upload_dir_recursive(sftp, "server/branding", f"{REMOTE_ROOT}/server/branding")

    # Upload ops/dist
    if os.path.exists("ops/dist"):
        print("Cleaning and uploading ops/dist...")
        ssh.exec_command(f"rm -rf {REMOTE_ROOT}/ops/dist/*")
        time.sleep(1)
        upload_dir_recursive(sftp, "ops/dist", f"{REMOTE_ROOT}/ops/dist")

    sftp.close()
    print("All files transferred successfully.")


    # Seed mock GHN orders on VPS
    print("Seeding mock GHN orders on VPS...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {REMOTE_ROOT} && python3 scripts/seed_mock_ghn_orders.py")
    seed_out = stdout.read().decode().strip()
    print("Seed output:\n", seed_out)

    # Restart service
    print("Restarting javis.service on VPS...")
    stdin, stdout, stderr = ssh.exec_command("systemctl restart javis.service")
    exit_status = stdout.channel.recv_exit_status()
    print(f"Restart finished with code {exit_status}")

    time.sleep(3)

    # Check status
    print("Checking service status...")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active javis.service")
    status = stdout.read().decode().strip()
    print(f"Service is-active: {status}")

    # Verify curl on VPS
    print("Testing HTTP endpoints on VPS...")
    for path in ["/", "/logo.png", "/brand-logo", "/ops/", "/api/modules", "/ops/hub/summary", "/ops/documents", "/ops/documents/stats", "/ops/documents/templates", "/ops/orders?limit=10"]:
        cmd = f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:7777{path}"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        code = stdout.read().decode().strip()
        print(f"GET http://127.0.0.1:7777{path} -> HTTP {code}")

    # Test GHN sync on mock order
    print("Testing GHN sync on mock order on VPS...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -X POST http://127.0.0.1:7777/ops/orders/ord_6455269a10/sync-shipment")
    sync_resp = stdout.read().decode().strip()
    print("GHN sync response:", sync_resp[:200])

    # Fetch executive summary from /ops/hub/summary to verify real aggregator
    stdin, stdout, stderr = ssh.exec_command("curl -s http://127.0.0.1:7777/ops/hub/summary")
    hub_json = stdout.read().decode().strip()
    try:
        import json
        parsed = json.loads(hub_json)
        exec_s = parsed.get("executive_summary", {})
        mods = parsed.get("modules", [])
        print("Verified Operations Hub Executive Command Center on VPS:")
        print(f"  - Need action today: {exec_s.get('need_action_today')}")
        print(f"  - Critical alerts: {exec_s.get('critical_alerts')}")
        print(f"  - Total modules: {len(mods)}")
        for m in mods[:4]:
            print(f"    * [{m.get('code')}] {m.get('name')} | KPI: {m.get('kpi', {}).get('main')} ({m.get('data_source_label')})")
    except Exception as e:
        print(f"Response preview: {hub_json[:200]} (parse err: {e})")

    ssh.close()
    print("Deployment completed successfully!")

if __name__ == "__main__":
    main()
