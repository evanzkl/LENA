from __future__ import annotations

import sys
from pathlib import Path

# Ensure the laptop_mvp directory is on the path when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gui.app import main

if __name__ == "__main__":
    main()

