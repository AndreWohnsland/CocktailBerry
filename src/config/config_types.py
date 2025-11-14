"""Module for configuration types.

They are used to wrap the validation of different types and composition within the yaml config file.
Simply separating by build in types is not enough for dict or list types.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Protocol, TypeVar, get_args

from src import SupportedLanguagesType, SupportedLedStatesType, SupportedRfidType, SupportedThemesType
from src.config.errors import ConfigError

SUPPORTED_LANGUAGES = list(get_args(SupportedLanguagesType))
SUPPORTED_THEMES = list(get_args(SupportedThemesType))
SUPPORTED_RFID = list(get_args(SupportedRfidType))
SUPPORTED_LED_STATES = list(get_args(SupportedLedStatesType))


class ConfigInterface(Protocol):
    """Interface for config values."""

    prefix: str | None = None
    suffix: str | None = None

    @abstractmethod
    def validate(self, configname: str, value: Any) -> None:
        """Validate the given value."""
        raise NotImplementedError

    @property
    @abstractmethod
    def ui_type(self) -> type:
        """Return the type for the UI."""
        raise NotImplementedError

    def from_config(self, value: Any) -> Any:
        """Serialize the given value."""
        return value

    def to_config(self, value: Any) -> Any:
        """Deserialize the given value."""
        return value


@dataclass
class ChooseType(ConfigInterface):
    """Base Class for auto generated single select drop down."""

    allowed: list[str] = field(default_factory=list)
    validator_functions: list[Callable[[str, Any], None]] = field(default_factory=list)

    def validate(self, configname: str, value: Any) -> None:
        if value not in self.allowed:
            raise ConfigError(f"Value <{value}> for '{configname}' is not supported, please use any of {self.allowed}")
        for validator in self.validator_functions:
            validator(configname, value)

    @property
    def ui_type(self) -> type[ChooseType]:
        return type(self)


class ChooseOptions:
    language = ChooseType(allowed=SUPPORTED_LANGUAGES)
    rfid = ChooseType(allowed=SUPPORTED_RFID)
    theme = ChooseType(allowed=SUPPORTED_THEMES)
    leds = ChooseType(allowed=SUPPORTED_LED_STATES)


@dataclass
class ConfigType(ConfigInterface):
    """Base class for configuration types."""

    config_type: type[str | int | float | bool]
    validator_functions: list[Callable[[str, Any], None]] = field(default_factory=list)
    prefix: str | None = None
    suffix: str | None = None

    def validate(self, configname: str, value: Any) -> None:
        """Validate the given value."""
        if not isinstance(value, self.config_type):
            raise ConfigError(f"The value <{value}> for '{configname}' is not of type {self.config_type}")
        for validator in self.validator_functions:
            validator(configname, value)

    @property
    def ui_type(self) -> type[str | int | float | bool]:
        """Return the type for the UI."""
        return self.config_type


class StringType(ConfigType):
    """String configuration type."""

    def __init__(
        self,
        validator_functions: list[Callable[[str, Any], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> None:
        super().__init__(str, validator_functions, prefix, suffix)


class IntType(ConfigType):
    """Integer configuration type."""

    def __init__(
        self,
        validator_functions: list[Callable[[str, Any], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> None:
        super().__init__(int, validator_functions, prefix, suffix)


class FloatType(ConfigType):
    """Float configuration type."""

    def __init__(
        self,
        validator_functions: list[Callable[[str, Any], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> None:
        super().__init__(float, validator_functions, prefix, suffix)

    def validate(self, configname: str, value: Any) -> None:
        """Validate the given value."""
        # also accepts integers since they are basically floats
        if not (isinstance(value, (int, float))):
            raise ConfigError(f"The value <{value}> for '{configname}' is not of type {self.config_type}")
        for validator in self.validator_functions:
            validator(configname, value)

    def to_config(self, value: float) -> float:
        """Deserialize the given value."""
        # deserialize to a float (in case an int was given)
        return float(value)


class BoolType(ConfigType):
    """Boolean configuration type."""

    def __init__(
        self,
        validator_functions: list[Callable[[str, Any], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
        check_name: str = "on",
    ) -> None:
        super().__init__(bool, validator_functions, prefix, suffix)
        self.check_name = check_name


class ListType(ConfigType):
    """List configuration type."""

    def __init__(
        self,
        list_type: ConfigType,
        min_length: int | Callable[[], int],
        validator_functions: list[Callable[[str, Any], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
        immutable: bool = False,
    ) -> None:
        # ignore type here, since parent class should only expose other types not child types
        super().__init__(list, validator_functions, prefix, suffix)  # type: ignore
        self.list_type = list_type
        # might be a callable to allow dynamic min length, if dependent on other config values
        self.min_length = min_length
        self.immutable = immutable

    def validate(self, configname: str, value: Any) -> None:
        """Validate the given value."""
        super().validate(configname, value)
        # check for min length
        min_len = self.min_length if isinstance(self.min_length, int) else self.min_length()
        actual_len = len(value)
        if actual_len < min_len:
            raise ConfigError(f"{configname} got only {actual_len} elements, but you need at least {min_len} elements")
        for i, item in enumerate(value, 1):
            config_text = f"{configname} at position {i}"
            self.list_type.validate(config_text, item)

    def from_config(self, value: Any) -> Any:
        return [self.list_type.from_config(item) for item in value]

    def to_config(self, value: Any) -> Any:
        return [self.list_type.to_config(item) for item in value]


class ConfigClass:
    # keep method to show that child implementation have at least one attribute for initialization
    def __init__(self, **kwargs: Any) -> None:
        pass

    def to_config(self) -> dict[str, Any]:
        """Serialize the given value."""
        return {}

    @classmethod
    def from_config(cls, config: dict) -> ConfigClass:
        """Deserialize the given value."""
        return cls(**config)


class PumpConfig(ConfigClass):
    def __init__(self, pin: int, volume_flow: float, tube_volume: int) -> None:
        self.pin = pin
        self.volume_flow = volume_flow
        self.tube_volume = tube_volume

    def to_config(self) -> dict[str, int | float]:
        return {"pin": self.pin, "volume_flow": self.volume_flow, "tube_volume": self.tube_volume}


class NormalLedConfig(ConfigClass):
    """LED configuration for normal (non-WS281x) LEDs."""

    def __init__(self, led_type: str = "normal", pins: list[int] | None = None) -> None:
        self.type = led_type
        self.pins = pins if pins is not None else []

    def to_config(self) -> dict[str, Any]:
        return {"type": self.type, "pins": self.pins}

    @classmethod
    def from_config(cls, config: dict) -> NormalLedConfig:
        return cls(led_type=config.get("type", "normal"), pins=config.get("pins", []))


class WsLedConfig(ConfigClass):
    """LED configuration for WS281x addressable LEDs."""

    def __init__(
        self,
        led_type: str = "ws281x",
        pin: int = 18,
        count: int = 24,
        brightness: int = 100,
        number_rings: int = 1,
    ) -> None:
        self.type = led_type
        self.pin = pin
        self.count = count
        self.brightness = brightness
        self.number_rings = number_rings

    def to_config(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "pin": self.pin,
            "count": self.count,
            "brightness": self.brightness,
            "number_rings": self.number_rings,
        }

    @classmethod
    def from_config(cls, config: dict) -> WsLedConfig:
        return cls(
            led_type=config.get("type", "ws281x"),
            pin=config.get("pin", 18),
            count=config.get("count", 24),
            brightness=config.get("brightness", 100),
            number_rings=config.get("number_rings", 1),
        )


T = TypeVar("T", bound="ConfigClass")


class DictType(ConfigType, Generic[T]):
    """Dict configuration type."""

    def __init__(
        self,
        dict_types: dict[str, ConfigType],
        config_class: type[T],
        validator_functions: list[Callable[[str, Any], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> None:
        # ignore type here, since parent class should only expose other types not child types
        super().__init__(dict, validator_functions, prefix, suffix)  # type: ignore
        self.dict_types = dict_types
        self.config_class = config_class

    def validate(self, configname: str, config_dict: dict[str, Any]) -> None:
        """Validate the given value."""
        super().validate(configname, config_dict)
        for key_name, key_type in self.dict_types.items():
            key_value = config_dict.get(key_name)
            if key_value is None:
                raise ConfigError(f"Config value for '{key_name}' is missing in '{configname}'")
            key_text = f"{configname} key {key_name}"
            key_type.validate(key_text, key_value)

    def from_config(self, config_dict: dict[str, Any]) -> ConfigClass:
        """Deserialize the given value."""
        return self.config_class.from_config(config_dict)

    def to_config(self, config_class: T) -> dict[str, Any]:
        """Serialize the given value."""
        return config_class.to_config()


class UnionType(ConfigType, Generic[T]):
    """Union configuration type that supports polymorphic config classes.

    This type allows selecting between multiple config class variants based on a discriminator field.
    Each variant has its own set of fields and validation.
    """

    def __init__(
        self,
        type_field: str,
        variants: dict[str, tuple[type[T], dict[str, ConfigType]]],
        validator_functions: list[Callable[[str, Any], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> None:
        """Initialize UnionType.

        Args:
            type_field: The name of the discriminator field (e.g., "type")
            variants: Dict mapping type values to (ConfigClass, field_types) tuples
            validator_functions: Additional validation functions
            prefix: Optional prefix for UI display
            suffix: Optional suffix for UI display

        """
        # ignore type here, since parent class should only expose other types not child types
        super().__init__(dict, validator_functions, prefix, suffix)  # type: ignore
        self.type_field = type_field
        self.variants = variants

    def validate(self, configname: str, config_dict: dict[str, Any]) -> None:
        """Validate the given value."""
        super().validate(configname, config_dict)

        # Check that type field exists
        type_value = config_dict.get(self.type_field)
        if type_value is None:
            allowed_types = list(self.variants.keys())
            raise ConfigError(
                f"Config '{configname}' is missing required '{self.type_field}' field. "
                f"Allowed values: {allowed_types}"
            )

        # Check that type value is valid
        if type_value not in self.variants:
            allowed_types = list(self.variants.keys())
            raise ConfigError(
                f"Config '{configname}' has invalid {self.type_field}='{type_value}'. "
                f"Allowed values: {allowed_types}"
            )

        # Validate fields for this variant
        _, field_types = self.variants[type_value]
        for key_name, key_type in field_types.items():
            # Skip the type field itself as it's already validated
            if key_name == self.type_field:
                continue
            key_value = config_dict.get(key_name)
            if key_value is None:
                raise ConfigError(f"Config value for '{key_name}' is missing in '{configname}'")
            key_text = f"{configname} key {key_name}"
            key_type.validate(key_text, key_value)

    def from_config(self, config_dict: dict[str, Any]) -> ConfigClass:
        """Deserialize the given value."""
        type_value = config_dict.get(self.type_field)
        if type_value is None or type_value not in self.variants:
            # Fallback to first variant if type is missing or invalid
            type_value = next(iter(self.variants.keys()))

        config_class, _ = self.variants[type_value]
        return config_class.from_config(config_dict)

    def to_config(self, config_class: T) -> dict[str, Any]:
        """Serialize the given value."""
        return config_class.to_config()
