"""Image parser implementation using OCR and optional VLM description."""

import logging
from pathlib import Path

from ..config import settings
from .base import BaseDocumentParser
from .models import ContentType, ParsedContent
from .ocr import PaddleOCREngine

logger = logging.getLogger(__name__)


class ImageDocumentParser(BaseDocumentParser):
    """Parser for image documents.

    Supports OCR text extraction with optional VLM description
    for enhanced semantic understanding of image content.
    """

    def __init__(self, vlm_client=None) -> None:
        """Initialize image parser.

        Args:
            vlm_client: Optional VLM client for image description
        """
        self.ocr_engine = PaddleOCREngine()
        self.vlm_client = vlm_client
        self.vlm_enabled = settings.vlm_enabled

    def parse(self, file_path: Path) -> list[ParsedContent]:
        """Parse image and return structured content."""
        # Extract text via OCR
        ocr_text = self.ocr_engine.extract_text_from_image(file_path)

        metadata = {"image_path": str(file_path), "parser": "image"}

        # VLM description (Phase 3)
        if self.vlm_enabled and self.vlm_client:
            if self.vlm_client.is_available():
                try:
                    vlm_result = self.vlm_client.describe_image(
                        file_path,
                        max_tokens=settings.vlm_max_tokens,
                    )
                    metadata["vlm_description"] = vlm_result.description

                    # Add VLM metadata if available
                    if vlm_result.confidence:
                        metadata["vlm_confidence"] = vlm_result.confidence
                    if vlm_result.metadata:
                        metadata["vlm_metadata"] = vlm_result.metadata

                    logger.info(
                        f"VLM description generated for {file_path.name}"
                    )

                except Exception as e:
                    logger.warning(
                        f"VLM description failed for {file_path.name}: {e}"
                    )
                    # VLM failure should not block parsing
                    metadata["vlm_error"] = str(e)
            else:
                logger.warning(
                    "VLM client not properly configured, skipping VLM description"
                )

        return [
            ParsedContent(
                content_type=ContentType.IMAGE,
                text=ocr_text,
                metadata=metadata,
            )
        ]

    def get_vlm_client(self):
        """Get VLM client instance (lazy initialization).

        Returns:
            VLM client or None if disabled
        """
        if not self.vlm_enabled:
            return None

        if self.vlm_client is None:
            try:
                from ..llm import build_vlm_client
                self.vlm_client = build_vlm_client()
                logger.info("VLM client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize VLM client: {e}")

        return self.vlm_client
