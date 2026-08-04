from __future__ import annotations

from pathlib import Path
from typing import Any, NamedTuple

import numpy as np

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None  # type: ignore[assignment,misc]


class TextRegion(NamedTuple):
    """A detected text region with its polygon, text content and confidence."""
    polygon: list[list[float]]  # 4-point quadrilateral [[x1,y1], [x2,y2], ...]
    text: str
    confidence: float


def build_paddle_engine(lang: str = "en") -> Any:
    """Initialise and return a PaddleOCR engine for the given source language."""
    if PaddleOCR is None:
        raise ImportError("paddleocr is not installed. Run: pip install paddleocr")
    return PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        lang=lang,
        device="cpu",
        enable_hpi=False,
        enable_mkldnn=False,
    )


def _regions_from_predict_result(result: Any) -> list[TextRegion]:
    """Parse the raw PaddleOCR `predict()` output into `TextRegion` objects."""
    regions: list[TextRegion] = []

    if not isinstance(result, list):
        return regions

    for item in result:
        if not isinstance(item, dict):
            continue

        polys: list[Any] = item.get("dt_polys", [])
        texts: list[Any] = item.get("rec_texts", [])
        scores: list[Any] = item.get("rec_scores", [])

        # Zip together, padding missing scores with 1.0
        for poly, text, score in zip(polys, texts, scores):
            text = str(text).strip()
            if not text:
                continue
            polygon = (
                poly.tolist() if hasattr(poly, "tolist") else list(poly)
            )
            regions.append(TextRegion(
                polygon=polygon,
                text=text,
                confidence=float(score),
            ))

    return regions


def run_paddle_ocr(engine: Any, image_path: Path) -> list[TextRegion]:
    """Run PaddleOCR on an image file and return detected text regions."""
    result = engine.predict(str(image_path))
    return _regions_from_predict_result(result)


def run_paddle_ocr_array(engine: Any, image: np.ndarray) -> list[TextRegion]:
    """Run PaddleOCR on an in-memory BGR image (e.g. a captured camera frame)."""
    result = engine.predict(image)
    return _regions_from_predict_result(result)
