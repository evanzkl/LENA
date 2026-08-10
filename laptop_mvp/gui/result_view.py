from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import numpy as np

from .image_utils import create_eye_icon, frame_to_photo


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
        self._eye_icon = create_eye_icon(self, size=44, hidden=False)
        self._eye_off_icon = create_eye_icon(self, size=44, hidden=True)

        self.image_label = ttk.Label(self, background="black")
        self.image_label.pack(side="top", fill="both", expand=True)
        self.image_label.bind("<Configure>", lambda _event: self._redraw())
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

        self.retake_btn = ttk.Button(
            self,
            text="Retake",
            command=app.retake,
            style="Pill.TButton",
        )

        self.accuracy_label = tk.Label(
            self,
            text="",
            anchor="center",
            justify="center",
            font=("Segoe UI", 11, "bold"),
            fg="#1C7D45",
            bg="#F9F9F9",
            relief="solid",
            bd=1,
            padx=14,
            pady=8,
        )

        # Everything in the top row except the eye toggle itself.
        self._toggleable_widgets = [self.retake_btn, self.accuracy_label]
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

    def _layout_controls(self) -> None:
        if not self._ui_visible:
            return
        control_specs = [
            (self.retake_btn, 112),
            (self.accuracy_label, 310),
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
