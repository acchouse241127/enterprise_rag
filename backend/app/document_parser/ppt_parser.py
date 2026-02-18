"""PowerPoint parser implementation."""

from pathlib import Path

from .base import BaseDocumentParser


class PptDocumentParser(BaseDocumentParser):
    """Parser for PPT/PPTX documents."""

    def parse(self, file_path: Path) -> str:
        path = Path(file_path)
        converted_path: Path | None = None
        try:
            if path.suffix.lower() == ".ppt":
                from .legacy_office import convert_ppt_to_pptx
                converted_path = convert_ppt_to_pptx(path)
                parse_path = converted_path
            else:
                parse_path = path

            from pptx import Presentation  # type: ignore
            prs = Presentation(str(parse_path))
            lines: list[str] = []
            for idx, slide in enumerate(prs.slides, start=1):
                lines.append(f"[Slide] {idx}")
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        text = shape.text.strip()
                        if text:
                            lines.append(text)
            return "\n".join(lines)
        finally:
            if converted_path is not None and converted_path.exists():
                try:
                    converted_path.unlink()
                except OSError:
                    pass

