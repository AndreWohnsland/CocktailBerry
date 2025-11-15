"""Module for configuration types.

They are used to wrap the validation of different types and composition within the yaml config file.
Simply separating by build in types is not enough for dict or list types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Protocol, TypeVar, get_args

from typing_extensions import Self

from src import SupportedLanguagesType, SupportedLedStatesType, SupportedRfidType, SupportedThemesType
from src.config.errors import ConfigError

SUPPORTED_LANGUAGES = list(get_args(SupportedLanguagesType))
SUPPORTED_THEMES = list(get_args(SupportedThemesType))
SUPPORTED_RFID = list(get_args(SupportedRfidType))
SUPPORTED_LED_STATES = list(get_args(SupportedLedStatesType))

T = TypeVar("T")


class ConfigInterface(Protocol[T]):
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

    @abstractmethod
    def get_default(self) -> Any:
        """Get the default value for this config type."""
        raise NotImplementedError

    def from_config(self, value: Any) -> T:
        """Serialize the given value."""
        return value

    def to_config(self, value: T) -> Any:
        """Deserialize the given value."""
        return value


@dataclass
class _ConfigType(ConfigInterface[T]):
    """Base class for configuration types holding type validation and iteratively executing validators.

    Used internally for reusing the same logic for different types.
    """

    config_type: type[str | int | float | bool | list | dict]
    validator_functions: Iterable[Callable[[str, Any], None]] = field(default_factory=list)
    prefix: str | None = None
    suffix: str | None = None

    def validate(self, configname: str, value: Any) -> None:
        """Validate the given value."""
        if not isinstance(value, self.config_type):
            raise ConfigError(f"The value <{value}> for '{configname}' is not of type {self.config_type}")
        for validator in self.validator_functions:
            validator(configname, value)

    @property
    def ui_type(self) -> type[str | int | float | bool | list | dict]:
        """Return the type for the UI."""
        return self.config_type

    def get_default(self) -> Any:  # noqa: PLR0911
        """Get the default value for this config type."""
        # Base implementation - specific types should override if needed
        if self.config_type is str:
            return ""
        if self.config_type is int:
            return 0
        if self.config_type is float:
            return 0.0
        if self.config_type is bool:
            return False
        if self.config_type is list:
            return []
        if self.config_type is dict:
            return {}
        return None


# NOTE: This is the only "special" class not using ConfigType as base class,
# since it does not fit into the type/validator scheme of the other types.
@dataclass
class ChooseType(ConfigInterface[str]):
    """Base Class for auto generated single select drop down."""

    allowed: list[str] = field(default_factory=list)
    validator_functions: Iterable[Callable[[str, Any], None]] = field(default_factory=list)

    def validate(self, configname: str, value: Any) -> None:
        if value not in self.allowed:
            raise ConfigError(f"Value <{value}> for '{configname}' is not supported, please use any of {self.allowed}")
        for validator in self.validator_functions:
            validator(configname, value)

    @property
    def ui_type(self) -> type[ChooseType]:
        return type(self)

    def get_default(self) -> str:
        """Get the default value - first allowed option."""
        return self.allowed[0] if self.allowed else ""


class ChooseOptions:
    language = ChooseType(allowed=SUPPORTED_LANGUAGES)
    rfid = ChooseType(allowed=SUPPORTED_RFID)
    theme = ChooseType(allowed=SUPPORTED_THEMES)
    leds = ChooseType(allowed=SUPPORTED_LED_STATES)


class StringType(_ConfigType[str]):
    """String configuration type."""

    def __init__(
        self,
        validator_functions: Iterable[Callable[[str, str], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> None:
        super().__init__(str, validator_functions, prefix, suffix)


class IntType(_ConfigType[int]):
    """Integer configuration type."""

    def __init__(
        self,
        validator_functions: Iterable[Callable[[str, int], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> None:
        super().__init__(int, validator_functions, prefix, suffix)


class FloatType(_ConfigType[float]):
    """Float configuration type."""

    def __init__(
        self,
        validator_functions: Iterable[Callable[[str, int | float], None]] = [],
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


class BoolType(_ConfigType[bool]):
    """Boolean configuration type."""

    def __init__(
        self,
        validator_functions: Iterable[Callable[[str, bool], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
        check_name: str = "on",
    ) -> None:
        super().__init__(bool, validator_functions, prefix, suffix)
        self.check_name = check_name


ListItemT = TypeVar("ListItemT")  # Type variable for items in a list


class ListType(_ConfigType[list[ListItemT]], Generic[ListItemT]):
    """List configuration type."""

    def __init__(
        self,
        list_type: ConfigInterface[ListItemT],
        min_length: int | Callable[[], int],
        validator_functions: Iterable[Callable[[str, Any], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
        immutable: bool = False,
    ) -> None:
        super().__init__(list, validator_functions, prefix, suffix)
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

    def from_config(self, value: Any) -> list[ListItemT]:
        return [self.list_type.from_config(item) for item in value]

    def to_config(self, value: list[ListItemT]) -> list[Any]:
        return [self.list_type.to_config(item) for item in value]

    def get_default(self) -> list[Any]:
        """Get the default value - empty list or list with min_length defaults."""
        min_len = self.min_length if isinstance(self.min_length, int) else 0
        if min_len > 0:
            # For immutable lists, fill with defaults
            return [self.list_type.get_default() for _ in range(min_len)]
        return []


ConfigClassT = TypeVar("ConfigClassT", bound="ConfigClass")


class ConfigClass(ABC):
    """Base class for configuration objects.

    Subclasses must implement the to_config() method to serialize their data.
    """

    # keep method to show that child implementation have at least one attribute for initialization
    def __init__(self, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def to_config(self) -> dict[str, Any]:
        """Serialize the given value."""
        ...

    @classmethod
    def from_config(cls, config: dict) -> Self:
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
    """Configuration for normal (non-WS281x) LEDs."""

    def __init__(
        self,
        led_type: str,
        pins: list[int],
        brightness: int,
        default_on: bool,
        preparation_state: str,
    ) -> None:
        self.led_type = led_type
        self.pins = pins
        self.brightness = brightness
        self.default_on = default_on
        self.preparation_state = preparation_state

    def to_config(self) -> dict[str, Any]:
        return {
            "led_type": self.led_type,
            "pins": self.pins,
            "brightness": self.brightness,
            "default_on": self.default_on,
            "preparation_state": self.preparation_state,
        }


class WS281xLedConfig(ConfigClass):
    """Configuration for WS281x (controllable) LEDs."""

    def __init__(
        self,
        led_type: str,
        pins: list[int],
        brightness: int,
        count: int,
        number_rings: int,
        default_on: bool,
        preparation_state: str,
    ) -> None:
        self.led_type = led_type
        self.pins = pins
        self.brightness = brightness
        self.count = count
        self.number_rings = number_rings
        self.default_on = default_on
        self.preparation_state = preparation_state

    def to_config(self) -> dict[str, Any]:
        return {
            "led_type": self.led_type,
            "pins": self.pins,
            "brightness": self.brightness,
            "count": self.count,
            "number_rings": self.number_rings,
            "default_on": self.default_on,
            "preparation_state": self.preparation_state,
        }


class DictType(_ConfigType[ConfigClassT]):
    """Dict configuration type.

    Generic over the ConfigClass type that it wraps.
    """

    def __init__(
        self,
        dict_types: Mapping[str, ConfigInterface[Any]],
        config_class: type[ConfigClassT],
        validator_functions: list[Callable[[str, Any], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> None:
        super().__init__(dict, validator_functions, prefix, suffix)
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

    def from_config(self, config_dict: dict[str, Any]) -> ConfigClassT:
        """Deserialize the given value."""
        return self.config_class.from_config(config_dict)

    def to_config(self, config_class: ConfigClassT) -> dict[str, Any]:
        """Serialize the given value."""
        return config_class.to_config()

    def get_default(self) -> dict[str, Any]:
        """Get the default value - dict with default values for all fields."""
        return {key: value_type.get_default() for key, value_type in self.dict_types.items()}


class DynamicConfigType(_ConfigType[ConfigClass]):
    """Dynamic configuration type with type discriminator.

    This type allows a single config to represent multiple different schemas based on a
    discriminator field. Each discriminator value maps to a specific DictType instance.

    Example:
        LED configuration can be either "normal" or "ws281x" type, each with different fields.

    """

    def __init__(
        self,
        discriminator_field: str,
        type_mapping: Mapping[str, DictType[Any]],
        validator_functions: list[Callable[[str, Any], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> None:
        """Initialize DynamicConfigType.

        Args:
            discriminator_field: The field name that determines which schema to use (e.g., "led_type")
            type_mapping: Maps discriminator values to DictType instances
            validator_functions: Additional validation functions
            prefix: Optional prefix for UI display
            suffix: Optional suffix for UI display

        """
        super().__init__(dict, validator_functions, prefix, suffix)
        self.discriminator_field = discriminator_field
        self.type_mapping = type_mapping

    def validate(self, configname: str, config_dict: dict[str, Any]) -> None:
        """Validate the given value."""
        super().validate(configname, config_dict)

        # Check discriminator field exists
        type_value = config_dict.get(self.discriminator_field)
        if type_value is None:
            raise ConfigError(f"Config '{configname}' is missing discriminator field '{self.discriminator_field}'")

        # Check discriminator value is valid
        if type_value not in self.type_mapping:
            allowed_types = list(self.type_mapping.keys())
            raise ConfigError(
                f"Config '{configname}' has invalid {self.discriminator_field} '{type_value}'. "
                f"Allowed values: {allowed_types}"
            )

        # Validate using the appropriate DictType
        dict_type = self.type_mapping[type_value]
        dict_type.validate(configname, config_dict)

    def from_config(self, config_dict: dict[str, Any]) -> ConfigClass:
        """Deserialize the given value."""
        type_value = config_dict.get(self.discriminator_field)
        if type_value is None or type_value not in self.type_mapping:
            # Fallback to first available type if discriminator is missing
            type_value = next(iter(self.type_mapping.keys()))

        dict_type = self.type_mapping[type_value]
        return dict_type.from_config(config_dict)

    def to_config(self, config_class: ConfigClass) -> dict[str, Any]:
        """Serialize the given value."""
        return config_class.to_config()

    def get_discriminator_options(self) -> list[str]:
        """Get list of valid discriminator values."""
        return list(self.type_mapping.keys())

    def get_schema_for_type(self, type_value: str) -> Mapping[str, ConfigInterface[Any]] | None:
        """Get the schema (dict_types) for a specific discriminator value."""
        if type_value in self.type_mapping:
            return self.type_mapping[type_value].dict_types
        return None

    def get_default(self) -> dict[str, Any]:
        """Get the default value - use first type's default."""
        first_type = next(iter(self.type_mapping.keys()))
        return self.type_mapping[first_type].get_default()
