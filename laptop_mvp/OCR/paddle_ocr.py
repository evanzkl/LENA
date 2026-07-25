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


def build_paddle_engine() -> Any:
    """Initialise and return a PaddleOCR engine for English text."""
    if PaddleOCR is None:
        raise ImportError("paddleocr is not installed. Run: pip install paddleocr")
    return PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        lang="en",
        device="cpu",
        enable_hpi=False,
        enable_mkldnn=False,
    )


def run_paddle_ocr(engine: Any, image_path: Path) -> list[TextRegion]:
    """Run PaddleOCR on an image and return detected text regions with bounding polygons."""
    result = engine.predict(str(image_path))
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
