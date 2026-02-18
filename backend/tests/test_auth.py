"""
Authentication API tests.

Author: O3
Date: 2026-02-13
"""

import pyotp
import pytest
from fastapi.testclient import TestClient


class TestAuthLogin:
    """Login API tests."""

    def test_login_success_no_totp(self, client: TestClient) -> None:
        """TC-AUTH-001: Login with valid credentials, no TOTP."""
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "access_token" in data.get("data", {})
        assert data["data"]["token_type"] == "bearer"

    def test_login_fail_wrong_username(self, client: TestClient) -> None:
        """TC-AUTH-002: Login with wrong username."""
        resp = client.post(
            "/api/auth/login",
            json={"username": "wronguser", "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 1002

    def test_login_fail_wrong_password(self, client: TestClient) -> None:
        """TC-AUTH-003: Login with wrong password."""
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrongpass"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 1002

    def test_logout(self, client: TestClient) -> None:
        """TC-AUTH-006: Logout returns success."""
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data.get("data", {}).get("logged_out") is True


class TestAuthMe:
    """GET /api/auth/me for SPA token validation."""

    def test_me_requires_auth(self, client: TestClient) -> None:
        """Without Authorization header returns 401."""
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_success(self, client: TestClient) -> None:
        """With valid token returns current user id, username, role."""
        login = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "password123"},
        )
        assert login.status_code == 200 and login.json().get("code") == 0
        token = login.json()["data"]["access_token"]
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "id" in data.get("data", {})
        assert data["data"]["username"] == "admin"
        assert "role" in data["data"]


class TestTotp:
    """TOTP API tests."""

    def test_totp_setup(self, client: TestClient) -> None:
        """TC-TOTP-001: TOTP setup returns secret and URI."""
        resp = client.post(
            "/api/auth/totp/setup",
            json={"username": "admin_totp", "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        secret = data.get("data", {}).get("secret")
        assert secret is not None
        assert len(secret) >= 16
        assert "otpauth://" in data.get("data", {}).get("otpauth_url", "")

    def test_totp_verify_and_bind(self, client: TestClient) -> None:
        """TC-TOTP-002: TOTP verify and bind."""
        # Get secret
        setup_resp = client.post(
            "/api/auth/totp/setup",
            json={"username": "admin_totp", "password": "password123"},
        )
        secret = setup_resp.json()["data"]["secret"]
        code = pyotp.TOTP(secret).now()

        # Verify and bind
        resp = client.post(
            "/api/auth/totp/verify",
            json={
                "username": "admin_totp",
                "password": "password123",
                "secret": secret,
                "code": code,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data.get("data", {}).get("totp_enabled") is True

    def test_totp_verify_wrong_code(self, client: TestClient) -> None:
        """TC-TOTP-003: TOTP verify fails with wrong code."""
        setup_resp = client.post(
            "/api/auth/totp/setup",
            json={"username": "admin_totp", "password": "password123"},
        )
        secret = setup_resp.json()["data"]["secret"]

        resp = client.post(
            "/api/auth/totp/verify",
            json={
                "username": "admin_totp",
                "password": "password123",
                "secret": secret,
                "code": "000000",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 1002


class TestSystem:
    """System API tests."""

    def test_health(self, client: TestClient) -> None:
        """TC-SYS-001: Health check returns ok."""
        resp = client.get("/api/system/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data.get("data", {}).get("status") == "ok"
