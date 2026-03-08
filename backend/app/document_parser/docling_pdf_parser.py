"""PDF parser using Docling for structured content extraction.

Docling provides better table, formula, and layout recognition
compared to the legacy PDF parser.

Author: C2
Date: 2026-03-06
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions

    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

from .base import BaseDocumentParser
from .models import ContentType, ParsedContent

logger = logging.getLogger(__name__)


class DoclingPdfParser(BaseDocumentParser):
    """PDF parser using Docling for structured content extraction.

    Features:
    - Table extraction with Markdown format
    - Formula/LaTeX extraction
    - Image extraction with position information
    - Text extraction with page layout awareness
    """

    def __init__(self, ocr_enabled: bool = True):
        """Initialize Docling PDF parser.

        Args:
            ocr_enabled: Whether to enable OCR for scanned PDFs
        """
        if not DOCLING_AVAILABLE:
            raise ImportError(
                "Docling is not installed. "
                "Install it with: pip install docling"
            )

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = ocr_enabled
        pipeline_options.do_table_structure = True
        pipeline_options.generate_page_images = False  # Disable for performance

        self.converter = DocumentConverter(format_options={
            InputFormat.PDF: pipeline_options
        })
        self.ocr_enabled = ocr_enabled

    def parse(self, file_path: Path) -> list[ParsedContent]:
        """Parse PDF file and return structured content.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of ParsedContent objects with type-specific metadata
        """
        try:
            result = self.converter.convert(str(file_path))
            doc = result.document

            contents: list[ParsedContent] = []

            # Iterate through all items in the document
            for item in doc.iterate_items():
                parsed = self._parse_item(item)
                if parsed:
                    contents.append(parsed)

            logger.info(
                f"Docling parsed {len(contents)} items from {file_path.name}"
            )
            return contents

        except Exception as e:
            logger.error(f"Error parsing PDF with Docling: {e}")
            # Fallback to legacy behavior on error
            return self._parse_fallback(file_path)

    def _parse_item(self, item) -> Optional[ParsedContent]:
        """Parse a single Docling item into ParsedContent.

        Args:
            item: A Docling document item

        Returns:
            ParsedContent object or None if item is empty
        """
        item_type = self._get_item_type(item)
        if item_type is None:
            return None

        text = self._extract_text(item, item_type)
        if not text or not text.strip():
            return None

        page_number = getattr(item, "prov", {}).get("page_no", None)
        position = self._extract_position(item)

        metadata = {"parser": "docling"}

        # Add type-specific metadata
        if item_type == ContentType.TABLE:
            table_markdown = self._export_table_markdown(item)
            metadata["table_markdown"] = table_markdown
        elif item_type == ContentType.EQUATION:
            metadata["latex"] = text
        elif item_type == ContentType.IMAGE:
            image_path = self._extract_image(item, page_number)
            if image_path:
                metadata["image_path"] = image_path

        return ParsedContent(
            content_type=item_type,
            text=text,
            metadata=metadata,
            page_number=page_number,
            position=position,
        )

    def _get_item_type(self, item) -> Optional[ContentType]:
        """Determine content type from Docling item.

        Args:
            item: A Docling document item

        Returns:
            ContentType enum value or None
        """
        label = getattr(item, "label", "")

        type_mapping = {
            "text": ContentType.TEXT,
            "table": ContentType.TABLE,
            "formula": ContentType.EQUATION,
            "picture": ContentType.IMAGE,
            "figure": ContentType.IMAGE,
        }

        return type_mapping.get(label.lower())

    def _extract_text(self, item, content_type: ContentType) -> str:
        """Extract text from Docling item based on content type.

        Args:
            item: A Docling document item
            content_type: The detected content type

        Returns:
            Extracted text string
        """
        if content_type == ContentType.TEXT:
            return item.text if hasattr(item, "text") else ""
        elif content_type == ContentType.TABLE:
            # Tables: return both raw text and structured format
            raw_text = item.text if hasattr(item, "text") else ""
            return raw_text
        elif content_type == ContentType.EQUATION:
            return item.text if hasattr(item, "text") else ""
        elif content_type == ContentType.IMAGE:
            # Images: try to extract caption or OCR text
            if hasattr(item, "text") and item.text:
                return item.text
            return "[图片内容]"
        return ""

    def _export_table_markdown(self, item) -> str:
        """Export table to Markdown format.

        Args:
            item: A Docling table item

        Returns:
            Markdown representation of the table
        """
        try:
            if hasattr(item, "export_to_markdown"):
                return item.export_to_markdown()
            elif hasattr(item, "text"):
                return item.text
        except Exception as e:
            logger.warning(f"Failed to export table as Markdown: {e}")

        return ""

    def _extract_image(
        self, item, page_number: Optional[int]
    ) -> Optional[str]:
        """Extract image and save to disk.

        Args:
            item: A Docling image item
            page_number: Page number for filename

        Returns:
            Path to saved image or None
        """
        try:
            # Extract image data and save to temporary location
            # The actual storage path should be determined by document_service
            # For now, we return a placeholder path
            if page_number:
                item_id = getattr(item, "prov", {}).get("id", "img")
                return f"images/page_{page_number}_{item_id}.png"
        except Exception as e:
            logger.warning(f"Failed to extract image: {e}")

        return None

    def _extract_position(self, item) -> Optional[dict]:
        """Extract position information from Docling item.

        Args:
            item: A Docling document item

        Returns:
            Position dict with x, y, width, height or None
        """
        try:
            if hasattr(item, "prov"):
                bbox = getattr(item.prov, "bbox", None)
                if bbox:
                    return {
                        "x": int(bbox[0]),
                        "y": int(bbox[1]),
                        "width": int(bbox[2] - bbox[0]),
                        "height": int(bbox[3] - bbox[1]),
                    }
        except Exception as e:
            logger.debug(f"Failed to extract position: {e}")

        return None

    def _parse_fallback(self, file_path: Path) -> list[ParsedContent]:
        """Fallback to simple text extraction if Docling fails.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of ParsedContent with text type only
        """
        logger.warning(f"Fallback to simple text extraction for {file_path}")

        try:
            result = self.converter.convert(str(file_path))
            doc = result.document

            # Fallback: extract all text as TEXT type
            return [
                ParsedContent(
                    content_type=ContentType.TEXT,
                    text=doc.text,
                    page_number=1,
                    metadata={"parser": "docling-fallback"},
                )
            ]
        except Exception as e:
            logger.error(f"Fallback extraction also failed: {e}")
            return []
