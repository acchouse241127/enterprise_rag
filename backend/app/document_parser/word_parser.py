"""Word parser implementation."""

from pathlib import Path

from .base import BaseDocumentParser


class WordDocumentParser(BaseDocumentParser):
    """Parser for Word documents (.doc, .docx)."""

    def parse(self, file_path: Path) -> str:
        path = Path(file_path)
        converted_path: Path | None = None
        try:
            if path.suffix.lower() == ".doc":
                from .legacy_office import convert_doc_to_docx
                converted_path = convert_doc_to_docx(path)
                parse_path = converted_path
            else:
                parse_path = path

            from docx import Document as DocxDocument  # type: ignore
            doc = DocxDocument(str(parse_path))
            lines = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
            return "\n".join(lines)
        finally:
            if converted_path is not None and converted_path.exists():
                try:
                    converted_path.unlink()
                except OSError:
                    pass

