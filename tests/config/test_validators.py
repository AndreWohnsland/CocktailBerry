import pytest

from src.config.config_manager import WS281X_SUPPORTED_PINS
from src.config.errors import ConfigError
from src.config.validators import build_allowed_values


def test_allowed_values_accepts_member() -> None:
    check = build_allowed_values([10, 12, 18, 21])
    for pin in (10, 12, 18, 21):
        check("pin", pin)  # must not raise


def test_allowed_values_rejects_non_member() -> None:
    check = build_allowed_values([10, 12, 18, 21], "10=SPI, 12/18=PWM, 21=PCM")
    with pytest.raises(ConfigError, match="10=SPI"):
        check("pin", 13)  # PWM1, needs channel 1 -> not supported


def test_wsled_pin_set_is_the_channel0_pins() -> None:
    # Guard against silently widening the set; 13/19 must stay out until channel is derived.
    assert WS281X_SUPPORTED_PINS == [10, 12, 18, 21]
