"""Video parser: extract audio then transcribe, or extract subtitle text."""

import tempfile
from pathlib import Path

from app.document_parser.base import BaseDocumentParser
from app.document_parser.audio_parser import AudioParser


class VideoParser(BaseDocumentParser):
    """Extract audio from video and transcribe via AudioParser."""

    _audio_parser = AudioParser()

    def parse(self, file_path: Path) -> str:
        try:
            from pydub import AudioSegment
        except ImportError:
            return "（视频解析需要安装 pydub：pip install pydub；并需系统安装 ffmpeg）"

        path_str = str(file_path.resolve())
        try:
            audio = AudioSegment.from_file(path_str)
        except Exception as e:
            return f"（抽取视频音轨失败: {e}）"

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name
        try:
            audio.export(wav_path, format="wav")
            return self._audio_parser.parse(Path(wav_path))
        finally:
            Path(wav_path).unlink(missing_ok=True)
