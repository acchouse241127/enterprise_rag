"""LLM provider package."""

from app.config import settings
from app.llm.base import BaseChatProvider, ChatMessage, LlmErrorCode, LlmProviderError
from app.llm.deepseek import DeepSeekProvider
from app.llm.openai_provider import OpenAIProvider


def build_chat_provider(
    *,
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
    provider = settings.llm_provider.lower()
    if provider == "openai":
        return OpenAIProvider(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
        )
    return DeepSeekProvider(
        api_key=api_key,
        model_name=model_name,
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        retry_base_delay=retry_base_delay,
    )


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
    "BaseChatProvider",
    "ChatMessage",
    "LlmErrorCode",
    "LlmProviderError",
    "DeepSeekProvider",
    "OpenAIProvider",
    "build_chat_provider",
    "get_provider_for_task",
]

