# -*- coding: utf-8 -*-
import json
import tempfile
import time
from pathlib import Path
import pytest

from _paths import ROOT, SERVER
import config
import fanpage_care_store as store
import ops_briefing
import ops_attribution
import tiktok_service


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Thiết lập SQLite DB và vault tạm biệt lập cho từng test case."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        p = Path(td)
        state_dir = p / "state"
        state_dir.mkdir(parents=True)
        vault_dir = p / "vault"
        vault_dir.mkdir(parents=True)
        (vault_dir / "Javis").mkdir(parents=True)

        db_path = state_dir / "test_fanpage_care.sqlite3"
        monkeypatch.setattr(config, "STATE_DIR", state_dir)
        monkeypatch.setattr(store, "DEFAULT_DB_PATH", db_path)
        monkeypatch.setattr(tiktok_service, "_get_vault_root", lambda *args, **kwargs: vault_dir)

        store.init_db(db_path)
        yield {
            "state_dir": state_dir,
            "vault_dir": vault_dir,
            "db_path": db_path,
        }


def test_empty_store_does_not_return_mock_customers():
    """a) Khi store rỗng: Không trả tên khách mẫu, lead_1, hay bài viết giả lập."""
    briefing = ops_briefing.get_daily_briefing()

    assert briefing["ok"] is True
    # Hot leads phải rỗng, không được fallback sang lead_1 hay khách hàng mẫu
    assert briefing["hot_leads"] == []
    assert briefing["urgent_hot_leads"] == []
    assert briefing["briefing"]["urgent_hot_leads"] == []

    # Kiểm tra không có bất kỳ chuỗi dữ liệu giả lập nào
    dumped = json.dumps(briefing, ensure_ascii=False)
    assert "lead_1" not in dumped
    assert "Khách hàng Fanpage" not in dumped
    assert "Nguyễn Thị Hoa" not in dumped
    assert "Trần Như Ý" not in dumped
    assert "Game Steam Offline" not in dumped

    # top_post phải là None khi chưa có bài đăng thật
    assert briefing["top_post"] is None
    assert briefing["briefing"]["top_converting_post"] is None


def test_real_stats_reflected_in_kpis():
    """b) Số liệu tương tác, nháp và khách hàng thật từ SQLite phản ánh chính xác vào KPIs."""
    now = time.time()

    # Thêm 2 sự kiện tương tác thật
    ev1_id, _ = store.record_event({
        "page_id": "page_999",
        "object_id": "cmt_001",
        "comment_id": "cmt_001",
        "from_id": "user_real_01",
        "from_name": "Phạm Minh Thật",
        "body": "Báo giá cho mình sản phẩm này với, SĐT 0912345678",
        "created_ts": now - 100,
        "ingested_ts": now - 100,
        "class": "lead",
        "kind": "comment",
    })
    ev2_id, _ = store.record_event({
        "page_id": "page_999",
        "object_id": "cmt_002",
        "comment_id": "cmt_002",
        "from_id": "user_real_02",
        "from_name": "Nguyễn Hoàng Minh",
        "body": "Có giao hàng tận nơi không shop?",
        "created_ts": now - 50,
        "ingested_ts": now - 50,
        "class": "hoi_mua",
        "kind": "comment",
    })

    # Thêm 1 bản nháp AI đang chờ duyệt
    store.create_draft(
        event_id=ev1_id,
        page_id="page_999",
        target_id="cmt_001",
        proposed="Dạ chào bạn Minh Thật, shop đã inbox giá ưu đãi rồi ạ!",
        class_name="lead",
    )

    # Tạo khách hàng thật vào CRM
    cust, _ = store.get_or_create_customer(
        name="Phạm Minh Thật",
        phones=["0912345678"],
        page_id="page_999",
        from_id="user_real_01",
        tag="lead",
    )
    crm_id = cust["crm_id"]

    briefing = ops_briefing.get_daily_briefing()

    assert briefing["ok"] is True
    kpis = briefing["kpis"]

    # KPIs phải phản ánh số liệu thực tế
    assert kpis["inbox_yesterday"] >= 2
    assert kpis["pending_drafts"] == 1

    # Hot leads phải trả đúng khách hàng thật vừa thêm
    hot_leads = briefing["hot_leads"]
    assert len(hot_leads) >= 1
    real_lead = next((l for l in hot_leads if l["name"] == "Phạm Minh Thật"), None)
    assert real_lead is not None
    assert real_lead["phone"] == "0912345678"
    assert real_lead["score"] >= 70  # Có SĐT và hỏi giá -> điểm cao theo lead_scoring
    assert real_lead["id"] == crm_id


def test_empty_attribution_does_not_contain_post_101():
    """c) Attribution và Competitor Radar khi chưa có dữ liệu: Không chứa post_101 hay đối thủ bịa."""
    attr = ops_attribution.get_content_attribution_matrix()

    assert attr["status"] == "ok"
    assert attr["data_source"] == "empty"
    assert attr["items"] == []
    assert attr["total_revenue_vnd"] == 0
    assert attr["total_orders"] == 0

    # Kiểm tra không có post_101..post_105
    attr_dump = json.dumps(attr, ensure_ascii=False)
    assert "post_101" not in attr_dump
    assert "post_102" not in attr_dump
    assert "Phím tắt Excel" not in attr_dump

    # Competitor Radar phải trả trạng thái not_configured/disconnected
    radar = ops_attribution.get_competitor_radar()
    assert radar["status"] == "not_configured"
    assert radar["status_code"] == "disconnected"
    assert radar["competitors"] == []
    assert radar["competitors_monitored"] == []

    radar_dump = json.dumps(radar, ensure_ascii=False)
    assert "Trung tâm Tin học X" not in radar_dump
    assert "Học viện Kỹ năng Y" not in radar_dump
    assert "DoanhNghiepTech" not in radar_dump
