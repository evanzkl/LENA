from __future__ import annotations

import numpy as np

from OCR.paddle_ocr import build_paddle_engine, run_paddle_ocr_array
from translation.translator import translate_texts
from blur_and_overlay.processor import process_image_array


class TranslationPipeline:
    """Wraps the OCR -> translate -> blur/overlay pipeline for in-memory frames."""

    def __init__(self) -> None:
        self._engines: dict[str, object] = {}

    def _get_engine(self, ocr_lang: str):
        engine = self._engines.get(ocr_lang)
        if engine is None:
            engine = build_paddle_engine(lang=ocr_lang)
            self._engines[ocr_lang] = engine
        return engine

    def process(
        self,
        frame_bgr: np.ndarray,
        ocr_lang: str,
        target_lang: str,
    ) -> tuple[np.ndarray, float]:
        """
        Run OCR on *frame_bgr*, translate the detected text, and render the
        blurred/translated result. Returns (result_image_bgr, avg_confidence_pct).
        """
        engine = self._get_engine(ocr_lang)
        regions = run_paddle_ocr_array(engine, frame_bgr)

        if not regions:
            return frame_bgr.copy(), 0.0

        translated_texts = translate_texts(
            [region.text for region in regions],
            target_lang=target_lang,
            source_lang=ocr_lang if ocr_lang != target_lang else None,
        )

        result_image = frame_bgr.copy()
        process_image_array(
            result_image,
            polygons=[region.polygon for region in regions],
            translated_texts=translated_texts,
        )

        avg_confidence = sum(region.confidence for region in regions) / len(regions) * 100
        return result_image, avg_confidence
