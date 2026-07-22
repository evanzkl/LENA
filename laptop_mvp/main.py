from __future__ import annotations

from pytesseract import TesseractNotFoundError
from cli import parse_args
from config import ENGINES
from dataset import list_first_images, load_ground_truth
from evaluation import evaluate_all_engines, save_combined_summary
from ocr_engines import (
    build_easyocr_reader,
    build_paddleocr_engine,
    configure_tesseract,
    ensure_engine_dependencies,
)


def main() -> None:
    args = parse_args()
    configure_tesseract(args.tesseract_cmd)

    selected_images = list_first_images(args.image_dir, args.limit)
    gt_map = load_ground_truth(args.gt_json)
    ensure_engine_dependencies()

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    easy_reader = build_easyocr_reader()
    paddle_engine = build_paddleocr_engine()

    all_summaries = evaluate_all_engines(
        image_paths=selected_images,
        gt_map=gt_map,
        output_dir=output_dir,
        psm=args.psm,
        easy_reader=easy_reader,
        paddle_engine=paddle_engine,
    )
    combined_summary_path = save_combined_summary(output_dir, all_summaries)

    print(f"Processed first {len(selected_images)} images from: {args.image_dir}")
    for engine_name in ENGINES:
        summary = all_summaries[engine_name]
        print(
            f"[{engine_name}] CER={summary['corpus_cer']} WER={summary['corpus_wer']} "
            f"TotalTime={summary['total_processing_time_seconds']:.3f}s"
        )
    print(f"Saved combined summary: {combined_summary_path}")


if __name__ == "__main__":
    try:
        main()
    except (TesseractNotFoundError, ImportError) as exc:
        raise SystemExit(
            "Missing OCR dependency. Ensure Tesseract is installed and easyocr/paddleocr are in the environment."
        ) from exc
