"""PDF parser with text-first and OCR fallback."""

import tempfile
from pathlib import Path

from .base import BaseDocumentParser
from .models import ContentType, ParsedContent
from .ocr import PaddleOCREngine


class PdfDocumentParser(BaseDocumentParser):
    """Parser for PDF documents."""

    def __init__(self) -> None:
        self.ocr_engine = PaddleOCREngine()

    def parse(self, file_path: Path) -> list[ParsedContent]:
        """Parse PDF and return structured content."""
        import fitz  # type: ignore

        doc = fitz.open(str(file_path))
        contents: list[ParsedContent] = []

        # First try to extract text directly
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text("text").strip()
            if page_text:
                contents.append(
                    ParsedContent(
                        content_type=ContentType.TEXT,
                        text=page_text,
                        page_number=page_num,
                    )
                )

        # If we got meaningful text, return it
        full_text = "\n".join(c.text for c in contents)
        if len(full_text) >= 20:
            return contents

        # Scanned PDF fallback: render pages and use OCR
        contents = []
        for page_num, page in enumerate(doc, start=1):
            pix = page.get_pixmap(dpi=200)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(pix.tobytes("png"))
                tmp_path = Path(tmp.name)
            try:
                text = self.ocr_engine.extract_text_from_image(tmp_path)
                if text:
                    contents.append(
                        ParsedContent(
                            content_type=ContentType.TEXT,
                            text=text,
                            page_number=page_num,
                        )
                    )
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()

        return contents
