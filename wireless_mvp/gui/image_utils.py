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
    """Load eye icons when available, otherwise render them with Pillow."""
    icon_name = "hide_ui.png" if hidden else "show_ui.png"
    icon_path = _ICON_ASSETS_DIR / icon_name
    if icon_path.exists():
        with Image.open(icon_path) as source:
            image = source.convert("RGBA")
    else:
        image = Image.new("RGBA", (size, size), background)
        draw = ImageDraw.Draw(image)
        margin = max(4, size // 6)
        eye_box = (margin, size // 3, size - margin, size - size // 3)
        draw.ellipse(eye_box, outline=stroke, width=max(2, size // 14))
        draw.ellipse((size // 2 - size // 10, size // 2 - size // 10,
                      size // 2 + size // 10, size // 2 + size // 10), fill=fill)
        if hidden:
            draw.line((margin, size - margin, size - margin, margin), fill=stroke, width=max(2, size // 14))
        return ImageTk.PhotoImage(image, master=master)

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
    overlay_subtext: str | None = None,
    overlay_subtext_color: tuple[int, int, int] = (255, 255, 255),
) -> ImageTk.PhotoImage | None:
    """Convert a BGR frame into a Tk PhotoImage scaled to fit within box_w x box_h.

    If *overlay_text* is given, it is drawn centered directly on the image
    (no background box) so it stays legible over whatever the frame shows.
    If *overlay_subtext* is also given, it is rendered as a smaller second line.
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
        title_font_size = max(18, new_h // 15)
        title_font = _load_overlay_font(title_font_size)
        title_left, title_top, title_right, title_bottom = draw.textbbox((0, 0), overlay_text, font=title_font)
        title_w = title_right - title_left
        title_h = title_bottom - title_top

        if overlay_subtext:
            subtitle_font = _load_overlay_font(max(12, int(title_font_size * 0.55)))
            sub_left, sub_top, sub_right, sub_bottom = draw.textbbox((0, 0), overlay_subtext, font=subtitle_font)
            sub_w = sub_right - sub_left
            sub_h = sub_bottom - sub_top
            gap = max(6, int(title_font_size * 0.28))
            total_h = title_h + gap + sub_h
            title_y = (new_h - total_h) / 2 - title_top
            sub_y = title_y + title_h + gap - sub_top
            title_x = (new_w - title_w) / 2 - title_left
            sub_x = (new_w - sub_w) / 2 - sub_left

            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                draw.text((title_x + dx, title_y + dy), overlay_text, font=title_font, fill=(0, 0, 0))
                draw.text((sub_x + dx, sub_y + dy), overlay_subtext, font=subtitle_font, fill=(0, 0, 0))
            draw.text((title_x, title_y), overlay_text, font=title_font, fill=overlay_text_color)
            draw.text((sub_x, sub_y), overlay_subtext, font=subtitle_font, fill=overlay_subtext_color)
        else:
            x = (new_w - title_w) / 2 - title_left
            y = (new_h - title_h) / 2 - title_top
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                draw.text((x + dx, y + dy), overlay_text, font=title_font, fill=(0, 0, 0))
            draw.text((x, y), overlay_text, font=title_font, fill=overlay_text_color)

    return ImageTk.PhotoImage(image)


def darken_frame(frame_bgr: np.ndarray, factor: float = 0.35) -> np.ndarray:
    """Return a copy of *frame_bgr* scaled toward black (factor 0=black, 1=unchanged)."""
    return (frame_bgr.astype(np.float32) * factor).astype(np.uint8)


