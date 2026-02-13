from __future__ import annotations

from collections.abc import Callable

from src.config.errors import ConfigError


def validate_max_length(configname: str, data: str, max_len: int = 30) -> None:
    """Validate if data exceeds maximum length."""
    if len(data) <= max_len:
        return
    raise ConfigError(f"{configname} is longer than {max_len}, please reduce length")


def build_number_limiter(min_val: float = 1, max_val: float = 100) -> Callable[[str, (int | float)], None]:
    """Build the function: Check if the number is within the given limits."""

    def limit_number(configname: str, data: float) -> None:
        if data < min_val or data > max_val:
            raise ConfigError(f"{configname} must be between {min_val} and {max_val}.")

    return limit_number


def valide_no_identical_active_i2c_devices(configname: str, data: list[dict]) -> None:
    """Validate that no I2C device type is enabled more than once."""
    active_types = [d["device_type"] for d in data if d["enabled"]]
    duplicates = {t for t in active_types if active_types.count(t) > 1}
    if duplicates:
        raise ConfigError(
            f"{configname} has duplicate enabled device types: "
            f"{', '.join(duplicates)}. Each type can only be enabled once."
        )
