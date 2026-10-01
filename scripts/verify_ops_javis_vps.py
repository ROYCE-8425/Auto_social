import paramiko
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("180.93.37.8", port=22, username="root", password="wh8bCLxIAitPOfIB", timeout=15)

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
    # 1. Product price
    ans1 = await ops_qa.answer_ops_qa('Khóa học Tin học văn phòng MOS giá bao nhiêu?', scope, user)
    print('[Q1] Product Price:', str(ans1.get('reply'))[:120], '...')
    print('     Citations:', ans1.get('citations'))

    # 2. Document vault
    ans2 = await ops_qa.answer_ops_qa('Có văn bản nào sắp hết hạn không?', scope, user)
    print('[Q2] Doc Vault:', str(ans2.get('reply'))[:120], '...')
    print('     Citations:', ans2.get('citations'))

    # 3. GHN tracking
    ans3 = await ops_qa.answer_ops_qa('Kiểm tra mã vận đơn GHNMOCK-HCM-001', scope, user)
    print('[Q3] GHN Tracking:', str(ans3.get('reply'))[:120], '...')
    print('     Citations:', ans3.get('citations'))

    # 4. Plugin tool execution
    p_out = await route['ops_catalog_query']['call']({'keyword': 'tin học'})
    print('[Plugin tool] ops_catalog_query:\n', p_out[:140], '...')

asyncio.run(run())
'''

sftp = ssh.open_sftp()
with sftp.file("/root/Auto_social/test_vps_ops_qa.py", "w") as f:
    f.write(test_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("cd /root/Auto_social && /root/Auto_social/.venv/bin/python -u test_vps_ops_qa.py")
print("=== VPS OUTPUT ===")
for line in iter(stdout.readline, ""):
    print(line, end="", flush=True)

err = stderr.read().decode("utf-8", errors="replace")
if err:
    print("=== VPS ERRORS ===")
    print(err)

ssh.close()

