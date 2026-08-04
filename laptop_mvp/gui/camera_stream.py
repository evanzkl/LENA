from __future__ import annotations

import sys
import threading

import cv2
import numpy as np


class CameraStream:
    """Continuously reads frames from a connected camera on a background thread."""

    def __init__(self, index: int = 0, width: int = 1280, height: int = 720) -> None:
        self._index = index
        self._width = width
        self._height = height
        self._cap: cv2.VideoCapture | None = None
        self._lock = threading.Lock()
        self._frame: np.ndarray | None = None
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        # CAP_DSHOW opens faster and more reliably on Windows.
        backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
        self._cap = cv2.VideoCapture(self._index, backend)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)

        if not self._cap.isOpened():
            raise RuntimeError(f"Could not open camera at index {self._index}.")

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        assert self._cap is not None
        while self._running:
            ok, frame = self._cap.read()
            if ok:
                with self._lock:
                    self._frame = frame

    def read(self) -> np.ndarray | None:
        """Return a copy of the most recently captured frame, or None if not ready."""
        with self._lock:
            return None if self._frame is None else self._frame.copy()

    def is_running(self) -> bool:
        return self._running

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        if self._cap is not None:
            self._cap.release()
            self._cap = None
