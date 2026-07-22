from __future__ import annotations

from pathlib import Path

DEFAULT_IMAGE_DIR = Path(r"C:\Projects\OCR\icdar2013\Challenge2_Test_Task12_Images")
DEFAULT_GT_JSON = Path(r"C:\Projects\OCR\icdar2013\test_gt.json")
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
DEFAULT_TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
ENGINES = ("tesseract", "easyocr", "paddleocr")
