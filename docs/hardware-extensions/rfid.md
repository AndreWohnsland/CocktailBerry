# RFID Readers

Custom RFID readers let you drive any NFC/RFID hardware that CocktailBerry does not support out of the box.
Each RFID extension is a single Python file placed in the `addons/rfid/` folder.
Once added, the new reader type appears in the RFID configuration dropdown alongside the built-in `No`, `MFRC522`, and `USB` drivers.

Unlike dispensers, a **single** RFID reader is created per machine (one `RFID_CONFIG` entry).
It is wired into the `HardwareContext` and shared across all RFID consumers — the NFC payment service, the waiter service, and the Qt RFID setup windows all access it through the `RFIDReader()` singleton facade.

For RFID readers, the base classes are:

- `ExtensionConfig` inherits from **`BaseRfidConfig`** (`src.config.config_types`)
- `Implementation` inherits from **`RFIDInterface`** (`src.machine.rfid.base`)

## Getting Started

!!! tip "Use the CLI"
    Create a skeleton file with the CLI command:

    ```bash
    uv run runme.py create-rfid "Your Reader Name"
    ```

    This creates a ready-to-fill file in `addons/rfid/your_reader_name.py`.

## Shared vs Custom Config Fields

Every RFID reader automatically gets the following shared fields injected — you do **not** need to define them:

- `rfid_type` — dropdown to select the RFID driver
- `enabled` — whether the reader is active

Only define your **extra** fields in `CONFIG_FIELDS` (e.g. SPI bus, USB reader index, polling interval, …).
These will appear in the configuration UI between the RFID type dropdown and the shared fields.

## ExtensionConfig

Your `ExtensionConfig` must inherit from `BaseRfidConfig`.
Define any extra attributes your reader needs and make sure to call `super().__init__()` with the shared fields.
The `to_config()` method must serialize all fields (call `super().to_config()` and update with your extras).

!!! warning "Accept **kwargs"
    Your `__init__` should accept `**kwargs` to be forward-compatible with future shared fields.

## Implementation

Your `Implementation` class must inherit from `RFIDInterface` and implement the following abstract methods:

| Method            | Required | Description                                                                                                                                            |
| ----------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `read_card()`     | **yes**  | Return a `(text, id)` tuple for a card currently in range, or `(None, None)` if no card is available. Should be non-blocking or use a short timeout.   |
| `write_card(text)`| **yes**  | Write `text` to the next card seen and return whether the operation succeeded. Return `False` immediately if your hardware does not support writing.   |
| `cleanup()`       | no       | Release any hardware resources held by the reader (close GPIO, SPI, USB). Default implementation is a no-op; override only if you hold resources.       |

The constructor receives `config` (your `ExtensionConfig` instance) and `hardware` (`HardwareContext` — provides access to pin controller, LED controller, scale, carriage, and `extra` dict of hardware extension instances). Built-in readers may ignore `hardware`; extensions may use it to access pins or shared hardware.

## Inherited Attributes & Helpers

`RFIDInterface` provides the following for your implementation:

| Attribute / Method | Description                                                                                                                                  |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `self.config`      | Your `ExtensionConfig` instance                                                                                                              |
| `self.hardware`    | `HardwareContext` — access to `pin_controller`, `led_controller`, `scale`, `carriage`, and `extra` (see [Hardware Context Extensions](hardware-context.md)) |
| `cleanup()`        | Default no-op base implementation. Override if your driver needs to close GPIO, SPI, or USB handles at shutdown.                              |

## Lifecycle

RFID extensions follow this lifecycle:

1. **Discovery & variant registration** — Extensions are discovered and registered as variants of `RFID_CONFIG` before config is read.
2. **Config load** — The GUI can now show and edit the RFID extension fields.
3. **Construction** — During `init_machine()`, after the carriage is created, `Implementation(config, hardware)` is called. You receive the full `HardwareContext` (pins, LEDs, scale, carriage, `extra`). The instance is wired into the context and attached to the `RFIDReader()` singleton.
4. **Runtime use** — The NFC payment service, the waiter service, and the Qt RFID setup windows call `RFIDReader().read_rfid(callback)` and `RFIDReader().write_rfid(value)`, which run on background threads and invoke your `read_card()` / `write_card()` in a loop.
5. **`cleanup()`** — Called at shutdown to release hardware resources (GPIO, SPI, USB).

## Full Example

Below is a complete example of a fake RFID reader that cycles through two static UIDs every minute — useful as a template or for dry-running without hardware:

```python
from __future__ import annotations

import time
from collections.abc import Iterator
from itertools import cycle
from typing import TYPE_CHECKING, Any

from src.config.config_types import BaseRfidConfig, ConfigInterface, FloatType # (1)!
from src.config.validators import build_number_limiter
from src.logger_handler import LoggerHandler
from src.machine.rfid.base import RFIDInterface # (2)!

if TYPE_CHECKING:
    from src.machine.hardware import HardwareContext


EXTENSION_NAME = "FakeRfid" # (3)!
_logger = LoggerHandler("FakeRfid")


class ExtensionConfig(BaseRfidConfig): # (4)!
    """Fake RFID config that emits a fixed pair of UIDs."""

    rotate_after_s: float

    def __init__(
        self,
        rotate_after_s: float = 60.0,
        rfid_type: str = EXTENSION_NAME,
        enabled: bool = False,
        **kwargs: Any, # (5)!
    ) -> None:
        super().__init__(
            rfid_type=rfid_type,
            enabled=enabled,
        )
        self.rotate_after_s = rotate_after_s

    def to_config(self) -> dict[str, Any]: # (6)!
        config = super().to_config()
        config.update({"rotate_after_s": self.rotate_after_s})
        return config


CONFIG_FIELDS: dict[str, ConfigInterface] = { # (7)!
    "rotate_after_s": FloatType([build_number_limiter(1.0, 3600.0)], suffix="s"),
}


class Implementation(RFIDInterface): # (8)!
    """Fake RFID reader cycling between two UIDs at a fixed interval."""

    def __init__(
        self, config: ExtensionConfig, hardware: HardwareContext,
    ) -> None:
        super().__init__(config, hardware)
        self._rotate_after_s = config.rotate_after_s
        self._ids: Iterator[str] = cycle(["DEADBEEF", "CAFEBABE"])
        self._current: str | None = None
        self._last_changed: float = 0.0
        _logger.info(f"Fake RFID initialized (rotate every {self._rotate_after_s}s)")

    def read_card(self) -> tuple[str | None, str | None]: # (9)!
        time.sleep(0.5)
        if time.time() - self._last_changed > self._rotate_after_s:
            self._current = next(self._ids)
            self._last_changed = time.time()
        return "Fake RFID payload", self._current

    def write_card(self, text: str) -> bool:
        return False

    def cleanup(self) -> None: # (10)!
        _logger.info("Fake RFID cleaned up")
```

1. Import `BaseRfidConfig` for your config class and any config field types you need (here `FloatType`).
2. Import `RFIDInterface` — the abstract base class for all RFID readers.
3. Unique name that appears in the RFID type dropdown. Must match the `rfid_type` default in your `ExtensionConfig`.
4. Your config class must inherit from `BaseRfidConfig`. Add any extra attributes your reader needs.
5. Always accept `**kwargs` to stay forward-compatible with future shared fields.
6. Serialize all fields — call `super().to_config()` first, then update with your extra fields.
7. Only define your **extra** config fields here. Shared fields (`enabled`) and the `rfid_type` dropdown are auto-injected.
8. Your reader implementation must inherit from `RFIDInterface`.
9. Implement `read_card()` non-blocking or with a short timeout so the read loop can be cancelled. Return `(None, None)` when no card is present.
10. Called at program shutdown — release GPIO, close SPI/USB handles. Skip the override if your driver holds no resources.
