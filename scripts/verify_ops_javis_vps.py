import os
import sys

import paramiko

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

VPS_HOST = os.getenv("SEOTRUM_VPS_HOST")
VPS_PORT = int(os.getenv("SEOTRUM_VPS_PORT", "22"))
VPS_USER = os.getenv("SEOTRUM_VPS_USER", "root")
VPS_PASS = os.getenv("SEOTRUM_VPS_PASSWORD")
VPS_KEY_FILE = os.getenv("SEOTRUM_VPS_KEY_FILE")

if not VPS_HOST:
    raise SystemExit("Set SEOTRUM_VPS_HOST before running this script.")
if not VPS_PASS and not VPS_KEY_FILE:
    raise SystemExit("Set SEOTRUM_VPS_PASSWORD or SEOTRUM_VPS_KEY_FILE before running this script.")

connect_kwargs = {
    "hostname": VPS_HOST,
    "port": VPS_PORT,
    "username": VPS_USER,
    "timeout": 15,
}
if VPS_KEY_FILE:
    connect_kwargs["key_filename"] = VPS_KEY_FILE
else:
    connect_kwargs["password"] = VPS_PASS

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(**connect_kwargs)

test_script = r'''
import sys, asyncio
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'server')
import ops_qa, plugins_host

print('--- CHECK PLUGINS ---')
specs, route = plugins_host.plugin_tools()
ops_names = [s['name'] for s in specs if s['name'].startswith('ops_')]
print('Loaded ops tools:', ops_names)

print('\n--- CHECK OPS QA ---')
user = {'id': 'test_admin', 'role': 'admin'}
scope = 'all'

async def run():
    ans1 = await ops_qa.answer_ops_qa('Khoa hoc Tin hoc van phong MOS gia bao nhieu?', scope, user)
    print('[Q1] Product Price:', str(ans1.get('reply'))[:120], '...')
    print('     Citations:', ans1.get('citations'))

    ans2 = await ops_qa.answer_ops_qa('Co van ban nao sap het han khong?', scope, user)
    print('[Q2] Doc Vault:', str(ans2.get('reply'))[:120], '...')
    print('     Citations:', ans2.get('citations'))

    ans3 = await ops_qa.answer_ops_qa('Kiem tra ma van don GHNMOCK-HCM-001', scope, user)
    print('[Q3] GHN Tracking:', str(ans3.get('reply'))[:120], '...')
    print('     Citations:', ans3.get('citations'))

    p_out = await route['ops_catalog_query']['call']({'keyword': 'tin hoc'})
    print('[Plugin tool] ops_catalog_query:\n', p_out[:140], '...')

asyncio.run(run())
'''

try:
    sftp = ssh.open_sftp()
    try:
        with sftp.file("/root/Auto_social/test_vps_ops_qa.py", "w") as f:
            f.write(test_script)
    finally:
        sftp.close()

    stdin, stdout, stderr = ssh.exec_command("cd /root/Auto_social && /root/Auto_social/.venv/bin/python -u test_vps_ops_qa.py")
    print("=== VPS OUTPUT ===")
    for line in iter(stdout.readline, ""):
        print(line, end="", flush=True)

    err = stderr.read().decode("utf-8", errors="replace")
    if err:
        print("=== VPS ERRORS ===")
        print(err)
finally:
    ssh.close()
