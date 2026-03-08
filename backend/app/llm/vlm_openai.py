"""OpenAI-compatible Vision Language Model client.

Supports OpenAI GPT-4o-mini and other vision-capable models
for image description generation.

Author: C2
Date: 2026-03-07
"""

import base64
import logging
from pathlib import Path
from typing import Any

import httpx

from .vlm_base import BaseVLMClient, VlmErrorCode, VlmError, VlmResult

logger = logging.getLogger(__name__)


class OpenAIVLMClient(BaseVLMClient):
    """OpenAI-compatible VLM client for image description.

    Supports models with vision capabilities like gpt-4o-mini,
    gpt-4-turbo, etc.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ) -> None:
        """Initialize OpenAI VLM client.

        Args:
            api_key: OpenAI API key
            model_name: Model name (default: gpt-4o-mini)
            base_url: API base URL
            timeout_seconds: Request timeout
            max_retries: Maximum retry attempts
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout_seconds,
                limits=httpx.Limits(
                    max_keepalive_connections=4,
                    keepalive_expiry=30.0,
                ),
            )
        return self._client

    def _headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64.

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded image string
        """
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
                return base64.b64encode(image_data).decode("utf-8")
        except Exception as e:
            raise VlmError(
                code=VlmErrorCode.INVALID_REQUEST,
                detail=f"Failed to read image: {e}",
            )

    def describe_image(
        self,
        image_path: Path,
        prompt: str | None = None,
        max_tokens: int | None = None,
    ) -> VlmResult:
        """Generate description for the given image.

        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt
            max_tokens: Optional maximum tokens

        Returns:
            VlmResult with description
        """
        # Default prompt for general image description
        default_prompt = (
            "Please describe this image in detail. "
            "Include information about:"
            "1) The main subject or content"
            "2) Any text visible in the image"
            "3) The context or setting"
            "4) Any notable features, colors, or styling"
        )
        effective_prompt = prompt or default_prompt

        # Encode image
        image_base64 = self._encode_image(image_path)

        # Build request payload
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": effective_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": max_tokens or 500,
        }

        # Make API call with retry logic
        client = self._get_client()
        for attempt in range(self.max_retries + 1):
            try:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()

                # Parse response
                body = response.json()
                content = body["choices"][0]["message"]["content"]

                # Extract usage info if available
                metadata: dict[str, Any] = {}
                if "usage" in body:
                    metadata["usage"] = body["usage"]

                return VlmResult(description=content, metadata=metadata)

            except Exception as exc:
                code = self._classify_error(str(exc))

                if attempt < self.max_retries and self._should_retry(code):
                    logger.warning(
                        f"VLM attempt {attempt + 1} failed ({code}), retrying..."
                    )
                    continue

                if attempt >= self.max_retries:
                    code = VlmErrorCode.MAX_RETRIES

                raise VlmError(code=code, detail=str(exc))

    def _classify_error(self, text: str) -> VlmErrorCode:
        """Classify error message into error code.

        Args:
            text: Error message string

        Returns:
            VlmErrorCode enum value
        """
        lower = text.lower()

        keywords = [
            (["rate limit", "429", "too many"], VlmErrorCode.RATE_LIMIT),
            (["auth", "apikey", "401", "forbidden"], VlmErrorCode.AUTH),
            (["invalid", "bad request", "400"], VlmErrorCode.INVALID_REQUEST),
            (["server", "503", "502", "504", "500"], VlmErrorCode.SERVER),
            (["timeout", "timed out"], VlmErrorCode.TIMEOUT),
            (["connect", "connection", "network"], VlmErrorCode.CONNECTION),
            (["model", "not found"], VlmErrorCode.MODEL),
        ]

        for words, code in keywords:
            if any(word in lower for word in words):
                return code

        return VlmErrorCode.GENERIC

    def _should_retry(self, code: VlmErrorCode) -> bool:
        """Determine if error is retryable.

        Args:
            code: Error code

        Returns:
            True if should retry, False otherwise
        """
        return code in {
            VlmErrorCode.RATE_LIMIT,
            VlmErrorCode.SERVER,
            VlmErrorCode.TIMEOUT,
            VlmErrorCode.CONNECTION,
        }

    def is_available(self) -> bool:
        """Check if VLM client is properly configured.

        Returns:
            True if API key is set, False otherwise
        """
        return bool(self.api_key and self.api_key.strip())
