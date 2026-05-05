# Carriages

Custom carriages (or slides) let you drive any linear positioning hardware that moves a glass between dispenser slots.
Each carriage extension is a single Python file placed in the `addons/carriages/` folder.
Once added, the new carriage type appears in the carriage configuration dropdown alongside the built-in `NoCarriage` sentinel.

!!! info "No built-in driver yet"
    CocktailBerry currently ships with only the `NoCarriage` sentinel — selecting it is equivalent to a disabled carriage.
    If you want an actually moving carriage you have to provide one yourself via an extension.

Unlike dispensers, a **single** carriage is created per machine (one `CARRIAGE_CONFIG` entry).
It is wired into the `HardwareContext` and used by the scheduler to position the glass between dispenses.

For carriages, the base classes are:

- `ExtensionConfig` inherits from **`BaseCarriageConfig`** (`src.config.config_types`)
- `Implementation` inherits from **`CarriageInterface`** (`src.machine.carriage.base`)

## Getting Started

!!! tip "Use the CLI"
    Create a skeleton file with the CLI command:

    ```bash
    uv run runme.py create-carriage "Your Carriage Name"
    ```

    This creates a ready-to-fill file in `addons/carriages/your_carriage_name.py`.

## Shared vs Custom Config Fields

Every carriage automatically gets the following shared fields injected — you do **not** need to define them:

- `carriage_type` — dropdown to select the carriage driver
- `enabled` — whether the carriage is active
- `home_position` — resting position (0–100%) the carriage returns to when idle
- `speed_pct_per_s` — movement speed in percent of total travel per second
- `move_during_cleaning` — whether the carriage should move between slots during cleaning
- `wait_after_dispense` — pause in seconds after a dispense before moving to the next position

Only define your **extra** fields in `CONFIG_FIELDS` (e.g. step/dir pins, microstep resolution, endstop pin, …).
These will appear in the configuration UI between the carriage type dropdown and the shared fields.

## Position Model

Positions are abstract values in the range **0–100**, representing the percentage of total travel.
Your implementation is responsible for translating percent values to its native unit — typically motor steps for a stepper-based carriage, encoder ticks, or a servo angle.
The 0–100 abstraction keeps pump configuration portable: the `carriage_position` field on each dispenser stays meaningful across different hardware.

## ExtensionConfig

Your `ExtensionConfig` must inherit from `BaseCarriageConfig`.
Define any extra attributes your carriage needs and make sure to call `super().__init__()` with the shared fields.
The `to_config()` method must serialize all fields (call `super().to_config()` and update with your extras).

!!! warning "Accept **kwargs"
    Your `__init__` should accept `**kwargs` to be forward-compatible with future shared fields.

## Implementation

Your `Implementation` class must inherit from `CarriageInterface` and implement the following abstract methods:

| Method              | Required | Description                                                                                                                                              |
| ------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `find_reference()`  | **yes**  | Drive toward a reference sensor (endstop) and set the internal position to the known reference. Called once after the GUI/API is up; must be idempotent. |
| `move_to(position)` | **yes**  | Move the carriage to the given position (0–100). Translate the percent value to your native unit (steps, ticks, …).                                      |
| `home()`            | **yes**  | Return the carriage to the configured `home_position`. A simple `self.move_to(self.home_position)` is usually enough.                                    |
| `jog(delta)`        | **yes**  | Move by a signed delta in the implementation's smallest unit (typically one motor step). Intended for commissioning/maintenance flows.                   |
| `cleanup()`         | **yes**  | Release any hardware resources (close GPIO pins, disable motor driver).                                                                                  |

The constructor receives `config` (your `ExtensionConfig` instance) and `hardware` (`HardwareContext` — provides access to pin controller, LED controller, scale, and `extra` dict of hardware extension instances).

## Inherited Attributes & Helpers

`CarriageInterface` provides the following for your implementation:

| Attribute / Method              | Description                                                                                                                                 |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `self.config`                   | Your `ExtensionConfig` instance                                                                                                             |
| `self.hardware`                 | `HardwareContext` — access to `pin_controller`, `led_controller`, `scale`, and `extra`                                                      |
| `self.home_position`            | Home position (0–100) from config                                                                                                           |
| `self.speed_pct_per_s`          | Movement speed in percent of total travel per second, from config                                                                           |
| `self.move_during_cleaning`     | Whether the carriage should move during cleaning                                                                                            |
| `self.wait_after_dispense`      | Pause (in seconds) after a dispense before moving, from config                                                                              |
| `travel_time(from_pos, to_pos)` | Default seconds estimate between two positions, computed from `speed_pct_per_s`. Override if your acceleration profile materially deviates. |

## Lifecycle

Carriage extensions follow this lifecycle:

1. **Discovery & variant registration** — Extensions are discovered and registered as variants of `CARRIAGE_CONFIG` before config is read.
2. **Config load** — The GUI can now show and edit the carriage extension fields.
3. **Construction** — During `init_machine()`, after the scale is created, `Implementation(config, hardware)` is called. You receive the full `HardwareContext` including the scale.
4. **`find_reference()`** — Called once after the GUI/API is up (deferred out of `init_machine()` because it can take several seconds). In v1 it runs on a background thread with a spinner; in v2 it runs at the end of the FastAPI lifespan. Must be idempotent.
5. **Runtime use** — The scheduler calls `move_to(position)` before each dispense group and `home()` after a run. You may also be jogged during commissioning flows.
6. **`cleanup()`** — Called at shutdown to release resources.

## Full Example

Below is a complete example of a simple dummy carriage that just tracks position in memory — useful as a template or for dry-running without hardware:

```python
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.config.config_types import BaseCarriageConfig, ConfigInterface, IntType # (1)!
from src.config.validators import build_number_limiter
from src.logger_handler import LoggerHandler
from src.machine.carriage.base import CarriageInterface # (2)!

if TYPE_CHECKING:
    from src.machine.hardware import HardwareContext


EXTENSION_NAME = "DummyCarriage" # (3)!
_logger = LoggerHandler("DummyCarriage")


class ExtensionConfig(BaseCarriageConfig): # (4)!
    """Dummy carriage config with step/dir pins."""

    step_pin: int
    dir_pin: int

    def __init__(
        self,
        step_pin: int = 0,
        dir_pin: int = 0,
        carriage_type: str = EXTENSION_NAME,
        enabled: bool = False,
        home_position: int = 0,
        speed_pct_per_s: float = 10.0,
        move_during_cleaning: bool = False,
        wait_after_dispense: float = 0.0,
        **kwargs: Any, # (5)!
    ) -> None:
        super().__init__(
            carriage_type=carriage_type,
            enabled=enabled,
            home_position=home_position,
            speed_pct_per_s=speed_pct_per_s,
            move_during_cleaning=move_during_cleaning,
            wait_after_dispense=wait_after_dispense,
        )
        self.step_pin = step_pin
        self.dir_pin = dir_pin

    def to_config(self) -> dict[str, Any]: # (6)!
        config = super().to_config()
        config.update({"step_pin": self.step_pin, "dir_pin": self.dir_pin})
        return config


CONFIG_FIELDS: dict[str, ConfigInterface] = { # (7)!
    "step_pin": IntType([build_number_limiter(0)], prefix="Step:"),
    "dir_pin": IntType([build_number_limiter(0)], prefix="Dir:"),
}


class Implementation(CarriageInterface): # (8)!
    """Dummy carriage that tracks position in memory only."""

    def __init__(
        self, config: ExtensionConfig, hardware: HardwareContext,
    ) -> None:
        super().__init__(config, hardware)
        self._step_pin = config.step_pin
        self._dir_pin = config.dir_pin
        self._position = 0
        _logger.info(f"Dummy carriage initialized (step={self._step_pin}, dir={self._dir_pin})")

    def find_reference(self) -> None: # (9)!
        _logger.info("Dummy carriage: driving to reference sensor")
        self._position = 0

    def move_to(self, position: int) -> None: # (10)!
        target = max(0, min(100, position))
        _logger.debug(f"Dummy carriage: moving from {self._position} to {target}")
        self._position = target

    def home(self) -> None:
        self.move_to(self.home_position)

    def jog(self, delta: int) -> None: # (11)!
        _logger.debug(f"Dummy carriage: jog {delta} step(s)")

    def cleanup(self) -> None: # (12)!
        _logger.info("Dummy carriage cleaned up")
```

1. Import `BaseCarriageConfig` for your config class and any config field types you need (here `IntType`).
2. Import `CarriageInterface` — the abstract base class for all carriages.
3. Unique name that appears in the carriage type dropdown. Must match the `carriage_type` default in your `ExtensionConfig`.
4. Your config class must inherit from `BaseCarriageConfig`. Add any extra attributes your carriage needs.
5. Always accept `**kwargs` to stay forward-compatible with future shared fields.
6. Serialize all fields — call `super().to_config()` first, then update with your extra fields.
7. Only define your **extra** config fields here. Shared fields (`enabled`, `home_position`, `speed_pct_per_s`, `move_during_cleaning`, `wait_after_dispense`) and the `carriage_type` dropdown are auto-injected.
8. Your carriage implementation must inherit from `CarriageInterface`.
9. Drive toward your reference sensor and set the internal position. Must be idempotent — may be called again at runtime after a mechanical intervention.
10. Translate the abstract 0–100 axis to your native unit (motor steps, encoder ticks) and drive the motor. Clamp the target to the valid range.
11. Move by a signed delta in your smallest native unit (typically one motor step). Intended for commissioning / maintenance; bulk motion belongs in `move_to`.
12. Called at program shutdown — release GPIO, disable the motor driver.
