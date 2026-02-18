"""Phase 2 QA enhancements tests: reranker and multi-turn history."""

from app.config import settings
from app.services.qa_service import QaService


class _FakeRetriever:
    def retrieve(self, knowledge_base_id: int, query: str, top_k: int = 5):
        _ = knowledge_base_id, query, top_k
        return [
            {"chunk_id": "doc1_chunk0", "content": "第一段内容", "metadata": {"document_id": 1, "chunk_index": 0}, "distance": 0.2},
            {"chunk_id": "doc1_chunk1", "content": "第二段内容", "metadata": {"document_id": 1, "chunk_index": 1}, "distance": 0.3},
        ], None


class _FakeReranker:
    def rerank(self, query: str, chunks: list[dict], top_n: int):
        _ = query
        return chunks[:top_n]


class _FakeProvider:
    def __init__(self) -> None:
        self.calls: list[list[object]] = []
        self._answers = ["第一次回答", "第二次回答"]

    def generate(self, messages, temperature: float = 0.2):
        _ = temperature
        self.calls.append(messages)
        idx = min(len(self.calls) - 1, len(self._answers) - 1)
        return self._answers[idx]


def test_multiturn_history_used_in_second_round(monkeypatch) -> None:
    fake_provider = _FakeProvider()
    monkeypatch.setattr("app.services.qa_service.build_chat_provider", lambda: fake_provider)
    monkeypatch.setattr(QaService, "_retriever", _FakeRetriever())
    monkeypatch.setattr(QaService, "_reranker", _FakeReranker())
    QaService._conversation_history = {}

    monkeypatch.setattr(settings, "reranker_enabled", True)
    monkeypatch.setattr(settings, "reranker_candidate_k", 20)
    monkeypatch.setattr(settings, "qa_history_max_turns", 6)

    data1, err1 = QaService.ask(knowledge_base_id=1, question="第一问", top_k=2, conversation_id="conv-a", history_turns=3)
    assert err1 is None
    assert data1 is not None
    assert data1["conversation_id"] == "conv-a"

    data2, err2 = QaService.ask(knowledge_base_id=1, question="第二问", top_k=2, conversation_id="conv-a", history_turns=3)
    assert err2 is None
    assert data2 is not None

    # Second call should include one previous user+assistant pair.
    second_messages = fake_provider.calls[1]
    contents = [m.content for m in second_messages]
    assert any("第一问" in c for c in contents)
    assert any("第一次回答" in c for c in contents)


def test_reranker_applies_top_n(monkeypatch) -> None:
    chunks = [
        {"chunk_id": "1", "content": "A"},
        {"chunk_id": "2", "content": "B"},
        {"chunk_id": "3", "content": "C"},
    ]
    monkeypatch.setattr(settings, "reranker_enabled", False)
    out = QaService._apply_reranker("query", chunks, final_top_k=2)
    assert len(out) == 2

