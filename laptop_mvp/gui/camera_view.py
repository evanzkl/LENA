from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from .image_utils import darken_frame, frame_to_photo
from .languages import LANGUAGE_NAMES

ICON_EYE = "👁"
ICON_EYE_OFF = "👁̸"


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

        self.video_label = ttk.Label(self, background="black")
        self.video_label.pack(side="top", fill="both", expand=True)
        self.video_label.bind("<Configure>", lambda _event: self._redraw())

        self.hide_show_btn = tk.Button(
            self,
            text=ICON_EYE_OFF,
            command=self._toggle_ui,
            font=("Segoe UI Emoji", 16),
            fg="#E8EEF8",
            bg="#1F3651",
            activeforeground="#FFFFFF",
            activebackground="#28486A",
            relief="flat",
            bd=0,
            width=3,
            pady=6,
        )
        self.hide_show_btn.place(x=18, y=18, anchor="nw")

        self.control_bar = tk.Frame(self, bg="#F9F9F9", bd=0, highlightthickness=0)
        self.control_bar.place(relx=0.5, y=22, anchor="n")
        for col in range(5):
            self.control_bar.grid_columnconfigure(col, weight=1, uniform="camera_toolbar")

        self.source_combo = ttk.Combobox(
            self.control_bar,
            textvariable=app.source_lang_var,
            values=LANGUAGE_NAMES,
            state="readonly",
            style="HUD.TCombobox",
        )
        self.source_combo.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        self.swap_btn = tk.Button(
            self.control_bar,
            text="<-> Swap",
            command=app.swap_languages,
            font=("Segoe UI", 11, "bold"),
            fg="#222222",
            bg="#F9F9F9",
            activeforeground="#111111",
            activebackground="#E7E7E7",
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
        )
        self.swap_btn.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        self.target_combo = ttk.Combobox(
            self.control_bar,
            textvariable=app.target_lang_var,
            values=LANGUAGE_NAMES,
            state="readonly",
            style="HUD.TCombobox",
        )
        self.target_combo.grid(row=0, column=2, sticky="nsew", padx=6, pady=6)

        self.upload_btn = tk.Button(
            self.control_bar,
            text="Upload Image",
            command=self._on_upload_image,
            font=("Segoe UI", 11, "bold"),
            fg="#222222",
            bg="#F9F9F9",
            activeforeground="#111111",
            activebackground="#E7E7E7",
            relief="flat",
            bd=0,
            padx=12,
            pady=5,
        )
        self.upload_btn.grid(row=0, column=3, sticky="nsew", padx=6, pady=6)

        self.capture_btn = tk.Button(
            self.control_bar,
            text="Capture",
            command=app.capture_and_process,
            font=("Segoe UI", 11, "bold"),
            fg="#222222",
            bg="#F9F9F9",
            activeforeground="#111111",
            activebackground="#E7E7E7",
            relief="flat",
            bd=0,
            padx=14,
            pady=5,
        )
        self.capture_btn.grid(row=0, column=4, sticky="nsew", padx=6, pady=6)

        # Everything in the top HUD except the eye toggle itself.
        self._toggleable_widgets = [self.control_bar]

    def _toggle_ui(self) -> None:
        self._ui_visible = not self._ui_visible
        if self._ui_visible:
            for widget in self._toggleable_widgets:
                widget.place(relx=0.5, y=22, anchor="n")
            self.hide_show_btn.config(text=ICON_EYE_OFF)
        else:
            for widget in self._toggleable_widgets:
                widget.place_forget()
            self.hide_show_btn.config(text=ICON_EYE)

    def set_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.capture_btn.config(state=state)
        self.upload_btn.config(state=state)

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
        if not self._show_live:
            return
        self._last_frame = frame_bgr
        self._redraw()

    def show_static_image(self, image_bgr) -> None:
        """Show *image_bgr* (e.g. an uploaded file) in place of the live feed, unfrozen."""
        self._show_live = False
        self._frozen = False
        self._last_frame = image_bgr
        self._redraw()

    def freeze_and_show_processing(self) -> None:
        """Freeze the feed on its current frame, darken it, and overlay a processing message."""
        self._show_live = False
        self._frozen = True
        self._redraw()

    def unfreeze(self) -> None:
        self._frozen = False
        self._show_live = True

    def _redraw(self) -> None:
        if self._last_frame is None:
            return
        box_w = self.video_label.winfo_width()
        box_h = self.video_label.winfo_height()
        if self._frozen:
            frame = darken_frame(self._last_frame)
            photo = frame_to_photo(frame, box_w, box_h, overlay_text="Processing...")
        else:
            photo = frame_to_photo(self._last_frame, box_w, box_h)
        if photo is None:
            return
        self.video_label.configure(image=photo)
        self._current_photo = photo  # keep a reference so Tk doesn't garbage-collect it

