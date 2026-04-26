# Scales

Custom scales let you drive any load-cell amplifier or weighing hardware that CocktailBerry does not support out of the box.
Each scale extension is a single Python file placed in the `addons/scales/` folder.
Once added, the new scale type appears in the scale configuration dropdown alongside the built-in `HX711` and `NAU7802` drivers.

Unlike dispensers, a **single** scale is created per machine (one `SCALE_CONFIG` entry).
It is wired into the `HardwareContext` and shared across all weight-based dispensers — any dispenser referencing the scale is automatically scheduled exclusively (no parallel dispensing) so readings stay consistent.

For scales, the base classes are:

- `ExtensionConfig` inherits from **`BaseScaleConfig`** (`src.config.config_types`)
- `Implementation` inherits from **`ScaleInterface`** (`src.machine.scale.base`)

## Getting Started

!!! tip "Use the CLI"
    Create a skeleton file with the CLI command:

    ```bash
    uv run runme.py create-scale "Your Scale Name"
    ```

    This creates a ready-to-fill file in `addons/scales/your_scale_name.py`.

## Shared vs Custom Config Fields

Every scale automatically gets the following shared fields injected — you do **not** need to define them:

- `scale_type` — dropdown to select the scale driver
- `enabled` — whether the scale is active
- `calibration_factor` — raw-units-per-gram, written by the calibration routine
- `zero_raw_offset` — raw ADC reading that corresponds to an empty scale (also persisted during calibration)

Only define your **extra** fields in `CONFIG_FIELDS` (e.g. data/clock pins, I²C address, spi bus, …).
These will appear in the configuration UI between the scale type dropdown and the shared fields.

## ExtensionConfig

Your `ExtensionConfig` must inherit from `BaseScaleConfig`.
Define any extra attributes your scale needs and make sure to call `super().__init__()` with the shared fields.
The `to_config()` method must serialize all fields (call `super().to_config()` and update with your extras).

!!! warning "Accept **kwargs"
    Your `__init__` should accept `**kwargs` to be forward-compatible with future shared fields.

## Implementation

Your `Implementation` class must inherit from `ScaleInterface` and implement the following abstract methods:

| Method              | Required | Description                                                                                                                                    |
| ------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `tare(samples)`     | **yes**  | Capture the current raw reading as the dynamic tare offset. Subsequent `read_grams()` calls are relative to this point. Returns the raw value. |
| `read_grams()`      | **yes**  | Return the weight in grams relative to the last `tare()` call.                                                                                 |
| `read_raw(samples)` | **yes**  | Return the averaged raw ADC reading (no offset, no calibration). Used during calibration.                                                      |
| `cleanup()`         | **yes**  | Release any hardware resources held by the scale.                                                                                              |
| `get_gross_grams()` | **yes**  | Return the absolute weight in grams relative to `_zero_raw_offset` (the one-time empty-scale calibration). Used for glass detection etc.       |

The constructor receives `config` (your `ExtensionConfig` instance) and `hardware` (`HardwareContext` — provides access to pin controller, LED controller, and `extra` dict of hardware extension instances). Built-in scales may ignore `hardware`; extensions may use it to access pins or shared hardware.

## Inherited Attributes & Helpers

`ScaleInterface` provides the following for your implementation:

| Attribute / Method                                                   | Description                                                                                                                            |
| -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `self.config`                                                        | Your `ExtensionConfig` instance                                                                                                        |
| `self.hardware`                                                      | `HardwareContext` — access to `pin_controller`, `led_controller`, and `extra` (see [Hardware Context Extensions](hardware-context.md)) |
| `self._calibration_factor`                                           | Raw-units-per-gram, loaded from config. Use it in `read_grams()` / `get_gross_grams()`.                                                |
| `self._zero_raw_offset`                                              | Raw ADC reading corresponding to 0 g on an empty scale. Written during one-time calibration.                                           |
| `calibrate_with_known_weight(weight_g, zero_raw_offset, samples=10)` | Default implementation: computes the scale factor from a known weight and persists it. Override if your scale needs a custom routine.  |
| `set_calibration_factor(factor)` / `set_zero_raw_offset(offset)`     | Setters used by the calibration flow. Override if you need additional side-effects (e.g. writing to EEPROM on the amplifier).          |

## Full Example

Below is a complete example of a fake software scale that reports a constant weight — useful as a template or for dry-running without hardware:

```python
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.config.config_types import BaseScaleConfig, ConfigInterface, FloatType # (1)!
from src.config.validators import build_number_limiter
from src.logger_handler import LoggerHandler
from src.machine.scale.base import ScaleInterface # (2)!

if TYPE_CHECKING:
    from src.machine.hardware import HardwareContext


EXTENSION_NAME = "FakeScale" # (3)!
_logger = LoggerHandler("FakeScale")


class ExtensionConfig(BaseScaleConfig): # (4)!
    """Fake scale config with a constant reading."""

    constant_grams: float

    def __init__(
        self,
        constant_grams: float = 100.0,
        scale_type: str = EXTENSION_NAME,
        enabled: bool = False,
        calibration_factor: float = 1.0,
        zero_raw_offset: int = 0,
        **kwargs: Any, # (5)!
    ) -> None:
        super().__init__(
            scale_type=scale_type,
            enabled=enabled,
            calibration_factor=calibration_factor,
            zero_raw_offset=zero_raw_offset,
        )
        self.constant_grams = constant_grams

    def to_config(self) -> dict[str, Any]: # (6)!
        config = super().to_config()
        config.update({"constant_grams": self.constant_grams})
        return config


CONFIG_FIELDS: dict[str, ConfigInterface] = { # (7)!
    "constant_grams": FloatType([build_number_limiter(0, 10000)], suffix="g"),
}


class Implementation(ScaleInterface): # (8)!
    """Fake scale that always reports ``constant_grams``."""

    def __init__(
        self, config: ExtensionConfig, hardware: HardwareContext,
    ) -> None:
        super().__init__(config, hardware)
        self._constant = config.constant_grams
        self._offset = 0
        _logger.info(f"Fake scale initialized with {self._constant}g")

    def _sample_raw(self, samples: int) -> int: # (9)!
        return int(self._constant * self._calibration_factor) + self._zero_raw_offset

    def tare(self, samples: int = 3) -> int:
        self._offset = self._sample_raw(samples)
        return self._offset

    def read_grams(self) -> float:
        return (self._sample_raw(1) - self._offset) / self._calibration_factor

    def read_raw(self, samples: int = 1) -> int:
        return self._sample_raw(samples)

    def get_gross_grams(self) -> float:
        return (self._sample_raw(1) - self._zero_raw_offset) / self._calibration_factor

    def cleanup(self) -> None: # (10)!
        _logger.info("Fake scale cleaned up")
```

1. Import `BaseScaleConfig` for your config class and any config field types you need (here `FloatType`).
2. Import `ScaleInterface` — the abstract base class for all scales.
3. Unique name that appears in the scale type dropdown. Must match the `scale_type` default in your `ExtensionConfig`.
4. Your config class must inherit from `BaseScaleConfig`. Add any extra attributes your scale needs.
5. Always accept `**kwargs` to stay forward-compatible with future shared fields.
6. Serialize all fields — call `super().to_config()` first, then update with your extra fields.
7. Only define your **extra** config fields here. Shared fields (`enabled`, `calibration_factor`, `zero_raw_offset`) and the `scale_type` dropdown are auto-injected.
8. Your scale implementation must inherit from `ScaleInterface`.
9. Helper to centralise raw-sample logic. Replace with real hardware reads (GPIO bit-bang, I²C/SPI transaction, serial protocol …).
10. Called at program shutdown — release GPIO, close buses, disable amplifier.
