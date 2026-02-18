"""LLM provider tests."""

import httpx
import pytest

from app.llm.base import ChatMessage, LlmErrorCode, LlmProviderError
from app.llm.deepseek import DeepSeekProvider


class _FakeResponse:
    def __init__(self, payload: dict | None = None, lines: list[str] | None = None) -> None:
        self._payload = payload or {}
        self._lines = lines or []

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload

    def iter_lines(self):
        for item in self._lines:
            yield item

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_generate_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeClient:
        def __init__(self, timeout: int = 60, limits: object = None, **kwargs: object) -> None:
            self.timeout = timeout
            _ = limits, kwargs

        def post(self, url: str, headers: dict, json: dict) -> _FakeResponse:  # noqa: A002
            assert url.endswith("/chat/completions")
            assert json["model"] == "deepseek-chat"
            return _FakeResponse(payload={"choices": [{"message": {"content": "hello"}}]})

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("app.llm.base.httpx.Client", _FakeClient)
    provider = DeepSeekProvider(api_key="test-key", retry_base_delay=0)
    out = provider.generate(messages=[ChatMessage(role="user", content="hi")])
    assert out == "hello"


def test_stream_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeClient:
        def __init__(self, timeout: int = 60, limits: object = None, **kwargs: object) -> None:
            self.timeout = timeout
            _ = limits, kwargs

        def stream(self, method: str, url: str, headers: dict = None, json: dict = None) -> _FakeResponse:  # noqa: A002
            assert method == "POST"
            assert (json or {}).get("stream") is True
            return _FakeResponse(
                lines=[
                    'data: {"choices":[{"delta":{"content":"你"}}]}',
                    'data: {"choices":[{"delta":{"content":"好"}}]}',
                    "data: [DONE]",
                ]
            )

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("app.llm.base._llm_client_cache", {})  # 避免复用上一用例的 client（无 stream）
    monkeypatch.setattr("app.llm.base.httpx.Client", _FakeClient)
    provider = DeepSeekProvider(api_key="test-key", retry_base_delay=0)
    chunks = list(provider.stream(messages=[ChatMessage(role="user", content="hi")]))
    assert "".join(chunks) == "你好"


def test_generate_retry_then_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FailClient:
        def __init__(self, timeout: int = 60, limits: object = None, **kwargs: object) -> None:
            self.timeout = timeout
            _ = limits, kwargs

        def post(self, url: str, headers: dict = None, json: dict = None) -> _FakeResponse:  # noqa: A002
            raise httpx.ConnectError("connection refused")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("app.llm.base._llm_client_cache", {})  # 确保使用本用例的 FailClient
    monkeypatch.setattr("app.llm.base.httpx.Client", _FailClient)
    provider = DeepSeekProvider(api_key="test-key", max_retries=1, retry_base_delay=0)

    with pytest.raises(LlmProviderError) as exc:
        provider.generate(messages=[ChatMessage(role="user", content="hi")])

    assert exc.value.code == LlmErrorCode.MAX_RETRIES
