"""Module for configuration types.

They are used to wrap the validation of different types and composition within the yaml config file.
Simply separating by build in types is not enough for dict or list types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol, Self, get_args

from src import (
    ConsumptionEstimationType,
    I2CExpanderType,
    SupportedDispenserType,
    SupportedLanguagesType,
    SupportedLedStatesType,
    SupportedPaymentOptions,
    SupportedPinControlType,
    SupportedRfidType,
    SupportedScaleDriverType,
    SupportedStepperDriverType,
    SupportedStepperStepType,
    SupportedThemesType,
)
from src.config.errors import ConfigError

SUPPORTED_LANGUAGES = list(get_args(SupportedLanguagesType))
SUPPORTED_THEMES = list(get_args(SupportedThemesType))
SUPPORTED_RFID = list(get_args(SupportedRfidType))
SUPPORTED_LED_STATES = list(get_args(SupportedLedStatesType))
SUPPORTED_PAYMENT = list(get_args(SupportedPaymentOptions))
SUPPORTED_PIN_CONTROL = list(get_args(SupportedPinControlType))
SUPPORTED_I2C_EXPANDERS = list(get_args(I2CExpanderType))
SUPPORTED_DISPENSERS = list(get_args(SupportedDispenserType))
SUPPORTED_STEPPER_DRIVERS = list(get_args(SupportedStepperDriverType))
SUPPORTED_STEPPER_STEP_TYPES = list(get_args(SupportedStepperStepType))
SUPPORTED_CONSUMPTION_ESTIMATIONS = list(get_args(ConsumptionEstimationType))
SUPPORTED_SCALE_DRIVERS = list(get_args(SupportedScaleDriverType))


class ConfigInterface[T](Protocol):
    """Interface for config values."""

    prefix: str | None = None
    suffix: str | None = None
    default: T | None = None

    @abstractmethod
    def validate(self, configname: str, value: Any) -> None:
        """Validate the given value."""
        raise NotImplementedError

    @property
    @abstractmethod
    def ui_type(self) -> type:
        """Return the type for the UI."""
        raise NotImplementedError

    def from_config(self, value: Any) -> T:
        """Serialize the given value."""
        return value

    def to_config(self, value: T) -> Any:
        """Deserialize the given value."""
        return value

    @abstractmethod
    def get_default(self) -> Any:
        """Get the default value for this config type."""
        raise NotImplementedError


@dataclass
class _ConfigType[T](ConfigInterface[T]):
    """Base class for configuration types holding type validation and iteratively executing validators.

    Used internally for reusing the same logic for different types.
    """

    config_type: type[str | int | float | bool | list | dict]
    validator_functions: Iterable[Callable[[str, Any], None]] = field(default_factory=list)
    prefix: str | None = None
    suffix: str | None = None
    default: T | None = None

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

    def get_default(self) -> Any:
        """Get the default value for this config type."""
        if self.default is not None:
            return self.default

        defaults: dict[type, Any] = {
            str: "",
            int: 0,
            float: 0.0,
            bool: False,
            list: [],
            dict: {},
        }
        return defaults.get(self.config_type)


# NOTE: This is the only "special" class not using ConfigType as base class,
# since it does not fit into the type/validator scheme of the other types.
@dataclass
class ChooseType(ConfigInterface[str]):
    """Base Class for auto generated single select drop down."""

    allowed: list[str] = field(default_factory=list)
    validator_functions: Iterable[Callable[[str, Any], None]] = field(default_factory=list)
    default: str | None = None

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
        first_element_with_fallback = self.allowed[0] if self.allowed else ""
        return self.default if self.default is not None else first_element_with_fallback


class ChooseOptions:
    language = ChooseType(allowed=SUPPORTED_LANGUAGES)
    rfid = ChooseType(allowed=SUPPORTED_RFID)
    theme = ChooseType(allowed=SUPPORTED_THEMES)
    leds = ChooseType(allowed=SUPPORTED_LED_STATES)
    payment = ChooseType(allowed=SUPPORTED_PAYMENT)
    pin = ChooseType(allowed=SUPPORTED_PIN_CONTROL, default="GPIO")
    i2c = ChooseType(allowed=SUPPORTED_I2C_EXPANDERS, default="PCF8574")
    dispenser = ChooseType(allowed=SUPPORTED_DISPENSERS, default="DC")
    stepper_driver = ChooseType(allowed=SUPPORTED_STEPPER_DRIVERS, default="A4988")
    stepper_step_type = ChooseType(allowed=SUPPORTED_STEPPER_STEP_TYPES, default="Full")
    consumption_estimation = ChooseType(allowed=SUPPORTED_CONSUMPTION_ESTIMATIONS, default="time")
    scale_driver = ChooseType(allowed=SUPPORTED_SCALE_DRIVERS, default="HX711")


class StringType(_ConfigType[str]):
    """String configuration type."""

    def __init__(
        self,
        validator_functions: Iterable[Callable[[str, str], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
        default: str = "",
    ) -> None:
        super().__init__(str, validator_functions, prefix, suffix, default)


class IntType(_ConfigType[int]):
    """Integer configuration type."""

    def __init__(
        self,
        validator_functions: Iterable[Callable[[str, int], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
        default: int = 0,
    ) -> None:
        super().__init__(int, validator_functions, prefix, suffix, default)


class FloatType(_ConfigType[float]):
    """Float configuration type."""

    def __init__(
        self,
        validator_functions: Iterable[Callable[[str, int | float], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
        default: float = 0.0,
    ) -> None:
        super().__init__(float, validator_functions, prefix, suffix, default)

    def validate(self, configname: str, value: Any) -> None:
        """Validate the given value."""
        # also accepts integers since they are basically floats
        if not (isinstance(value, int | float)):
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
        default: bool = False,
    ) -> None:
        super().__init__(bool, validator_functions, prefix, suffix, default)
        self.check_name = check_name


class ListType[ListItemT](_ConfigType[list[ListItemT]]):
    """List configuration type."""

    def __init__(
        self,
        list_type: ConfigInterface[ListItemT],
        min_length: int | Callable[[], int],
        validator_functions: Iterable[Callable[[str, Any], None]] = [],
        prefix: str | None = None,
        suffix: str | None = None,
        immutable: bool = False,
        default: list[ListItemT] = [],
    ) -> None:
        super().__init__(list, validator_functions, prefix, suffix, default)
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


class DictType[ConfigClassT: ConfigClass](_ConfigType[ConfigClassT]):
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

    def validate(self, configname: str, config_dict: dict[str, Any]) -> None:  # ty:ignore[invalid-method-override]
        """Validate the given value."""
        super().validate(configname, config_dict)
        for key_name, key_type in self.dict_types.items():
            key_value = config_dict.get(key_name)
            if key_type.default is not None and key_value is None:
                key_value = key_type.default
            if key_value is None:
                raise ConfigError(f"Config value for '{key_name}' is missing in '{configname}'")
            key_text = f"{configname} key {key_name}"
            key_type.validate(key_text, key_value)

    def from_config(self, config_dict: dict[str, Any]) -> ConfigClassT:  # ty:ignore[invalid-method-override]
        """Deserialize the given value."""
        return self.config_class.from_config(config_dict)

    def to_config(self, config_class: ConfigClassT) -> dict[str, Any]:  # ty:ignore[invalid-method-override]
        """Serialize the given value."""
        return config_class.to_config()

    def get_default(self) -> dict[str, Any]:
        """Get the default value - dict with default values for all fields."""
        return {key: value_type.get_default() for key, value_type in self.dict_types.items()}

    def get_default_config_class(self) -> ConfigClassT:
        """Get the default config class instance."""
        return self.from_config(self.get_default())


class DiscriminatedDictType[ConfigClassT: ConfigClass](_ConfigType[ConfigClassT]):
    """Dict type that dispatches to variant DictTypes based on a discriminator field.

    Used for polymorphic config where a single list can hold different config class types,
    distinguished by a discriminator field value (e.g. pump_type -> DC or Stepper).
    """

    def __init__(
        self,
        discriminator: str,
        variants: dict[str, DictType[Any]],
        default_variant: str | None = None,
    ) -> None:
        super().__init__(dict, [], None, None)
        self.discriminator = discriminator
        self.variants = variants
        self.default_variant = default_variant

    def _resolve_variant(self, configname: str, config_dict: dict[str, Any]) -> DictType[Any]:
        """Get the variant DictType for the given config dict."""
        disc_value = config_dict.get(self.discriminator)
        if disc_value is None:
            disc_value = self.default_variant
        if disc_value is None:
            raise ConfigError(f"Missing discriminator '{self.discriminator}' in '{configname}'")
        variant = self.variants.get(disc_value)
        if variant is None:
            allowed = ", ".join(self.variants.keys())
            raise ConfigError(f"Unknown {self.discriminator} '{disc_value}' in '{configname}', allowed: {allowed}")
        return variant

    def validate(self, configname: str, config_dict: dict[str, Any]) -> None:  # ty:ignore[invalid-method-override]
        super().validate(configname, config_dict)
        variant = self._resolve_variant(configname, config_dict)
        variant.validate(configname, config_dict)

    def from_config(self, config_dict: dict[str, Any]) -> ConfigClassT:  # ty:ignore[invalid-method-override]
        variant = self._resolve_variant("", config_dict)
        return variant.from_config(config_dict)

    def to_config(self, config_class: ConfigClassT) -> dict[str, Any]:  # ty:ignore[invalid-method-override]
        disc_value = getattr(config_class, self.discriminator)
        variant = self.variants[disc_value]
        return variant.to_config(config_class)

    def get_default(self) -> dict[str, Any]:
        """Get the default value from the first variant."""
        first_variant = next(iter(self.variants.values()))
        return first_variant.get_default()


### -------------------- Specific Config Classes -------------------- ###


@dataclass(frozen=True)
class PinId:
    """Unique identifier for a pin, combining the pin type, board number, and pin number."""

    pin_type: SupportedPinControlType
    board_number: int
    pin: int

    def __str__(self) -> str:
        return f"{self.pin_type}-{self.board_number}-{self.pin}"

    def __repr__(self) -> str:
        return f"{self.pin_type}-{self.board_number}-{self.pin}"


class BasePumpConfig(ConfigClass):
    """Base configuration shared by all dispenser types."""

    pump_type: str
    volume_flow: float
    tube_volume: int
    consumption_estimation: ConsumptionEstimationType
    carriage_position: int

    def __init__(
        self,
        pump_type: str = "DC",
        volume_flow: float = 30.0,
        tube_volume: int = 0,
        consumption_estimation: ConsumptionEstimationType = "time",
        carriage_position: int = 0,
        **kwargs: Any,
    ) -> None:
        self.pump_type = pump_type
        self.volume_flow = volume_flow
        self.tube_volume = tube_volume
        self.consumption_estimation = consumption_estimation
        self.carriage_position = carriage_position

    def to_config(self) -> dict[str, Any]:
        return {
            "pump_type": self.pump_type,
            "volume_flow": self.volume_flow,
            "tube_volume": self.tube_volume,
            "consumption_estimation": self.consumption_estimation,
            "carriage_position": self.carriage_position,
        }


class DCPumpConfig(BasePumpConfig):
    """Configuration for DC pump dispensers."""

    pin_type: SupportedPinControlType
    pin: int
    board_number: int

    def __init__(
        self,
        pin: int = 0,
        volume_flow: float = 30.0,
        tube_volume: int = 0,
        pin_type: SupportedPinControlType = "GPIO",
        board_number: int = 1,
        pump_type: SupportedDispenserType = "DC",
        consumption_estimation: ConsumptionEstimationType = "time",
        carriage_position: int = 0,
    ) -> None:
        super().__init__(
            pump_type=pump_type,
            volume_flow=volume_flow,
            tube_volume=tube_volume,
            consumption_estimation=consumption_estimation,
            carriage_position=carriage_position,
        )
        self.pin_type = pin_type
        self.pin = pin
        self.board_number = board_number

    @property
    def pin_id(self) -> PinId:
        """Build PinId from this config's pin_type, board_number and pin."""
        return PinId(self.pin_type, self.board_number, self.pin)

    def to_config(self) -> dict[str, Any]:
        config = super().to_config()
        config.update(
            {
                "pin_type": self.pin_type,
                "board_number": self.board_number,
                "pin": self.pin,
            }
        )
        return config


class StepperPumpConfig(BasePumpConfig):
    """Configuration for stepper motor dispensers."""

    pin: int
    dir_pin: int
    driver_type: SupportedStepperDriverType
    step_type: SupportedStepperStepType

    def __init__(
        self,
        pin: int = 0,
        dir_pin: int = 0,
        driver_type: SupportedStepperDriverType = "A4988",
        step_type: SupportedStepperStepType = "Full",
        volume_flow: float = 30.0,
        tube_volume: int = 0,
        pump_type: SupportedDispenserType = "Stepper",
        consumption_estimation: ConsumptionEstimationType = "time",
        carriage_position: int = 0,
    ) -> None:
        super().__init__(
            pump_type=pump_type,
            volume_flow=volume_flow,
            tube_volume=tube_volume,
            consumption_estimation=consumption_estimation,
            carriage_position=carriage_position,
        )
        self.pin = pin
        self.dir_pin = dir_pin
        self.driver_type = driver_type
        self.step_type = step_type

    def to_config(self) -> dict[str, Any]:
        config = super().to_config()
        config.update(
            {
                "pin": self.pin,
                "dir_pin": self.dir_pin,
                "driver_type": self.driver_type,
                "step_type": self.step_type,
            }
        )
        return config


# Backwards compatibility alias
PumpConfig = DCPumpConfig


class BaseScaleConfig(ConfigClass):
    """Base configuration shared by all scale driver types."""

    scale_type: SupportedScaleDriverType
    enabled: bool
    calibration_factor: float

    def __init__(
        self,
        scale_type: SupportedScaleDriverType = "HX711",
        enabled: bool = False,
        calibration_factor: float = 1.0,
        **kwargs: Any,
    ) -> None:
        self.scale_type = scale_type
        self.enabled = enabled
        self.calibration_factor = calibration_factor

    def to_config(self) -> dict[str, Any]:
        return {
            "scale_type": self.scale_type,
            "enabled": self.enabled,
            "calibration_factor": self.calibration_factor,
        }


class HX711ScaleConfig(BaseScaleConfig):
    """Configuration for HX711 load cell amplifier (2-wire bit-bang protocol)."""

    data_pin: int
    clock_pin: int

    def __init__(
        self,
        data_pin: int = 5,
        clock_pin: int = 6,
        enabled: bool = False,
        calibration_factor: float = 1.0,
        scale_type: SupportedScaleDriverType = "HX711",
    ) -> None:
        super().__init__(scale_type=scale_type, enabled=enabled, calibration_factor=calibration_factor)
        self.data_pin = data_pin
        self.clock_pin = clock_pin

    def to_config(self) -> dict[str, Any]:
        config = super().to_config()
        config.update(
            {
                "data_pin": self.data_pin,
                "clock_pin": self.clock_pin,
            }
        )
        return config


class NAU7802ScaleConfig(BaseScaleConfig):
    """Configuration for NAU7802 I2C load cell amplifier."""

    i2c_address: str

    def __init__(
        self,
        i2c_address: str = "2A",
        enabled: bool = False,
        calibration_factor: float = 1.0,
        scale_type: SupportedScaleDriverType = "NAU7802",
    ) -> None:
        super().__init__(scale_type=scale_type, enabled=enabled, calibration_factor=calibration_factor)
        self.i2c_address = i2c_address.upper()

    @property
    def address_hex(self) -> int:
        return int(self.i2c_address, 16)

    def to_config(self) -> dict[str, Any]:
        config = super().to_config()
        config.update(
            {
                "i2c_address": self.i2c_address,
            }
        )
        return config


class I2CExpanderConfig(ConfigClass):
    """Base configuration for I2C GPIO expander devices.

    Shared by MCP23017 (16 pins, 0-15), PCF8574 (8 pins, 0-7), and PCA9535 (16 pins, 0-15).
    Default I2C address is 0x20, configurable to 0x20-0x27.
    Multiple boards of the same type are distinguished by board_number.
    """

    device_type: I2CExpanderType
    enabled: bool
    address: str
    inverted: bool
    board_number: int

    def __init__(
        self,
        device_type: I2CExpanderType,
        enabled: bool,
        address: str = "20",
        inverted: bool = False,
        board_number: int = 1,
    ) -> None:
        self.device_type = device_type
        self.enabled = enabled
        self.address = address.upper()
        self.inverted = inverted
        self.board_number = board_number

    @property
    def address_hex(self) -> int:
        return int(self.address, 16)

    def to_config(self) -> dict[str, bool | int | str]:
        return {
            "device_type": self.device_type,
            "board_number": self.board_number,
            "enabled": self.enabled,
            "address": self.address,
            "inverted": self.inverted,
        }


class ReversionConfig(ConfigClass):
    """Configuration for pump reversion."""

    use_reversion: bool
    pin: int
    inverted: bool
    pin_type: SupportedPinControlType
    board_number: int

    def __init__(
        self,
        use_reversion: bool,
        pin: int,
        inverted: bool,
        pin_type: SupportedPinControlType = "GPIO",
        board_number: int = 1,
    ) -> None:
        self.use_reversion = use_reversion
        self.pin = pin
        self.pin_type = pin_type
        self.inverted = inverted
        self.board_number = board_number

    @property
    def pin_id(self) -> PinId:
        """Build PinId from this config's pin_type, board_number and pin."""
        return PinId(self.pin_type, self.board_number, self.pin)

    def to_config(self) -> dict[str, Any]:
        return {
            "pin_type": self.pin_type,
            "board_number": self.board_number,
            "pin": self.pin,
            "use_reversion": self.use_reversion,
            "inverted": self.inverted,
        }


class NormalLedConfig(ConfigClass):
    """Configuration for normal (non-WS281x) LEDs."""

    pin: int
    default_on: bool
    preparation_state: SupportedLedStatesType
    pin_type: SupportedPinControlType
    board_number: int

    def __init__(
        self,
        pin: int,
        default_on: bool,
        preparation_state: SupportedLedStatesType,
        pin_type: SupportedPinControlType = "GPIO",
        board_number: int = 1,
    ) -> None:
        self.pin = pin
        self.default_on = default_on
        self.preparation_state = preparation_state
        self.pin_type = pin_type
        self.board_number = board_number

    @property
    def pin_id(self) -> PinId:
        """Build PinId from this config's pin_type, board_number and pin."""
        return PinId(self.pin_type, self.board_number, self.pin)

    def to_config(self) -> dict[str, Any]:
        return {
            "pin_type": self.pin_type,
            "board_number": self.board_number,
            "pin": self.pin,
            "default_on": self.default_on,
            "preparation_state": self.preparation_state,
        }


class WS281xLedConfig(ConfigClass):
    """Configuration for WS281x (controllable) LEDs."""

    pin: int
    brightness: int
    count: int
    number_rings: int
    default_on: bool
    preparation_state: SupportedLedStatesType

    def __init__(
        self,
        pin: int,
        brightness: int,
        count: int,
        number_rings: int,
        default_on: bool,
        preparation_state: SupportedLedStatesType,
    ) -> None:
        self.pin = pin
        self.brightness = brightness
        self.count = count
        self.number_rings = number_rings
        self.default_on = default_on
        self.preparation_state = preparation_state

    @property
    def pin_id(self) -> PinId:
        """Build PinId from this config's pin_type and pin."""
        return PinId("GPIO", 1, self.pin)

    def to_config(self) -> dict[str, Any]:
        return {
            "pin": self.pin,
            "brightness": self.brightness,
            "count": self.count,
            "number_rings": self.number_rings,
            "default_on": self.default_on,
            "preparation_state": self.preparation_state,
        }


class BaseCarriageConfig(ConfigClass):
    """Configuration for the optional carriage/slide hardware.

    Positions are abstract values from 0 to 100 representing the percentage
    of total travel range. The home_position defines where the carriage
    rests when idle (0 = start, 50 = middle, 100 = end).
    speed_pct_per_s defines how fast the carriage moves in percent of total
    range per second (e.g. 10.0 means it takes 10s for the full range).
    """

    enabled: bool
    home_position: int
    speed_pct_per_s: float
    move_during_cleaning: bool
    wait_after_dispense: float

    def __init__(
        self,
        enabled: bool = False,
        home_position: int = 0,
        speed_pct_per_s: float = 10.0,
        move_during_cleaning: bool = False,
        wait_after_dispense: float = 0.0,
        **kwargs: Any,
    ) -> None:
        self.enabled = enabled
        self.home_position = home_position
        self.speed_pct_per_s = speed_pct_per_s
        self.move_during_cleaning = move_during_cleaning
        self.wait_after_dispense = wait_after_dispense

    def to_config(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "home_position": self.home_position,
            "speed_pct_per_s": self.speed_pct_per_s,
            "move_during_cleaning": self.move_during_cleaning,
            "wait_after_dispense": self.wait_after_dispense,
        }
