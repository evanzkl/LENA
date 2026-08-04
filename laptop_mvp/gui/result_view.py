from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import numpy as np

from .image_utils import frame_to_photo


def _confidence_label(accuracy: float) -> str:
    if accuracy >= 90:
        return "High Confidence"
    if accuracy >= 70:
        return "Medium Confidence"
    return "Low Confidence"


class ResultView(ttk.Frame):
    """Final state: translated/blurred image with a retake button and accuracy readout."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent)
        self.app = app
        self._ui_visible = True
        self._current_photo = None
        self._result_image: np.ndarray | None = None

        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(side="top", fill="x")
        for col in range(3):
            self.toolbar.columnconfigure(col, weight=1, uniform="result_toolbar")

        self.hide_show_btn = ttk.Button(self.toolbar, text="Hide UI", command=self._toggle_ui)
        self.hide_show_btn.grid(row=0, column=0, sticky="nsew", padx=4, pady=6)

        self.retake_btn = ttk.Button(self.toolbar, text="Retake", command=app.retake)
        self.retake_btn.grid(row=0, column=1, sticky="nsew", padx=4, pady=6)

        self.accuracy_label = ttk.Label(self.toolbar, text="", anchor="center", justify="center")
        self.accuracy_label.grid(row=0, column=2, sticky="nsew", padx=4, pady=6)

        # Everything in the toolbar except the hide/show toggle itself.
        self._toggleable_widgets = [self.retake_btn, self.accuracy_label]

        self.image_label = ttk.Label(self, background="black")
        self.image_label.pack(side="top", fill="both", expand=True)
        self.image_label.bind("<Configure>", lambda _event: self._redraw())

    def _toggle_ui(self) -> None:
        self._ui_visible = not self._ui_visible
        if self._ui_visible:
            for widget in self._toggleable_widgets:
                widget.grid()
            self.hide_show_btn.config(text="Hide UI")
        else:
            for widget in self._toggleable_widgets:
                widget.grid_remove()
            self.hide_show_btn.config(text="Show UI")

    def display_result(self, image_bgr: np.ndarray, accuracy: float) -> None:
        self._result_image = image_bgr
        self.accuracy_label.config(
            text=f"Estimated Accuracy: {accuracy:.1f}% ({_confidence_label(accuracy)})"
        )
        self._redraw()

    def _redraw(self) -> None:
        if self._result_image is None:
            return
        box_w = self.image_label.winfo_width()
        box_h = self.image_label.winfo_height()
        photo = frame_to_photo(self._result_image, box_w, box_h)
        if photo is None:
            return
        self.image_label.configure(image=photo)
        self._current_photo = photo  # keep a reference so Tk doesn't garbage-collect it
