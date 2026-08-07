from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
import pytesseract
from PIL import Image
from PIL import ImageFilter

from config import DEFAULT_TESSERACT_CMD
from text_utils import normalize_text

try:
    import easyocr
except ImportError:
    easyocr = None

try:
    import paddle
except ImportError:
    paddle = None  # type: ignore[assignment,misc]

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None


EasyOCRReader = Any
PaddleEngine = Any


def _resolve_paddle_device() -> str:
    requested_device = (os.environ.get("OCR_PADDLE_DEVICE") or os.environ.get("PADDLE_DEVICE") or "gpu").strip().lower()
    if requested_device in {"auto", ""}:
        requested_device = "gpu" if paddle is not None and paddle.device.is_compiled_with_cuda() else "cpu"

    if requested_device == "gpu":
        if paddle is None:
            raise RuntimeError(
                "GPU mode was requested, but Paddle is not installed. Install the Jetson CUDA build of paddlepaddle-gpu."
            )
        if not paddle.device.is_compiled_with_cuda():
            raise RuntimeError(
                "GPU mode was requested, but your installed Paddle build is CPU-only. Install the Jetson CUDA-enabled paddlepaddle-gpu wheel."
            )

    return requested_device


def _resolve_ocr_version() -> str:
    ocr_version = (os.environ.get("OCR_PADDLE_OCR_VERSION") or "PP-OCRv5").strip()
    return ocr_version or "PP-OCRv5"


def configure_tesseract(tesseract_cmd: str | None) -> None:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd or DEFAULT_TESSERACT_CMD


def ensure_engine_dependencies() -> None:
    if easyocr is None:
        raise SystemExit("easyocr is not installed. Install it with: pip install easyocr")
    if PaddleOCR is None:
        raise SystemExit("paddleocr is not installed. Install it with: pip install paddleocr")


def preprocess_image(image_path: Path) -> Image.Image:
    with Image.open(image_path) as img:
        grayscale = img.convert("L")
        denoised = grayscale.filter(ImageFilter.MedianFilter(size=3))
        return denoised.copy()


def run_tesseract(image_path: Path, psm: int = 3) -> str:
    preprocessed = preprocess_image(image_path)
    raw_text = pytesseract.image_to_string(preprocessed, config=f"--psm {psm}")
    return normalize_text(raw_text)


def build_easyocr_reader() -> EasyOCRReader:
    if easyocr is None:
        raise ImportError("easyocr is not installed. Run: pip install easyocr")
    return easyocr.Reader(["en"], gpu=False)


def run_easyocr(reader: EasyOCRReader, image_path: Path) -> str:
    preprocessed = preprocess_image(image_path)
    img_np = np.array(preprocessed)
    detections = reader.readtext(img_np, detail=1)
    lines = [entry[1] for entry in detections if len(entry) >= 2]
    return normalize_text(" ".join(lines))


def build_paddleocr_engine() -> PaddleEngine:
    if PaddleOCR is None:
        raise ImportError("paddleocr is not installed. Run: pip install paddleocr")
    device = _resolve_paddle_device()
    ocr_version = _resolve_ocr_version()
    return PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        lang="en",
        ocr_version=ocr_version,
        device=device,
        enable_hpi=False,
        enable_mkldnn=False,
    )


def run_paddleocr(ocr_engine: PaddleEngine, image_path: Path) -> str:
    result = ocr_engine.predict(str(image_path))

    lines: list[str] = []
    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict):
                rec_texts = item.get("rec_texts")
                if isinstance(rec_texts, list):
                    lines.extend(str(text) for text in rec_texts)
            elif isinstance(item, list):
                for det in item:
                    if isinstance(det, list) and len(det) >= 2:
                        text_info = det[1]
                        if isinstance(text_info, (list, tuple)) and text_info:
                            lines.append(str(text_info[0]))

    return normalize_text(" ".join(lines))
