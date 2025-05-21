from __future__ import annotations

from src.config.errors import ConfigError


def validate_max_length(configname: str, data: str, max_len: int = 30):
    """Validate if data exceeds maximum length."""
    if len(data) <= max_len:
        return
    raise ConfigError(f"{configname} is longer than {max_len}, please reduce length")


def build_number_limiter(min_val: int | float = 1, max_val: int | float = 100):
    """Build the function: Check if the number is within the given limits."""

    def limit_number(configname: str, data: int | float) -> None:
        if data < min_val or data > max_val:
            raise ConfigError(f"{configname} must be between {min_val} and {max_val}.")

    return limit_number
