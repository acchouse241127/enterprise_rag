"""CORS middleware tests for SPA cross-origin requests."""

import pytest
from fastapi.testclient import TestClient


def test_cors_preflight_returns_allow_origin(client: TestClient) -> None:
    """OPTIONS request with Origin header should return Access-Control-Allow-Origin."""
    resp = client.options(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert resp.status_code in (200, 204)
    assert "access-control-allow-origin" in [h.lower() for h in resp.headers]
    # Default config allows localhost:3000
    assert resp.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000" or "http://localhost:3000" in resp.headers.get("Access-Control-Allow-Origin", "")


def test_cors_get_includes_allow_origin(client: TestClient) -> None:
    """GET request with Origin should include CORS headers in response."""
    resp = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" in [h.lower() for h in resp.headers]
