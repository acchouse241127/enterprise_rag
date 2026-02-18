"""LLM provider package."""

from app.config import settings
from app.llm.base import BaseChatProvider, ChatMessage, LlmErrorCode, LlmProviderError
from app.llm.deepseek import DeepSeekProvider
from app.llm.openai_provider import OpenAIProvider


def build_chat_provider() -> BaseChatProvider:
    provider = settings.llm_provider.lower()
    if provider == "openai":
        return OpenAIProvider(
            api_key=settings.llm_api_key,
            model_name=settings.llm_model_name,
            base_url=settings.llm_base_url,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
            retry_base_delay=settings.llm_retry_base_delay,
        )
    return DeepSeekProvider(
        api_key=settings.llm_api_key,
        model_name=settings.llm_model_name,
        base_url=settings.llm_base_url,
        timeout_seconds=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
        retry_base_delay=settings.llm_retry_base_delay,
    )


__all__ = [
    "BaseChatProvider",
    "ChatMessage",
    "LlmErrorCode",
    "LlmProviderError",
    "DeepSeekProvider",
    "OpenAIProvider",
    "build_chat_provider",
]

