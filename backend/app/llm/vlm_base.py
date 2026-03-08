"""Vision Language Model (VLM) base class for image understanding.

Provides abstraction for different VLM providers (OpenAI, DeepSeek, etc.)
to generate image descriptions for RAG systems.

Author: C2
Date: 2026-03-07
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class VlmErrorCode(str, Enum):
    """VLM error codes for classification."""

    RATE_LIMIT = "RATE_LIMIT_EXCEEDED"
    AUTH = "AUTH_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    SERVER = "SERVER_ERROR"
    TIMEOUT = "TIMEOUT"
    CONNECTION = "CONNECTION_ERROR"
    MODEL = "MODEL_ERROR"
    GENERIC = "GENERIC_ERROR"
    MAX_RETRIES = "MAX_RETRIES_EXCEEDED"


@dataclass(frozen=True)
class VlmResult:
    """Result from VLM image description.

    Attributes:
        description: Generated image description
        confidence: Confidence score (0-1) if available
        metadata: Additional metadata from the VLM
    """

    description: str
    confidence: float | None = None
    metadata: dict[str, Any] | None = None


class VlmError(RuntimeError):
    """VLM call failed with classified error code."""

    def __init__(self, code: VlmErrorCode, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code.value}: {detail}")


class BaseVLMClient(ABC):
    """Base class for Vision Language Model clients.

    Provides interface for generating image descriptions,
    which can be used to enhance image-based RAG retrieval.
    """

    @abstractmethod
    def describe_image(
        self,
        image_path: Path,
        prompt: str | None = None,
        max_tokens: int | None = None,
    ) -> VlmResult:
        """Generate description for the given image.

        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt for the VLM
            max_tokens: Optional maximum tokens for the response

        Returns:
            VlmResult with description and optional metadata

        Raises:
            VlmError: If the VLM call fails
        """
        raise NotImplementedError

    def describe_images(
        self,
        image_paths: list[Path],
        prompt: str | None = None,
        max_tokens: int | None = None,
    ) -> list[VlmResult]:
        """Generate descriptions for multiple images.

        Args:
            image_paths: List of paths to image files
            prompt: Optional custom prompt for the VLM
            max_tokens: Optional maximum tokens for the response

        Returns:
            List of VlmResult objects
        """
        results = []
        for image_path in image_paths:
            try:
                result = self.describe_image(
                    image_path,
                    prompt=prompt,
                    max_tokens=max_tokens,
                )
                results.append(result)
            except VlmError as e:
                # Log error but continue with other images
                results.append(
                    VlmResult(
                        description=f"Error: {e.detail}",
                        metadata={"error": e.code.value},
                    )
                )
        return results

    def is_available(self) -> bool:
        """Check if the VLM client is properly configured.

        Returns:
            True if client can be used, False otherwise
        """
        # Default implementation assumes available
        # Subclasses can override for specific checks
        return True
