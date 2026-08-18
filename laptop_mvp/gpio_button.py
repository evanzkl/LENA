from __future__ import annotations

import time
from collections.abc import Callable


class GpioCaptureTrigger:
    """Optional Jetson GPIO trigger that maps a hardware button to capture.

    Uses polling via poll() instead of add_event_detect(): on some JetPack/
    kernel combinations add_event_detect() silently never fires even though
    the pin electrically toggles, while gpio.input() still reads correctly.
    """

    def __init__(
        self,
        on_press: Callable[[], None],
        pin: int = 29,
        debounce_ms: int = 300,
    ) -> None:
        self._on_press = on_press
        self._pin = pin
        self._debounce_ms = debounce_ms
        self._gpio = None
        self._enabled = False
        self._last_value: int | None = None
        self._last_press_time = 0.0

    @property
    def enabled(self) -> bool:
        return self._enabled

    def start(self) -> bool:
        try:
            import Jetson.GPIO as gpio  # type: ignore[import-not-found]
        except ImportError as exc:
            print(f"[gpio pin {self._pin}] Jetson.GPIO not importable, button disabled: {exc}")
            return False

        self._gpio = gpio
        try:
            gpio.setwarnings(False)
            gpio.setmode(gpio.BOARD)
            gpio.setup(self._pin, gpio.IN, pull_up_down=gpio.PUD_UP)
            self._last_value = gpio.input(self._pin)
        except Exception as exc:
            # e.g. the line is claimed by another driver (busy pinmux/peripheral)
            print(f"[gpio pin {self._pin}] setup failed, button disabled: {exc}")
            self._gpio = None
            return False
        self._enabled = True
        print(f"[gpio pin {self._pin}] button armed (polling mode, idle value={self._last_value})")
        return True

    def poll(self) -> None:
        """Call periodically (e.g. once per UI tick) from the main thread."""
        if not self._enabled or self._gpio is None:
            return
        value = self._gpio.input(self._pin)
        if value == self._last_value:
            return
        self._last_value = value
        if value != self._gpio.LOW:
            return
        now = time.monotonic()
        if (now - self._last_press_time) * 1000 < self._debounce_ms:
            return
        self._last_press_time = now
        print(f"[gpio pin {self._pin}] edge detected")
        try:
            self._on_press()
        except Exception as exc:
            print(f"[gpio pin {self._pin}] on_press callback raised: {exc}")

    def stop(self) -> None:
        if not self._enabled or self._gpio is None:
            return
        self._gpio.cleanup(self._pin)
        self._enabled = False
        self._gpio = None