"""Document parsers package."""

from .base import BaseDocumentParser
from .converter import content_list_to_chunks, get_content_metadata
from .models import ContentType, ParsedContent

# Parsers
from .audio_parser import AudioParser
from .docling_pdf_parser import DoclingPdfParser, DOCLING_AVAILABLE
from .excel_parser import ExcelDocumentParser
from .image_parser import ImageDocumentParser
from .pdf_parser import PdfDocumentParser
from .ppt_parser import PptDocumentParser
from .txt_parser import TxtDocumentParser
from .url_parser import UrlParser
from .video_parser import VideoParser
from .word_parser import WordDocumentParser

# Factory
from .factory import ParserFactory, get_parser

__all__ = [
    # Models and converters
    "ContentType",
    "ParsedContent",
    "content_list_to_chunks",
    "get_content_metadata",
    # Base class
    "BaseDocumentParser",
    # Parsers
    "AudioParser",
    "ExcelDocumentParser",
    "ImageDocumentParser",
    "PdfDocumentParser",
    "PptDocumentParser",
    "TxtDocumentParser",
    "UrlParser",
    "VideoParser",
    "WordDocumentParser",
    # Docling parser
    "DoclingPdfParser",
    "DOCLING_AVAILABLE",
    # Factory
    "ParserFactory",
    "get_parser",
    # Legacy (deprecated - use get_parser instead)
    "get_parser_for_extension",
]


def get_parser_for_extension(file_extension: str) -> BaseDocumentParser | None:
    """Return parser instance for extension.

    DEPRECATED: Use get_parser(file_path) instead.
    """
    parser_map = {
        ".txt": TxtDocumentParser(),
        ".md": TxtDocumentParser(),
        ".pdf": PdfDocumentParser(),
        ".doc": WordDocumentParser(),
        ".docx": WordDocumentParser(),
        ".xls": ExcelDocumentParser(),
        ".xlsx": ExcelDocumentParser(),
        ".ppt": PptDocumentParser(),
        ".pptx": PptDocumentParser(),
        ".png": ImageDocumentParser(),
        ".jpg": ImageDocumentParser(),
        ".jpeg": ImageDocumentParser(),
        ".mp3": AudioParser(),
        ".wav": AudioParser(),
        ".m4a": AudioParser(),
        ".flac": AudioParser(),
        ".mp4": VideoParser(),
        ".webm": VideoParser(),
        ".mov": VideoParser(),
    }
    return parser_map.get(file_extension.lower())
