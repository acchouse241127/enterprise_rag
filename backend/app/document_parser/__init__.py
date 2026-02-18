"""Document parsers package."""

from .base import BaseDocumentParser
from .excel_parser import ExcelDocumentParser
from .image_parser import ImageDocumentParser
from .pdf_parser import PdfDocumentParser
from .ppt_parser import PptDocumentParser
from .txt_parser import TxtDocumentParser
from .word_parser import WordDocumentParser


def get_parser_for_extension(file_extension: str) -> BaseDocumentParser | None:
    """Return parser instance for extension."""
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
    }
    return parser_map.get(file_extension.lower())

