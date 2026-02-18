"""QA pipeline and API tests."""

from app.rag.pipeline import RagPipeline
from fastapi.testclient import TestClient


class _DummyRetriever:
    def retrieve(self, knowledge_base_id: int, query: str, top_k: int = 5):
        return [], None


class _RuleEmbedding:
    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            if ("价值" in text) or ("长期" in text):
                vectors.append([1.0, 0.0])
            elif ("风险" in text) or ("分散" in text):
                vectors.append([0.0, 1.0])
            else:
                vectors.append([0.5, 0.5])
        return vectors


def test_pipeline_insert_citations() -> None:
    pipeline = RagPipeline(_DummyRetriever(), _RuleEmbedding())
    answer = "基金采用长期价值投资。风险控制需要分散配置。"
    chunks = [
        {"chunk_id": "doc1_chunk0", "content": "长期价值投资是核心策略", "metadata": {"document_id": 1, "chunk_index": 0}},
        {"chunk_id": "doc1_chunk1", "content": "风险控制依赖分散配置", "metadata": {"document_id": 1, "chunk_index": 1}},
    ]
    cited_answer, citations = pipeline.insert_citations(answer, chunks, similarity_threshold=0.2)
    assert "[ID:0]" in cited_answer
    assert "[ID:1]" in cited_answer
    assert len(citations) == 2


def test_qa_ask_api(monkeypatch, client: TestClient, auth_headers: dict) -> None:
    def _fake_ask(
        knowledge_base_id: int,
        question: str,
        top_k: int | None = None,
        conversation_id: str | None = None,
        history_turns: int | None = None,
    ):
        _ = conversation_id, history_turns
        return (
            {
                "answer": "这是测试回答 [ID:0]。",
                "citations": [{"id": 0, "chunk_id": "doc1_chunk0"}],
                "retrieved_count": 1,
            },
            None,
        )

    monkeypatch.setattr("app.api.qa.QaService.ask", _fake_ask)
    resp = client.post(
        "/api/qa/ask",
        json={"knowledge_base_id": 1, "question": "测试问题", "top_k": 3},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert "[ID:0]" in body["data"]["answer"]


def test_qa_stream_api(monkeypatch, client: TestClient, auth_headers: dict) -> None:
    def _fake_stream(
        knowledge_base_id: int,
        question: str,
        top_k: int | None = None,
        conversation_id: str | None = None,
        history_turns: int | None = None,
    ):
        _ = conversation_id, history_turns
        yield 'data: {"type":"answer","delta":"你好"}\n\n'
        yield "data: [DONE]\n\n"

    monkeypatch.setattr("app.api.qa.QaService.stream_ask", _fake_stream)
    resp = client.post(
        "/api/qa/stream",
        json={"knowledge_base_id": 1, "question": "测试流式"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert "data: " in resp.text
    assert "[DONE]" in resp.text


def test_qa_ask_no_answer(monkeypatch, client: TestClient, auth_headers: dict) -> None:
    """无检索结果时返回明确提示，不编造答案。"""

    def _fake_ask(
        knowledge_base_id: int,
        question: str,
        top_k: int | None = None,
        conversation_id: str | None = None,
        history_turns: int | None = None,
    ):
        _ = conversation_id, history_turns
        return (
            {
                "answer": "未检索到足够知识，无法给出可靠答案。",
                "citations": [],
                "retrieved_count": 0,
            },
            None,
        )

    monkeypatch.setattr("app.api.qa.QaService.ask", _fake_ask)
    resp = client.post(
        "/api/qa/ask",
        json={"knowledge_base_id": 1, "question": "无关问题"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["retrieved_count"] == 0
    assert body["data"]["citations"] == []
    assert "未检索到足够知识" in body["data"]["answer"]


def test_qa_ask_validation(client: TestClient, auth_headers: dict) -> None:
    """参数校验：knowledge_base_id 必须 > 0，question 不能为空。"""

    resp_invalid_kb = client.post(
        "/api/qa/ask",
        json={"knowledge_base_id": 0, "question": "x"},
        headers=auth_headers,
    )
    assert resp_invalid_kb.status_code == 422

    resp_empty_q = client.post(
        "/api/qa/ask",
        json={"knowledge_base_id": 1, "question": ""},
        headers=auth_headers,
    )
    assert resp_empty_q.status_code == 422


def test_qa_unauthorized(client: TestClient) -> None:
    """Test that QA APIs require authentication."""
    resp = client.post(
        "/api/qa/ask",
        json={"knowledge_base_id": 1, "question": "测试"},
    )
    assert resp.status_code == 401
