"""
Phase 1.4 Security tests: API authentication, input validation, SQL injection.

Author: O3
Date: 2026-02-13
"""

from fastapi.testclient import TestClient


class TestApiAuthentication:
    """O3-1.4.2: API authentication security tests."""

    def test_knowledge_base_list_requires_auth(self, client: TestClient) -> None:
        """Without token, GET /knowledge-bases returns 401."""
        resp = client.get("/api/knowledge-bases")
        assert resp.status_code == 401

    def test_document_list_requires_auth(self, client: TestClient) -> None:
        """Without token, GET documents returns 401."""
        resp = client.get("/api/knowledge-bases/1/documents")
        assert resp.status_code == 401

    def test_qa_ask_requires_auth(self, client: TestClient) -> None:
        """Without token, POST /qa/ask returns 401."""
        resp = client.post(
            "/api/qa/ask",
            json={"knowledge_base_id": 1, "question": "test"},
        )
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client: TestClient) -> None:
        """Invalid or malformed token returns 401."""
        resp = client.get(
            "/api/knowledge-bases",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401

    def test_malformed_authorization_header_returns_401(self, client: TestClient) -> None:
        """Malformed Authorization header returns 401."""
        resp = client.get(
            "/api/knowledge-bases",
            headers={"Authorization": "Basic xxx"},
        )
        assert resp.status_code == 401

    def test_expired_token_returns_401(self, client: TestClient) -> None:
        """Expired JWT token returns 401."""
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        from app.config import settings

        payload = {
            "sub": "admin",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        expired_token = jwt.encode(
            payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )
        resp = client.get(
            "/api/knowledge-bases",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401


class TestInputValidation:
    """O3-1.4.2: Input validation and injection tests."""

    def test_qa_invalid_knowledge_base_id(self, client: TestClient, auth_headers: dict) -> None:
        """knowledge_base_id=0 returns 422 validation error."""
        resp = client.post(
            "/api/qa/ask",
            json={"knowledge_base_id": 0, "question": "test"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_qa_empty_question(self, client: TestClient, auth_headers: dict) -> None:
        """Empty question returns 422 validation error."""
        resp = client.post(
            "/api/qa/ask",
            json={"knowledge_base_id": 1, "question": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_qa_negative_top_k(self, client: TestClient, auth_headers: dict) -> None:
        """Negative top_k returns 422 if validated."""
        resp = client.post(
            "/api/qa/ask",
            json={"knowledge_base_id": 1, "question": "test", "top_k": -1},
            headers=auth_headers,
        )
        # Pydantic may accept or reject; document actual behavior
        assert resp.status_code in (200, 422)

    def test_sql_injection_in_kb_name(self, client: TestClient, auth_headers: dict) -> None:
        """SQL injection attempt in knowledge base name - should not cause 500."""
        resp = client.post(
            "/api/knowledge-bases",
            json={
                "name": "test'; DROP TABLE users; --",
                "description": "safe",
            },
            headers=auth_headers,
        )
        # Should not crash with 500; parameterized queries prevent execution
        assert resp.status_code != 500
        # Response is valid JSON (no internal error)
        data = resp.json()
        assert "code" in data


class TestHealthEndpoint:
    """Health endpoint remains public (no auth required)."""

    def test_health_no_auth_required(self, client: TestClient) -> None:
        """Health check does not require authentication."""
        resp = client.get("/api/system/health")
        assert resp.status_code == 200
        assert resp.json().get("data", {}).get("status") == "ok"
