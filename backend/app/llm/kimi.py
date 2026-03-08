"""Kimi K2.5 provider (Moonshot AI).

Kimi uses OpenAI-compatible API.
API Docs: https://platform.moonshot.cn/docs

Note: Kimi K2.5 only supports temperature=1.0.
"""

from app.llm.base import BaseChatProvider


class KimiProvider(BaseChatProvider):
    """Kimi K2.5 chat provider through OpenAI-compatible API."""

    # Kimi API only supports temperature=1.0
    SUPPORTED_TEMPERATURE = 1.0

    def __init__(
        self,
        api_key: str,
        model_name: str = "moonshot-v1-8k",
        base_url: str = "https://api.moonshot.cn/v1",
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

    def generate(
        self,
        messages,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        """Generate non-stream response. Kimi only supports temperature=1.0."""
        return super().generate(
            messages,
            temperature=self.SUPPORTED_TEMPERATURE,
            max_tokens=max_tokens,
        )

    def stream(
        self,
        messages,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ):
        """Yield streamed text chunks. Kimi only supports temperature=1.0."""
        return super().stream(
            messages,
            temperature=self.SUPPORTED_TEMPERATURE,
            max_tokens=max_tokens,
        )
