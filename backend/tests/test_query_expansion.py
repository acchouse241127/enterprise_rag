"""Unit tests for query expansion modes."""

import re

from app.rag.query_expansion import expand_query
from app.services.qa_service import QaService


class _DummyProvider:
    def __init__(self, response: str) -> None:
        self._response = response

    def generate(self, messages, temperature: float = 0.3) -> str:
        _ = messages, temperature
        return self._response


class _FailProvider:
    def generate(self, messages, temperature: float = 0.3) -> str:
        _ = messages, temperature
        raise RuntimeError("mock llm failure")


def test_expand_query_hybrid_merges_rule_and_llm() -> None:
    provider = _DummyProvider("基金配置策略\n资产配置方案")
    out = expand_query("如何配置基金策略", mode="hybrid", llm_provider=provider, max_extra=3)
    assert out[0] == "如何配置基金策略"
    assert "基金配置策略" in out
    assert "资产配置方案" in out
    assert len(out) <= 4


def test_expand_query_hybrid_deduplicates_case_and_space() -> None:
    provider = _DummyProvider("  HOW   TO  CREATE API  \nhow to create api")
    out = expand_query("How to create API", mode="hybrid", llm_provider=provider, max_extra=3)
    assert out[0] == "How to create API"
    # 与原 query 仅大小写/空白差异的 LLM 候选应被去重，不应重复出现
    normalized = [re.sub(r"\s+", " ", q.strip().lower()) for q in out]
    assert normalized.count("how to create api") == 1


def test_expand_query_hybrid_fallbacks_when_llm_fails() -> None:
    provider = _FailProvider()
    out = expand_query("如何配置基金策略", mode="hybrid", llm_provider=provider, max_extra=2)
    assert out
    assert out[0] == "如何配置基金策略"
    assert len(out) <= 3


def test_expand_query_hybrid_respects_max_extra() -> None:
    provider = _DummyProvider("A\nB\nC\nD")
    out = expand_query("base", mode="hybrid", llm_provider=provider, max_extra=2)
    assert len(out) <= 3
    assert out[0] == "base"


def test_resolve_query_expansion_config_prefers_request_level_llm(monkeypatch) -> None:
    monkeypatch.setattr("app.services.qa_service.get_provider_for_task", lambda _: {"kind": "task_override"})

    def _fake_build_chat_provider(**kwargs):
        return {"kind": "request_level", "kwargs": kwargs}

    monkeypatch.setattr("app.services.qa_service.build_chat_provider", _fake_build_chat_provider)
    mode, provider = QaService._resolve_query_expansion_config(
        query_expansion_mode="hybrid",
        query_expansion_target="cloud",
        query_expansion_llm={"provider": "openai", "model_name": "test-model"},
    )

    assert mode == "hybrid"
    assert provider["kind"] == "request_level"
    assert provider["kwargs"]["provider"] == "openai"


def test_resolve_query_expansion_config_fallbacks_to_task_provider(monkeypatch) -> None:
    monkeypatch.setattr("app.services.qa_service.get_provider_for_task", lambda _: {"kind": "task_override"})
    mode, provider = QaService._resolve_query_expansion_config(
        query_expansion_mode="llm",
        query_expansion_target="local",
        query_expansion_llm=None,
    )

    assert mode == "llm"
    assert provider == {"kind": "task_override"}


def test_resolve_query_expansion_config_rejects_unsafe_base_url(monkeypatch) -> None:
    monkeypatch.setattr("app.services.qa_service.get_provider_for_task", lambda _: {"kind": "task_override"})
    mode, provider = QaService._resolve_query_expansion_config(
        query_expansion_mode="llm",
        query_expansion_target="cloud",
        query_expansion_llm={"provider": "openai", "base_url": "http://127.0.0.1:8000/v1"},
    )
    assert mode == "llm"
    assert provider == {"kind": "task_override"}


def test_resolve_query_expansion_config_clamps_timeout_and_retry(monkeypatch) -> None:
    monkeypatch.setattr("app.services.qa_service.get_provider_for_task", lambda _: {"kind": "task_override"})

    def _fake_build_chat_provider(**kwargs):
        return {"kind": "request_level", "kwargs": kwargs}

    monkeypatch.setattr("app.services.qa_service.build_chat_provider", _fake_build_chat_provider)
    _, provider = QaService._resolve_query_expansion_config(
        query_expansion_mode="llm",
        query_expansion_target="cloud",
        query_expansion_llm={
            "provider": "openai",
            "timeout_seconds": 120,
            "max_retries": 9,
            "retry_base_delay": 10.0,
        },
    )

    kwargs = provider["kwargs"]
    assert kwargs["timeout_seconds"] == 30
    assert kwargs["max_retries"] == 2
    assert kwargs["retry_base_delay"] == 5.0
