from __future__ import annotations

import re
from pathlib import Path


def numeric_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"(\d+)", path.stem)
    number = int(match.group(1)) if match else 10**9
    return number, path.name.lower()


def normalize_text(text: str) -> str:
    # Keep evaluation stable by normalizing line breaks and repeated spaces.
    return " ".join(text.replace("\n", " ").split()).strip()
