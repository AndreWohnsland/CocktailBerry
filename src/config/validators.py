from __future__ import annotations

from collections.abc import Callable
from typing import Any

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


def build_distinct_validator(keys: list[str], fallback: dict[str, Any] = {}) -> Callable[[str, list[dict]], None]:
    """Build a validator that checks list items have distinct values across the given keys.

    Each combination of values for the specified keys must be unique across all items in the list.
    Can provide fallback values for missing keys to ensure they are included in the uniqueness check.
    This is useful for sealed classes where different types may have different key sets.
    """

    def validate_distinct(configname: str, data: list[dict]) -> None:
        seen: list[tuple] = []
        for item in data:
            key_tuple = tuple(item.get(k, fallback.get(k, "undefined")) for k in keys)
            if key_tuple in seen:
                readable = ", ".join(f"{k}={item.get(k, 'undefined')}" for k in keys)
                raise ConfigError(
                    f"{configname} has duplicate entries for ({readable}). "
                    f"Each combination of {', '.join(keys)} must be unique."
                )
            seen.append(key_tuple)

    return validate_distinct


def validate_i2c_address(configname: str, data: str) -> None:
    """Validate that data is a valid I2C hex address string (e.g. '20', '2A', '3f').

    Accepts 1-2 hex characters (case-insensitive). Addresses must be in the valid
    7-bit I2C range (0x03-0x77). Stores uppercase internally.
    """
    if not data:
        raise ConfigError(f"{configname} must not be empty")
    try:
        value = int(data, 16)
    except ValueError:
        raise ConfigError(f"{configname} must be a valid hex address (e.g. '20', '2A'), got '{data}'")
    _min_i2c_address = 0x03
    _max_i2c_address = 0x77
    if value < _min_i2c_address or value > _max_i2c_address:
        raise ConfigError(f"{configname} must be a valid 7-bit I2C address (03-77 hex), got '{data}'")
