"""Legacy Office format (.doc, .ppt) conversion via LibreOffice.

Converts .doc -> .docx and .ppt -> .pptx for parsing by python-docx / python-pptx.
Requires LibreOffice (soffice) to be installed and available in PATH or at common paths.
"""

from __future__ import annotations

import shutil
import uuid
import subprocess
import tempfile
from pathlib import Path


def _find_soffice() -> str | None:
    """Find soffice (LibreOffice) executable."""
    for name in ("soffice", "libreoffice"):
        path = shutil.which(name)
        if path:
            return path
    # Windows common path
    if Path("C:/Program Files/LibreOffice/program/soffice.exe").exists():
        return str(Path("C:/Program Files/LibreOffice/program/soffice.exe"))
    if Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe").exists():
        return str(Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe"))
    return None


def convert_doc_to_docx(doc_path: Path) -> Path:
    """Convert .doc to .docx via LibreOffice. Returns path to generated .docx file."""
    return _convert(doc_path, "docx")


def convert_ppt_to_pptx(ppt_path: Path) -> Path:
    """Convert .ppt to .pptx via LibreOffice. Returns path to generated .pptx file."""
    return _convert(ppt_path, "pptx")


def _convert(input_path: Path, target_ext: str) -> Path:
    """Run LibreOffice conversion. Returns path to converted file."""
    soffice = _find_soffice()
    if not soffice:
        raise RuntimeError(
            "无法解析 .doc/.ppt 旧格式：未检测到 LibreOffice。请安装 LibreOffice 或将文件转换为 .docx/.pptx 后上传。"
        )
    input_path = input_path.resolve()
    if not input_path.exists():
        raise FileNotFoundError(str(input_path))
    with tempfile.TemporaryDirectory() as tmpdir:
        outdir = Path(tmpdir)
        cmd = [
            soffice,
            "--headless",
            "--convert-to",
            target_ext,
            "--outdir",
            str(outdir),
            str(input_path),
        ]
        try:
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                check=True,
            )
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(
                f"LibreOffice 转换超时（120秒），请检查文件是否过大或损坏"
            ) from e
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"LibreOffice 转换失败: {e.stderr or e.stdout or str(e)}"
            ) from e
        # Output filename is input stem + target_ext, e.g. file.doc -> file.docx
        output_file = outdir / f"{input_path.stem}.{target_ext}"
        if not output_file.exists():
            raise RuntimeError(f"转换后文件未生成: {output_file}")
        # Copy to a persistent temp file; caller must delete after use
        persistent = Path(tempfile.gettempdir()) / f"rag_conv_{uuid.uuid4().hex}.{target_ext}"
        shutil.copy2(output_file, persistent)
        return persistent
