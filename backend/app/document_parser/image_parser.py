"""Image parser implementation using OCR."""

from pathlib import Path

from .base import BaseDocumentParser
from .ocr import PaddleOCREngine


class ImageDocumentParser(BaseDocumentParser):
    """Parser for image documents."""

    def __init__(self) -> None:
        self.ocr_engine = PaddleOCREngine()

    def parse(self, file_path: Path) -> str:
        return self.ocr_engine.extract_text_from_image(file_path)

