# Dispensers

Custom dispensers let you control any pump or valve hardware that CocktailBerry does not support out of the box.
Each dispenser extension is a single Python file placed in the `addons/dispensers/` folder.
Once added, the new dispenser type appears in the pump configuration dropdown alongside the built-in DC and Stepper types.

For dispensers, the base classes are:

- `ExtensionConfig` inherits from **`BasePumpConfig`** (`src.config.config_types`)
- `Implementation` inherits from **`BaseDispenser`** (`src.machine.dispensers.base`)

## Getting Started

!!! tip "Use the CLI"
    Create a skeleton file with the CLI command:

    ```bash
    uv run runme.py create-dispenser "Your Dispenser Name"
    ```

    This creates a ready-to-fill file in `addons/dispensers/your_dispenser_name.py`.

## Shared vs Custom Config Fields

Every dispenser automatically gets the following shared fields injected — you do **not** need to define them:

- `pump_type` — dropdown to select the dispenser type
- `volume_flow` — flow rate in ml/s
- `tube_volume` — tube volume in ml
- `consumption_estimation` — time or weight based
- `carriage_position` — position 0–100%

Only define your **extra** fields in `CONFIG_FIELDS`.
These will appear in the configuration UI between the pump type dropdown and the shared fields.
While you might not need all these shared fields for every dispenser, they are commonly used and provide a consistent configuration experience across dispenser types.

## ExtensionConfig

Your `ExtensionConfig` must inherit from `BasePumpConfig`.
Define any extra attributes your dispenser needs and make sure to call `super().__init__()` with the shared fields.
The `to_config()` method must serialize all fields (call `super().to_config()` and update with your extras).

!!! warning "Accept **kwargs"
    Your `__init__` should accept `**kwargs` to be forward-compatible with future shared fields.

## Implementation

Your `Implementation` class must inherit from `BaseDispenser` and implement these methods:

| Method                                   | Required | Description                                                                                                                                        |
| ---------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `setup()`                                | **yes**  | Initialize hardware resources                                                                                                                      |
| `_dispense_steps(amount_ml, pump_speed)` | **yes**  | Generator that yields consumption values. Use `try/finally` for hardware cleanup. See details below.                                               |
| `stop()`                                 | no       | Emergency stop. Default sets the internal stop event. Override and call `super().stop()` if you need additional hardware cleanup (e.g. close pin). |
| `cleanup()`                              | no       | Release hardware resources at shutdown. Default does nothing.                                                                                      |

The constructor receives `slot` (pump position), `config` (your `ExtensionConfig` instance), `hardware` (`HardwareContext` — provides access to pin controller, scale, LED controller, carriage, and `extra` dict of hardware extension instances).

### How `_dispense_steps()` Works

The base class provides a concrete `dispense()` method that drives your generator automatically:

1. Clears the stop event
2. Tares the scale (if connected)
3. Iterates your `_dispense_steps()` generator
4. Checks for cancellation between each yield
5. Calls progress callbacks on each yielded value

Your generator just needs to: activate hardware, yield consumption updates in a loop, and deactivate hardware in a `finally` block. The `finally` block runs on both normal completion and cancellation (the generator is automatically closed when the stop event fires).

## Inherited Attributes & Helpers

`BaseDispenser` provides several attributes and methods you can use in your implementation — no need to define them yourself:

| Attribute / Method                | Description                                                                                                                                                 |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `self.slot`                       | Pump slot number (int), set from constructor                                                                                                                |
| `self.config`                     | Your `ExtensionConfig` instance                                                                                                                             |
| `self.volume_flow`                | Configured flow rate in ml/s (from config)                                                                                                                  |
| `self.carriage_position`          | Carriage position 0–100 (from config)                                                                                                                       |
| `self.hardware`                   | `HardwareContext` — access to `pin_controller`, `led_controller`, `scale`, `carriage`, and `extra` (see [Hardware Context Extensions](hardware-context.md)) |
| `self._scale`                     | `ScaleInterface` or `None` — the connected scale, if any and dispensing is based on weight                                                                  |
| `self._get_consumption(estimate)` | Returns the scale reading in ml if a scale is present, otherwise returns the passed time/step-based `estimate`                                              |
| `self.needs_exclusive`            | Property, `True` when a scale is attached. Used by the scheduler to run this dispenser exclusively (not in parallel with others)                            |

### Using the Scale

Scale taring is handled automatically by the base `dispense()` method. In your `_dispense_steps()` generator, just use `_get_consumption()` to transparently read either the scale or a time-based estimate:

```python
# In your _dispense_steps loop, use _get_consumption instead of a raw time estimate:
time_estimate = elapsed * effective_flow
consumption = self._get_consumption(time_estimate)
# If a scale is present, this returns the actual weight reading.
# Otherwise it returns your time_estimate as a fallback.
```

## Lifecycle

Dispenser extensions follow this lifecycle:

1. **Discovery & variant registration** — Extensions are discovered and registered as variants of `PUMP_CONFIG` before config is read.
2. **Config load** — The GUI can now show and edit the dispenser extension fields.
3. **Construction** — During `init_machine()`, after the scale and carriage are created, `Implementation(slot, config, hardware)` is called once per pump slot. You receive the fully assembled `HardwareContext` (pin controller, LEDs, scale, carriage, `extra`).
4. **Runtime use** — The scheduler calls `dispense(amount_ml, pump_speed, callback)` on each slot. The base class drives your `_dispense_steps()` generator and dispatches progress updates. `stop()` may be called from another thread to cancel.
5. **`cleanup()`** — Called at shutdown to release hardware resources.

## Full Example

Below is a complete example of a simple dummy dispenser that simulates dispensing via sleep:

```python
from __future__ import annotations

import time
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from src import ConsumptionEstimationType
from src.config.config_types import BasePumpConfig, ConfigInterface, StringType # (1)!
from src.logger_handler import LoggerHandler
from src.machine.dispensers.base import BaseDispenser # (2)!

if TYPE_CHECKING:
    from src.machine.hardware import HardwareContext


EXTENSION_NAME = "Dummy" # (3)!
_logger = LoggerHandler("DummyDispenser")


class ExtensionConfig(BasePumpConfig): # (4)!
    """Dummy dispenser config with a custom label field."""

    label: str

    def __init__(
        self,
        label: str = "dummy",
        pump_type: str = EXTENSION_NAME,
        volume_flow: float = 30.0,
        tube_volume: int = 0,
        consumption_estimation: ConsumptionEstimationType = "time",
        carriage_position: int = 0,
        **kwargs: Any, # (5)!
    ) -> None:
        super().__init__(
            pump_type=pump_type,
            volume_flow=volume_flow,
            tube_volume=tube_volume,
            consumption_estimation=consumption_estimation,
            carriage_position=carriage_position,
        )
        self.label = label

    def to_config(self) -> dict[str, Any]: # (6)!
        config = super().to_config()
        config.update({"label": self.label})
        return config


CONFIG_FIELDS: dict[str, ConfigInterface] = { # (7)!
    "label": StringType(default="dummy"),
}


class Implementation(BaseDispenser): # (8)!
    """Dummy dispenser that simulates dispensing via sleep."""

    def __init__(
        self, slot: int, config: ExtensionConfig, hardware: HardwareContext,
    ) -> None:
        super().__init__(slot, config, hardware)
        self.label = config.label

    def setup(self) -> None: # (9)!
        _logger.info(f"Dummy dispenser '{self.label}' slot {self.slot} set up")

    def _dispense_steps( # (10)!
        self, amount_ml: float, pump_speed: int
    ) -> Generator[float, None, None]:
        effective_flow = self.volume_flow * pump_speed / 100
        step_interval = 0.1
        elapsed = 0.0

        _logger.info(
            f"Dummy '{self.label}' slot {self.slot}: "
            f"dispensing {amount_ml:.1f} ml"
        )
        consumption = 0.0
        try:
            # >>> Activate your hardware here <<<
            while True: # (11)!
                time.sleep(step_interval)
                elapsed += step_interval
                time_estimate = min(elapsed * effective_flow, amount_ml)
                consumption = self._get_consumption(time_estimate)
                yield consumption # (12)!
                if consumption >= amount_ml:
                    return
        finally:
            # >>> Deactivate your hardware here <<< (13)!
            _logger.info(
                f"Dummy '{self.label}' slot {self.slot}: "
                f"done, dispensed {consumption:.1f} ml"
            )

    def cleanup(self) -> None: # (14)!
        _logger.info(
            f"Dummy dispenser '{self.label}' slot {self.slot} cleaned up"
        )
```

1. Import `BasePumpConfig` for your config class and any config field types you need (here `StringType`).
2. Import `BaseDispenser` — the base class for all dispensers.
3. Unique name that appears in the pump type dropdown. Must match the `pump_type` default in your `ExtensionConfig`.
4. Your config class must inherit from `BasePumpConfig`. Add any extra attributes your dispenser needs.
5. Always accept `**kwargs` to stay forward-compatible with future shared fields.
6. Serialize all fields — call `super().to_config()` first, then update with your extra fields.
7. Only define your **extra** config fields here. Shared fields (`volume_flow`, `tube_volume`, etc.) and the `pump_type` dropdown are auto-injected.
8. Your dispenser implementation must inherit from `BaseDispenser`.
9. Called once to initialize hardware resources (e.g. GPIO pins, SPI buses).
10. Generator that yields consumption values. The base `dispense()` method handles stop events, scale taring, and progress callbacks — you just yield.
11. Use a simple `while True` loop. No need to check `self._stop_event` — the base class checks it between yields and closes the generator on cancellation.
12. Yield the current consumption. The base class passes this to the scheduler's progress callback. Important to do this regularly (e.g. every 0.1s) so the UI can update and cancellations are responsive.
13. The `finally` block runs on both normal completion and cancellation — use it for hardware cleanup (e.g. closing relay pins, stopping motors).
14. Called at program shutdown to release hardware resources.
