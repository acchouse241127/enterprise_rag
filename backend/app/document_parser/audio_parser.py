"""Audio parser: transcribe to text via faster-whisper (optional)."""

from pathlib import Path

from app.document_parser.base import BaseDocumentParser


class AudioParser(BaseDocumentParser):
    """Transcribe audio files to text. Requires faster-whisper."""

    def parse(self, file_path: Path) -> str:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            return "（音频转写需要安装 faster-whisper：pip install faster-whisper）"

        path_str = str(file_path.resolve())
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(path_str, language=None, beam_size=1)
        return " ".join(s.text for s in segments if s.text).strip() or "（转写无输出）"
