from __future__ import annotations

import sys
import threading
import tkinter as tk
from typing import Any
from pathlib import Path
from tkinter import messagebox, ttk

import cv2

from .camera_stream import CameraStream, find_camera_index
from .camera_view import CameraView
from gpio_button import GpioCaptureTrigger
from .languages import LANGUAGES, language_by_display_name
from .pipeline import TranslationPipeline
from .result_view import ResultView


# Layout/fonts below are sized for this reference resolution; ui_scale adapts them to the real screen.
_REFERENCE_SIZE = (1100, 750)


class TranslatorApp(tk.Tk):
    def __init__(self, camera_index: int | None = None) -> None:
        super().__init__()
        self.title("Handheld OCR Translator")
        self.geometry("1100x750")
        self.minsize(800, 600)
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", lambda _event: self.attributes("-fullscreen", False))
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.ui_scale = max(0.5, min(1.3, min(screen_w / _REFERENCE_SIZE[0], screen_h / _REFERENCE_SIZE[1])))
        self._configure_styles()

        self.source_lang_var = tk.StringVar(value=LANGUAGES[0].display_name)
        self.target_lang_var = tk.StringVar(value=LANGUAGES[1].display_name)

        self.pipeline = TranslationPipeline()
        self.camera: CameraStream | None = None
        self._processing = False
        self._preferred_camera_index = camera_index
        self._camera_status = "detected"
        self._missing_frame_count = 0
        self._detected_frame_count = 0
        self._recovery_job: Any = None
        self._reconnect_job: Any = None
        self._reconnect_in_progress = False
        self._gpio_capture = GpioCaptureTrigger(on_press=self._on_gpio_capture_request)

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        self.camera_view = CameraView(container, app=self)
        self.result_view = ResultView(container, app=self)
        for view in (self.camera_view, self.result_view):
            view.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._state = "camera"
        self.camera_view.lift()
        self._gpio_capture.start()

        # Connect to the camera in the background so the window appears immediately
        # instead of freezing while candidate camera indices are probed.
        threading.Thread(target=self._connect_camera_worker, args=(camera_index,), daemon=True).start()

        self._preview_job = self.after(33, self._update_camera_preview)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def scaled(self, value: int) -> int:
        return max(1, round(value * self.ui_scale))

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        for theme_name in ("vista", "xpnative", "clam"):
            try:
                style.theme_use(theme_name)
                break
            except tk.TclError:
                continue
        style.configure(
            "Pill.TButton",
            font=("Segoe UI", self.scaled(11), "bold"),
            padding=(self.scaled(12), self.scaled(7)),
        )
        style.map(
            "Pill.TButton",
            foreground=[("disabled", "#888888")],
        )
        style.configure(
            "HUD.TCombobox",
            fieldbackground="#F9F9F9",
            background="#F9F9F9",
            foreground="#222222",
            borderwidth=0,
            arrowsize=self.scaled(14),
            padding=(self.scaled(8), self.scaled(6)),
        )
        style.map(
            "HUD.TCombobox",
            fieldbackground=[("readonly", "#F9F9F9")],
            foreground=[("readonly", "#222222")],
            selectbackground=[("readonly", "#F9F9F9")],
            selectforeground=[("readonly", "#222222")],
        )

    def _connect_camera_worker(self, camera_index: int | None) -> None:
        try:
            if camera_index is None:
                camera_index = find_camera_index(candidates=self._build_camera_candidates())
                if camera_index is None:
                    raise RuntimeError(
                        "No working camera was found. Connect a camera and restart the app."
                    )
            camera = CameraStream(camera_index)
            camera.start()
        except RuntimeError as exc:
            self.after(0, self._on_camera_error, str(exc))
            return
        self.after(0, self._on_camera_ready, camera, camera_index)

    def _on_camera_ready(self, camera: CameraStream, camera_index: int) -> None:
        if self.camera is not None and self.camera is not camera:
            self.camera.stop()
        self.camera = camera
        self._preferred_camera_index = camera_index

    def _build_camera_candidates(self) -> list[int]:
        candidates: list[int] = []
        if self._preferred_camera_index is not None:
            candidates.append(self._preferred_camera_index)
        if self.camera is not None:
            candidates.append(self.camera.index)
        candidates.extend([0, 1, 2, 3, 4, 5])

        deduped: list[int] = []
        for idx in candidates:
            if idx not in deduped:
                deduped.append(idx)
        return deduped

    def _schedule_reconnect_probe(self, delay_ms: int = 1200) -> None:
        if self._reconnect_job is not None or self._camera_status != "missing":
            return
        self._reconnect_job = self.after(delay_ms, self._start_reconnect_probe)

    def _start_reconnect_probe(self) -> None:
        self._reconnect_job = None
        if self._camera_status != "missing" or self._reconnect_in_progress:
            return
        self._reconnect_in_progress = True
        threading.Thread(target=self._reconnect_probe_worker, daemon=True).start()

    def _cancel_reconnect_probe(self) -> None:
        if self._reconnect_job is not None:
            self.after_cancel(self._reconnect_job)
            self._reconnect_job = None

    def _reconnect_probe_worker(self) -> None:
        camera = None
        camera_index = None
        try:
            found_index = find_camera_index(candidates=self._build_camera_candidates(), timeout_per_candidate=0.8)
            if found_index is not None:
                camera = CameraStream(found_index)
                camera.start()
                camera_index = found_index
        except RuntimeError:
            camera = None
            camera_index = None
        self.after(0, self._on_reconnect_probe_done, camera, camera_index)

    def _on_reconnect_probe_done(self, camera: CameraStream | None, camera_index: int | None) -> None:
        self._reconnect_in_progress = False
        if self._camera_status != "missing":
            if camera is not None:
                camera.stop()
            return
        if camera is not None and camera_index is not None:
            self._on_camera_ready(camera, camera_index)
            return
        self._schedule_reconnect_probe()

    def _on_camera_error(self, message: str) -> None:
        messagebox.showerror("Camera error", message)

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

    def _can_capture(self) -> bool:
        return self._state == "camera" and self._camera_status == "detected" and not self._processing

    def _on_gpio_capture_request(self) -> None:
        self.after(0, self._capture_from_gpio)

    def _capture_from_gpio(self) -> None:
        if self._state == "camera":
            self.camera_view.flash_center_message("Button Detected")
        if not self._can_capture():
            return
        self.capture_and_process()

    # -- camera preview loop ---------------------------------------------

    def _update_camera_preview(self) -> None:
        self._gpio_capture.poll()
        if self._state == "camera":
            frame = self.camera.read() if self.camera is not None else None
            frame_invalid = frame is None or self._is_black_frame(frame)

            if frame_invalid:
                self._detected_frame_count = 0
                self._missing_frame_count += 1
                if self._missing_frame_count >= 8:
                    self._set_camera_missing()
            else:
                self._missing_frame_count = 0
                self._detected_frame_count += 1
                self.camera_view.display_frame(frame)

                if self._camera_status == "missing" and self._detected_frame_count >= 8:
                    self._set_camera_recovering()

        self._preview_job = self.after(33, self._update_camera_preview)

    def _is_black_frame(self, frame) -> bool:
        return float(frame.mean()) <= 5.0

    def _set_camera_missing(self) -> None:
        if self._camera_status == "missing":
            return
        if self._recovery_job is not None:
            self.after_cancel(self._recovery_job)
            self._recovery_job = None
        self._camera_status = "missing"
        self.camera_view.show_status_screen(
            "Image Not Detected...",
            text_color=(210, 32, 32),
            subtext="Please Check Camera Connection",
            subtext_color=(245, 245, 245),
        )
        self.camera_view.set_capture_enabled(False)
        self._schedule_reconnect_probe(delay_ms=300)

    def _set_camera_recovering(self) -> None:
        if self._camera_status != "missing":
            return
        self._cancel_reconnect_probe()
        self._camera_status = "recovering"
        self.camera_view.show_status_screen("Image Detected ✔", text_color=(28, 153, 72))
        self.camera_view.set_capture_enabled(False)
        self._recovery_job = self.after(900, self._finish_camera_recovery)

    def _finish_camera_recovery(self) -> None:
        self._recovery_job = None
        if self._camera_status != "recovering":
            return
        self._camera_status = "detected"
        self.camera_view.clear_status_screen()
        self.camera_view.set_capture_enabled(True)

    # -- language controls ---------------------------------------------

    def swap_languages(self) -> None:
        source = self.source_lang_var.get()
        target = self.target_lang_var.get()
        self.source_lang_var.set(target)
        self.target_lang_var.set(source)

    # -- capture / processing ---------------------------------------------

    def capture_and_process(self) -> None:
        if not self._can_capture():
            return
        frame = self.camera.read() if self.camera is not None else None
        if frame is None:
            messagebox.showwarning("No camera frame", "No frame is available from the camera yet.")
            return
        self._start_processing(frame)

    def process_uploaded_image(self, path: Path) -> None:
        image = cv2.imread(str(path))
        if image is None:
            messagebox.showerror("Invalid image", f"Could not read image file:\n{path}")
            return
        # Show the uploaded image in place of the live feed before freezing into the processing state.
        self.camera_view.show_static_image(image)
        self.after(150, lambda: self._start_processing(image))

    def _start_processing(self, image) -> None:
        self._processing = True
        source_lang = language_by_display_name(self.source_lang_var.get())
        target_lang = language_by_display_name(self.target_lang_var.get())

        self.camera_view.set_controls_enabled(False)
        self.camera_view.freeze_and_show_processing()

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
        self._processing = False
        self.camera_view.set_controls_enabled(True)
        self.camera_view.unfreeze()

        if error is not None:
            messagebox.showerror("Processing failed", error)
            return

        self.result_view.display_result(result_image, accuracy)
        self.show_result_state()

    # -- shutdown ---------------------------------------------

    def _on_close(self) -> None:
        if self._preview_job is not None:
            self.after_cancel(self._preview_job)
        if self._recovery_job is not None:
            self.after_cancel(self._recovery_job)
        self._cancel_reconnect_probe()
        if self.camera is not None:
            self.camera.stop()
        self._gpio_capture.stop()
        self.destroy()


def main() -> None:
    camera_index = int(sys.argv[1]) if len(sys.argv) > 1 else None
    app = TranslatorApp(camera_index=camera_index)
    app.mainloop()


if __name__ == "__main__":
    main()
