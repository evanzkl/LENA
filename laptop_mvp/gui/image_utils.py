from __future__ import annotations

from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTk


@lru_cache(maxsize=32)
def _load_overlay_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for font_path in ("arial.ttf", "Arial.ttf", "C:/Windows/Fonts/arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(font_path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def create_eye_icon(
    master,
    size: int = 34,
    hidden: bool = False,
    fill: str = "#E8EEF8",
    stroke: str = "#E8EEF8",
    background: str = "#1F3651",
) -> ImageTk.PhotoImage:
    """Create a small font-independent eye icon for the UI toggle button."""
    image = Image.new("RGBA", (size, size), background)
    draw = ImageDraw.Draw(image)

    left = size * 0.14
    top = size * 0.30
    right = size * 0.86
    bottom = size * 0.70
    center_x = size / 2
    center_y = size / 2
    pupil_r = max(1, int(size * 0.10))

    draw.arc((left, top, right, bottom), start=0, end=360, fill=stroke, width=max(1, size // 12))
    draw.ellipse((center_x - pupil_r, center_y - pupil_r, center_x + pupil_r, center_y + pupil_r), fill=fill)
    draw.line((left - 1, center_y, right + 1, center_y), fill=stroke, width=max(1, size // 15))

    if hidden:
        draw.line((size * 0.22, size * 0.78, size * 0.78, size * 0.22), fill=stroke, width=max(2, size // 10))

    return ImageTk.PhotoImage(image, master=master)


def frame_to_photo(
    frame_bgr: np.ndarray,
    box_w: int,
    box_h: int,
    overlay_text: str | None = None,
) -> ImageTk.PhotoImage | None:
    """Convert a BGR frame into a Tk PhotoImage scaled to fit within box_w x box_h.

    If *overlay_text* is given, it is drawn centered directly on the image
    (no background box) so it stays legible over whatever the frame shows.
    """
    if frame_bgr is None or box_w <= 1 or box_h <= 1:
        return None

    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(frame_rgb)

    src_w, src_h = image.size
    scale = min(box_w / src_w, box_h / src_h)
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))
    image = image.resize((new_w, new_h), Image.LANCZOS)

    if overlay_text:
        draw = ImageDraw.Draw(image)
        font = _load_overlay_font(max(18, new_h // 15))
        left, top, right, bottom = draw.textbbox((0, 0), overlay_text, font=font)
        text_w, text_h = right - left, bottom - top
        x = (new_w - text_w) / 2 - left
        y = (new_h - text_h) / 2 - top
        # Dark shadow offset in every direction keeps the text legible on any background.
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            draw.text((x + dx, y + dy), overlay_text, font=font, fill=(0, 0, 0))
        draw.text((x, y), overlay_text, font=font, fill=(255, 255, 255))

    return ImageTk.PhotoImage(image)


def darken_frame(frame_bgr: np.ndarray, factor: float = 0.35) -> np.ndarray:
    """Return a copy of *frame_bgr* scaled toward black (factor 0=black, 1=unchanged)."""
    return (frame_bgr.astype(np.float32) * factor).astype(np.uint8)


