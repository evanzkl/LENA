from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageTk


def frame_to_photo(frame_bgr: np.ndarray, box_w: int, box_h: int) -> ImageTk.PhotoImage | None:
    """Convert a BGR frame into a Tk PhotoImage scaled to fit within box_w x box_h."""
    if frame_bgr is None or box_w <= 1 or box_h <= 1:
        return None

    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(frame_rgb)

    src_w, src_h = image.size
    scale = min(box_w / src_w, box_h / src_h)
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))
    image = image.resize((new_w, new_h), Image.LANCZOS)

    return ImageTk.PhotoImage(image)
