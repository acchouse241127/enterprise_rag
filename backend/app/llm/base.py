"""LLM abstraction and OpenAI-compatible provider."""

from __future__ import annotations

import json
import random
import threading
import time
from abc import ABC
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum

import httpx

# 复用同一 base_url 的 HTTP 连接，减少 LLM 公网请求的建连与 TLS 开销（不改变任何推理逻辑与精度）
_llm_client_cache: dict[tuple[str, int], httpx.Client] = {}
_llm_client_lock = threading.Lock()


def _get_llm_client(base_url: str, timeout_seconds: int) -> httpx.Client:
    key = (base_url.rstrip("/"), timeout_seconds)
    with _llm_client_lock:
        if key not in _llm_client_cache:
            _llm_client_cache[key] = httpx.Client(
                timeout=timeout_seconds,
                limits=httpx.Limits(max_keepalive_connections=4, keepalive_expiry=30.0),
            )
        return _llm_client_cache[key]


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


class LlmErrorCode(str, Enum):
    RATE_LIMIT = "RATE_LIMIT_EXCEEDED"
    AUTH = "AUTH_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    SERVER = "SERVER_ERROR"
    TIMEOUT = "TIMEOUT"
    CONNECTION = "CONNECTION_ERROR"
    MODEL = "MODEL_ERROR"
    GENERIC = "GENERIC_ERROR"
    MAX_RETRIES = "MAX_RETRIES_EXCEEDED"


class LlmProviderError(RuntimeError):
    """Provider call failed with classified error code."""

    def __init__(self, code: LlmErrorCode, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code.value}: {detail}")


class BaseChatProvider(ABC):
    """Shared retry and error handling for chat providers."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: str,
        timeout_seconds: int = 60,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
    ) -> None:
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay

    def _classify_error(self, text: str) -> LlmErrorCode:
        lower = text.lower()
        keywords: list[tuple[list[str], LlmErrorCode]] = [
            (["rate limit", "429", "too many requests"], LlmErrorCode.RATE_LIMIT),
            (["auth", "apikey", "api key", "401", "forbidden", "permission"], LlmErrorCode.AUTH),
            (["invalid", "bad request", "400", "malformed", "parameter"], LlmErrorCode.INVALID_REQUEST),
            (["server", "503", "502", "504", "500", "unavailable"], LlmErrorCode.SERVER),
            (["timeout", "timed out"], LlmErrorCode.TIMEOUT),
            (["connect", "connection", "network", "dns"], LlmErrorCode.CONNECTION),
            (["model", "not found", "does not exist"], LlmErrorCode.MODEL),
        ]
        for words, code in keywords:
            if any(word in lower for word in words):
                return code
        return LlmErrorCode.GENERIC

    def _should_retry(self, code: LlmErrorCode) -> bool:
        return code in {
            LlmErrorCode.RATE_LIMIT,
            LlmErrorCode.SERVER,
            LlmErrorCode.TIMEOUT,
            LlmErrorCode.CONNECTION,
        }

    def _sleep_backoff(self, attempt: int) -> None:
        # jitter + exponential backoff
        delay = self.retry_base_delay * (2**attempt) * random.uniform(0.8, 1.2)
        time.sleep(delay)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _messages_payload(self, messages: list[ChatMessage]) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in messages]

    def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        """Generate non-stream response with retries."""
        payload: dict[str, object] = {
            "model": self.model_name,
            "messages": self._messages_payload(messages),
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        client = _get_llm_client(self.base_url, self.timeout_seconds)
        for attempt in range(self.max_retries + 1):
            try:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                body = resp.json()
                return str(body["choices"][0]["message"]["content"])
            except Exception as exc:  # noqa: BLE001
                code = self._classify_error(str(exc))
                if attempt < self.max_retries and self._should_retry(code):
                    self._sleep_backoff(attempt)
                    continue
                if attempt >= self.max_retries:
                    code = LlmErrorCode.MAX_RETRIES
                raise LlmProviderError(code=code, detail=str(exc)) from exc

    def stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        """Yield streamed text chunks from SSE response."""
        payload: dict[str, object] = {
            "model": self.model_name,
            "messages": self._messages_payload(messages),
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        client = _get_llm_client(self.base_url, self.timeout_seconds)
        for attempt in range(self.max_retries + 1):
            try:
                with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                ) as resp:
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        if not line:
                            continue
                        if not line.startswith("data: "):
                            continue
                        data = line[6:].strip()
                        if data == "[DONE]":
                            return
                        obj = json.loads(data)
                        delta = obj["choices"][0].get("delta", {})
                        piece = delta.get("content")
                        if piece:
                            yield str(piece)
                    return
            except Exception as exc:  # noqa: BLE001
                code = self._classify_error(str(exc))
                if attempt < self.max_retries and self._should_retry(code):
                    self._sleep_backoff(attempt)
                    continue
                if attempt >= self.max_retries:
                    code = LlmErrorCode.MAX_RETRIES
                raise LlmProviderError(code=code, detail=str(exc)) from exc
