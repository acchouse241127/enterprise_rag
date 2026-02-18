"""
Phase 2.3 健康检查与监控端点测试.

Author: O3
Date: 2026-02-13
Task: O3-2.3.2 (TC-P23-MON-001～004)
"""

from fastapi.testclient import TestClient


def test_liveness_probe(client: TestClient) -> None:
    """TC-P23-MON-002: GET /health/live 返回 200 且 status=alive."""
    resp = client.get("/health/live")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "alive"
    assert "timestamp" in data


def test_health_check(client: TestClient) -> None:
    """TC-P23-MON-001: GET /health 返回结构化健康信息."""
    resp = client.get("/health")
    # 数据库可用时 200，不可用时 503
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
    assert "uptime_seconds" in data
    assert "timestamp" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert data["checks"]["database"]["status"] in ("healthy", "unhealthy")


def test_readiness_probe(client: TestClient) -> None:
    """TC-P23-MON-003: GET /health/ready 返回就绪状态."""
    resp = client.get("/health/ready")
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data
    assert data["status"] in ("ready", "not_ready")
    assert "timestamp" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert isinstance(data["checks"]["database"], bool)


def test_metrics(client: TestClient) -> None:
    """TC-P23-MON-004: GET /metrics 返回应用指标与配置."""
    resp = client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "app_info" in data
    assert "name" in data["app_info"]
    assert "version" in data["app_info"]
    assert "uptime_seconds" in data
    assert "timestamp" in data
    assert "stats" in data
    assert "knowledge_bases" in data["stats"]
    assert "documents" in data["stats"]
    assert "users" in data["stats"]
    assert "config" in data
    assert "retrieval_top_k" in data["config"]
    assert "dedup_enabled" in data["config"]
    assert "dynamic_threshold_enabled" in data["config"]
