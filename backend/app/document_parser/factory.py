"""Document parser factory for dynamic parser selection.

Factory pattern allows switching between different parser backends
based on configuration without changing calling code.

Author: C2
Date: 2026-03-06
"""

import logging
from pathlib import Path
from typing import Union

from ..config import settings
from .base import BaseDocumentParser
from .docling_pdf_parser import DoclingPdfParser, DOCLING_AVAILABLE
from .pdf_parser import PdfDocumentParser
from .excel_parser import ExcelDocumentParser
from .word_parser import WordDocumentParser
from .ppt_parser import PptDocumentParser
from .txt_parser import TxtDocumentParser
from .image_parser import ImageDocumentParser
from .audio_parser import AudioParser
from .video_parser import VideoParser
from .url_parser import UrlParser

logger = logging.getLogger(__name__)

# File extension to parser mapping
PARSER_MAP: dict[str, type[BaseDocumentParser]] = {
    ".pdf": PdfDocumentParser,
    ".xlsx": ExcelDocumentParser,
    ".xls": ExcelDocumentParser,
    ".docx": WordDocumentParser,
    ".doc": WordDocumentParser,  # LegacyOfficeParser handles this
    ".pptx": PptDocumentParser,
    ".ppt": PptDocumentParser,  # LegacyOfficeParser handles this
    ".txt": TxtDocumentParser,
    ".md": TxtDocumentParser,
    ".png": ImageDocumentParser,
    ".jpg": ImageDocumentParser,
    ".jpeg": ImageDocumentParser,
    ".gif": ImageDocumentParser,
    ".bmp": ImageDocumentParser,
    ".webp": ImageDocumentParser,
    ".mp3": AudioParser,
    ".wav": AudioParser,
    ".m4a": AudioParser,
    ".mp4": VideoParser,
    ".avi": VideoParser,
    ".mov": VideoParser,
    ".wmv": VideoParser,
    ".webm": VideoParser,
}


class ParserFactory:
    """Factory for creating document parser instances.

    Supports:
    - Dynamic parser selection by file type
    - Configurable backend switching (e.g., legacy vs Docling for PDF)
    - Singleton pattern for parser reuse
    """

    _instances: dict[str, BaseDocumentParser] = {}

    @classmethod
    def get_parser(cls, file_path: Union[str, Path]) -> BaseDocumentParser:
        """Get appropriate parser for the given file.

        Args:
            file_path: Path to the file to parse

        Returns:
            Parser instance suitable for the file type

        Raises:
            ValueError: If file type is not supported
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension == ".url":
            return UrlDocumentParser()

        parser_class = PARSER_MAP.get(extension)
        if not parser_class:
            raise ValueError(
                f"Unsupported file type: {extension}. "
                f"Supported types: {', '.join(PARSER_MAP.keys())}"
            )

        # Handle PDF parser selection based on config
        if extension == ".pdf":
            return cls._get_pdf_parser()

        # For other file types, use default parser
        return cls._get_or_create_instance(parser_class)

    @classmethod
    def _get_pdf_parser(cls) -> BaseDocumentParser:
        """Get PDF parser based on configuration.

        Returns:
            PDF parser instance (Docling or legacy)
        """
        backend = settings.pdf_parser_backend.lower()

        if backend == "docling":
            if not DOCLING_AVAILABLE:
                logger.warning(
                    "Docling not available, falling back to legacy PDF parser. "
                    "Install with: pip install docling"
                )
                return cls._get_or_create_instance(PdfDocumentParser)

            try:
                return DoclingPdfParser(
                    ocr_enabled=settings.docling_ocr_enabled
                )
            except Exception as e:
                logger.error(f"Failed to initialize Docling parser: {e}")
                logger.info("Falling back to legacy PDF parser")
                return cls._get_or_create_instance(PdfDocumentParser)

        elif backend == "legacy":
            return cls._get_or_create_instance(PdfDocumentParser)

        else:
            logger.warning(
                f"Unknown PDF parser backend: {backend}. "
                "Using legacy parser."
            )
            return cls._get_or_create_instance(PdfDocumentParser)

    @classmethod
    def _get_or_create_instance(
        cls, parser_class: type[BaseDocumentParser]
    ) -> BaseDocumentParser:
        """Get existing instance or create new one (singleton pattern).

        Args:
            parser_class: Parser class to instantiate

        Returns:
            Parser instance
        """
        class_name = parser_class.__name__

        if class_name not in cls._instances:
            try:
                cls._instances[class_name] = parser_class()
                logger.debug(f"Created new parser instance: {class_name}")
            except Exception as e:
                logger.error(f"Failed to create parser {class_name}: {e}")
                raise

        return cls._instances[class_name]

    @classmethod
    def clear_instances(cls) -> None:
        """Clear all cached parser instances.

        Useful for testing or when parser configuration changes.
        """
        cls._instances.clear()
        logger.debug("Cleared all parser instances")

    @classmethod
    def is_supported(cls, file_path: Union[str, Path]) -> bool:
        """Check if a file type is supported.

        Args:
            file_path: Path to the file

        Returns:
            True if file type is supported, False otherwise
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension == ".url":
            return True

        return extension in PARSER_MAP

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """Get list of supported file extensions.

        Returns:
            List of file extensions (e.g., [".pdf", ".txt", ".png"])
        """
        return sorted(list(PARSER_MAP.keys()))


# Convenience function for direct usage
def get_parser(file_path: Union[str, Path]) -> BaseDocumentParser:
    """Get appropriate parser for the given file (convenience function).

    Args:
        file_path: Path to the file to parse

    Returns:
        Parser instance suitable for the file type
    """
    return ParserFactory.get_parser(file_path)
