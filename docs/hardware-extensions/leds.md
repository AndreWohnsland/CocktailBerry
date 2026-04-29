# LEDs

Custom LEDs let you drive any indicator/lighting hardware that CocktailBerry does not support out of the box.
They are used for an idle lighting state and an optional preparation animation, both configurable per LED.
Each LED extension is a single Python file placed in the `addons/leds/` folder.
Once added, the new LED type appears in the LED configuration dropdown alongside the built-in `Normal` and `WSLED` types.

For LEDs, the base classes are:

- `ExtensionConfig` inherits from **`BaseLedConfig`** (`src.config.config_types`)
- `Implementation` inherits from **`LedInterface`** (`src.machine.leds.base`)

## Getting Started

!!! tip "Use the CLI"
    Create a skeleton file with the CLI command:

    ```bash
    uv run runme.py create-led "Your LED Name"
    ```

    This creates a ready-to-fill file in `addons/leds/your_led_name.py`.

## Shared vs Custom Config Fields

Every LED automatically gets the following shared fields injected — you do **not** need to define them:

- `led_type` — dropdown to select the LED driver
- `default_on` — whether the LED should be on when idle
- `preparation_state` — `On` / `Off` / `Effect` during preparation

Only define your **extra** fields in `CONFIG_FIELDS`.
These will appear in the configuration UI between the LED type dropdown and the shared fields.

## ExtensionConfig

Your `ExtensionConfig` must inherit from `BaseLedConfig`.
Define any extra attributes your LED needs and make sure to call `super().__init__()` with the shared fields.
The `to_config()` method must serialize all fields (call `super().to_config()` and update with your extras).

!!! warning "Accept **kwargs"
    Your `__init__` should accept `**kwargs` to be forward-compatible with future shared fields.

## Implementation

Your `Implementation` class inherits from `LedInterface`. The base class owns the threading, cancellation, and the `preparation_state` switch — you only implement the visual side.

| Method            | Required | Description                                                                                                                                                                       |
| ----------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `turn_on()`       | **yes**  | Turns the LED on.                                                                                                                                                                 |
| `turn_off()`      | **yes**  | Turns the LED off.                                                                                                                                                                |
| `active_frames()` | no       | Generator that yields seconds-to-sleep between frames of the during-preparation animation. Default: empty (the base class falls back to `turn_on()`).                             |
| `end_frames()`    | no       | Generator that yields seconds-to-sleep between frames of the post-preparation animation. The implementation decides total duration. Default: empty (falls back to idle state).    |
| `cleanup()`       | no       | Release driver-specific handles. The base implementation already cancels and joins any running effect — override only for extra resources.                                        |

The constructor receives `config` (your `ExtensionConfig` instance) and `hardware` (`HardwareContext` — provides access to pin controller, scale, carriage, RFID, and `extra` dict of hardware extension instances).

### How animations are driven

You never spawn threads or check cancel flags. The base class:

1. Cancels any previously running effect (sets a stop event, joins the thread for up to 0.5 s).
2. On `preparation_state = "Effect"`, spawns a daemon thread that pulls one frame at a time from your generator and waits the yielded seconds on a `threading.Event` — cancellation interrupts the wait immediately.
3. Closes the generator if a new preparation starts, the controller is turned off, or the program shuts down — your `try/finally` (if any) runs as expected.
4. If your generator yields **nothing**, the base class silently falls back to `turn_on()` (for `active_frames`) or to the idle state (for `end_frames`). Static LEDs never need to special-case anything.

!!! warning "Keep frame bodies non-blocking"
    Yielded sleeps can be any duration — they are interrupted immediately on cancellation via `Event.wait`. The constraint is the **frame body**: the work between yields (and inside `turn_on` / `turn_off`) cannot be interrupted. Avoid `time.sleep`, slow SPI/I²C writes, or any blocking I/O inside a frame body. If the join times out the base class logs a warning and the orphan thread keeps writing to hardware until it next observes the stop event.

Effects therefore look like ordinary Python loops:

```python
def end_frames(self) -> Iterator[float]:
    duration = 5.0
    elapsed = 0.0
    while elapsed < duration:
        self.turn_on()
        yield 0.1
        elapsed += 0.1
        self.turn_off()
        yield 0.1
        elapsed += 0.1
```

For long-running animations the loop can be `while True:` — you do **not** need a manual stop check; the base class will close the generator at the right moment.

## Inherited Attributes & Helpers

`LedInterface` provides several attributes you can use in your implementation — no need to define them yourself:

| Attribute / Method       | Description                                                                                                                                                         |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `self.config`            | Your `ExtensionConfig` instance                                                                                                                                     |
| `self.hardware`          | `HardwareContext` — access to `pin_controller`, `led_controller`, `scale`, `carriage`, `rfid`, and `extra` (see [Hardware Context Extensions](hardware-context.md)) |
| `self.default_on`        | Whether the LED should be on when idle (from config)                                                                                                                |
| `self.preparation_state` | `On` / `Off` / `Effect` during preparation (from config)                                                                                                            |
| `cleanup()`              | Stops any running effect, then is a no-op. Override only if your driver holds extra resources beyond the central `PinController`.                                   |

## Lifecycle

LED extensions follow this lifecycle:

1. **Discovery & variant registration** — Extensions are discovered and registered as variants of `LED_CONFIG` before config is read.
2. **Config load** — The GUI can now show and edit the LED extension fields.
3. **Construction** — During `init_machine()`, after the `HardwareContext` is created and hardware extensions are wired, `Implementation(config, hardware)` is called once per `LED_CONFIG` entry.
4. **Runtime use** — `MachineController` calls `preparation_start()` before each cocktail run, `preparation_end()` after it completes, and `default_led()` when idle. The base class drives `active_frames()` / `end_frames()` automatically and cancels them when re-triggered.
5. **`cleanup()`** — Called at shutdown via `LedController.cleanup()`. The base implementation already stops any running effect; override only for extra resources.

## Full Example

Below is a complete example of a software-only LED that just logs every state change — useful as a template or for dry-running without hardware:

```python
from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from src import SupportedLedStatesType
from src.config.config_types import BaseLedConfig, ConfigInterface, StringType # (1)!
from src.logger_handler import LoggerHandler
from src.machine.leds.base import LedInterface # (2)!

if TYPE_CHECKING:
    from src.machine.hardware import HardwareContext


EXTENSION_NAME = "SoftwareLed" # (3)!
_logger = LoggerHandler("SoftwareLed")


class ExtensionConfig(BaseLedConfig): # (4)!
    """Software-only LED config with a free-form label."""

    label: str

    def __init__(
        self,
        label: str = "log",
        led_type: str = EXTENSION_NAME,
        default_on: bool = False,
        preparation_state: SupportedLedStatesType = "Effect",
        **kwargs: Any, # (5)!
    ) -> None:
        super().__init__(
            led_type=led_type,
            default_on=default_on,
            preparation_state=preparation_state,
        )
        self.label = label

    def to_config(self) -> dict[str, Any]: # (6)!
        config = super().to_config()
        config.update({"label": self.label})
        return config


CONFIG_FIELDS: dict[str, ConfigInterface] = { # (7)!
    "label": StringType(default="log"),
}


class Implementation(LedInterface): # (8)!
    """Logs every state change instead of touching real hardware."""

    def __init__(
        self, config: ExtensionConfig, hardware: HardwareContext,
    ) -> None:
        super().__init__(config, hardware)
        self.label = config.label
        _logger.info(f"SoftwareLed '{self.label}' initialised")

    def turn_on(self) -> None: # (9)!
        _logger.info(f"SoftwareLed '{self.label}' on")

    def turn_off(self) -> None:
        _logger.info(f"SoftwareLed '{self.label}' off")

    def active_frames(self) -> Iterator[float]: # (10)!
        """Heartbeat blink while a cocktail is being prepared."""
        while True:
            self.turn_on()
            yield 0.2
            self.turn_off()
            yield 0.2

    def end_frames(self) -> Iterator[float]: # (11)!
        """Blink at 5 Hz for 5 seconds."""
        step = 0.1
        duration = 5.0
        elapsed = 0.0
        while elapsed < duration:
            self.turn_on()
            yield step
            elapsed += step
            self.turn_off()
            yield step
            elapsed += step
```

1. Import `BaseLedConfig` for your config class and any config field types you need (here `StringType`).
2. Import `LedInterface` — the abstract base class for all LEDs.
3. Unique name that appears in the LED type dropdown. Must match the `led_type` default in your `ExtensionConfig`.
4. Your config class must inherit from `BaseLedConfig`. Add any extra attributes your LED needs.
5. Always accept `**kwargs` to stay forward-compatible with future shared fields.
6. Serialize all fields — call `super().to_config()` first, then update with your extra fields.
7. Only define your **extra** config fields here. Shared fields (`default_on`, `preparation_state`) and the `led_type` dropdown are auto-injected.
8. Your LED implementation must inherit from `LedInterface`.
9. Translate the abstract on/off calls to your real driver (GPIO write, SPI command, …).
10. The base class drives this generator on a daemon thread between `preparation_start` and `preparation_end`. Use ``while True`` — no stop flag needed; the generator is closed on cancellation.
11. Same idiom as `active_frames`. The implementation decides total duration; cancellation is still automatic if a new preparation starts.
