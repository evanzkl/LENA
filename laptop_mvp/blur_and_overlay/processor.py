from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

# Type alias for a 4-point polygon [[x1,y1],[x2,y1],[x2,y2],[x1,y2]]
Polygon = list[list[float]]

_FONT = cv2.FONT_HERSHEY_SIMPLEX
_MAX_LINES = 4
_LINE_SPACING = 1.3  # multiplier applied to line height for vertical gap
_MIN_FONT_SCALE = 0.15
_MAX_FONT_SCALE = 4.0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _bounding_rect(polygon: Polygon) -> tuple[int, int, int, int]:
    """Return axis-aligned (x, y, w, h) bounding rectangle for a polygon."""
    pts = np.array(polygon, dtype=np.float32)
    x, y, w, h = cv2.boundingRect(pts)
    return int(x), int(y), int(w), int(h)


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _wrap_into_n_lines(words: list[str], n: int) -> list[str]:
    """Split *words* as evenly as possible across *n* lines."""
    if n <= 1 or len(words) <= 1:
        return [" ".join(words)]
    per_line = math.ceil(len(words) / n)
    return [
        " ".join(words[i : i + per_line])
        for i in range(0, len(words), per_line)
    ]


def _fit_text_to_box(
    text: str,
    box_w: int,
    box_h: int,
    thickness: int = 1,
    max_lines: int = _MAX_LINES,
) -> tuple[list[str], float]:
    """
    Find the line-wrapping and font scale that best fill (box_w, box_h)
    with *text*, trying an increasing number of lines and picking whichever
    combination yields the largest font scale (i.e. best fill).
    """
    words = text.split()
    if not words:
        return [], 1.0

    avail_w = max(box_w, 1)
    avail_h = max(box_h, 1)

    best_scale = 0.0
    best_lines = [text]

    for n in range(1, min(max_lines, len(words)) + 1):
        lines = _wrap_into_n_lines(words, n)

        max_line_w = 0
        max_line_h = 0
        for line in lines:
            (line_w, line_h), baseline = cv2.getTextSize(line, _FONT, 1.0, thickness)
            max_line_w = max(max_line_w, line_w)
            max_line_h = max(max_line_h, line_h + baseline)

        total_h = max_line_h * len(lines) * _LINE_SPACING
        scale_w = avail_w / max_line_w if max_line_w > 0 else _MAX_FONT_SCALE
        scale_h = avail_h / total_h if total_h > 0 else _MAX_FONT_SCALE
        font_scale = float(np.clip(min(scale_w, scale_h), _MIN_FONT_SCALE, _MAX_FONT_SCALE))

        if font_scale > best_scale:
            best_scale = font_scale
            best_lines = lines

    return best_lines, best_scale


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def blur_region(
    image: np.ndarray,
    polygon: Polygon,
    blur_kernel: int = 35,
) -> np.ndarray:
    """
    Gaussian-blur the rectangular region that encloses *polygon* in *image*.
    The image is modified in-place and returned.
    """
    ih, iw = image.shape[:2]
    x, y, w, h = _bounding_rect(polygon)

    x1 = _clamp(x, 0, iw)
    y1 = _clamp(y, 0, ih)
    x2 = _clamp(x + w, 0, iw)
    y2 = _clamp(y + h, 0, ih)

    if x2 <= x1 or y2 <= y1:
        return image  # degenerate box – skip

    # Kernel size must be positive and odd
    k = max(3, blur_kernel | 1)
    roi = image[y1:y2, x1:x2]
    image[y1:y2, x1:x2] = cv2.GaussianBlur(roi, (k, k), 0)
    return image


def overlay_text(
    image: np.ndarray,
    polygon: Polygon,
    text: str,
    text_color: tuple[int, int, int] = (0, 0, 0),
    bg_color: tuple[int, int, int] | None = (255, 255, 200),
    padding: int = 2,
) -> np.ndarray:
    """
    Render *text* inside the bounding box of *polygon*, wrapping onto
    multiple lines and scaling the font so the text fills as much of the
    box (width and height) as possible.
    Optionally draws a semi-transparent background rectangle first.
    The image is modified in-place and returned.
    """
    ih, iw = image.shape[:2]
    x, y, w, h = _bounding_rect(polygon)

    x1 = _clamp(x, 0, iw)
    y1 = _clamp(y, 0, ih)
    x2 = _clamp(x + w, 0, iw)
    y2 = _clamp(y + h, 0, ih)

    if x2 <= x1 or y2 <= y1 or not text.strip():
        return image

    box_w = x2 - x1
    box_h = y2 - y1
    avail_w = max(box_w - 2 * padding, 1)
    avail_h = max(box_h - 2 * padding, 1)

    base_thickness = 1
    lines, font_scale = _fit_text_to_box(text, avail_w, avail_h, base_thickness)
    if not lines:
        return image

    # Scale stroke thickness with font size for readability
    font_thickness = max(1, round(font_scale * 1.6))

    # Recompute exact line sizes at the chosen font scale
    line_sizes = [cv2.getTextSize(line, _FONT, font_scale, font_thickness) for line in lines]
    line_heights = [line_h + baseline for (_, line_h), baseline in line_sizes]
    gaps = [int(lh * (_LINE_SPACING - 1)) for lh in line_heights]
    total_text_h = sum(line_heights) + sum(gaps[:-1])

    # Draw optional background rectangle
    if bg_color is not None:
        overlay = image.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), bg_color, thickness=-1)
        cv2.addWeighted(overlay, 0.6, image, 0.4, 0, image)

    # Vertically centre the whole text block inside the box
    cursor_y = y1 + (box_h - total_text_h) // 2

    for line, ((line_w, line_h), baseline) in zip(lines, line_sizes):
        line_full_h = line_h + baseline
        text_x = x1 + (box_w - line_w) // 2  # centre each line horizontally
        text_y = cursor_y + line_h
        cv2.putText(
            image,
            line,
            (text_x, text_y),
            _FONT,
            font_scale,
            text_color,
            font_thickness,
            cv2.LINE_AA,
        )
        cursor_y += int(line_full_h * _LINE_SPACING)

    return image


def process_image(
    image_path: Path,
    polygons: list[Polygon],
    translated_texts: list[str],
    output_path: Path,
    blur_kernel: int = 35,
) -> np.ndarray:
    """
    Full pipeline for a single image:
      1. Blur each detected text region.
      2. Overlay the corresponding translated text.
      3. Save the result to *output_path*.

    Returns the processed image as a NumPy array (BGR).
    """
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Cannot load image: {image_path}")

    for polygon, translated in zip(polygons, translated_texts):
        blur_region(image, polygon, blur_kernel=blur_kernel)
        overlay_text(image, polygon, translated)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), image)

    return image
