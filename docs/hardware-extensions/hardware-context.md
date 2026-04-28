# Hardware Context Extensions

Hardware context extensions let you register **shared hardware** — such as a UART board, SPI bus, or any custom controller — that multiple dispenser extensions (or other code) can access at runtime.
Each hardware context extension is a single Python file placed in the `addons/hardware/` folder.
Once added, the extension gets its own configuration page in the UI and its instance is stored in `HardwareContext.extra["YourExtensionName"]` for other components to access.

Unlike dispenser extensions, which create one instance *per pump slot*, a hardware context extension creates **one instance per extension**.
Dispensers (and other extension code) access it from the `HardwareContext` they receive.

This is the recommended approach when:

- Multiple pumps share a single communication bus (e.g. a UART board controlling N pumps)
- You need one-time initialization for hardware that several dispensers depend on
- You want GUI-configurable settings for that shared hardware (not hard-coded)

For hardware context extensions, the base classes are:

- `ExtensionConfig` inherits from **`ConfigClass`** (`src.config.config_types`)
- `Implementation` inherits from **`BaseHardwareExtension`** (`src.programs.addons`)

## Getting Started

!!! tip "Use the CLI"
    Create a skeleton file with the CLI command:

    ```bash
    uv run runme.py create-hardware "Your Hardware Name"
    ```

    This creates a ready-to-fill file in `addons/hardware/your_hardware_name.py`.

## Shared vs Custom Config Fields

Unlike dispenser, scale, and carriage extensions, hardware context extensions have **no shared fields** — define every field your hardware needs yourself in `CONFIG_FIELDS` and on `ExtensionConfig`.
The framework registers the whole config under the key `HW_<EXTENSION_NAME>` (uppercase, spaces replaced with underscores), so each hardware extension gets its own top-level config page in the UI.

## ExtensionConfig

Your `ExtensionConfig` must inherit from `ConfigClass`.
Define every attribute your hardware needs and assign them in `__init__`.
The `to_config()` method must serialize all fields to a dict; `from_config()` must rebuild the instance from a dict.

!!! warning "Accept **kwargs"
    Your `__init__` should accept `**kwargs` to be forward-compatible with future framework fields.

## Implementation

Your `Implementation` class must inherit from `BaseHardwareExtension[ExtensionConfig]` and implement these methods:

| Method               | Required | Description                                                                                                                                       |
| -------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `create(config)`     | **yes**  | Build and return the shared hardware instance. The returned object is stored in `hardware.extra["EXTENSION_NAME"]` and may be of any type.        |
| `cleanup(instance)`  | **yes**  | Release resources held by the instance previously returned from `create()`. Called at shutdown before core hardware is released.                  |

The actual hardware class itself can be any Python class — `BaseHardwareExtension` only manages the lifecycle, not the shape of the instance.

## Inherited Attributes & Helpers

`BaseHardwareExtension` is a thin lifecycle wrapper and provides no inherited attributes or helpers — your `Implementation` is stateless aside from what `create()` returns.
All state belongs on the hardware class you return from `create()`.

## Lifecycle

Hardware context extensions follow this lifecycle:

1. **Discovery & config registration** — Extensions are discovered and `CONFIG_FIELDS` are registered before config is read. The config key is `HW_<EXTENSION_NAME>` (uppercase, spaces replaced with underscores).
2. **Config load** — The GUI can now show and edit the hardware extension fields.
3. **`Implementation.create(config)`** — Called during `init_machine()`, before specific hardware (sub-)components are set up. The returned instance is stored in `hardware.extra["YourExtensionName"]`.
4. **Component set up** — Other components like scales, carriages, and dispensers receive the full `HardwareContext` (including `extra`). They access your hardware via `hardware.extra["YourExtensionName"]`.
5. **`Implementation.cleanup(instance)`** — Called at shutdown, before pins and other core hardware are released.

## Full Example

Below is a complete example of a hardware extension for a hypothetical UART pump board:

```python
from __future__ import annotations

from typing import Any

from src.config.config_types import ConfigClass, ConfigInterface, IntType, StringType # (1)!
from src.config.validators import build_number_limiter
from src.logger_handler import LoggerHandler
from src.programs.addons import BaseHardwareExtension # (2)!

EXTENSION_NAME = "UartBoard" # (3)!
_logger = LoggerHandler("UartBoard")


class ExtensionConfig(ConfigClass): # (4)!
    """Configuration for the UART pump board."""

    port: str
    baud_rate: int

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baud_rate: int = 9600,
        **kwargs: Any, # (5)!
    ) -> None:
        self.port = port
        self.baud_rate = baud_rate

    def to_config(self) -> dict[str, Any]: # (6)!
        return {"port": self.port, "baud_rate": self.baud_rate}

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ExtensionConfig: # (7)!
        return cls(**config)


CONFIG_FIELDS: dict[str, ConfigInterface] = { # (8)!
    "port": StringType(default="/dev/ttyUSB0"),
    "baud_rate": IntType([build_number_limiter(1200, 115200)]),
}


class UartConnection: # (9)!
    """Singleton-like UART connection managed by the framework."""

    def __init__(self, port: str, baud_rate: int) -> None:
        self.port = port
        self.baud_rate = baud_rate
        _logger.info(
            f"Connected to UART board on {port} @ {baud_rate}"
        )

    def send_command(self, pump_id: int, amount: float) -> None:
        """Send a dispense command to a specific pump."""
        # Your serial communication logic here
        pass

    def close(self) -> None:
        _logger.info("UART connection closed")


class Implementation(BaseHardwareExtension[ExtensionConfig]):  # (10)!
    """Manages the UART board lifecycle."""

    def create(self, config: ExtensionConfig) -> UartConnection:  # (11)!
        return UartConnection(config.port, config.baud_rate)

    def cleanup(self, instance: UartConnection) -> None:  # (12)!
        instance.close()
```

1. Import `ConfigClass` for your config and any field types you need. `ConfigInterface` is the type hint for the `CONFIG_FIELDS` dict values.
2. Import `BaseHardwareExtension` — the base class for all hardware context extensions.
3. Unique name used to identify this extension. The config key will be `HW_UARTBOARD`. Dispensers access the instance via `hardware.extra["UartBoard"]`.
4. Your config class must inherit from `ConfigClass`. Define all settings your hardware needs as attributes.
5. Always accept `**kwargs` to stay forward-compatible with future framework fields.
6. Serialize all fields to a dict — the framework calls this to persist your config.
7. Deserialize from a dict — the framework calls this to restore your config from the saved state.
8. Define your config fields here. These appear in the configuration UI so the user can adjust settings. Use validators like `build_number_limiter` to constrain values.
9. This is your actual hardware class — it can be any type you want. The framework stores the instance returned by `create()` in `hardware.extra["UartBoard"]` so dispensers can use it.
10. Your implementation must inherit from `BaseHardwareExtension`, parameterized with your `ExtensionConfig` type.
11. Called once during `init_machine()`. Create and return your hardware instance here. The return value can be any type — your dispenser extensions cast it accordingly.
12. Called at shutdown to release resources. Receives the same instance that `create()` returned.

## Using from a Dispenser Extension

A dispenser extension accesses the hardware context extension via `self.hardware.extra`:

```python
class Implementation(BaseDispenser):
    def __init__(self, slot, config, hardware):
        super().__init__(slot, config, hardware)
        self._board = hardware.extra["UartBoard"] # (1)!

    def _dispense_steps(self, amount_ml, pump_speed):
        self._board.send_command(self.slot, amount_ml) # (2)!
        # ... yield consumption updates ...
```

1. The key must match the `EXTENSION_NAME` of your hardware context extension. The framework guarantees that hardware extensions are created before dispensers, so the instance is always available here.
2. You can now call any method on the shared hardware instance. Since all dispensers receive the same `HardwareContext`, they all share the same `UartConnection` object.

For the full dispenser extension guide (including `hardware` access), see [Dispensers](dispensers.md).
