"""OCR utilities with PaddleOCR primary and EasyOCR fallback."""

from pathlib import Path

import cv2  # type: ignore[import-untyped]
import numpy as np  # type: ignore[import-untyped]


def _load_image_from_path(image_path: Path) -> np.ndarray:
    """Load image as numpy array from path. Uses bytes + imdecode to avoid path encoding issues (e.g. Chinese on Windows)."""
    path = image_path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"图片文件不存在: {path}")

    raw = path.read_bytes()
    if not raw:
        raise ValueError("图片文件为空")

    # Decode from memory to avoid OpenCV path/encoding issues
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError(
            "无法解码图片，可能格式不支持或文件已损坏。请尝试另存为 JPG/PNG 后再上传。"
        )
    return img


def _extract_with_paddle(img: np.ndarray) -> str:
    """Extract text using PaddleOCR (input: BGR numpy array)."""
    from paddleocr import PaddleOCR  # type: ignore[import-untyped]

    ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    result = ocr.ocr(img, cls=True)
    if not result:
        return ""
    lines: list[str] = []
    for block in (result or []):
        if block is None:
            continue
        for item in block:
            if item and len(item) >= 2:
                text = item[1][0]
                if text:
                    lines.append(str(text))
    return "\n".join(lines)


def _extract_with_easyocr(img: np.ndarray) -> str:
    """Extract text using EasyOCR (input: BGR numpy array)."""
    import easyocr  # type: ignore[import-untyped]

    reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
    result = reader.readtext(img, detail=0)
    return "\n".join(str(t) for t in result) if result else ""


def _build_preprocessed_variants(img: np.ndarray) -> list[np.ndarray]:
    """Build several image variants to improve OCR robustness on scans/photos."""
    variants: list[np.ndarray] = [img]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variants.append(gray)

    # Denoise + adaptive threshold helps low-contrast scans.
    denoised = cv2.GaussianBlur(gray, (3, 3), 0)
    adaptive = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        5,
    )
    variants.append(adaptive)

    # Upscale small images for better character clarity.
    h, w = gray.shape[:2]
    if min(h, w) < 1200:
        upscaled = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        variants.append(upscaled)
        variants.append(
            cv2.adaptiveThreshold(
                upscaled,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                31,
                5,
            )
        )
    return variants


class PaddleOCREngine:
    """Lazy OCR wrapper with PaddleOCR primary and EasyOCR fallback."""

    def __init__(self) -> None:
        self._engine_used: str | None = None

    def extract_text_from_image(self, image_path: Path) -> str:
        """OCR image and return joined plain text. Tries PaddleOCR first, falls back to EasyOCR."""
        # Load image from bytes to avoid path/encoding issues (e.g. Chinese filename on Windows)
        img = _load_image_from_path(image_path)

        variants = _build_preprocessed_variants(img)

        # 1. Try PaddleOCR on multiple variants, keep best result.
        try:
            best = ""
            for variant in variants:
                text = _extract_with_paddle(variant).strip()
                if len(text) > len(best):
                    best = text
            if best:
                return best
        except Exception:
            pass

        # 2. Fallback to EasyOCR
        try:
            import easyocr  # noqa: F401
        except ImportError:
            raise RuntimeError(
                "图片 OCR 失败：PaddleOCR 不可用，且未安装 EasyOCR。"
                "请执行 pip install paddleocr 或 pip install easyocr"
            ) from None
        try:
            best = ""
            for variant in variants:
                text = _extract_with_easyocr(variant).strip()
                if len(text) > len(best):
                    best = text
            return best
        except Exception as e2:
            raise RuntimeError(
                f"图片 OCR 失败：PaddleOCR 与 EasyOCR 均不可用。原错误: {e2}"
            ) from e2

