"""PDF parser with text-first and OCR fallback."""

import tempfile
from pathlib import Path

from .base import BaseDocumentParser
from .ocr import PaddleOCREngine


class PdfDocumentParser(BaseDocumentParser):
    """Parser for PDF documents."""

    def __init__(self) -> None:
        self.ocr_engine = PaddleOCREngine()

    def parse(self, file_path: Path) -> str:
        import fitz  # type: ignore

        doc = fitz.open(str(file_path))
        texts: list[str] = []
        for page in doc:
            page_text = page.get_text("text").strip()
            if page_text:
                texts.append(page_text)

        full_text = "\n".join(texts).strip()
        if len(full_text) >= 20:
            return full_text

        # Scanned PDF fallback: render pages and use OCR.
        ocr_texts: list[str] = []
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(pix.tobytes("png"))
                tmp_path = Path(tmp.name)
            try:
                text = self.ocr_engine.extract_text_from_image(tmp_path)
                if text:
                    ocr_texts.append(text)
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()

        return "\n".join(ocr_texts).strip()

