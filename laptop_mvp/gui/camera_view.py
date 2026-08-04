from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from .image_utils import frame_to_photo
from .languages import LANGUAGE_NAMES


class CameraView(ttk.Frame):
    """Initial state: live camera preview with language pickers and a capture button."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent)
        self.app = app
        self._ui_visible = True
        self._current_photo = None

        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(side="top", fill="x")
        for col in range(6):
            self.toolbar.columnconfigure(col, weight=1, uniform="camera_toolbar")

        self.hide_show_btn = ttk.Button(self.toolbar, text="Hide UI", command=self._toggle_ui)
        self.hide_show_btn.grid(row=0, column=0, sticky="nsew", padx=4, pady=6)

        self.source_combo = ttk.Combobox(
            self.toolbar,
            textvariable=app.source_lang_var,
            values=LANGUAGE_NAMES,
            state="readonly",
        )
        self.source_combo.grid(row=0, column=1, sticky="nsew", padx=4, pady=6)

        self.swap_btn = ttk.Button(self.toolbar, text="\u21c4 Swap", command=app.swap_languages)
        self.swap_btn.grid(row=0, column=2, sticky="nsew", padx=4, pady=6)

        self.target_combo = ttk.Combobox(
            self.toolbar,
            textvariable=app.target_lang_var,
            values=LANGUAGE_NAMES,
            state="readonly",
        )
        self.target_combo.grid(row=0, column=3, sticky="nsew", padx=4, pady=6)

        self.image_mode_btn = ttk.Button(self.toolbar, text="Image Mode", command=self._show_image_mode_menu)
        self.image_mode_btn.grid(row=0, column=4, sticky="nsew", padx=4, pady=6)

        self.image_mode_menu = tk.Menu(self, tearoff=0)
        self.image_mode_menu.add_command(label="Upload Image...", command=self._on_upload_image)
        self.image_mode_menu.add_command(label="Capture Image", command=app.capture_and_process)

        self.capture_btn = ttk.Button(self.toolbar, text="Capture", command=app.capture_and_process)
        self.capture_btn.grid(row=0, column=5, sticky="nsew", padx=4, pady=6)

        # Everything in the toolbar except the hide/show toggle itself.
        self._toggleable_widgets = [
            self.source_combo,
            self.swap_btn,
            self.target_combo,
            self.image_mode_btn,
            self.capture_btn,
        ]

        self.status_label = ttk.Label(self, text="", anchor="center")
        self.status_label.pack(side="top", fill="x")
        self._toggleable_widgets.append(self.status_label)

        self.video_label = ttk.Label(self, background="black")
        self.video_label.pack(side="top", fill="both", expand=True)

    def _toggle_ui(self) -> None:
        self._ui_visible = not self._ui_visible
        if self._ui_visible:
            for widget in self._toggleable_widgets:
                if widget is self.status_label:
                    widget.pack(side="top", fill="x")
                else:
                    widget.grid()
            self.hide_show_btn.config(text="Hide UI")
        else:
            for widget in self._toggleable_widgets:
                if widget is self.status_label:
                    widget.pack_forget()
                else:
                    widget.grid_remove()
            self.hide_show_btn.config(text="Show UI")

    def set_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.capture_btn.config(state=state)
        self.image_mode_btn.config(state=state)

    def set_status(self, text: str) -> None:
        self.status_label.config(text=text)

    def _show_image_mode_menu(self) -> None:
        x = self.image_mode_btn.winfo_rootx()
        y = self.image_mode_btn.winfo_rooty() + self.image_mode_btn.winfo_height()
        self.image_mode_menu.tk_popup(x, y)

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
        box_w = self.video_label.winfo_width()
        box_h = self.video_label.winfo_height()
        photo = frame_to_photo(frame_bgr, box_w, box_h)
        if photo is None:
            return
        self.video_label.configure(image=photo)
        self._current_photo = photo  # keep a reference so Tk doesn't garbage-collect it
