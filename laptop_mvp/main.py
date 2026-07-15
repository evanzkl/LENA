from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Iterable

import pytesseract
from PIL import Image
from pytesseract import TesseractNotFoundError


DEFAULT_IMAGE_DIR = Path(r"C:\Projects\OCR\icdar2013\Challenge2_Test_Task12_Images")
DEFAULT_GT_JSON = Path(r"C:\Projects\OCR\icdar2013\test_gt.json")
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run OCR on the first N ICDAR images with pytesseract and evaluate CER/WER."
        )
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
        default=30,
        help="How many images to process from the sorted list (default: 30)",
    )
    parser.add_argument(
        "--tesseract-cmd",
        type=str,
        default=None,
        help=(
            "Optional explicit path to tesseract executable, e.g. "
            "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
        ),
    )
    return parser.parse_args()


def numeric_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"(\d+)", path.stem)
    number = int(match.group(1)) if match else 10**9
    return number, path.name.lower()


def normalize_text(text: str) -> str:
    # Keep evaluation stable by normalizing line breaks and repeated spaces.
    return " ".join(text.replace("\n", " ").split()).strip()


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


def levenshtein_distance(seq1: Iterable[str], seq2: Iterable[str]) -> int:
    a = list(seq1)
    b = list(seq2)

    if not a:
        return len(b)
    if not b:
        return len(a)

    previous_row = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current_row = [i]
        for j, cb in enumerate(b, start=1):
            insertion = previous_row[j] + 1
            deletion = current_row[j - 1] + 1
            substitution = previous_row[j - 1] + (0 if ca == cb else 1)
            current_row.append(min(insertion, deletion, substitution))
        previous_row = current_row

    return previous_row[-1]


def evaluate_pair(gt_text: str, pred_text: str) -> dict[str, float | int]:
    gt_chars = list(gt_text)
    pred_chars = list(pred_text)
    char_dist = levenshtein_distance(gt_chars, pred_chars)
    char_total = max(1, len(gt_chars))

    gt_words = gt_text.split()
    pred_words = pred_text.split()
    word_dist = levenshtein_distance(gt_words, pred_words)
    word_total = max(1, len(gt_words))

    return {
        "char_dist": char_dist,
        "char_total": char_total,
        "cer": char_dist / char_total,
        "word_dist": word_dist,
        "word_total": word_total,
        "wer": word_dist / word_total,
    }


def run_ocr(image_path: Path) -> str:
    with Image.open(image_path) as img:
        raw_text = pytesseract.image_to_string(img)
    return normalize_text(raw_text)


def main() -> None:
    args = parse_args()

    if args.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = args.tesseract_cmd

    selected_images = list_first_images(args.image_dir, args.limit)
    gt_map = load_ground_truth(args.gt_json)

    output_dir = args.output_dir
    texts_dir = output_dir / "texts"
    output_dir.mkdir(parents=True, exist_ok=True)
    texts_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    total_char_dist = 0
    total_char_count = 0
    total_word_dist = 0
    total_word_count = 0
    evaluated_count = 0

    for image_path in selected_images:
        pred_text = run_ocr(image_path)
        gt_text = gt_map.get(image_path.name)

        (texts_dir / f"{image_path.stem}.txt").write_text(pred_text + "\n", encoding="utf-8")

        row: dict[str, object] = {
            "image": image_path.name,
            "prediction": pred_text,
            "ground_truth": gt_text,
            "cer": None,
            "wer": None,
        }

        if gt_text is not None:
            metrics = evaluate_pair(gt_text, pred_text)
            row["cer"] = metrics["cer"]
            row["wer"] = metrics["wer"]
            total_char_dist += int(metrics["char_dist"])
            total_char_count += int(metrics["char_total"])
            total_word_dist += int(metrics["word_dist"])
            total_word_count += int(metrics["word_total"])
            evaluated_count += 1

        rows.append(row)

    csv_path = output_dir / "results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["image", "cer", "wer", "ground_truth", "prediction"],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "processed_images": len(selected_images),
        "evaluated_images": evaluated_count,
        "corpus_cer": (total_char_dist / total_char_count) if total_char_count else None,
        "corpus_wer": (total_word_dist / total_word_count) if total_word_count else None,
        "missing_ground_truth_images": [
            row["image"] for row in rows if row["ground_truth"] is None
        ],
        "output_files": {
            "results_csv": str(csv_path),
            "texts_dir": str(texts_dir),
        },
    }

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Processed: {summary['processed_images']} images")
    print(f"Evaluated: {summary['evaluated_images']} images")
    print(f"Corpus CER: {summary['corpus_cer']}")
    print(f"Corpus WER: {summary['corpus_wer']}")
    print(f"Saved CSV: {csv_path}")
    print(f"Saved summary: {summary_path}")


if __name__ == "__main__":
    try:
        main()
    except TesseractNotFoundError as exc:
        raise SystemExit(
            "Tesseract is not installed or not on PATH. Install Tesseract OCR and/or pass --tesseract-cmd."
        ) from exc
