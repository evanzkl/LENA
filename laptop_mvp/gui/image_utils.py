from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTk


_ICON_ASSETS_DIR = Path(__file__).resolve().parent / "assets"


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
    fill: str = "#FFFFFF",
    stroke: str = "#FFFFFF",
    background: str = "#243450",
) -> ImageTk.PhotoImage:
    """Load user-provided eye/eye-off icons and render them as circular high-quality badges."""
    icon_name = "hide_ui.png" if hidden else "show_ui.png"
    icon_path = _ICON_ASSETS_DIR / icon_name
    with Image.open(icon_path) as source:
        image = source.convert("RGBA")

    side = min(image.width, image.height)
    left = (image.width - side) // 2
    top = (image.height - side) // 2
    image = image.crop((left, top, left + side, top + side))

    # Keep the original art while forcing circular edges so the button appears round.
    mask = Image.new("L", (side, side), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, side - 1, side - 1), fill=255)
    image.putalpha(mask)

    image = image.resize((size, size), Image.LANCZOS)
    return ImageTk.PhotoImage(image, master=master)


def frame_to_photo(
    frame_bgr: np.ndarray,
    box_w: int,
    box_h: int,
    overlay_text: str | None = None,
    overlay_text_color: tuple[int, int, int] = (255, 255, 255),
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
        draw.text((x, y), overlay_text, font=font, fill=overlay_text_color)

    return ImageTk.PhotoImage(image)


def darken_frame(frame_bgr: np.ndarray, factor: float = 0.35) -> np.ndarray:
    """Return a copy of *frame_bgr* scaled toward black (factor 0=black, 1=unchanged)."""
    return (frame_bgr.astype(np.float32) * factor).astype(np.uint8)


