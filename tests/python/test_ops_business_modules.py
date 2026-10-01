# -*- coding: utf-8 -*-
"""Test Suite for Javis Business Operational Modules (Phase 1).

Kiểm thử toàn diện:
- Khởi tạo Database và Seeding 11 phân hệ
- Đọc danh sách phân hệ kèm trạng thái động
- CRUD hồ sơ Tuyển dụng (Recruitment), Hợp đồng (Contract), SOP
- Quy trình chuyển đổi trạng thái (Status workflow)
- Nhật ký hoạt động & vết kiểm toán (Activity Log / Audit Trail)
- Thêm bình luận (Comments) và tệp đính kèm (Attachments)
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Đảm bảo import được server
SERVER_DIR = Path(__file__).resolve().parents[2] / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

import ops_business_store


class TestOpsBusinessModules(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_business_modules.sqlite3"
        ops_business_store.init_db(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_init_and_seed_modules(self):
        """Kiểm tra khởi tạo thành công 11 phân hệ mặc định."""
        modules = ops_business_store.list_modules(db_path=self.db_path)
        self.assertEqual(len(modules), 11)
        codes = [m["code"] for m in modules]
        self.assertIn("recruitment", codes)
        self.assertIn("contract", codes)
        self.assertIn("sop", codes)
        self.assertIn("crm_lead", codes)
        self.assertIn("orders", codes)
        self.assertIn("kanban", codes)
        self.assertIn("kpi", codes)
        self.assertIn("projects", codes)
        self.assertIn("inbox", codes)
        self.assertIn("finance", codes)
        self.assertIn("calendar", codes)

    def test_02_get_module_with_alias(self):
        """Kiểm tra đọc chi tiết phân hệ với alias ID từ giao diện Hub."""
        mod = ops_business_store.get_module("people_recruitment", db_path=self.db_path)
        self.assertIsNotNone(mod)
        self.assertEqual(mod["code"], "recruitment")
        self.assertEqual(mod["computed_status"], "connected")
        self.assertEqual(mod["record_count"], 0)
        self.assertTrue(len(mod["workflows"]) >= 4)

    def test_03_recruitment_flow(self):
        """Kiểm thử chu trình Tuyển dụng: tạo ứng viên -> phỏng vấn -> đạt tuyển dụng."""
        # 1. Tạo hồ sơ ứng viên
        rec = ops_business_store.create_record(
            module_code="recruitment",
            title="Nguyễn Văn A - Lập trình viên Fullstack",
            description="Ứng viên 3 năm kinh nghiệm React + Python",
            status="new",
            priority="high",
            owner_id="HR_Mai",
            payload={
                "candidate_name": "Nguyễn Văn A",
                "position": "Lập trình viên Fullstack",
                "phone": "0987654321",
                "email": "nguyenvana@example.com",
                "cv_link": "https://drive.google.com/cv/nguyenvana.pdf",
                "rating": 5,
            },
            actor_id="HR_Mai",
            db_path=self.db_path,
        )
        self.assertTrue(rec["id"].startswith("rec_"))
        self.assertEqual(rec["status"], "new")
        self.assertEqual(rec["payload"]["phone"], "0987654321")

        # Kiểm tra activity log tạo hồ sơ
        self.assertEqual(len(rec["activities"]), 1)
        self.assertEqual(rec["activities"][0]["action"], "created")

        # 2. Chuyển trạng thái sang 'interviewing'
        rec_id = rec["id"]
        updated = ops_business_store.update_record(
            rec_id,
            {"status": "interviewing", "due_at": "2026-10-05T09:00:00"},
            actor_id="HR_Mai",
            db_path=self.db_path,
        )
        self.assertEqual(updated["status"], "interviewing")
        self.assertEqual(len(updated["activities"]), 2)
        latest_act = updated["activities"][0]
        self.assertEqual(latest_act["action"], "status_changed")
        self.assertEqual(latest_act["before"]["status"], "new")
        self.assertEqual(latest_act["after"]["status"], "interviewing")

        # 3. Thêm bình luận phỏng vấn
        cmt = ops_business_store.add_comment(
            rec_id,
            content="Phỏng vấn chuyên môn đạt 9/10, thái độ rất chủ động. Đề xuất pass vòng cuối.",
            actor_id="Tech_Lead_Nam",
            db_path=self.db_path,
        )
        self.assertIsNotNone(cmt)

        # 4. Thêm file đính kèm bài test
        att = ops_business_store.add_attachment(
            rec_id,
            file_name="Coding_Test_Result.pdf",
            file_url="https://drive.google.com/test_result.pdf",
            file_type="pdf",
            actor_id="Tech_Lead_Nam",
            db_path=self.db_path,
        )
        self.assertIsNotNone(att)

        # 5. Chuyển sang 'passed'
        passed_rec = ops_business_store.update_record(
            rec_id,
            {"status": "passed"},
            actor_id="HR_Mai",
            db_path=self.db_path,
        )
        self.assertEqual(passed_rec["status"], "passed")
        self.assertEqual(len(passed_rec["comments"]), 1)
        self.assertEqual(len(passed_rec["attachments"]), 1)

        # 6. Kiểm tra lại module detail thấy record_count = 1 và status = has_data
        mod = ops_business_store.get_module("recruitment", db_path=self.db_path)
        self.assertEqual(mod["record_count"], 1)
        self.assertEqual(mod["computed_status"], "has_data")
        self.assertEqual(mod["status_counts"]["passed"], 1)

    def test_04_contract_flow(self):
        """Kiểm thử chu trình Hợp đồng: tạo hợp đồng -> ký duyệt -> tra cứu."""
        rec = ops_business_store.create_record(
            module_code="people_contract",
            title="Hợp đồng Cung cấp Giải pháp Javis OS - Cty Sao Việt",
            status="draft",
            priority="urgent",
            owner_id="Sale_Tuan",
            payload={
                "contract_number": "HD-2026-SV-008",
                "party_a": "Công ty TNHH Đầu tư & Phát triển Sao Việt",
                "party_b": "Hộ kinh doanh Javis Solutions",
                "contract_value": 150000000,
                "contract_type": "Triển khai phần mềm",
            },
            actor_id="Sale_Tuan",
            db_path=self.db_path,
        )
        self.assertEqual(rec["status"], "draft")
        self.assertEqual(rec["payload"]["contract_value"], 150000000)

        # Cập nhật ký hợp đồng
        updated = ops_business_store.update_record(
            rec["id"],
            {"status": "signed", "payload": {"signer": "Giám đốc Nguyễn Hữu Toàn"}},
            actor_id="Director_Toan",
            db_path=self.db_path,
        )
        self.assertEqual(updated["status"], "signed")
        self.assertEqual(updated["payload"]["signer"], "Giám đốc Nguyễn Hữu Toàn")

    def test_05_sop_flow(self):
        """Kiểm thử chu trình SOP & Quy trình nội bộ."""
        rec = ops_business_store.create_record(
            module_code="sop",
            title="Quy trình Tiếp nhận & Phục hồi Lead dừng tương tác",
            status="draft",
            priority="normal",
            owner_id="Ops_Manager",
            payload={
                "sop_code": "SOP-OPS-03",
                "version": "v1.2",
                "department": "Chăm sóc khách hàng & Vận hành",
                "author": "Trần Thị Bích",
                "approver": "Nguyễn Hữu Toàn",
                "content_markdown": "# Quy trình cứu lead\n1. Quét tệp 3d\n2. Gợi ý tin nhắn AI\n3. Handoff CSKH",
            },
            actor_id="Ops_Manager",
            db_path=self.db_path,
        )
        self.assertEqual(rec["status"], "draft")

        # Ban hành SOP
        published = ops_business_store.update_record(
            rec["id"],
            {"status": "published"},
            actor_id="Director_Toan",
            db_path=self.db_path,
        )
        self.assertEqual(published["status"], "published")

        # Tìm kiếm theo từ khóa
        list_res = ops_business_store.list_records(
            module_code="sop",
            search="cứu lead",
            db_path=self.db_path,
        )
        self.assertEqual(list_res["total"], 1)
        self.assertEqual(list_res["records"][0]["id"], rec["id"])

    def test_06_delete_record(self):
        """Kiểm thử xóa hồ sơ."""
        rec = ops_business_store.create_record(
            module_code="calendar",
            title="Lịch họp giao ban sáng thứ 2",
            status="scheduled",
            db_path=self.db_path,
        )
        rec_id = rec["id"]
        deleted = ops_business_store.delete_record(rec_id, db_path=self.db_path)
        self.assertTrue(deleted)
        self.assertIsNone(ops_business_store.get_record(rec_id, db_path=self.db_path))

    def test_07_fastapi_endpoints(self):
        """Kiểm thử qua HTTP TestClient cho các API /api/modules và /ops/modules."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import ops_business_modules

        old_db = ops_business_store.DEFAULT_DB_PATH
        ops_business_store.DEFAULT_DB_PATH = self.db_path
        try:
            app = FastAPI()
            app.include_router(ops_business_modules.router)
            client = TestClient(app)

            # 1. GET /api/modules
            res = client.get("/api/modules")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["ok"])
            self.assertEqual(len(data["modules"]), 11)

            # 2. POST /api/modules/recruitment/records
            create_res = client.post(
                "/api/modules/recruitment/records",
                json={
                    "title": "Trần Thị C - Sale B2B",
                    "status": "new",
                    "priority": "normal",
                    "payload": {"phone": "0912345678", "position": "Sale B2B"},
                },
            )
            self.assertEqual(create_res.status_code, 200)
            rec = create_res.json()["record"]
            rec_id = rec["id"]

            # 3. GET /api/modules/recruitment/records/{id}
            get_res = client.get(f"/api/modules/recruitment/records/{rec_id}")
            self.assertEqual(get_res.status_code, 200)
            self.assertEqual(get_res.json()["record"]["title"], "Trần Thị C - Sale B2B")

            # 4. POST comment
            cmt_res = client.post(
                f"/api/modules/recruitment/records/{rec_id}/comments",
                json={"content": "Đã hẹn lịch phỏng vấn ngày mai"},
            )
            self.assertEqual(cmt_res.status_code, 200)
            self.assertTrue(cmt_res.json()["ok"])

            # 5. POST attachment
            att_res = client.post(
                f"/api/modules/recruitment/records/{rec_id}/attachments",
                json={"file_name": "CV.pdf", "file_url": "https://example.com/cv.pdf"},
            )
            self.assertEqual(att_res.status_code, 200)
            self.assertTrue(att_res.json()["ok"])

            # 6. PATCH /api/modules/recruitment/records/{id}
            patch_res = client.patch(
                f"/api/modules/recruitment/records/{rec_id}",
                json={"status": "interviewing"},
            )
            self.assertEqual(patch_res.status_code, 200)
            self.assertEqual(patch_res.json()["record"]["status"], "interviewing")

            # 7. DELETE /api/modules/recruitment/records/{id}
            del_res = client.delete(f"/api/modules/recruitment/records/{rec_id}")
            self.assertEqual(del_res.status_code, 200)
            self.assertTrue(del_res.json()["deleted"])

            # 8. GET /ops/hub/summary (Executive Command Center Aggregator)
            summary_res = client.get("/ops/hub/summary")
            self.assertEqual(summary_res.status_code, 200)
            summary_data = summary_res.json()
            self.assertTrue(summary_data["ok"])
            self.assertIn("executive_summary", summary_data)
            self.assertIn("need_action_today", summary_data["executive_summary"])
            self.assertIn("modules", summary_data)
            self.assertGreaterEqual(len(summary_data["modules"]), 11)

            # Check real module vs needs_config module
            mods_by_code = {m["code"]: m for m in summary_data["modules"]}
            self.assertTrue(mods_by_code["orders"]["has_real_source"])
            self.assertTrue(mods_by_code["crm_lead"]["has_real_source"])
            self.assertIn("/ops/orders", mods_by_code["orders"]["primary_action"]["path"])
            self.assertFalse(mods_by_code["recruitment"]["has_real_source"])
            self.assertEqual(mods_by_code["recruitment"]["status"], "needs_config")
        finally:
            ops_business_store.DEFAULT_DB_PATH = old_db


if __name__ == "__main__":
    unittest.main()

