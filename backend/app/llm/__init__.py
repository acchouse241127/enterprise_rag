"""LLM provider package."""

from app.config import settings
from app.llm.base import BaseChatProvider, ChatMessage, LlmErrorCode, LlmProviderError
from app.llm.deepseek import DeepSeekProvider
from app.llm.kimi import KimiProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.vlm_base import BaseVLMClient, VlmErrorCode, VlmError, VlmResult
from app.llm.vlm_openai import OpenAIVLMClient


def build_chat_provider(
    *,
    provider: str | None = None,
    api_key: str | None = None,
    model_name: str | None = None,
    base_url: str | None = None,
    timeout_seconds: int | None = None,
    max_retries: int | None = None,
    retry_base_delay: float | None = None,
) -> BaseChatProvider:
    api_key = api_key or settings.llm_api_key
    model_name = model_name or settings.llm_model_name
    base_url = base_url or settings.llm_base_url
    timeout_seconds = timeout_seconds if timeout_seconds is not None else settings.llm_timeout_seconds
    max_retries = max_retries if max_retries is not None else settings.llm_max_retries
    retry_base_delay = retry_base_delay if retry_base_delay is not None else settings.llm_retry_base_delay
    provider_name = (provider or settings.llm_provider).lower()
    if provider_name == "openai":
        return OpenAIProvider(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
        )
    if provider_name == "deepseek":
        return DeepSeekProvider(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
        )
    if provider_name == "kimi":
        return KimiProvider(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
        )
    raise ValueError(f"Unsupported LLM provider: {provider_name}")


def get_provider_for_task(task_type: str | None = None) -> BaseChatProvider:
    """
    Return LLM provider for the given task type. Strategy A: all use default.
    Strategy B: use llm_task_overrides[task_type] when set (model_name, base_url, api_key).
    """
    overrides = getattr(settings, "llm_task_overrides", None) or {}
    if task_type and isinstance(overrides, dict) and task_type in overrides:
        opts = overrides[task_type]
        if isinstance(opts, dict):
            return build_chat_provider(
                api_key=opts.get("api_key"),
                model_name=opts.get("model_name"),
                base_url=opts.get("base_url"),
                timeout_seconds=opts.get("timeout_seconds"),
                max_retries=opts.get("max_retries"),
                retry_base_delay=opts.get("retry_base_delay"),
            )
    return build_chat_provider()


__all__ = [
    # Chat providers
    "BaseChatProvider",
    "ChatMessage",
    "LlmErrorCode",
    "LlmProviderError",
    "DeepSeekProvider",
    "KimiProvider",
    "OpenAIProvider",
    "build_chat_provider",
    "get_provider_for_task",
    # VLM providers
    "BaseVLMClient",
    "VlmErrorCode",
    "VlmError",
    "VlmResult",
    "OpenAIVLMClient",
    "build_vlm_client",
]


def build_vlm_client() -> BaseVLMClient | None:
    """Build VLM client based on configuration.

    Returns:
        VLM client instance or None if disabled
    """
    if not settings.vlm_enabled:
        return None

    provider = settings.vlm_provider.lower()

    # Use LLM API key/base URL if VLM specific not provided
    api_key = settings.vlm_api_key or settings.llm_api_key
    base_url = settings.vlm_base_url or settings.llm_base_url

    if provider == "openai":
        return OpenAIVLMClient(
            api_key=api_key,
            model_name=settings.vlm_model_name,
            base_url=base_url,
            timeout_seconds=settings.vlm_timeout_seconds,
            max_retries=settings.vlm_max_retries,
        )

    # Add more providers here if needed (e.g., DeepSeek, Kimi)

    raise ValueError(f"Unsupported VLM provider: {provider}")

