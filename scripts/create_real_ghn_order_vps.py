import sys
import json
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('180.93.37.8', port=22, username='root', password='wh8bCLxIAitPOfIB', timeout=15)

remote_script = """
import sys
sys.path.insert(0, 'server')
import ops_order_store
import ops_orders
import json

order = ops_order_store.create_order(
    customer_name='Trần Minh Tuấn (Test Webhook GHN)',
    customer_phone='0989819057',
    shipping_address='72 Thành Thái, Phường Võ Thị Sáu, Quận 3, TP.HCM',
    items=[{
        'name': 'Bàn phím cơ Silent Office Bluetooth',
        'sku': 'SKU-KEY-04',
        'quantity': 1,
        'price': 850000
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
with sftp.file('/root/Auto_social/run_ghn_create.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('cd /root/Auto_social && /root/Auto_social/.venv/bin/python run_ghn_create.py')
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUT:\n" + out)
if err:
    print("ERR:\n" + err)

ssh.exec_command('rm -f /root/Auto_social/run_ghn_create.py')
ssh.close()
