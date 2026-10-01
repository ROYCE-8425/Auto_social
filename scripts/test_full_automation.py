import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('server'))

import fanpage_care_policy as policy
import fanpage_care_classify as classify
import ops_automation_engine as auto_eng
import ops_order_store

print('=== 1. KIỂM TRA QUYỀN HÀNH ĐỘNG KHI BẬT FULL TỰ ĐỘNG ===')
cases = [
    ('faq_reply', 'faq'),
    ('lead_thanks', 'lead'),
    ('comment_hide', 'spam'),
    ('comment_hide', 'toxic'),
    ('comment_like', 'khen'),
    ('llm_reply', 'ky_thuat'),
    ('messenger_reply', 'sales_automation'),
]
for act, cls in cases:
    allowed, reason = policy.policy_allows(act, mode='full', class_name=cls, like_khen=True)
    status_icon = '✅' if allowed else '❌'
    print(f'{status_icon} Hành động: {act:<18} | Nhóm: {cls:<16} -> Được gửi: {str(allowed):<5} (Lý do: {reason})')

print('\n=== 2. KIỂM TRA NHẬN DIỆN Ý ĐỊNH & PHÂN LOẠI YÊU CẦU ===')
sample_texts = [
    'Khóa học MOS học phí bao nhiêu vậy shop?',
    'Bàn phím cơ silent còn hàng không em?',
    'Cho mình đặt 1 cái bàn phím cơ silent về 72 Thành Thái Q3, SĐT 0989819057',
    'Shop có cơ sở ở đâu vậy?',
    'Khóa học này dạy online hay offline, thời gian học thế nào?',
    'Cho vay tiền online không thế chấp lãi suất 0% inbox zalo...'
]
for txt in sample_texts:
    intent = auto_eng.detect_intent(txt)
    cls_res = classify.classify_comment(txt)
    print(f'💬 Khách: "{txt}"')
    c_name = str(cls_res.get("class") or "unknown")
    print(f'   👉 Ý định: {intent:<15} | Care: {c_name:<10} (Độ tin cậy: {cls_res.get("confidence")})')

print('\n=== 3. CHẠY THỬ QUY TRÌNH TỰ ĐỘNG CHỐT ĐƠN (EVALUATE & RUN) ===')
test_msgs = [
    {"sender": "customer", "body": "Mình muốn mua 1 bàn phím cơ silent office về 72 Thành Thái, P. Võ Thị Sáu, Q.3, SĐT 0989819057"}
]
res = auto_eng.evaluate_and_run(
    thread_id="test_thread_full_auto",
    page_id="default_page",
    messages=test_msgs,
    customer_info={"name": "Trần Minh Tuấn", "from_id": "cust_123"}
)
print("Kết quả đánh giá Case bán hàng:")
print(f" - Cases đã đánh giá: {res.get('cases_evaluated')}")
print(f" - Cases đã thực thi: {res.get('cases_executed')}")
if res.get('outbox_messages'):
    print(f" - Tin nhắn Javis chuẩn bị gửi ra:")
    for out in res.get('outbox_messages'):
        print(f"   💬 \"{out.get('body')}\"")
