from __future__ import annotations

import tkinter as tk


class RoundedButton(tk.Canvas):
    """Canvas-based button that keeps a rectangular layout but renders rounded corners."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str = "",
        command=None,
        *,
        width: int = 120,
        height: int = 40,
        bg: str = "#F9F9F9",
        fg: str = "#1F2937",
        active_bg: str = "#EAF2EC",
        border_color: str = "#D6DCE3",
        disabled_bg: str = "#F1F1F1",
        disabled_fg: str = "#8A8A8A",
        radius: int = 18,
        font: tuple[str, int, str] | None = None,
        **kwargs,
    ) -> None:
        try:
            parent_bg = parent.cget("background")
        except tk.TclError:
            parent_bg = "#F5F5F5"

        super().__init__(
            parent,
            width=width,
            height=height,
            bd=0,
            highlightthickness=0,
            bg=parent_bg,
            cursor="hand2",
            **kwargs,
        )
        self._text = text
        self._command = command
        self._bg = bg
        self._fg = fg
        self._active_bg = active_bg
        self._border_color = border_color
        self._disabled_bg = disabled_bg
        self._disabled_fg = disabled_fg
        self._radius = max(8, min(radius, min(width, height) // 2))
        self._font = font or ("Segoe UI", 11, "bold")
        self._state = tk.NORMAL
        self._hover = False
        self._pressed = False

        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonPress-1>", lambda _event: self._set_pressed(True))
        self.bind("<ButtonRelease-1>", lambda _event: self._set_pressed(False))
        self.bind("<Enter>", lambda _event: self._set_hover(True))
        self.bind("<Leave>", lambda _event: self._set_hover(False))

        self._redraw()

    def _current_fill(self) -> str:
        if self._state == tk.DISABLED:
            return self._disabled_bg
        if self._pressed or self._hover:
            return self._active_bg
        return self._bg

    def _current_text_color(self) -> str:
        return self._disabled_fg if self._state == tk.DISABLED else self._fg

    def _set_hover(self, hovered: bool) -> None:
        if self._state == tk.DISABLED:
            return
        self._hover = hovered
        self._redraw()

    def _set_pressed(self, pressed: bool) -> None:
        if self._state == tk.DISABLED:
            return
        self._pressed = pressed
        self._redraw()

    def _redraw(self) -> None:
        self.delete("all")
        width = max(10, self.winfo_width())
        height = max(10, self.winfo_height())
        radius = min(self._radius, width // 2, height // 2)
        fill = self._current_fill()
        outline = self._border_color if self._state != tk.DISABLED else "#E5E7EB"

        self.create_rectangle(radius, 0, width - radius, height, fill=fill, outline=outline, width=1)
        self.create_rectangle(0, radius, width, height - radius, fill=fill, outline=outline, width=1)
        self.create_oval(0, 0, 2 * radius, 2 * radius, fill=fill, outline=outline, width=1)
        self.create_oval(width - 2 * radius, 0, width, 2 * radius, fill=fill, outline=outline, width=1)
        self.create_oval(width - 2 * radius, height - 2 * radius, width, height, fill=fill, outline=outline, width=1)
        self.create_oval(0, height - 2 * radius, 2 * radius, height, fill=fill, outline=outline, width=1)

        self.create_text(
            width / 2,
            height / 2,
            text=self._text,
            fill=self._current_text_color(),
            font=self._font,
            anchor="center",
        )

    def _on_click(self, _event: tk.Event) -> None:
        if self._state == tk.DISABLED or self._command is None:
            return
        self._command()

    def config(self, **kwargs) -> None:
        if "text" in kwargs:
            self._text = str(kwargs["text"])
        if "command" in kwargs:
            self._command = kwargs["command"]
        if "state" in kwargs:
            self.state(kwargs["state"])
        if "fg" in kwargs:
            self._fg = kwargs["fg"]
        if "bg" in kwargs:
            self._bg = kwargs["bg"]
        if "activebackground" in kwargs:
            self._active_bg = kwargs["activebackground"]
        if "disabledforeground" in kwargs:
            self._disabled_fg = kwargs["disabledforeground"]
        if "width" in kwargs:
            super().config(width=kwargs["width"])
        if "height" in kwargs:
            super().config(height=kwargs["height"])
        self._redraw()

    def state(self, *args) -> str | None:
        if not args:
            return self._state

        state_spec = args[0]
        values = state_spec if isinstance(state_spec, (list, tuple, set)) else [state_spec]
        for value in values:
            if value == "disabled":
                self._state = tk.DISABLED
            elif value == "!disabled":
                self._state = tk.NORMAL
            elif value == "active":
                self._state = tk.ACTIVE
            elif value == "normal":
                self._state = tk.NORMAL

        self._redraw()
        return self._state

    def cget(self, key: str):
        if key == "text":
            return self._text
        if key == "state":
            return self._state
        return super().cget(key)

    def set_text(self, text: str) -> None:
        self._text = text
        self._redraw()

    def set_command(self, command) -> None:
        self._command = command
