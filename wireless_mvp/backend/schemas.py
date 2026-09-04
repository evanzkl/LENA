from __future__ import annotations

from pydantic import BaseModel


class LanguageInfo(BaseModel):
    display_name: str
    ocr_code: str
    translate_code: str


class ProcessResult(BaseModel):
    image_base64: str
    image_format: str
    accuracy: float
    processing_time_seconds: float
