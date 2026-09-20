import base64
import tempfile
import unittest
from pathlib import Path

import app as caseflow


class FeatureClosureTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        caseflow.DATA_DIR = Path(self.temp_dir.name)
        caseflow.DB_PATH = caseflow.DATA_DIR / "caseflow.db"
        caseflow.init_db()
        self.client = caseflow.app.test_client()
        response = self.client.post(
            "/api/cases",
            json={"case_number": "TEST-001", "name": "功能闭环测试案件", "case_type": "合同纠纷"},
        )
        self.case_id = response.get_json()["id"]

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_work_record_crud_and_total(self):
        response = self.client.post(
            f"/api/cases/{self.case_id}/work-records",
            json={"work_date": "2026-09-20", "category": "起草", "content": "起草代理词", "hours": 2.5},
        )
        self.assertEqual(response.status_code, 201)
        record_id = response.get_json()["id"]

        payload = self.client.get(f"/api/cases/{self.case_id}/work-records").get_json()
        self.assertEqual(payload["total_hours"], 2.5)
        self.assertEqual(len(payload["records"]), 1)

        response = self.client.put(
            f"/api/cases/{self.case_id}/work-records/{record_id}",
            json={"work_date": "2026-09-21", "category": "调研", "content": "检索案例", "hours": 3},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(f"/api/cases/{self.case_id}/work-records").get_json()["total_hours"], 3)
        self.assertEqual(self.client.delete(f"/api/cases/{self.case_id}/work-records/{record_id}").status_code, 200)

    def test_template_crud_download_and_batch_delete(self):
        pdf = b"%PDF-1.4 caseflow test"
        response = self.client.post(
            "/api/templates",
            json={
                "name": "附件模板",
                "category": "合同",
                "content": "正文",
                "file_name": "sample.pdf",
                "file_mime": "application/pdf",
                "file_data": base64.b64encode(pdf).decode(),
            },
        )
        self.assertEqual(response.status_code, 201)
        template_id = response.get_json()["id"]
        self.assertEqual(self.client.get(f"/api/templates/{template_id}/download").data, pdf)

        text_id = self.client.post(
            "/api/templates", json={"name": "文本模板", "category": "备忘录", "content": "客户：{客户名称}"}
        ).get_json()["id"]
        response = self.client.post("/api/templates/batch-delete", json={"ids": [template_id, text_id]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["deleted"], 2)
        self.assertEqual(self.client.get("/api/templates").get_json(), [])


if __name__ == "__main__":
    unittest.main()
