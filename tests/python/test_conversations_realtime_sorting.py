from pathlib import Path
from server import fanpage_care_store as store

def test_conversations_sorting_and_unreplied(tmp_path: Path):
    db_path = tmp_path / "test_care.db"
    store.init_db(db_path)

    # 1. Customer A sends message at t=100
    store.update_messaging_window(
        page_id="page_1",
        psid="psid_A",
        is_user=True,
        user_ts=100.0,
        db_path=db_path,
    )
    store.record_event(
        {
            "page_id": "page_1",
            "object_id": "msg_A_1",
            "thread_id": "psid_A",
            "from_id": "psid_A",
            "from_name": "Customer A",
            "kind": "message",
            "platform": "messenger",
            "body": "Alo shop ơi?",
            "created_ts": 100.0,
        },
        db_path=db_path,
    )

    convs = store.get_recent_conversations(page_id="page_1", db_path=db_path)
    assert len(convs) == 1
    assert convs[0]["psid"] == "psid_A"
    assert convs[0]["is_unreplied"] is True
    assert convs[0]["last_sender"] == "customer"
    assert convs[0]["latest_activity_ts"] == 100.0
    assert convs[0]["waiting_since"] == 100.0
    assert convs[0]["customer_name"] == "Customer A"

    # 2. Customer B sends message at t=150
    store.update_messaging_window(
        page_id="page_1",
        psid="psid_B",
        is_user=True,
        user_ts=150.0,
        db_path=db_path,
    )
    store.record_event(
        {
            "page_id": "page_1",
            "object_id": "msg_B_1",
            "thread_id": "psid_B",
            "from_id": "psid_B",
            "from_name": "Customer B",
            "kind": "message",
            "platform": "messenger",
            "body": "Bao nhiêu tiền khoá học?",
            "created_ts": 150.0,
        },
        db_path=db_path,
    )

    convs = store.get_recent_conversations(page_id="page_1", db_path=db_path)
    assert len(convs) == 2
    # B was active at 150 > A's 100, so B must be index 0
    assert convs[0]["psid"] == "psid_B"
    assert convs[0]["is_unreplied"] is True
    assert convs[1]["psid"] == "psid_A"
    assert convs[1]["is_unreplied"] is True

    # 3. Javis or staff responds to Customer A at t=200
    store.update_messaging_window(
        page_id="page_1",
        psid="psid_A",
        is_user=False,
        page_ts=200.0,
        db_path=db_path,
    )
    store.record_event(
        {
            "page_id": "page_1",
            "object_id": "echo_A_1",
            "thread_id": "psid_A",
            "from_id": "page_1",
            "from_name": "Nhân viên Fanpage",
            "kind": "echo",
            "platform": "messenger",
            "body": "Dạ chào bạn, Javis hỗ trợ bạn nhé!",
            "created_ts": 200.0,
        },
        db_path=db_path,
    )

    convs = store.get_recent_conversations(page_id="page_1", db_path=db_path)
    # A had response at 200 > B's 150 -> A floats to top (index 0)
    assert convs[0]["psid"] == "psid_A"
    assert convs[0]["is_unreplied"] is False
    assert convs[0]["last_sender"] == "page"
    assert convs[0]["latest_activity_ts"] == 200.0
    assert convs[0]["waiting_since"] in (0.0, None)

    # B is at index 1 and still unreplied
    assert convs[1]["psid"] == "psid_B"
    assert convs[1]["is_unreplied"] is True
    assert convs[1]["last_sender"] == "customer"
