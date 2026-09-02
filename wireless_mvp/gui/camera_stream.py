from __future__ import annotations

import sys
import threading
import time

import cv2
import numpy as np


def _camera_backend() -> int:
    # CAP_DSHOW opens faster and more reliably on Windows.
    return cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY


def _release_capture(cap: cv2.VideoCapture) -> None:
    try:
        cap.release()
    except cv2.error:
        pass


def find_camera_index(candidates: list[int] | None = None, timeout_per_candidate: float = 2.0) -> int | None:
    """
    Return the first camera index in *candidates* that actually produces a
    real (non-black) picture. Devices can shift indices between reboots/plug
    events (e.g. an external webcam bumping the integrated one), and some
    indices open successfully but only ever return black frames (IR cameras
    used for Windows Hello), so opening isn't enough - a live frame must be checked.
    """
    if candidates is None:
        candidates = [0, 1, 2, 3]

    backend = _camera_backend()
    for idx in candidates:
        try:
            cap = cv2.VideoCapture(idx, backend)
        except cv2.error:
            continue
        if not cap.isOpened():
            _release_capture(cap)
            continue

        deadline = time.monotonic() + timeout_per_candidate
        found = False
        try:
            while time.monotonic() < deadline:
                ok, frame = cap.read()
                if ok and frame is not None and frame.mean() > 5.0:
                    found = True
                    break
                time.sleep(0.1)
        except cv2.error:
            pass
        finally:
            _release_capture(cap)

        if found:
            return idx

    return None


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
        try:
            self._cap = cv2.VideoCapture(self._index, _camera_backend())
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)

            if not self._cap.isOpened():
                _release_capture(self._cap)
                self._cap = None
                raise RuntimeError(f"Could not open camera at index {self._index}.")
        except cv2.error as exc:
            if self._cap is not None:
                _release_capture(self._cap)
                self._cap = None
            raise RuntimeError(f"Could not open camera at index {self._index}.") from exc

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        assert self._cap is not None
        while self._running:
            try:
                ok, frame = self._cap.read()
            except cv2.error:
                with self._lock:
                    self._frame = None
                self._running = False
                break
            if ok:
                with self._lock:
                    self._frame = frame
            else:
                with self._lock:
                    self._frame = None
                time.sleep(0.03)

    def read(self) -> np.ndarray | None:
        """Return a copy of the most recently captured frame, or None if not ready."""
        with self._lock:
            return None if self._frame is None else self._frame.copy()

    @property
    def index(self) -> int:
        return self._index

    def is_running(self) -> bool:
        return self._running

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        if self._cap is not None:
            _release_capture(self._cap)
            self._cap = None

