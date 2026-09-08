from __future__ import annotations

from typing import Literal, Optional

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


class JobCreateRequest(BaseModel):
    source_lang: str
    target_lang: str


class JobCreateResponse(BaseModel):
    job_id: str
    status: Literal["pending"]


class JobStatusResponse(BaseModel):
    job_id: str
    status: Literal["pending", "done", "error"]
    result: Optional[ProcessResult] = None
    error: Optional[str] = None
