from __future__ import annotations

import sys
from pathlib import Path

# Ensure the laptop_mvp directory is on the path when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from OCR.paddle_ocr import build_paddle_engine, run_paddle_ocr
from translation.translator import DEFAULT_PROJECT_ID, translate_texts
from blur_and_overlay.processor import process_image

TEST_IMAGE = Path(r"C:\Projects\OCR\icdar2013\Challenge2_Test_Task12_Images\img_1.jpg")
OUTPUT_DIR = Path(__file__).resolve().parent / "output" / "translated"


def main() -> None:
    print(f"Image : {TEST_IMAGE}")

    print("\n[1/3] Initialising PaddleOCR engine...")
    engine = build_paddle_engine()

    print("[2/3] Running OCR...")
    regions = run_paddle_ocr(engine, TEST_IMAGE)
    print(f"  Detected {len(regions)} text region(s).")
    for r in regions:
        print(f"  [{r.confidence:.2f}] {r.text!r}")

    print(f"\n[3/3] Translating to Spanish (Google Cloud, project={DEFAULT_PROJECT_ID})...")
    translated_texts = translate_texts([r.text for r in regions], target_lang="es")
    for original, spanish in zip(regions, translated_texts):
        print(f"  {original.text!r}  ->  {spanish!r}")

    output_path = OUTPUT_DIR / f"translated_{TEST_IMAGE.name}"
    print(f"\nRendering output -> {output_path}")
    process_image(
        image_path=TEST_IMAGE,
        polygons=[r.polygon for r in regions],
        translated_texts=translated_texts,
        output_path=output_path,
    )
    print("Done.")


if __name__ == "__main__":
    main()
