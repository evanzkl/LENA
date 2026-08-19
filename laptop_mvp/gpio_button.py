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
        heartbeat_s: float = 2.0,
    ) -> None:
        self._on_press = on_press
        self._pin = pin
        self._debounce_ms = debounce_ms
        self._gpio = None
        self._enabled = False
        self._last_value: int | None = None
        self._last_press_time = 0.0
        # Periodically log the raw pin reading so a stuck/floating line (common
        # cause: pull_up_down has no effect on some JetPack/kernel combos) is
        # visible even when no edge is ever detected.
        self._heartbeat_s = heartbeat_s
        self._last_heartbeat_time = 0.0

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
        self._check_pull_up_functional()
        return True

    def _check_pull_up_functional(self) -> None:
        """Warn if the idle line isn't a stable HIGH, since PUD_UP silently has
        no effect on some JetPack/kernel combos, leaving the pin floating."""
        assert self._gpio is not None
        samples = [self._gpio.input(self._pin) for _ in range(20)]
        for _ in range(20):
            time.sleep(0.005)
            samples.append(self._gpio.input(self._pin))
        if all(sample == self._gpio.HIGH for sample in samples):
            print(f"[gpio pin {self._pin}] internal pull-up looks functional (stable idle HIGH)")
            return
        print(
            f"[gpio pin {self._pin}] WARNING: idle reading is not a stable HIGH "
            f"(samples={samples}). The internal pull-up is likely not applied on "
            "this JetPack/kernel combo - wire an external ~10k pull-up resistor "
            "from 3.3V to this pin."
        )

    def poll(self) -> None:
        """Call periodically (e.g. once per UI tick) from the main thread."""
        if not self._enabled or self._gpio is None:
            return
        value = self._gpio.input(self._pin)

        now = time.monotonic()
        if now - self._last_heartbeat_time >= self._heartbeat_s:
            self._last_heartbeat_time = now
            print(f"[gpio pin {self._pin}] heartbeat: raw value={value}")

        if value == self._last_value:
            return
        self._last_value = value
        if value != self._gpio.LOW:
            return
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