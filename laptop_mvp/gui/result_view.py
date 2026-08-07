from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import numpy as np

from .image_utils import frame_to_photo

ICON_EYE = "👁"
ICON_EYE_OFF = "👁̸"


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

        self.image_label = ttk.Label(self, background="black")
        self.image_label.pack(side="top", fill="both", expand=True)
        self.image_label.bind("<Configure>", lambda _event: self._redraw())

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
        for col in range(2):
            self.control_bar.grid_columnconfigure(col, weight=1, uniform="result_toolbar")

        self.retake_btn = tk.Button(
            self.control_bar,
            text="Retake",
            command=app.retake,
            font=("Segoe UI", 11, "bold"),
            fg="#222222",
            bg="#F9F9F9",
            activeforeground="#111111",
            activebackground="#E7E7E7",
            relief="flat",
            bd=0,
            padx=16,
            pady=5,
        )
        self.retake_btn.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        self.accuracy_label = tk.Label(
            self.control_bar,
            text="",
            anchor="center",
            justify="center",
            font=("Segoe UI", 11, "bold"),
            fg="#1C7D45",
            bg="#F9F9F9",
            padx=14,
            pady=8,
        )
        self.accuracy_label.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        # Everything in the top HUD except the UI toggle itself.
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

    def display_result(self, image_bgr: np.ndarray, accuracy: float) -> None:
        self._result_image = image_bgr
        self.accuracy_label.config(
            text=f"Accuracy: {accuracy:.1f}% ({_confidence_label(accuracy)})"
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
