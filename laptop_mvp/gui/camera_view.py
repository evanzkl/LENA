from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

import numpy as np

from .image_utils import create_eye_icon, darken_frame, frame_to_photo
from .languages import LANGUAGE_NAMES


class CameraView(ttk.Frame):
    """Initial state: live camera preview with language pickers and capture/upload controls."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent)
        self.app = app
        self._ui_visible = True
        self._current_photo = None
        self._last_frame = None
        self._frozen = False
        self._show_live = True
        self._status_overlay: tuple[str, tuple[int, int, int]] | None = None
        self._eye_icon = create_eye_icon(self, size=44, hidden=False)
        self._eye_off_icon = create_eye_icon(self, size=44, hidden=True)

        self.video_label = ttk.Label(self, background="black")
        self.video_label.pack(side="top", fill="both", expand=True)
        self.video_label.bind("<Configure>", lambda _event: self._redraw())
        self.bind("<Configure>", lambda _event: self._layout_controls())

        self.hide_show_btn = tk.Button(
            self,
            image=self._eye_off_icon,
            command=self._toggle_ui,
            relief="flat",
            bd=0,
            borderwidth=0,
            padx=0,
            pady=0,
            highlightthickness=0,
            takefocus=False,
            overrelief="flat",
        )
        self.hide_show_btn.place(x=18, y=18, width=44, height=44, anchor="nw")

        self.source_combo = ttk.Combobox(
            self,
            textvariable=app.source_lang_var,
            values=LANGUAGE_NAMES,
            state="readonly",
            style="HUD.TCombobox",
        )

        self.swap_btn = ttk.Button(
            self,
            text="<-> Swap",
            command=app.swap_languages,
            style="Pill.TButton",
        )

        self.target_combo = ttk.Combobox(
            self,
            textvariable=app.target_lang_var,
            values=LANGUAGE_NAMES,
            state="readonly",
            style="HUD.TCombobox",
        )

        self.upload_btn = ttk.Button(
            self,
            text="Upload Image",
            command=self._on_upload_image,
            style="Pill.TButton",
        )

        self.capture_btn = ttk.Button(
            self,
            text="Capture",
            command=app.capture_and_process,
            style="Pill.TButton",
        )

        # Everything in the top row except the eye toggle itself.
        self._toggleable_widgets = [
            self.source_combo,
            self.swap_btn,
            self.target_combo,
            self.upload_btn,
            self.capture_btn,
        ]
        self._layout_controls()

    def _toggle_ui(self) -> None:
        self._ui_visible = not self._ui_visible
        if self._ui_visible:
            self._layout_controls()
            self.hide_show_btn.config(image=self._eye_off_icon)
        else:
            for widget in self._toggleable_widgets:
                widget.place_forget()
            self.hide_show_btn.config(image=self._eye_icon)

    def set_controls_enabled(self, enabled: bool) -> None:
        state = "!disabled" if enabled else "disabled"
        self.capture_btn.state([state])
        self.upload_btn.state([state])

    def set_capture_enabled(self, enabled: bool) -> None:
        state = "!disabled" if enabled else "disabled"
        self.capture_btn.state([state])

    def _layout_controls(self) -> None:
        if not self._ui_visible:
            return
        control_specs = [
            (self.source_combo, 150),
            (self.swap_btn, 104),
            (self.target_combo, 150),
            (self.upload_btn, 138),
            (self.capture_btn, 104),
        ]
        gap = 12
        top_y = 22
        height = 40
        total_w = sum(width for _, width in control_specs) + gap * (len(control_specs) - 1)
        start_x = max((self.winfo_width() - total_w) // 2, 92)
        cursor_x = start_x
        for widget, width in control_specs:
            widget.place(x=cursor_x, y=top_y, width=width, height=height)
            cursor_x += width + gap

    def _on_upload_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Select an image to translate",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        self.app.process_uploaded_image(Path(path))

    def display_frame(self, frame_bgr) -> None:
        """Called by the live camera preview loop; ignored while showing a static/frozen image."""
        self._last_frame = frame_bgr
        if not self._show_live:
            return
        self._redraw()

    def show_static_image(self, image_bgr) -> None:
        """Show *image_bgr* (e.g. an uploaded file) in place of the live feed, unfrozen."""
        self._show_live = False
        self._frozen = False
        self._status_overlay = None
        self._last_frame = image_bgr
        self._redraw()

    def freeze_and_show_processing(self) -> None:
        """Freeze the feed on its current frame, darken it, and overlay a processing message."""
        self._show_live = False
        self._frozen = True
        self._status_overlay = None
        self._redraw()

    def unfreeze(self) -> None:
        self._frozen = False
        self._show_live = True

    def show_status_screen(self, text: str, text_color: tuple[int, int, int]) -> None:
        """Show a gray placeholder with centered status text."""
        self._show_live = False
        self._frozen = False
        self._status_overlay = (text, text_color)
        self._redraw()

    def clear_status_screen(self) -> None:
        self._status_overlay = None
        self._show_live = True

    def _redraw(self) -> None:
        if self._last_frame is None:
            base_h, base_w = 720, 1280
        else:
            base_h, base_w = self._last_frame.shape[:2]

        box_w = self.video_label.winfo_width()
        box_h = self.video_label.winfo_height()
        if self._status_overlay is not None:
            text, text_color = self._status_overlay
            gray_frame = np.full((base_h, base_w, 3), 112, dtype=np.uint8)
            photo = frame_to_photo(gray_frame, box_w, box_h, overlay_text=text, overlay_text_color=text_color)
        elif self._frozen:
            if self._last_frame is None:
                return
            frame = darken_frame(self._last_frame)
            photo = frame_to_photo(frame, box_w, box_h, overlay_text="Processing...")
        else:
            if self._last_frame is None:
                return
            photo = frame_to_photo(self._last_frame, box_w, box_h)
        if photo is None:
            return
        self.video_label.configure(image=photo)
        self._current_photo = photo  # keep a reference so Tk doesn't garbage-collect it

