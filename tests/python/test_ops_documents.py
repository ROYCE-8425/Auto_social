# -*- coding: utf-8 -*-
"""Unit and integration tests for Company Document Vault (Kho Tài Liệu Doanh Nghiệp)."""
import io
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from _paths import ROOT, SERVER
import config
import ops_documents_store
import ops_documents
from main import app


@pytest.fixture(autouse=True)
def setup_documents_env(monkeypatch):
    """Thiết lập thư mục tạm và SQLite cho Document Vault."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        p = Path(td)
        state_dir = p / "state"
        state_dir.mkdir(parents=True)
        db_path = state_dir / "test_ops_documents.sqlite3"

        monkeypatch.setattr(config, "STATE_DIR", state_dir)
        monkeypatch.setattr(ops_documents_store, "DEFAULT_DB_PATH", db_path)

        ops_documents_store.init_db(db_path, seed_demo=True)

        # Mock authentication cho ops user trong TestClient
        import ops_rbac
        monkeypatch.setattr(
            ops_rbac,
            "get_current_ops_user",
            lambda request: {"username": "admin_test", "role": "owner", "name": "Giám Đốc Test"},
        )

        yield {
            "state_dir": state_dir,
            "db_path": db_path,
        }


def test_seed_documents_created():
    """1. Kiểm tra seed tài liệu: file thật được tạo trên đĩa và metadata được lưu trong SQLite."""
    res = ops_documents_store.list_documents()
    docs = res.get("documents", [])
    assert len(docs) >= 5

    # Kiểm tra các file vật lý thật tồn tại trên đĩa
    for d in docs:
        file_path = ops_documents_store.get_document_file_path(d["id"])
        assert file_path is not None, f"Không tìm thấy file vật lý cho doc {d['id']}"
        assert file_path.exists(), f"File vật lý không tồn tại: {file_path}"
        assert file_path.stat().st_size > 0


def test_document_stats_calculation():
    """2. Kiểm tra tổng hợp thống kê stats: chờ duyệt, sắp hết hạn, hợp đồng."""
    stats = ops_documents_store.get_stats()
    assert stats["total_documents"] >= 5
    assert "contract" in stats["by_category"]
    assert "sop" in stats["by_category"]
    assert stats["contracts_count"] >= 1
    assert stats["sop_count"] >= 1
    assert stats["expiring_soon"] >= 1


def test_document_versioning():
    """3. Kiểm tra nâng cấp phiên bản (Version History) và bảo toàn file cũ."""
    res = ops_documents_store.list_documents(category="sop")
    docs = res.get("documents", [])
    assert len(docs) > 0
    sop_doc = docs[0]
    original_version = sop_doc["version"]

    updated = ops_documents_store.add_version(
        doc_id=sop_doc["id"],
        new_version="v3.0",
        file_name="SOP_ban_moi.pdf",
        file_path="2026/sop/SOP_ban_moi.pdf",
        file_size=1024,
        change_note="Cập nhật quy trình mới 2026",
        actor_id="Trưởng phòng Vận hành",
    )

    assert updated is not None
    assert updated["version"] == "v3.0"
    assert len(updated.get("versions", [])) >= 2
    past_versions = [v["version"] for v in updated["versions"]]
    assert original_version in past_versions


def test_document_approval_and_signing():
    """4. Kiểm tra luồng phê duyệt và ký số hợp đồng."""
    res = ops_documents_store.list_documents()
    docs = res.get("documents", [])
    assert len(docs) > 0
    target = docs[0]

    # Duyệt tài liệu
    approved = ops_documents_store.approve_document(
        doc_id=target["id"],
        approved=True,
        note="Đã xem xét và đồng ý",
        actor_id="Ban Giám Đốc",
    )
    assert approved["approval_status"] == "approved"

    # Ký hợp đồng
    signed = ops_documents_store.sign_document(
        doc_id=target["id"],
        note="Ký điện tử xác thực",
        actor_id="Trần Như Ý",
    )
    assert signed["approval_status"] == "signed"


def test_api_list_and_stats():
    """5. Kiểm tra API GET /ops/documents và GET /ops/documents/stats."""
    client = TestClient(app, base_url="http://127.0.0.1")
    res = client.get("/ops/documents")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert len(data["documents"]) >= 5

    res_stats = client.get("/ops/documents/stats")
    assert res_stats.status_code == 200
    stats_data = res_stats.json()
    assert stats_data["ok"] is True
    assert stats_data["stats"]["total_documents"] >= 5


def test_ops_documents_requires_ops_session(monkeypatch):
    """API kho tài liệu không được public khi không có ops session."""
    import ops_rbac

    monkeypatch.setattr(ops_rbac, "get_current_ops_user", lambda request: None)
    client = TestClient(app, base_url="http://127.0.0.1")

    res = client.get("/ops/documents")
    assert res.status_code == 401
    assert res.json()["auth_required"] is True


def test_api_upload_multipart_document():
    """6. Kiểm tra API upload multipart file thật và lưu metadata."""
    client = TestClient(app, base_url="http://127.0.0.1")
    fake_file = io.BytesIO(b"%PDF-1.4 Mock Contract Content For Client ABC")
    files = {
        "file": ("HD-TEST-KHACH-HANG.pdf", fake_file, "application/pdf")
    }
    data = {
        "title": "Hợp đồng dịch vụ Khách hàng ABC",
        "category": "contract",
        "department": "kinh_doanh",
        "owner_id": "nv_sale_01",
        "version": "v1.0",
        "approval_status": "pending_approval",
        "permission_level": "confidential",
        "linked_entity_type": "customer",
        "linked_entity_id": "crm_khach_hang_abc",
        "linked_entity_name": "Khách hàng ABC",
    }

    res = client.post("/ops/documents/upload", files=files, data=data)
    assert res.status_code == 200
    resp_data = res.json()
    assert resp_data["ok"] is True
    doc = resp_data["document"]
    assert doc["title"] == "Hợp đồng dịch vụ Khách hàng ABC"
    assert doc["category"] == "contract"
    assert doc["linked_entity_id"] == "crm_khach_hang_abc"

    # Thử tải file thật đã upload
    file_res = client.get(f"/ops/documents/{doc['id']}/file")
    assert file_res.status_code == 200
    assert b"Mock Contract Content" in file_res.content


def test_upload_filename_is_sanitized_inside_vault():
    """Tên file upload có path separator phải được lưu an toàn trong Document Vault."""
    client = TestClient(app, base_url="http://127.0.0.1")
    files = {
        "file": ("..\\..\\hop dong/HD TEST.pdf", io.BytesIO(b"%PDF safe name"), "application/pdf")
    }
    data = {
        "title": "Hợp đồng tên file cần làm sạch",
        "category": "contract",
        "department": "phap_che",
    }

    res = client.post("/ops/documents/upload", files=files, data=data)
    assert res.status_code == 200
    doc = res.json()["document"]
    assert "/" not in doc["file_name"]
    assert "\\" not in doc["file_name"]

    stored_path = ops_documents_store.get_document_file_path(doc["id"])
    vault_root = ops_documents_store.get_base_storage_dir().resolve()
    assert stored_path is not None
    assert vault_root == stored_path or vault_root in stored_path.parents


def test_ops_hub_summary_includes_documents():
    """7. Kiểm tra OperationsHub summary kết nối trực tiếp với Document Vault."""
    client = TestClient(app, base_url="http://127.0.0.1")
    res = client.get("/ops/hub/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    modules = {m["code"]: m for m in data.get("modules", [])}

    # Module 'contracts' phải lấy data từ Document Vault
    assert "contracts" in modules
    contracts_mod = modules["contracts"]
    assert contracts_mod["has_real_source"] is True
    assert "Document Vault" in contracts_mod["data_source_label"]

    # Module 'sop' phải trỏ về Document Vault
    assert "sop" in modules
    sop_mod = modules["sop"]
    assert sop_mod["has_real_source"] is True
    assert sop_mod["primary_action"]["path"] == "/ops/documents"
