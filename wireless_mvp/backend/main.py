from __future__ import annotations

import base64
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

# Make the existing wireless_mvp packages (gui, OCR, translation, blur_and_overlay) importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gui.languages import LANGUAGES, language_by_display_name  # noqa: E402
from gui.pipeline import TranslationPipeline  # noqa: E402

from .schemas import LanguageInfo, ProcessResult  # noqa: E402

app = FastAPI(title="Handheld OCR Translator API", version="1.0.0")

# Allow a local Flutter web dev server (served from a different port) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared pipeline so the Vision/Translation clients are created once and reused.
pipeline = TranslationPipeline()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/languages", response_model=list[LanguageInfo])
def get_languages() -> list[LanguageInfo]:
    return [
        LanguageInfo(
            display_name=lang.display_name,
            ocr_code=lang.ocr_code,
            translate_code=lang.translate_code,
        )
        for lang in LANGUAGES
    ]


async def _run_pipeline(
    file: UploadFile, source_lang: str, target_lang: str
) -> tuple[bytes, float, float]:
    """Decode the upload, run the shared pipeline, and return (png_bytes, accuracy, seconds)."""
    try:
        source = language_by_display_name(source_lang)
        target = language_by_display_name(target_lang)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown language: {exc}") from exc

    content = await file.read()
    image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Could not decode uploaded image")

    started_at = time.perf_counter()
    try:
        result_image, accuracy = pipeline.process(image, source.ocr_code, target.translate_code)
    except Exception as exc:  # noqa: BLE001 - surface pipeline failures to the caller
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    processing_time = time.perf_counter() - started_at

    ok, encoded = cv2.imencode(".png", result_image)
    if not ok:
        raise HTTPException(status_code=500, detail="Could not encode processed image")

    return encoded.tobytes(), accuracy, processing_time


@app.post("/api/process", response_model=ProcessResult)
async def process_image(
    file: UploadFile = File(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...),
) -> ProcessResult:
    png_bytes, accuracy, processing_time = await _run_pipeline(file, source_lang, target_lang)
    return ProcessResult(
        image_base64=base64.b64encode(png_bytes).decode("ascii"),
        image_format="png",
        accuracy=accuracy,
        processing_time_seconds=processing_time,
    )


@app.post(
    "/api/process/image",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}},
)
async def process_image_raw(
    file: UploadFile = File(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...),
) -> Response:
    """Same processing as /api/process, but returns the PNG directly for easy viewing in /docs."""
    png_bytes, accuracy, processing_time = await _run_pipeline(file, source_lang, target_lang)
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "X-Accuracy": f"{accuracy:.4f}",
            "X-Processing-Time-Seconds": f"{processing_time:.4f}",
        },
    )
