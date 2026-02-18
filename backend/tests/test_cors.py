"""CORS middleware tests for SPA cross-origin requests."""

import pytest
from fastapi.testclient import TestClient


def test_cors_preflight_returns_allow_origin(client: TestClient) -> None:
    """OPTIONS preflight (with Access-Control-Request-Method) should return Access-Control-Allow-Origin."""
    # Starlette CORSMiddleware 仅当存在 access-control-request-method 时按 preflight 处理 OPTIONS
    resp = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code in (200, 204)
    allow_origin = resp.headers.get("Access-Control-Allow-Origin") or resp.headers.get("access-control-allow-origin")
    assert allow_origin == "http://localhost:3000"


def test_cors_get_includes_allow_origin(client: TestClient) -> None:
    """GET request with Origin should include CORS headers in response."""
    resp = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" in [h.lower() for h in resp.headers]
