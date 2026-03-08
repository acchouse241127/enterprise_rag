"""Tests for VLM (Vision Language Model) image description.

Author: C2
Date: 2026-03-07
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.llm.vlm_base import BaseVLMClient, VlmErrorCode, VlmError, VlmResult
from app.llm.vlm_openai import OpenAIVLMClient


class MockVLMClient(BaseVLMClient):
    """Mock VLM client for testing."""

    def __init__(self, description: str = "Mock description"):
        self.description = description
        self._available = True

    def describe_image(
        self,
        image_path: Path,
        prompt: str | None = None,
        max_tokens: int | None = None,
    ) -> VlmResult:
        return VlmResult(description=self.description, confidence=0.9)

    def is_available(self) -> bool:
        return self._available


class TestVlmBase:
    """Test VLM base classes and models."""

    def test_vlm_result_creation(self):
        """Test VlmResult dataclass."""
        result = VlmResult(
            description="Test description",
            confidence=0.95,
            metadata={"test": "data"}
        )

        assert result.description == "Test description"
        assert result.confidence == 0.95
        assert result.metadata == {"test": "data"}

    def test_vlm_result_optional_fields(self):
        """Test VlmResult with optional fields."""
        result = VlmResult(description="Test")

        assert result.description == "Test"
        assert result.confidence is None
        assert result.metadata is None

    def test_vlm_error_creation(self):
        """Test VlmError exception."""
        error = VlmError(
            code=VlmErrorCode.TIMEOUT,
            detail="Request timed out"
        )

        assert error.code == VlmErrorCode.TIMEOUT
        assert "TIMEOUT" in str(error)
        assert "Request timed out" in str(error)


class TestOpenAIVLMClient:
    """Test OpenAI VLM client."""

    def test_client_initialization(self):
        """Test client initialization with default values."""
        client = OpenAIVLMClient(api_key="test-key")

        assert client.api_key == "test-key"
        assert client.model_name == "gpt-4o-mini"
        assert client.base_url == "https://api.openai.com/v1"
        assert client.timeout_seconds == 60
        assert client.max_retries == 3

    def test_client_initialization_custom(self):
        """Test client initialization with custom values."""
        client = OpenAIVLMClient(
            api_key="test-key",
            model_name="gpt-4-turbo",
            base_url="https://custom.api.com/v1",
            timeout_seconds=30,
            max_retries=5,
        )

        assert client.api_key == "test-key"
        assert client.model_name == "gpt-4-turbo"
        assert client.base_url == "https://custom.api.com/v1"
        assert client.timeout_seconds == 30
        assert client.max_retries == 5

    def test_client_is_available(self):
        """Test is_available method."""
        client = OpenAIVLMClient(api_key="test-key")
        assert client.is_available() is True

        client_no_key = OpenAIVLMClient(api_key="")
        assert client_no_key.is_available() is False

    @patch("app.llm.vlm_openai.httpx.Client")
    def test_describe_image_mock(self, mock_client_class):
        """Test image description with mocked HTTP client."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test image description."
                    }
                }
            ]
        }

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = OpenAIVLMClient(api_key="test-key")

        # Create test image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"fake image data")
            result = client.describe_image(Path(tmp.name))

        assert result.description == "This is a test image description."
        assert mock_client.post.called

    def test_encode_image(self):
        """Test image encoding to base64."""
        client = OpenAIVLMClient(api_key="test-key")

        # Create test image with enough data to get padding
        tmp_path = Path(tempfile.mktemp(suffix=".png"))
        try:
            # Write enough data to trigger base64 padding
            tmp_path.write_bytes(b"test image data" * 10)
            encoded = client._encode_image(tmp_path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

        assert isinstance(encoded, str)
        assert len(encoded) > 0
        # Base64 strings end with = or == (padding)
        assert encoded.endswith(("=", "=="))

    def test_classify_error(self):
        """Test error classification."""
        client = OpenAIVLMClient(api_key="test-key")

        assert client._classify_error("rate limit exceeded") == VlmErrorCode.RATE_LIMIT
        assert client._classify_error("401 unauthorized") == VlmErrorCode.AUTH
        assert client._classify_error("connection failed") == VlmErrorCode.CONNECTION
        assert client._classify_error("unknown error") == VlmErrorCode.GENERIC

    def test_should_retry(self):
        """Test retry logic."""
        client = OpenAIVLMClient(api_key="test-key")

        assert client._should_retry(VlmErrorCode.RATE_LIMIT) is True
        assert client._should_retry(VlmErrorCode.SERVER) is True
        assert client._should_retry(VlmErrorCode.TIMEOUT) is True
        assert client._should_retry(VlmErrorCode.AUTH) is False
        assert client._should_retry(VlmErrorCode.INVALID_REQUEST) is False


class TestVlmIntegration:
    """Test VLM integration with image parser."""

    @patch("app.document_parser.image_parser.settings")
    def test_image_parser_with_vlm_enabled(self, mock_settings):
        """Test image parser with VLM enabled."""
        mock_settings.vlm_enabled = True

        from app.document_parser.image_parser import ImageDocumentParser

        mock_vlm = MockVLMClient(description="VLM generated description")
        parser = ImageDocumentParser(vlm_client=mock_vlm)

        # Create test image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"test image")
            result = parser.parse(Path(tmp.name))

        assert len(result) == 1
        assert result[0].content_type.value == "image"
        assert "vlm_description" in result[0].metadata
        assert result[0].metadata["vlm_description"] == "VLM generated description"

    @patch("app.document_parser.image_parser.settings")
    def test_image_parser_with_vlm_disabled(self, mock_settings):
        """Test image parser with VLM disabled."""
        mock_settings.vlm_enabled = False

        from app.document_parser.image_parser import ImageDocumentParser

        mock_vlm = MockVLMClient(description="Should not be used")
        parser = ImageDocumentParser(vlm_client=mock_vlm)

        # Create test image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"test image")
            result = parser.parse(Path(tmp.name))

        assert len(result) == 1
        # VLM description should not be added when disabled
        assert "vlm_description" not in result[0].metadata

    @patch("app.document_parser.image_parser.settings")
    def test_image_parser_vlm_failure(self, mock_settings):
        """Test image parser handles VLM failure gracefully."""
        mock_settings.vlm_enabled = True

        # Mock VLM client that raises error
        class FailingVLMClient(BaseVLMClient):
            def describe_image(self, image_path, **kwargs):
                raise VlmError(
                    code=VlmErrorCode.TIMEOUT,
                    detail="Mock timeout"
                )

        parser = ImageDocumentParser(vlm_client=FailingVLMClient())

        # Create test image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"test image")
            result = parser.parse(Path(tmp.name))

        assert len(result) == 1
        # Should have error metadata but still return OCR text
        assert "vlm_error" in result[0].metadata
        assert result[0].text  # OCR text should still be available


class TestVlmFactory:
    """Test VLM client factory function."""

    @patch("app.llm.settings")
    def test_build_vlm_client_disabled(self, mock_settings):
        """Test factory returns None when VLM disabled."""
        mock_settings.vlm_enabled = False

        from app.llm import build_vlm_client

        client = build_vlm_client()
        assert client is None

    @patch("app.llm.settings")
    def test_build_vlm_client_openai(self, mock_settings):
        """Test factory builds OpenAI VLM client."""
        mock_settings.vlm_enabled = True
        mock_settings.vlm_provider = "openai"
        mock_settings.vlm_api_key = "test-key"
        mock_settings.vlm_model_name = "gpt-4o-mini"
        mock_settings.vlm_base_url = "https://api.openai.com/v1"
        mock_settings.vlm_timeout_seconds = 30
        mock_settings.vlm_max_retries = 2

        from app.llm import build_vlm_client

        client = build_vlm_client()
        assert isinstance(client, OpenAIVLMClient)
        assert client.api_key == "test-key"
        assert client.model_name == "gpt-4o-mini"

    @patch("app.llm.settings")
    @patch("app.llm.settings.llm_api_key", "llm-api-key")
    def test_build_vlm_client_fallback_to_llm(self, mock_settings):
        """Test factory falls back to LLM config when VLM config missing."""
        mock_settings.vlm_enabled = True
        mock_settings.vlm_provider = "openai"
        mock_settings.vlm_api_key = ""  # Empty, should use LLM key
        mock_settings.llm_api_key = "llm-api-key"
        mock_settings.llm_base_url = "https://llm.api.com/v1"
        mock_settings.vlm_base_url = ""  # Empty, should use LLM URL

        from app.llm import build_vlm_client

        client = build_vlm_client()
        assert isinstance(client, OpenAIVLMClient)
        assert client.api_key == "llm-api-key"  # Should fall back
        assert client.base_url == "https://llm.api.com/v1"  # Should fall back

    @patch("app.llm.settings")
    def test_build_vlm_client_unsupported_provider(self, mock_settings):
        """Test factory raises error for unsupported provider."""
        mock_settings.vlm_enabled = True
        mock_settings.vlm_provider = "unknown"

        from app.llm import build_vlm_client

        with pytest.raises(ValueError, match="Unsupported VLM provider"):
            build_vlm_client()
