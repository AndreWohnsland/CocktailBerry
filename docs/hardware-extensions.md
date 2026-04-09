# Custom Hardware Extensions

CocktailBerry allows you to create your own implementations of hardware components.
This way you can integrate custom dispensers, scales, or carriages that are not natively supported.
Hardware extensions live in subfolders of the `addons` folder and are automatically discovered at startup.

!!! info "Only needed for unsupported hardware"
    In general, you only need to create custom hardware extensions if you have pumps, scales, or carriages that CocktailBerry does not support out of the box.
    If your hardware is already supported, you can configure it directly in the UI without any coding.

Supported types are:

- **Dispensers** — control pumps and valves for dispensing liquids
- **Scales** — read weight measurements for weight-based recipes and estimation
- **Carriages** — control the movement of the pump carriage for multi-position setups

## Extension Structure

Every hardware extension file — regardless of type — must export four things:

| Export           | Description                                                       |
| ---------------- | ----------------------------------------------------------------- |
| `EXTENSION_NAME` | Unique name shown in the configuration dropdown (e.g. `"MyPump"`) |
| `ConfigClass`    | Config class inheriting from the type-specific base config        |
| `CONFIG_FIELDS`  | Dict of **extra** config fields beyond the shared ones            |
| `Implementation` | Hardware class inheriting from the type-specific base class       |

The concrete base classes for `ConfigClass` and `Implementation` depend on the hardware type.
See the type-specific sections below for details.

### Available Config Field Types

Use these types from `src.config.config_types` to define your custom fields:

| Type         | Description   | Example                                                      |
| ------------ | ------------- | ------------------------------------------------------------ |
| `IntType`    | Integer input | `IntType([build_number_limiter(0)], prefix="Pin:")`          |
| `FloatType`  | Float input   | `FloatType([build_number_limiter(0.1, 100)], suffix="ml/s")` |
| `StringType` | Text input    | `StringType(default="my_value")`                             |
| `BoolType`   | Checkbox      | `BoolType(check_name="Enable Feature")`                      |
| `ChooseType` | Dropdown      | `ChooseType(allowed=["A", "B"], default="A")`                |

Validators like `build_number_limiter(min, max)` from `src.config.validators` can be used to constrain values.
You always can write your own, for more information, see also the config section under addons.

## Dispensers

Custom dispensers let you control any pump or valve hardware that CocktailBerry does not support out of the box.
Each dispenser extension is a single Python file placed in the `addons/dispensers/` folder.
Once added, the new dispenser type appears in the pump configuration dropdown alongside the built-in DC and Stepper types.

For dispensers, the base classes are:

- `ConfigClass` inherits from **`BasePumpConfig`** (`src.config.config_types`)
- `Implementation` inherits from **`BaseDispenser`** (`src.machine.dispensers.base`)

### Getting Started

First, clone the latest version of CocktailBerry in your development environment and install all dependencies with `uv sync`.

!!! tip "Use the CLI"
    Create a skeleton file with the CLI command:

    ```bash
    uv run runme.py create-dispenser "Your Dispenser Name"
    ```

    This creates a ready-to-fill file in `addons/dispensers/your-dispenser-name.py`.

### Shared vs Custom Config Fields

Every dispenser automatically gets the following shared fields injected — you do **not** need to define them:

- `pump_type` — dropdown to select the dispenser type
- `volume_flow` — flow rate in ml/s
- `tube_volume` — tube volume in ml
- `consumption_estimation` — time or weight based
- `carriage_position` — position 0–100%

Only define your **extra** fields in `CONFIG_FIELDS`.
These will appear in the configuration UI between the pump type dropdown and the shared fields.

### ConfigClass

Your `ConfigClass` must inherit from `BasePumpConfig`.
Define any extra attributes your dispenser needs and make sure to call `super().__init__()` with the shared fields.
The `to_config()` method must serialize all fields (call `super().to_config()` and update with your extras).

!!! warning "Accept **kwargs"
    Your `__init__` should accept `**kwargs` to be forward-compatible with future shared fields.

### Implementation

Your `Implementation` class must inherit from `BaseDispenser` and implement these methods:

| Method                                      | Required | Description                                                                                                                                                                                                         |
| ------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `setup()`                                   | **yes**  | Initialize hardware resources                                                                                                                                                                                       |
| `dispense(amount_ml, pump_speed, callback)` | **yes**  | Dispense the given amount. Must be **blocking**. Clear `self._stop_event` at the start, then check it for cancellation. Return actual consumption in ml. Call `callback(dispensed_ml, is_done)` to report progress. |
| `stop()`                                    | no       | Emergency stop. Default sets `self._stop_event`. Override and call `super().stop()` if you need additional hardware cleanup.                                                                                        |
| `cleanup()`                                 | no       | Release hardware resources at shutdown. Default does nothing.                                                                                                                                                       |

The constructor receives `slot` (pump position), `config` (your `ConfigClass` instance), and optionally `scale` (for weight-based estimation).

### Inherited Attributes & Helpers

`BaseDispenser` provides several attributes and methods you can use in your implementation — no need to define them yourself:

| Attribute / Method                           | Description                                                                                                                                                             |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `self.slot`                                  | Pump slot number (int), set from constructor                                                                                                                            |
| `self.config`                                | Your `ConfigClass` instance                                                                                                                                             |
| `self.volume_flow`                           | Configured flow rate in ml/s (from config)                                                                                                                              |
| `self.carriage_position`                     | Carriage position 0–100 (from config)                                                                                                                                   |
| `self._stop_event`                           | `threading.Event` — set by `stop()` to signal cancellation. Must be cleared at the start of `dispense()` via `self._stop_event.clear()`. Check it in your dispense loop |
| `self._scale`                                | `ScaleInterface` or `None` — the connected scale, if any                                                                                                                |
| `self._get_consumption(estimate)`            | Returns the scale reading in ml if a scale is present, otherwise returns the passed time/step-based `estimate`                                                          |
| `self.needs_exclusive`                       | Property, `True` when a scale is attached. Used by the scheduler to run this dispenser exclusively (not in parallel with others)                                        |

#### Using the Scale

If a scale is connected (`self._scale is not None`), you can use it for precise weight-based dispensing instead of relying on time estimates:

```python
# Tare the scale before dispensing
if self._scale is not None:
    self._scale.tare()

# In your dispense loop, use _get_consumption instead of a raw time estimate:
time_estimate = elapsed * effective_flow
consumption = self._get_consumption(time_estimate)
# If a scale is present, this returns the actual weight reading.
# Otherwise it returns your time_estimate as a fallback.
```

### Full Example

Below is a complete example of a simple dummy dispenser that simulates dispensing via sleep:

```python
from __future__ import annotations

import time
from typing import Any

from src import ConsumptionEstimationType
from src.config.config_types import BasePumpConfig, StringType # (1)!
from src.logger_handler import LoggerHandler
from src.machine.dispensers.base import BaseDispenser, ProgressCallback # (2)!
from src.machine.scale import ScaleInterface

EXTENSION_NAME = "Dummy" # (3)!
_logger = LoggerHandler("DummyDispenser")


class ConfigClass(BasePumpConfig): # (4)!
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


CONFIG_FIELDS: dict[str, Any] = { # (7)!
    "label": StringType(default="dummy"),
}


class Implementation(BaseDispenser): # (8)!
    """Dummy dispenser that simulates dispensing via sleep."""

    def __init__(
        self, slot: int, config: ConfigClass, scale: ScaleInterface | None = None
    ) -> None:
        super().__init__(slot, config, scale)
        self.label = config.label

    def setup(self) -> None: # (9)!
        _logger.info(f"Dummy dispenser '{self.label}' slot {self.slot} set up")

    def dispense( # (10)!
        self, amount_ml: float, pump_speed: int, callback: ProgressCallback
    ) -> float:
        self._stop_event.clear()
        effective_flow = self.volume_flow * pump_speed / 100
        total_time = amount_ml / effective_flow
        step_interval = 0.1
        elapsed = 0.0
        dispensed = 0.0

        _logger.info(
            f"Dummy '{self.label}' slot {self.slot}: "
            f"dispensing {amount_ml:.1f} ml over {total_time:.1f}s"
        )
        while dispensed < amount_ml and not self._stop_event.is_set(): # (11)!
            time.sleep(step_interval)
            elapsed += step_interval
            dispensed = min(elapsed * effective_flow, amount_ml)
            callback(dispensed, False) # (12)!

        callback(dispensed, True)
        return dispensed

    def stop(self) -> None: # (13)!
        super().stop()

    def cleanup(self) -> None: # (14)!
        _logger.info(
            f"Dummy dispenser '{self.label}' slot {self.slot} cleaned up"
        )
```

1. Import `BasePumpConfig` for your config class and any config field types you need (here `StringType`).
2. Import `BaseDispenser` and `ProgressCallback` — the base class and callback signature for all dispensers.
3. Unique name that appears in the pump type dropdown. Must match the `pump_type` default in your `ConfigClass`.
4. Your config class must inherit from `BasePumpConfig`. Add any extra attributes your dispenser needs.
5. Always accept `**kwargs` to stay forward-compatible with future shared fields.
6. Serialize all fields — call `super().to_config()` first, then update with your extra fields.
7. Only define your **extra** config fields here. Shared fields (`volume_flow`, `tube_volume`, etc.) and the `pump_type` dropdown are auto-injected.
8. Your dispenser implementation must inherit from `BaseDispenser`.
9. Called once to initialize hardware resources (e.g. GPIO pins, SPI buses).
10. Core dispensing logic. Must be **blocking** — return only when done or cancelled. Clear `self._stop_event` at the start to reset from any previous `stop()`. Return actual consumption in ml.
11. Check `self._stop_event` regularly to support cancellation during dispensing.
12. Report progress via the callback: `callback(dispensed_ml, is_done)`. Use `False` for intermediate updates, `True` when finished.
13. Called on emergency stop. Setting `self._stop_event` (via `super().stop()`) will cause the `dispense()` loop to exit.
14. Called at program shutdown to release hardware resources.

## Scales

*TBD*

## Carriages

*TBD*
