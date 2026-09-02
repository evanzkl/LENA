from __future__ import annotations

import argparse
from pathlib import Path

from config import DEFAULT_GT_JSON, DEFAULT_IMAGE_DIR, DEFAULT_OUTPUT_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run OCR on the first N ICDAR images and evaluate CER/WER/time."
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=DEFAULT_IMAGE_DIR,
        help=f"Folder containing source images (default: {DEFAULT_IMAGE_DIR})",
    )
    parser.add_argument(
        "--gt-json",
        type=Path,
        default=DEFAULT_GT_JSON,
        help=f"Ground-truth JSON path (default: {DEFAULT_GT_JSON})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output folder for OCR text and metrics (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="How many images to process from the sorted list (default: 10)",
    )
    return parser.parse_args()
