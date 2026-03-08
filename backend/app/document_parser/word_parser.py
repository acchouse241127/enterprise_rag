"""Word parser implementation."""

from pathlib import Path

from .base import BaseDocumentParser
from .models import ContentType, ParsedContent


class WordDocumentParser(BaseDocumentParser):
    """Parser for Word documents (.doc, .docx)."""

    def parse(self, file_path: Path) -> list[ParsedContent]:
        """Parse Word document and return structured content."""
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

            contents: list[ParsedContent] = []
            current_text_parts: list[str] = []

            for para in doc.paragraphs:
                # Handle None text
                text = (para.text or "").strip()
                if text:
                    current_text_parts.append(text)

            # Combine all paragraphs into a single text content
            if current_text_parts:
                contents.append(
                    ParsedContent(
                        content_type=ContentType.TEXT,
                        text="\n".join(current_text_parts),
                    )
                )

            return contents
        finally:
            if converted_path is not None and converted_path.exists():
                try:
                    converted_path.unlink()
                except OSError:
                    pass
