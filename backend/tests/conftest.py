"""Pytest fixtures for backend tests.

C2-3.1.2: 测试环境标准化
- 添加 pytest markers 用于区分单元测试和集成测试
- 添加 skipif 辅助函数用于环境依赖检测
- 支持 CI 和本地环境运行

Author: C2
Date: 2026-02-13
"""

import os
import socket

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from main import app


# ========== 环境检测辅助函数 ==========

def is_service_available(host: str, port: int, timeout: float = 1.0) -> bool:
    """检测服务是否可用（TCP 连接测试）"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def is_postgres_available() -> bool:
    """检测 Postgres 是否可用"""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    return is_service_available(host, port)


def is_chroma_available() -> bool:
    """检测 ChromaDB 是否可用"""
    host = os.getenv("CHROMA_HOST", "localhost")
    port = int(os.getenv("CHROMA_PORT", "8001"))
    return is_service_available(host, port)


def is_llm_configured() -> bool:
    """检测 LLM API 是否配置"""
    return bool(os.getenv("LLM_API_KEY"))


# ========== Pytest Markers ==========

def pytest_configure(config):
    """注册自定义 markers"""
    config.addinivalue_line(
        "markers", "integration: 集成测试，需要外部服务（Postgres/Chroma）"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试，可能需要较长时间"
    )
    config.addinivalue_line(
        "markers", "llm: 需要 LLM API 的测试"
    )


# ========== Skip 条件 ==========

skip_no_postgres = pytest.mark.skipif(
    not is_postgres_available(),
    reason="Postgres 不可用，跳过集成测试"
)

skip_no_chroma = pytest.mark.skipif(
    not is_chroma_available(),
    reason="ChromaDB 不可用，跳过向量存储测试"
)

skip_no_llm = pytest.mark.skipif(
    not is_llm_configured(),
    reason="LLM API 未配置，跳过 LLM 相关测试"
)

skip_no_external_services = pytest.mark.skipif(
    not (is_postgres_available() and is_chroma_available()),
    reason="外部服务（Postgres/Chroma）不可用，跳过集成测试"
)


# ========== Fixtures ==========

@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers() -> dict:
    """
    Generate authentication headers with a valid JWT token.
    Uses 'admin' as the test user subject.
    """
    token = create_access_token(subject="admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_client(client: TestClient, auth_headers: dict):
    """
    Test client wrapper that automatically includes auth headers.
    Returns a tuple of (client, headers) for convenience.
    """
    return client, auth_headers


@pytest.fixture
def postgres_available():
    """Fixture that skips test if Postgres is not available."""
    if not is_postgres_available():
        pytest.skip("Postgres 不可用")
    return True


@pytest.fixture
def chroma_available():
    """Fixture that skips test if ChromaDB is not available."""
    if not is_chroma_available():
        pytest.skip("ChromaDB 不可用")
    return True


@pytest.fixture
def llm_available():
    """Fixture that skips test if LLM API is not configured."""
    if not is_llm_configured():
        pytest.skip("LLM API 未配置")
    return True
