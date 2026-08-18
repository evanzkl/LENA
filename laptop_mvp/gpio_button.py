from __future__ import annotations

from collections.abc import Callable


class GpioCaptureTrigger:
    """Optional Jetson GPIO trigger that maps a hardware button to capture."""

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
        gpio.setwarnings(False)
        gpio.setmode(gpio.BOARD)
        gpio.setup(self._pin, gpio.IN, pull_up_down=gpio.PUD_UP)
        gpio.add_event_detect(
            self._pin,
            gpio.FALLING,
            callback=self._handle_press,
            bouncetime=self._debounce_ms,
        )
        self._enabled = True
        print(f"[gpio pin {self._pin}] button armed")
        return True

    def _handle_press(self, _channel: int) -> None:
        print(f"[gpio pin {self._pin}] edge detected")
        # An uncaught exception here can kill Jetson.GPIO's event-detect
        # thread, silently disabling the button after the first press.
        try:
            self._on_press()
        except Exception as exc:
            print(f"[gpio pin {self._pin}] on_press callback raised, button would otherwise die: {exc}")

    def stop(self) -> None:
        if not self._enabled or self._gpio is None:
            return
        try:
            self._gpio.remove_event_detect(self._pin)
        except RuntimeError:
            pass
        self._gpio.cleanup(self._pin)
        self._enabled = False
        self._gpio = None