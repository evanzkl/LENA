from __future__ import annotations

import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import cv2

from .camera_stream import CameraStream
from .camera_view import CameraView
from .languages import LANGUAGES, language_by_display_name
from .pipeline import TranslationPipeline
from .result_view import ResultView


class TranslatorApp(tk.Tk):
    def __init__(self, camera_index: int = 1) -> None:
        super().__init__()
        self.title("Handheld OCR Translator")
        self.geometry("1100x750")
        self.minsize(800, 600)

        self.source_lang_var = tk.StringVar(value=LANGUAGES[0].display_name)
        self.target_lang_var = tk.StringVar(value=LANGUAGES[1].display_name)

        self.pipeline = TranslationPipeline()
        self.camera = CameraStream(camera_index)

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        self.camera_view = CameraView(container, app=self)
        self.result_view = ResultView(container, app=self)
        for view in (self.camera_view, self.result_view):
            view.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._state = "camera"
        self.camera_view.lift()

        try:
            self.camera.start()
        except RuntimeError as exc:
            messagebox.showerror("Camera error", str(exc))

        self._preview_job = self.after(33, self._update_camera_preview)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # -- state transitions ---------------------------------------------

    def show_camera_state(self) -> None:
        self._state = "camera"
        self.result_view.lower()
        self.camera_view.lift()

    def show_result_state(self) -> None:
        self._state = "result"
        self.camera_view.lower()
        self.result_view.lift()

    def retake(self) -> None:
        self.show_camera_state()

    # -- camera preview loop ---------------------------------------------

    def _update_camera_preview(self) -> None:
        if self._state == "camera":
            frame = self.camera.read()
            if frame is not None:
                self.camera_view.display_frame(frame)
        self._preview_job = self.after(33, self._update_camera_preview)

    # -- language controls ---------------------------------------------

    def swap_languages(self) -> None:
        source = self.source_lang_var.get()
        target = self.target_lang_var.get()
        self.source_lang_var.set(target)
        self.target_lang_var.set(source)

    # -- capture / processing ---------------------------------------------

    def capture_and_process(self) -> None:
        frame = self.camera.read()
        if frame is None:
            messagebox.showwarning("No camera frame", "No frame is available from the camera yet.")
            return
        self._start_processing(frame)

    def process_uploaded_image(self, path: Path) -> None:
        image = cv2.imread(str(path))
        if image is None:
            messagebox.showerror("Invalid image", f"Could not read image file:\n{path}")
            return
        self._start_processing(image)

    def _start_processing(self, image) -> None:
        source_lang = language_by_display_name(self.source_lang_var.get())
        target_lang = language_by_display_name(self.target_lang_var.get())

        self.camera_view.set_controls_enabled(False)
        self.camera_view.set_status("Processing...")

        threading.Thread(
            target=self._process_worker,
            args=(image, source_lang.ocr_code, target_lang.translate_code),
            daemon=True,
        ).start()

    def _process_worker(self, frame, ocr_lang: str, translate_lang: str) -> None:
        try:
            result_image, accuracy = self.pipeline.process(frame, ocr_lang, translate_lang)
            error = None
        except Exception as exc:  # noqa: BLE001 - surface any pipeline failure to the user
            result_image, accuracy, error = None, None, str(exc)

        self.after(0, self._on_process_done, result_image, accuracy, error)

    def _on_process_done(self, result_image, accuracy, error: str | None) -> None:
        self.camera_view.set_controls_enabled(True)
        self.camera_view.set_status("")

        if error is not None:
            messagebox.showerror("Processing failed", error)
            return

        self.result_view.display_result(result_image, accuracy)
        self.show_result_state()

    # -- shutdown ---------------------------------------------

    def _on_close(self) -> None:
        if self._preview_job is not None:
            self.after_cancel(self._preview_job)
        self.camera.stop()
        self.destroy()


def main() -> None:
    camera_index = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    app = TranslatorApp(camera_index=camera_index)
    app.mainloop()


if __name__ == "__main__":
    main()
