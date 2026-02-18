"""DeepSeek provider."""

from app.llm.base import BaseChatProvider


class DeepSeekProvider(BaseChatProvider):
    """DeepSeek chat provider through OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com/v1",
        timeout_seconds: int = 60,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
    ) -> None:
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
        )
