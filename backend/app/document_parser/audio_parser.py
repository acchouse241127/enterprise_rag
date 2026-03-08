"""Audio parser: transcribe to text via faster-whisper (optional)."""

from pathlib import Path

from app.document_parser.base import BaseDocumentParser
from app.document_parser.models import ContentType, ParsedContent


class AudioParser(BaseDocumentParser):
    """Transcribe audio files to text. Requires faster-whisper."""

    def parse(self, file_path: Path) -> list[ParsedContent]:
        """Parse audio file and return transcribed content."""
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            return [
                ParsedContent(
                    content_type=ContentType.AUDIO,
                    text="（音频转写需要安装 faster-whisper：pip install faster-whisper）",
                    metadata={"error": "faster-whisper not installed"},
                )
            ]

        path_str = str(file_path.resolve())
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(path_str, language=None, beam_size=1)
        text = " ".join(s.text for s in segments if s.text).strip() or "（转写无输出）"

        return [
            ParsedContent(
                content_type=ContentType.AUDIO,
                text=text,
                metadata={"source_file": str(file_path)},
            )
        ]
