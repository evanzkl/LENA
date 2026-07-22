from __future__ import annotations

import json
from pathlib import Path

from config import SUPPORTED_EXTENSIONS
from text_utils import normalize_text, numeric_sort_key


def list_first_images(image_dir: Path, limit: int) -> list[Path]:
    if not image_dir.exists() or not image_dir.is_dir():
        raise FileNotFoundError(f"Image directory not found: {image_dir}")

    images = [
        path
        for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    images.sort(key=numeric_sort_key)

    if not images:
        raise FileNotFoundError(f"No supported images found in: {image_dir}")

    return images[:limit]


def load_ground_truth(gt_json_path: Path) -> dict[str, str]:
    if not gt_json_path.exists():
        raise FileNotFoundError(f"Ground-truth file not found: {gt_json_path}")

    with gt_json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    annots = data.get("annots", {})
    gt_map: dict[str, str] = {}

    for image_name, item in annots.items():
        text_segments = item.get("text", [])
        if isinstance(text_segments, list):
            gt_text = " ".join(str(x) for x in text_segments)
        else:
            gt_text = str(text_segments)
        gt_map[image_name] = normalize_text(gt_text)

    return gt_map
