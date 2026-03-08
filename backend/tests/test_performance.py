"""
Phase 1.4 Performance tests: API response time, basic latency.

Author: O3
Date: 2026-02-13
"""

import time

from fastapi.testclient import TestClient


class TestApiLatency:
    """O3-1.4.3: Basic API latency tests."""

    def test_health_endpoint_latency(self, client: TestClient) -> None:
        """Health endpoint responds within 1 second."""
        start = time.perf_counter()
        resp = client.get("/api/system/health")
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 1.0, f"Health check took {elapsed:.2f}s (> 1s)"

    def test_login_latency(self, client: TestClient) -> None:
        """Login API responds within 3 seconds."""
        start = time.perf_counter()
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "password123"},
        )
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 3.0, f"Login took {elapsed:.2f}s (> 3s)"

    def test_kb_list_latency(self, client: TestClient, auth_headers: dict) -> None:
        """Knowledge base list API responds within 2 seconds."""
        start = time.perf_counter()
        resp = client.get("/api/knowledge-bases", headers=auth_headers)
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 2.0, f"KB list took {elapsed:.2f}s (> 2s)"

    def test_qa_ask_latency_mocked(self, client: TestClient, auth_headers: dict, monkeypatch) -> None:
        """QA ask (mocked LLM) responds within 5 seconds."""
        def _fake_ask(*args, **kwargs):
            return (
                {"answer": "test", "citations": [], "retrieved_count": 0},
                None,
            )

        monkeypatch.setattr("app.api.qa.QaService.ask", _fake_ask)
        start = time.perf_counter()
        resp = client.post(
            "/api/qa/ask",
            json={"knowledge_base_id": 1, "question": "test"},
            headers=auth_headers,
        )
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 5.0, f"QA ask (mocked) took {elapsed:.2f}s (> 5s)"
