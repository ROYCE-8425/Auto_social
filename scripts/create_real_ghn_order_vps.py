import os
import paramiko

VPS_HOST = os.getenv("SEOTRUM_VPS_HOST")
VPS_PORT = int(os.getenv("SEOTRUM_VPS_PORT", "22"))
VPS_USER = os.getenv("SEOTRUM_VPS_USER", "root")
VPS_PASS = os.getenv("SEOTRUM_VPS_PASSWORD")

if not VPS_HOST or not VPS_PASS:
    raise SystemExit("Set SEOTRUM_VPS_HOST and SEOTRUM_VPS_PASSWORD before running this script.")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

remote_script = """
import sys
sys.path.insert(0, 'server')
import ops_order_store
import ops_orders

order = ops_order_store.create_order(
    customer_name='GHN Sandbox Customer',
    customer_phone='0900000000',
    shipping_address='Demo shipping address',
    items=[{
        'name': 'Sandbox product',
        'sku': 'SKU-SANDBOX-01',
        'quantity': 1,
        'price': 100000
    }],
    status='confirmed',
    source='ghn_real_test'
)
print('ORDER_ID:' + order['id'])

res = ops_orders.create_shipment_for_order(order['id'], provider_id='ghn', actor='ops_admin')
if res.get('ok'):
    ship = res['shipment']
    print('SUCCESS:' + ship.get('tracking_code'))
    print('FEE:' + str(ship.get('fee')))
    print('STATUS:' + str(ship.get('status')))
else:
    print('ERROR:' + str(res.get('error')))
"""

sftp = ssh.open_sftp()
try:
    with sftp.file("/root/Auto_social/run_ghn_create.py", "w") as f:
        f.write(remote_script)
finally:
    sftp.close()

try:
    stdin, stdout, stderr = ssh.exec_command("cd /root/Auto_social && /root/Auto_social/.venv/bin/python run_ghn_create.py")
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    print("OUT:\n" + out)
    if err:
        print("ERR:\n" + err)
finally:
    ssh.exec_command("rm -f /root/Auto_social/run_ghn_create.py")
    ssh.close()
