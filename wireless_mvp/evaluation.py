from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any

from config import ENGINES
from metrics import evaluate_pair
from OCR.google_vision import run_google_vision_ocr


def evaluate_engine(
    engine_name: str,
    image_paths: list[Path],
    gt_map: dict[str, str],
    output_dir: Path,
    vision_engine: Any = None,
) -> dict[str, object]:
    engine_output_dir = output_dir / engine_name
    texts_dir = engine_output_dir / "texts"
    engine_output_dir.mkdir(parents=True, exist_ok=True)
    texts_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    total_char_dist = 0
    total_char_count = 0
    total_word_dist = 0
    total_word_count = 0
    evaluated_count = 0
    total_time_seconds = 0.0

    for image_path in image_paths:
        start = time.perf_counter()
        if engine_name != "google_vision":
            raise ValueError(f"Unknown engine: {engine_name}")
        if vision_engine is None:
            raise RuntimeError("Google Cloud Vision client was not initialized")
        regions = run_google_vision_ocr(vision_engine, image_path)
        pred_text = " ".join(region.text for region in regions)

        processing_time = time.perf_counter() - start
        total_time_seconds += processing_time

        gt_text = gt_map.get(image_path.name)
        (texts_dir / f"{image_path.stem}.txt").write_text(pred_text + "\n", encoding="utf-8")

        row: dict[str, object] = {
            "image": image_path.name,
            "processing_time_seconds": processing_time,
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

    csv_path = engine_output_dir / "results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "image",
                "processing_time_seconds",
                "cer",
                "wer",
                "ground_truth",
                "prediction",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "engine": engine_name,
        "processed_images": len(image_paths),
        "evaluated_images": evaluated_count,
        "corpus_cer": (total_char_dist / total_char_count) if total_char_count else None,
        "corpus_wer": (total_word_dist / total_word_count) if total_word_count else None,
        "total_processing_time_seconds": total_time_seconds,
        "avg_processing_time_seconds": (
            total_time_seconds / len(image_paths) if image_paths else None
        ),
        "missing_ground_truth_images": [
            row["image"] for row in rows if row["ground_truth"] is None
        ],
        "output_files": {
            "results_csv": str(csv_path),
            "texts_dir": str(texts_dir),
        },
    }

    summary_path = engine_output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return summary


def evaluate_all_engines(
    image_paths: list[Path],
    gt_map: dict[str, str],
    output_dir: Path,
    vision_engine: Any,
) -> dict[str, dict[str, object]]:
    all_summaries: dict[str, dict[str, object]] = {}
    for engine_name in ENGINES:
        summary = evaluate_engine(
            engine_name=engine_name,
            image_paths=image_paths,
            gt_map=gt_map,
            output_dir=output_dir,
            vision_engine=vision_engine,
        )
        all_summaries[engine_name] = summary
    return all_summaries


def save_combined_summary(output_dir: Path, all_summaries: dict[str, dict[str, object]]) -> Path:
    combined_summary_path = output_dir / "summary_all_engines.json"
    combined_summary_path.write_text(json.dumps(all_summaries, indent=2), encoding="utf-8")
    return combined_summary_path
