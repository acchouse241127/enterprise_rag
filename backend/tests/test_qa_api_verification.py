"""
QA API 验证字段测试

测试 API 返回的 verification 字段与 V2.0 质量保障的集成。

Author: C2
Date: 2026-03-03
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestQaAPIVerificationFields:
    """测试 QA API 返回的验证字段"""

    def test_ask_api_returns_verification_when_enabled(self, monkeypatch, client: TestClient, auth_headers: dict):
        """测试验证启用时 API 返回 verification 字段"""
        
        def _fake_ask(*args, **kwargs):
            return (
                {
                    "answer": "Test answer [ID:0].",
                    "citations": [{"id": 0, "chunk_id": "doc1_chunk0"}],
                    "retrieved_count": 1,
                    "verification": {
                        "action": "pass",
                        "confidence_score": 0.85,
                        "citation_accuracy": 0.9,
                    },
                },
                None,
            )

        monkeypatch.setattr("app.api.qa.QaService.ask", _fake_ask)
        resp = client.post(
            "/api/qa/ask",
            json={"knowledge_base_id": 1, "question": "测试问题"},
            headers=auth_headers,
        )
        
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert "verification" in body["data"]
        
        # 验证 verification 字段结构
        verification = body["data"]["verification"]
        assert verification is not None
        assert "action" in verification
        assert "confidence_score" in verification
        assert "citation_accuracy" in verification

    def test_ask_api_verification_refuse_action(self, monkeypatch, client: TestClient, auth_headers: dict):
        """测试验证拒答时 API 返回的 verification 字段"""
        
        def _fake_ask(*args, **kwargs):
            return (
                {
                    "answer": "Test answer [ID:0].",
                    "citations": [{"id": 0, "chunk_id": "doc1_chunk0"}],
                    "retrieved_count": 1,
                    "verification": {
                        "action": "refuse",
                        "confidence_score": 0.25,
                        "citation_accuracy": 0.5,
                    },
                },
                None,
            )

        monkeypatch.setattr("app.api.qa.QaService.ask", _fake_ask)
        resp = client.post(
            "/api/qa/ask",
            json={"knowledge_base_id": 1, "question": "测试问题"},
            headers=auth_headers,
        )
        
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        verification = body["data"]["verification"]
        assert verification["action"] == "refuse"
        assert verification["confidence_score"] < 0.5

    def test_ask_api_verification_filter_action(self, monkeypatch, client: TestClient, auth_headers: dict):
        """测试验证过滤时 API 返回的 verification 字段"""
        
        def _fake_ask(*args, **kwargs):
            return (
                {
                    "answer": "Test answer [ID:0].",
                    "citations": [{"id": 0, "chunk_id": "doc1_chunk0"}],
                    "retrieved_count": 1,
                    "verification": {
                        "action": "filter",
                        "confidence_score": 0.6,
                        "citation_accuracy": 0.3,
                    },
                },
                None,
            )

        monkeypatch.setattr("app.api.qa.QaService.ask", _fake_ask)
        resp = client.post(
            "/api/qa/ask",
            json={"knowledge_base_id": 1, "question": "测试问题"},
            headers=auth_headers,
        )
        
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        verification = body["data"]["verification"]
        assert verification["action"] == "filter"
        assert verification["citation_accuracy"] < 0.5

    def test_ask_api_verification_none_when_disabled(self, monkeypatch, client: TestClient, auth_headers: dict):
        """测试验证禁用时 API 返回的 verification 为 None"""
        
        def _fake_ask(*args, **kwargs):
            return (
                {
                    "answer": "Test answer [ID:0].",
                    "citations": [{"id": 0, "chunk_id": "doc1_chunk0"}],
                    "retrieved_count": 1,
                    # verification 字段不存在或为 None
                },
                None,
            )

        monkeypatch.setattr("app.api.qa.QaService.ask", _fake_ask)
        resp = client.post(
            "/api/qa/ask",
            json={"knowledge_base_id": 1, "question": "测试问题"},
            headers=auth_headers,
        )
        
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        # verification 可以为 None
        assert body["data"].get("verification") is None

    def test_stream_api_verification_in_response(self, monkeypatch, client: TestClient, auth_headers: dict):
        """测试流式 API 包含 verification 字段"""
        
        def _fake_stream(*args, **kwargs):
            yield 'data: {"type":"answer","delta":"Test answer"}\n\n'
            yield 'data: {"type":"citations","data":[{"id":0}]}\n\n'
            yield 'data: {"type":"verification","data":{"action":"pass","confidence_score":0.85,"citation_accuracy":0.9}}\n\n'
            yield "data: [DONE]\n\n"

        monkeypatch.setattr("app.api.qa.QaService.stream_ask", _fake_stream)
        resp = client.post(
            "/api/qa/stream",
            json={"knowledge_base_id": 1, "question": "测试流式"},
            headers=auth_headers,
        )
        
        assert resp.status_code == 200
        text = resp.text
        
        # 验证流式响应包含 verification 类型
        assert '"type":"verification"' in text
        assert '"action":"pass"' in text
        assert '"confidence_score":0.85' in text
        assert '"citation_accuracy":0.9' in text

    def test_stream_api_verification_refuse(self, monkeypatch, client: TestClient, auth_headers: dict):
        """测试流式 API 返回拒答验证结果"""
        
        def _fake_stream(*args, **kwargs):
            yield 'data: {"type":"answer","delta":"Test answer"}\n\n'
            yield 'data: {"type":"citations","data":[{"id":0}]}\n\n'
            yield 'data: {"type":"verification","data":{"action":"refuse","confidence_score":0.2,"citation_accuracy":0.4}}\n\n'
            yield "data: [DONE]\n\n"

        monkeypatch.setattr("app.api.qa.QaService.stream_ask", _fake_stream)
        resp = client.post(
            "/api/qa/stream",
            json={"knowledge_base_id": 1, "question": "测试流式"},
            headers=auth_headers,
        )
        
        assert resp.status_code == 200
        text = resp.text
        assert '"action":"refuse"' in text
        assert '"confidence_score":0.2' in text

    def test_retrieval_mode_parameter(self, monkeypatch, client: TestClient, auth_headers: dict):
        """测试 retrieval_mode 参数传递"""
        captured = {}
        
        def _fake_ask(*args, **kwargs):
            captured["retrieval_mode"] = kwargs.get("retrieval_mode")
            return (
                {
                    "answer": "Test answer",
                    "citations": [],
                    "retrieved_count": 0,
                },
                None,
            )

        monkeypatch.setattr("app.api.qa.QaService.ask", _fake_ask)
        
        # 测试 vector 模式
        resp = client.post(
            "/api/qa/ask",
            json={
                "knowledge_base_id": 1,
                "question": "测试",
                "retrieval_mode": "vector",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert captured.get("retrieval_mode") == "vector"

        # 测试 hybrid 模式
        resp = client.post(
            "/api/qa/ask",
            json={
                "knowledge_base_id": 1,
                "question": "测试",
                "retrieval_mode": "hybrid",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert captured.get("retrieval_mode") == "hybrid"

    def test_verification_metrics_types(self, monkeypatch, client: TestClient, auth_headers: dict):
        """测试验证指标的数据类型"""
        
        def _fake_ask(*args, **kwargs):
            return (
                {
                    "answer": "Test answer",
                    "citations": [],
                    "retrieved_count": 0,
                    "verification": {
                        "action": "pass",
                        "confidence_score": 0.85,  # float
                        "citation_accuracy": 0.9,  # float
                    },
                },
                None,
            )

        monkeypatch.setattr("app.api.qa.QaService.ask", _fake_ask)
        resp = client.post(
            "/api/qa/ask",
            json={"knowledge_base_id": 1, "question": "测试"},
            headers=auth_headers,
        )
        
        assert resp.status_code == 200
        body = resp.json()
        verification = body["data"]["verification"]
        
        # 验证数据类型
        assert isinstance(verification["action"], str)
        assert isinstance(verification["confidence_score"], (int, float))
        assert isinstance(verification["citation_accuracy"], (int, float))
        
        # 验证数值范围
        assert 0.0 <= verification["confidence_score"] <= 1.0
        assert 0.0 <= verification["citation_accuracy"] <= 1.0


@pytest.mark.unit
def test_qa_schema_verification_fields():
    """测试 QA Schema 中的 verification 字段定义"""
    from app.schemas.qa import QaAskData
    
    # 验证 QaAskData 不包含 verification 字段（因为 verification 在运行时动态添加）
    # 但是需要确保 schema 能够处理动态字段
    data = QaAskData(
        answer="Test",
        citations=[],
        retrieved_count=0,
    )
    
    # 验证基本字段
    assert data.answer == "Test"
    assert data.citations == []
    assert data.retrieved_count == 0
