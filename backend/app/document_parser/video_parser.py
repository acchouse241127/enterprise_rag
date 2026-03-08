"""Video parser: extract audio then transcribe, or extract subtitle text."""

import tempfile
from pathlib import Path

from app.document_parser.base import BaseDocumentParser
from app.document_parser.audio_parser import AudioParser
from app.document_parser.models import ContentType, ParsedContent


class VideoParser(BaseDocumentParser):
    """Extract audio from video and transcribe via AudioParser."""

    _audio_parser = AudioParser()

    def parse(self, file_path: Path) -> list[ParsedContent]:
        """Parse video file and return transcribed content."""
        try:
            from pydub import AudioSegment
        except ImportError:
            return [
                ParsedContent(
                    content_type=ContentType.VIDEO,
                    text="（视频解析需要安装 pydub：pip install pydub；并需系统安装 ffmpeg）",
                    metadata={"error": "pydub not installed"},
                )
            ]

        path_str = str(file_path.resolve())
        try:
            audio = AudioSegment.from_file(path_str)
        except Exception as e:
            return [
                ParsedContent(
                    content_type=ContentType.VIDEO,
                    text=f"（抽取视频音轨失败: {e}）",
                    metadata={"error": str(e)},
                )
            ]

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name
        try:
            audio.export(wav_path, format="wav")
            audio_contents = self._audio_parser.parse(Path(wav_path))
            # Convert audio content type to video
            return [
                ParsedContent(
                    content_type=ContentType.VIDEO,
                    text=c.text,
                    metadata={**c.metadata, "source_file": str(file_path)},
                )
                for c in audio_contents
            ]
        finally:
            Path(wav_path).unlink(missing_ok=True)
