"""Knowledge base and document API tests."""

import uuid
from pathlib import Path

import pytest

from fastapi.testclient import TestClient

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures"


class TestKnowledgeBase:
    """Knowledge base CRUD tests."""

    def test_kb_crud(self, client: TestClient, auth_headers: dict) -> None:
        kb_name = f"phase12-kb-{uuid.uuid4().hex[:8]}"
        create_resp = client.post(
            "/api/knowledge-bases",
            json={"name": kb_name, "description": "for phase 1.2 tests"},
            headers=auth_headers,
        )
        assert create_resp.status_code == 200
        create_data = create_resp.json()
        assert create_data["code"] == 0
        kb_id = create_data["data"]["id"]

        list_resp = client.get("/api/knowledge-bases", headers=auth_headers)
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["code"] == 0
        assert any(item["id"] == kb_id for item in list_data["data"])

        update_resp = client.put(
            f"/api/knowledge-bases/{kb_id}",
            json={"description": "updated"},
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        update_data = update_resp.json()
        assert update_data["code"] == 0
        assert update_data["data"]["description"] == "updated"

        delete_resp = client.delete(f"/api/knowledge-bases/{kb_id}", headers=auth_headers)
        assert delete_resp.status_code == 200
        delete_data = delete_resp.json()
        assert delete_data["code"] == 0

    def test_kb_unauthorized(self, client: TestClient) -> None:
        """Test that knowledge base APIs require authentication."""
        resp = client.get("/api/knowledge-bases")
        assert resp.status_code == 401


class TestDocument:
    """Document upload tests."""

    def test_upload_txt_and_versioning(self, client: TestClient, auth_headers: dict) -> None:
        kb_name = f"phase12-doc-kb-{uuid.uuid4().hex[:8]}"
        kb_resp = client.post("/api/knowledge-bases", json={"name": kb_name}, headers=auth_headers)
        assert kb_resp.status_code == 200
        kb_data = kb_resp.json()
        assert kb_data["code"] == 0
        kb_id = kb_data["data"]["id"]

        upload_resp_1 = client.post(
            f"/api/knowledge-bases/{kb_id}/documents",
            files={"file": ("sample.txt", b"hello world", "text/plain")},
            headers=auth_headers,
        )
        assert upload_resp_1.status_code == 200
        doc_data_1 = upload_resp_1.json()
        assert doc_data_1["code"] == 0
        assert doc_data_1["data"]["version"] == 1
        assert doc_data_1["data"]["status"] in {"parsed", "vectorized"}

        upload_resp_2 = client.post(
            f"/api/knowledge-bases/{kb_id}/documents",
            files={"file": ("sample.txt", b"hello world v2", "text/plain")},
            headers=auth_headers,
        )
        assert upload_resp_2.status_code == 200
        doc_data_2 = upload_resp_2.json()
        assert doc_data_2["code"] == 0
        assert doc_data_2["data"]["version"] == 2
        assert doc_data_2["data"]["is_current"] is True

    def test_batch_upload(self, client: TestClient, auth_headers: dict) -> None:
        kb_name = f"phase12-batch-kb-{uuid.uuid4().hex[:8]}"
        kb_resp = client.post("/api/knowledge-bases", json={"name": kb_name}, headers=auth_headers)
        assert kb_resp.status_code == 200
        kb_data = kb_resp.json()
        assert kb_data["code"] == 0
        kb_id = kb_data["data"]["id"]

        resp = client.post(
            f"/api/knowledge-bases/{kb_id}/documents/batch",
            files=[
                ("files", ("a.txt", b"hello a", "text/plain")),
                ("files", ("b.md", b"# title", "text/markdown")),
            ],
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["total"] == 2
        assert data["data"]["success_count"] == 2
        assert data["data"]["failed_count"] == 0

    @pytest.mark.parametrize(
        "filename,mime",
        [
            ("test_chinese.txt", "text/plain"),
            ("test_english.txt", "text/plain"),
            ("test_mixed.md", "text/markdown"),
        ],
    )
    def test_upload_txt_md_formats(
        self, client: TestClient, auth_headers: dict, filename: str, mime: str
    ) -> None:
        path = FIXTURES_DIR / filename
        if not path.exists():
            pytest.skip(f"Fixture {filename} not found")
        content = path.read_bytes()
        kb_name = f"phase12-{uuid.uuid4().hex[:8]}"
        kb_resp = client.post("/api/knowledge-bases", json={"name": kb_name}, headers=auth_headers)
        assert kb_resp.status_code == 200
        kb_id = kb_resp.json()["data"]["id"]
        resp = client.post(
            f"/api/knowledge-bases/{kb_id}/documents",
            files={"file": (filename, content, mime)},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["status"] in {"parsed", "vectorized"}

    @pytest.mark.parametrize(
        "filename,mime",
        [
            ("test_normal.pdf", "application/pdf"),
            ("test_normal.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("test_normal.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("test_normal.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
        ],
    )
    def test_upload_office_pdf_formats(
        self, client: TestClient, auth_headers: dict, filename: str, mime: str
    ) -> None:
        path = FIXTURES_DIR / filename
        if not path.exists():
            pytest.skip(f"Fixture {filename} not found")
        content = path.read_bytes()
        kb_name = f"phase12-{uuid.uuid4().hex[:8]}"
        kb_resp = client.post("/api/knowledge-bases", json={"name": kb_name}, headers=auth_headers)
        assert kb_resp.status_code == 200
        kb_id = kb_resp.json()["data"]["id"]
        resp = client.post(
            f"/api/knowledge-bases/{kb_id}/documents",
            files={"file": (filename, content, mime)},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["status"] in {"parsed", "vectorized", "parser_not_implemented"}

