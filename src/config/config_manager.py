from __future__ import annotations

import contextlib
import random
from collections.abc import Callable
from enum import IntEnum
from typing import TYPE_CHECKING, Any, ClassVar

import typer
import yaml
from pydantic.dataclasses import dataclass as api_dataclass
from pyfiglet import Figlet

if TYPE_CHECKING:
    from src.api.models import WaiterResponse

from src import (
    MAX_SUPPORTED_BOTTLES,
    PROJECT_NAME,
    SupportedLanguagesType,
    SupportedPaymentOptions,
    SupportedThemesType,
    __version__,
)
from src.config.config_types import (
    BaseCarriageConfig,
    BaseLedConfig,
    BasePumpConfig,
    BaseRfidConfig,
    BoolType,
    ChooseOptions,
    ChooseType,
    ConfigInterface,
    DCPumpConfig,
    DictType,
    DiscriminatedDictType,
    FloatType,
    HX711ScaleConfig,
    I2CExpanderConfig,
    IntType,
    ListType,
    NAU7802ScaleConfig,
    NormalLedConfig,
    ReversionConfig,
    StepperPumpConfig,
    StringType,
    WS281xLedConfig,
)
from src.config.errors import ConfigError
from src.config.validators import (
    build_distinct_validator,
    build_number_limiter,
    validate_i2c_address,
    validate_max_length,
)
from src.filepath import CUSTOM_CONFIG_FILE
from src.logger_handler import LoggerHandler
from src.models import CocktailStatus
from src.utils import get_platform_data

_logger = LoggerHandler("config_manager")


_default_pins = [14, 15, 18, 23, 24, 25, 8, 7, 17, 27]
_default_volume_flow = [30.0] * 10


class Tab(IntEnum):
    MAKER = 0
    INGREDIENTS = 1
    RECIPES = 2
    BOTTLES = 3


TAB_ORDER = [Tab.MAKER, Tab.INGREDIENTS, Tab.RECIPES, Tab.BOTTLES]

# -----------------------------------------------------------------------------
# Shared UI-field definitions for DiscriminatedDictType config families.
#
# Each constant is the single source of truth for the shared fields of a
# Base*Config family. Both the built-in variants in ``config_manager.py`` and
# the addon variants registered by the extension managers in
# ``src/programs/addons/`` spread (``**``) these dicts into their variant
# DictType so the shared fields are declared exactly once.
# -----------------------------------------------------------------------------

SHARED_PUMP_FIELDS: dict[str, ConfigInterface[Any]] = {
    "pump_type": ChooseOptions.dispenser,
    "volume_flow": FloatType([build_number_limiter(0.1, 1000)], suffix="ml/s"),
    "tube_volume": IntType([build_number_limiter(0, 100)], suffix="ml"),
    "consumption_estimation": ChooseOptions.consumption_estimation,
    "carriage_position": IntType([build_number_limiter(0, 100)], suffix="pos"),
}

SHARED_SCALE_FIELDS: dict[str, ConfigInterface[Any]] = {
    "scale_type": ChooseOptions.scale_driver,
    "enabled": BoolType(check_name="Enabled"),
    "calibration_factor": FloatType(prefix="cali:", allow_negative=True),
    "zero_raw_offset": IntType(prefix="offset:", allow_negative=True),
    "minimal_weight": IntType([build_number_limiter(0)], prefix="min:", suffix="g"),
}

SHARED_CARRIAGE_FIELDS: dict[str, ConfigInterface[Any]] = {
    "carriage_type": ChooseOptions.carriage_type,
    "enabled": BoolType(check_name="Enabled"),
    "home_position": IntType([build_number_limiter(0, 100)], suffix="pos"),
    "speed_pct_per_s": FloatType([build_number_limiter(0.1, 100)], suffix="%/s"),
    "move_during_cleaning": BoolType(check_name="Move During Cleaning"),
    "wait_after_dispense": FloatType([build_number_limiter(0, 30)], suffix="s"),
}

SHARED_RFID_FIELDS: dict[str, ConfigInterface[Any]] = {
    "rfid_type": ChooseOptions.rfid,
    "enabled": BoolType(check_name="Enabled"),
}

SHARED_LED_FIELDS: dict[str, ConfigInterface[Any]] = {
    "led_type": ChooseOptions.led_driver,
    "default_on": BoolType(check_name="Default On"),
    "preparation_state": ChooseOptions.leds,
}


class ConfigManager:
    """Manager for all static configuration of the machine.

    The Settings defined here are the default settings and will be overwritten by the config file.
    """

    # Activating some dev features like mouse cursor
    UI_DEVENVIRONMENT: bool = True
    # Password to lock clean, delete and other critical operators
    UI_MASTERPASSWORD: int = 0
    # Password to lock other tabs than maker tab
    UI_MAKER_PASSWORD: int = 0
    # specify which of the tabs will be locked
    UI_LOCKED_TABS: ClassVar[list[bool]] = [False, True, True, True]
    # Language to use, use two chars look up documentation, if not provided fallback to en
    UI_LANGUAGE: SupportedLanguagesType = "en"
    # Width and height of the touchscreen
    # Mainly used for dev and comparison for the desired touch dimensions
    UI_WIDTH: int = 800
    UI_HEIGHT: int = 480
    UI_PICTURE_SIZE: int = 240
    UI_ONLY_MAKER_TAB: bool = False
    PUMP_CONFIG: ClassVar[list[BasePumpConfig]] = [
        DCPumpConfig(pin, flow, 0, "GPIO") for pin, flow in zip(_default_pins, _default_volume_flow)
    ]
    # Inverts the pin signal (on is low, off is high)
    MAKER_PINS_INVERTED: bool = True
    # MCP23017 I2C GPIO expander configuration (16 pins, address 0x20-0x27)
    I2C_CONFIG: ClassVar[list[I2CExpanderConfig]] = []
    # Custom name of the Maker
    MAKER_NAME: str = f"CocktailBerry (#{random.randint(0, 1000000):07})"
    # Number of bottles possible at the machine
    MAKER_NUMBER_BOTTLES: int = 8
    # Volume options to choose from when preparing a cocktail
    MAKER_PREPARE_VOLUME: ClassVar[list[int]] = [150, 250, 350]
    # Number of pumps parallel in production
    MAKER_SIMULTANEOUSLY_PUMPS: int = 16
    # Time in seconds to execute clean program
    MAKER_CLEAN_TIME: int = 20
    # Base multiplier for alcohol in the recipe
    MAKER_ALCOHOL_FACTOR: int = 100
    # Reversion for cleaning
    MAKER_PUMP_REVERSION_CONFIG = ReversionConfig(use_reversion=False, pin=0, pin_type="GPIO", inverted=False)
    # If the maker should check automatically for updates
    MAKER_SEARCH_UPDATES: bool = True
    # If the maker should check if there is enough in the bottle before making a cocktail
    MAKER_CHECK_BOTTLE: bool = True
    # Theme Setting to load according qss file
    MAKER_THEME: SupportedThemesType = "default"
    # How many ingredients are allowed to be added by hand to be available cocktail
    MAKER_MAX_HAND_INGREDIENTS: int = 3
    # Flag to check if internet is up at start
    MAKER_CHECK_INTERNET: bool = True
    # Option to not scale the recipe volume but use always the defined one
    MAKER_USE_RECIPE_VOLUME: bool = False
    # Option to add the single ingredient option to the maker pane
    MAKER_ADD_SINGLE_INGREDIENT: bool = False
    # Option to show a random cocktail tile in the maker tab
    MAKER_RANDOM_COCKTAIL: bool = False
    # List of LED configurations (discriminated by ``led_type``: Normal or WSLED)
    LED_CONFIG: ClassVar[list[BaseLedConfig]] = []
    # RFID reader configuration (discriminated by ``rfid_type``)
    RFID_CONFIG = BaseRfidConfig(rfid_type="USB", enabled=False)
    # If to use microservice (mostly docker on same device) to handle external API calls and according url
    MICROSERVICE_ACTIVE: bool = False
    MICROSERVICE_BASE_URL: str = "http://127.0.0.1:5000"
    # if to use the teams function and according options.
    # URL should be 'device_ip:8080' where dashboard container is running and in the same network
    # Button names must be two strings in the list
    TEAMS_ACTIVE: bool = False
    TEAM_BUTTON_NAMES: ClassVar[list[str]] = ["Team 1", "Team 2"]
    TEAM_API_URL: str = "http://127.0.0.1:8080"
    # Payment related configurations
    PAYMENT_TYPE: SupportedPaymentOptions = "Disabled"
    PAYMENT_PRICE_ROUNDING: float = 0.25
    PAYMENT_VIRGIN_MULTIPLIER: int = 80
    PAYMENT_TIMEOUT_S: int = 20
    PAYMENT_SHOW_NOT_POSSIBLE: bool = True
    PAYMENT_LOCK_SCREEN_NO_USER: bool = True
    PAYMENT_SERVICE_URL: str = "http://127.0.0.1:9876"
    PAYMENT_SECRET_KEY: str = "CocktailBerry-Secret-Change-Me"
    PAYMENT_SUMUP_API_KEY: str = ""
    PAYMENT_SUMUP_MERCHANT_CODE: str = ""
    PAYMENT_SUMUP_TERMINAL_ID: str = ""
    PAYMENT_AUTO_LOGOUT_TIME_S: int = 60
    PAYMENT_LOGOUT_AFTER_PREPARATION: bool = True
    # Waiter mode settings
    WAITER_MODE: bool = False
    WAITER_LOGOUT_AFTER_COCKTAIL: bool = False
    WAITER_AUTO_LOGOUT_S: int = 0
    # Custom theme settings
    CUSTOM_COLOR_PRIMARY: str = "#007bff"
    CUSTOM_COLOR_SECONDARY: str = "#ef9700"
    CUSTOM_COLOR_NEUTRAL: str = "#96adba"
    CUSTOM_COLOR_BACKGROUND: str = "#0d0d0d"
    CUSTOM_COLOR_DANGER: str = "#d00000"
    # Config to change the displayed values in the maker to another unit
    # Scale configuration for weight-based dispensing
    SCALE_CONFIG = HX711ScaleConfig(enabled=False)
    CARRIAGE_CONFIG = BaseCarriageConfig(enabled=False)
    EXP_MAKER_UNIT: str = "ml"
    EXP_MAKER_FACTOR: float = 1.0
    EXP_DEMO_MODE: bool = False

    def __init__(self) -> None:
        """Try to read in the custom configs. If the file is not there, ignores the error.

        At the initialization of the program the config is synced to the file, therefore creating it at the first start.
        The sync is not within the __init__ because the initialization of the inheriting classes would also add their
        attributes within the config, which is not a desired behavior. The sync will include all latest features within
        the config as well as allow custom settings without git overriding changes.
        """
        # Tracks whether addon-contributed config variants have been registered.
        # Flipped to True only via mark_addon_configs_initialized().
        self._addon_configs_initialized: bool = False
        # Dict of Format "configname": (type, List[CheckCallbacks])
        # The check function needs to be a callable with interface fn(configname, configvalue)
        self.config_type: dict[str, ConfigInterface] = {
            "UI_DEVENVIRONMENT": BoolType(check_name="Dev active"),
            "UI_MASTERPASSWORD": IntType(),
            "UI_MAKER_PASSWORD": IntType(),
            "UI_LOCKED_TABS": ListType(BoolType(check_name="locked"), 4, immutable=True),
            "UI_LANGUAGE": ChooseOptions.language,
            "UI_WIDTH": IntType([build_number_limiter(1, 10000)]),
            "UI_HEIGHT": IntType([build_number_limiter(1, 3000)]),
            "UI_PICTURE_SIZE": IntType([build_number_limiter(100, 1000)]),
            "UI_ONLY_MAKER_TAB": BoolType(check_name="Only Maker Tab Accessible"),
            "MAKER_PINS_INVERTED": BoolType(check_name="Inverted"),
            "PUMP_CONFIG": ListType(
                DiscriminatedDictType(
                    "pump_type",
                    {
                        "DC": DictType(
                            {
                                **SHARED_PUMP_FIELDS,
                                "pin_type": ChooseOptions.pin,
                                "board_number": IntType([build_number_limiter(1, 99)], prefix="#", default=1),
                                "pin": IntType([build_number_limiter(0)], prefix="Pin:"),
                            },
                            DCPumpConfig,
                        ),
                        "Stepper": DictType(
                            {
                                **SHARED_PUMP_FIELDS,
                                "pin": IntType([build_number_limiter(0)], prefix="Pin:"),
                                "dir_pin": IntType([build_number_limiter(0)], prefix="Dir:"),
                                "driver_type": ChooseOptions.stepper_driver,
                                "step_type": ChooseOptions.stepper_step_type,
                            },
                            StepperPumpConfig,
                        ),
                    },
                    default_variant="DC",
                ),
                lambda: self.choose_bottle_number(ignore_limits=True),
                [
                    build_distinct_validator(
                        ["pin_type", "board_number", "pin"],
                        fallback={"pin_type": "GPIO", "board_number": 1},
                    )
                ],
            ),
            "I2C_CONFIG": ListType(
                DictType(
                    {
                        "device_type": ChooseOptions.i2c,
                        "board_number": IntType([build_number_limiter(1, 99)], prefix="#", default=1),
                        "enabled": BoolType(check_name="Enabled", default=True),
                        "address": StringType([validate_i2c_address], prefix="0x", default="20"),
                        "inverted": BoolType(check_name="Inverted"),
                    },
                    I2CExpanderConfig,
                ),
                0,
                [build_distinct_validator(["device_type", "board_number"])],
            ),
            "MAKER_NAME": StringType([validate_max_length]),
            "MAKER_NUMBER_BOTTLES": IntType([build_number_limiter(1, 999)]),
            "MAKER_PREPARE_VOLUME": ListType(IntType([build_number_limiter(25, 1000)], suffix="ml", default=100), 1),
            "MAKER_SIMULTANEOUSLY_PUMPS": IntType([build_number_limiter(1, 999)]),
            "MAKER_CLEAN_TIME": IntType([build_number_limiter()], suffix="s"),
            "MAKER_ALCOHOL_FACTOR": IntType([build_number_limiter(10, 200)], suffix="%"),
            "MAKER_PUMP_REVERSION_CONFIG": DictType(
                {
                    "use_reversion": BoolType(check_name="active", default=False),
                    "pin_type": ChooseOptions.pin,
                    "board_number": IntType([build_number_limiter(1, 99)], prefix="#", default=1),
                    "pin": IntType([build_number_limiter(0)], default=0, prefix="Pin:"),
                    "inverted": BoolType(check_name="Inverted", default=False),
                },
                ReversionConfig,
            ),
            "MAKER_SEARCH_UPDATES": BoolType(check_name="Search for Updates"),
            "MAKER_CHECK_BOTTLE": BoolType(check_name="Check Bottle Volume"),
            "MAKER_THEME": ChooseOptions.theme,
            "MAKER_MAX_HAND_INGREDIENTS": IntType([build_number_limiter(0, 10)]),
            "MAKER_CHECK_INTERNET": BoolType(check_name="Check Internet"),
            "MAKER_USE_RECIPE_VOLUME": BoolType(check_name="Use Recipe Volume"),
            "MAKER_ADD_SINGLE_INGREDIENT": BoolType(check_name="Can Spend Single Ingredient"),
            "MAKER_RANDOM_COCKTAIL": BoolType(check_name="Random Cocktail Option"),
            "LED_CONFIG": ListType(
                DiscriminatedDictType(
                    "led_type",
                    {
                        "Normal": DictType(
                            {
                                **SHARED_LED_FIELDS,
                                "pin_type": ChooseOptions.pin,
                                "board_number": IntType([build_number_limiter(1, 99)], prefix="#", default=1),
                                "pin": IntType([build_number_limiter(0)], prefix="Pin:"),
                            },
                            NormalLedConfig,
                        ),
                        "WSLED": DictType(
                            {
                                **SHARED_LED_FIELDS,
                                "pin": IntType([build_number_limiter(0)], prefix="Pin:"),
                                "brightness": IntType([build_number_limiter(1, 100)], suffix="%", default=100),
                                "count": IntType([build_number_limiter(1, 500)], suffix="LEDs", default=24),
                                "number_rings": IntType([build_number_limiter(1, 10)], suffix="X", default=1),
                            },
                            WS281xLedConfig,
                        ),
                    },
                    default_variant="Normal",
                ),
                0,
            ),
            "RFID_CONFIG": DiscriminatedDictType(
                "rfid_type",
                {
                    "MFRC522": DictType({**SHARED_RFID_FIELDS}, BaseRfidConfig),
                    "USB": DictType({**SHARED_RFID_FIELDS}, BaseRfidConfig),
                },
                default_variant="USB",
            ),
            "MICROSERVICE_ACTIVE": BoolType(check_name="Microservice Active"),
            "MICROSERVICE_BASE_URL": StringType(),
            "TEAMS_ACTIVE": BoolType(check_name="Teams Active"),
            "TEAM_BUTTON_NAMES": ListType(StringType(), 2),
            "TEAM_API_URL": StringType(),
            "PAYMENT_TYPE": ChooseOptions.payment,
            "PAYMENT_PRICE_ROUNDING": FloatType(
                [build_number_limiter(0, 5)], prefix="round up to", suffix="next multiple of"
            ),
            "PAYMENT_VIRGIN_MULTIPLIER": IntType([build_number_limiter(0, 200)], suffix="%"),
            "PAYMENT_TIMEOUT_S": IntType([build_number_limiter(0, 100)], suffix="s"),
            "PAYMENT_SHOW_NOT_POSSIBLE": BoolType(check_name="Show Not Possible Cocktails"),
            "PAYMENT_LOCK_SCREEN_NO_USER": BoolType(check_name="Lock Screen When No User"),
            "PAYMENT_SERVICE_URL": StringType(),
            "PAYMENT_SECRET_KEY": StringType(),
            "PAYMENT_SUMUP_API_KEY": StringType(),
            "PAYMENT_SUMUP_MERCHANT_CODE": StringType(),
            "PAYMENT_SUMUP_TERMINAL_ID": StringType(),
            "PAYMENT_AUTO_LOGOUT_TIME_S": IntType([build_number_limiter(0, 1000000000)], suffix="s"),
            "PAYMENT_LOGOUT_AFTER_PREPARATION": BoolType(check_name="Logout After Preparation"),
            "WAITER_MODE": BoolType(check_name="Enable Service Personnel Mode"),
            "WAITER_LOGOUT_AFTER_COCKTAIL": BoolType(check_name="Logout After Cocktail"),
            "WAITER_AUTO_LOGOUT_S": IntType([build_number_limiter(0, 100000)], suffix="s"),
            "CUSTOM_COLOR_PRIMARY": StringType(),
            "CUSTOM_COLOR_SECONDARY": StringType(),
            "CUSTOM_COLOR_NEUTRAL": StringType(),
            "CUSTOM_COLOR_BACKGROUND": StringType(),
            "CUSTOM_COLOR_DANGER": StringType(),
            "SCALE_CONFIG": DiscriminatedDictType(
                "scale_type",
                {
                    "HX711": DictType(
                        {
                            **SHARED_SCALE_FIELDS,
                            "data_pin": IntType([build_number_limiter(0)], prefix="Data:"),
                            "clock_pin": IntType([build_number_limiter(0)], prefix="Clock:"),
                        },
                        HX711ScaleConfig,
                    ),
                    "NAU7802": DictType(
                        {
                            **SHARED_SCALE_FIELDS,
                            "i2c_address": StringType([validate_i2c_address], prefix="0x", default="2A"),
                        },
                        NAU7802ScaleConfig,
                    ),
                },
                default_variant="HX711",
            ),
            "CARRIAGE_CONFIG": DiscriminatedDictType(
                "carriage_type",
                {
                    "NoCarriage": DictType(
                        {**SHARED_CARRIAGE_FIELDS},
                        BaseCarriageConfig,
                    ),
                },
                default_variant="NoCarriage",
            ),
            "EXP_MAKER_UNIT": StringType(),
            "EXP_MAKER_FACTOR": FloatType([build_number_limiter(0.01, 100)]),
            "EXP_DEMO_MODE": BoolType(check_name="Activate Demo Mode"),
        }

    def add_discriminator_variant(
        self,
        config_name: str,
        variant_name: str,
        variant: DictType,
    ) -> None:
        """Add a new variant to a DiscriminatedDictType config entry.

        Finds the DiscriminatedDictType for the given config_name (unwrapping ListType if needed),
        registers the new variant, and updates the discriminator ChooseType's allowed list.
        """
        setting = self.config_type.get(config_name)
        if setting is None:
            _logger.warning(f"Cannot add variant '{variant_name}': config '{config_name}' not found")
            return
        disc_type: DiscriminatedDictType | None = None
        if isinstance(setting, DiscriminatedDictType):
            disc_type = setting
        elif isinstance(setting, ListType) and isinstance(setting.list_type, DiscriminatedDictType):
            disc_type = setting.list_type
        if disc_type is None:
            _logger.warning(f"Cannot add variant '{variant_name}': '{config_name}' is not a DiscriminatedDictType")
            return
        disc_type.variants[variant_name] = variant
        # Update the discriminator ChooseType allowed list in existing variants
        discriminator_field = disc_type.discriminator
        for existing_variant in disc_type.variants.values():
            choose_type = existing_variant.dict_types.get(discriminator_field)
            if isinstance(choose_type, ChooseType) and variant_name not in choose_type.allowed:
                choose_type.allowed.append(variant_name)

    @property
    def sumup_payment(self) -> bool:
        """Check if SumUp payment option is selected."""
        return self.PAYMENT_TYPE == "SumUp"

    @property
    def cocktailberry_payment(self) -> bool:
        """Check if CocktailBerry internal payment option is selected."""
        return self.PAYMENT_TYPE == "CocktailBerry"

    @property
    def payment_enabled(self) -> bool:
        """Check if any payment option is selected."""
        return self.PAYMENT_TYPE != "Disabled"

    @property
    def waiter_mode_active(self) -> bool:
        """Check if waiter mode is enabled."""
        return self.WAITER_MODE

    @property
    def nfc_enabled(self) -> bool:
        """Check if any NFC reader is enabled."""
        return self.RFID_CONFIG.enabled

    def mark_addon_configs_initialized(self) -> None:
        """Signal that addon-contributed config variants have been registered.

        Called once by ``initialize_addon_configs`` at startup. Idempotent — calling
        more than once is a no-op. There is intentionally no way to unset the flag.
        """
        self._addon_configs_initialized = True

    def read_local_config(self, update_config: bool = False, validate: bool = True) -> None:
        """Read the local config file and set the values if they are valid.

        Might throw a ConfigError if the config is not valid and should be validated.
        Ignore the error if the file is not found, as it is created at the first start of the program.
        """
        if not self._addon_configs_initialized:
            raise RuntimeError(
                "read_local_config() called before initialize_addon_configs(). "
                "Addon-contributed config variants would be silently dropped, leading to "
                "validation errors at runtime. Call "
                "src.programs.addons.bootstrap.initialize_addon_configs() first."
            )
        configuration: dict = {}
        with contextlib.suppress(FileNotFoundError), CUSTOM_CONFIG_FILE.open(encoding="UTF-8") as stream:
            configuration = yaml.safe_load(stream)
        if configuration:
            self.set_config(configuration, validate)
        if update_config:
            self.sync_config_to_file()

    def sync_config_to_file(self) -> None:
        """Write the config attributes to the config file.

        Is used to sync new properties into the file.
        """
        config = self.get_config()
        with CUSTOM_CONFIG_FILE.open("w", encoding="UTF-8") as stream:
            yaml.dump(config, stream, default_flow_style=False)

    def get_config(self) -> dict[str, Any]:
        """Get a dict of all config values."""
        config = {}
        for name, setting in self.config_type.items():
            config[name] = setting.to_config(getattr(self, name))
        return config

    def get_config_with_ui_information(self) -> dict[str, dict[str, Any]]:
        """Get a dict of all config values with additional information for the UI."""
        from src.dialog_handler import UI_LANGUAGE

        config: dict[str, dict[str, Any]] = {}
        for name, setting in self.config_type.items():
            setting_data = {"value": setting.to_config(getattr(self, name))}
            setting_data["description"] = UI_LANGUAGE.get_config_description(name)
            self._enhance_config_specific_information(setting_data, setting)
            config[name] = setting_data
        return config

    def _enhance_config_specific_information(self, config: dict[str, Any], setting: ConfigInterface) -> None:
        config["prefix"] = setting.prefix
        config["suffix"] = setting.suffix
        config["default"] = setting.get_default()
        if isinstance(setting, ChooseType):
            config["allowed"] = setting.allowed
        if isinstance(setting, BoolType):
            config["check_name"] = setting.check_name
        if isinstance(setting, ListType):
            config["immutable"] = setting.immutable
            list_type = setting.list_type
            # in case of list we need to go into the object, all list object types are the same
            self._enhance_config_specific_information(config, list_type)
        if isinstance(setting, DictType):
            for key, value in setting.dict_types.items():
                config[key] = {}
                self._enhance_config_specific_information(config[key], value)
        if isinstance(setting, DiscriminatedDictType):
            config["discriminator"] = setting.discriminator
            config["variants"] = {}
            for variant_name, variant_dict_type in setting.variants.items():
                variant_config: dict[str, Any] = {}
                for key, value in variant_dict_type.dict_types.items():
                    variant_config[key] = {}
                    self._enhance_config_specific_information(variant_config[key], value)
                config["variants"][variant_name] = variant_config

    def set_config(self, configuration: dict, validate: bool) -> None:
        """Validate the config and set new values."""
        # Some lists may depend on other config variables like number of bottles
        # Therefore, by default, split list types from the rest and check them afterwards
        no_list_or_dict = {k: value for k, value in configuration.items() if not isinstance(value, list | dict)}
        self._set_config(no_list_or_dict, validate)
        list_or_dict = {k: value for k, value in configuration.items() if isinstance(value, list | dict)}
        self._set_config(list_or_dict, validate)
        # Cross-config validation for dependencies between configs
        self._validate_cross_config(validate)

    def _set_config(self, configuration: dict, validate: bool) -> None:
        for config_name, config_value in configuration.items():
            config_setting = self.config_type.get(config_name)
            # old or user added configs will not be validated
            if config_setting is None:
                continue
            # Validate and set the value, if not possible to validate, do not set (use default)
            # If validate is False, the error will be ignored, otherwise raised
            try:
                config_setting.validate(config_name, config_value)
                setattr(self, config_name, config_setting.from_config(config_value))
            except ConfigError as e:
                _logger.error(f"Config Error: {e}")
                if validate:
                    raise e

    def _validate_cross_config(self, validate: bool) -> None:
        """Validate cross-config dependencies.

        Currently implemented:
        - Checks that I2C pin types used in PUMP_CONFIG have corresponding enabled devices in I2C_CONFIG.
        - Checks that WAITER_MODE is not enabled alongside CocktailBerry NFC payment.
        - Check that some nfc is active when payment/waiter mode is active.
        - Checks that weight-based pumps have an enabled scale.
        """
        self._validate_i2c_boards(validate)
        self._validate_waiter_payment(validate)
        self._validate_scale_config(validate)

    def _validate_i2c_boards(self, validate: bool) -> None:
        # Collect all I2C (pin_type, board_number) pairs used in PUMP_CONFIG (excluding GPIO)
        required_i2c_boards: set[tuple[str, int]] = set()
        for pump in self.PUMP_CONFIG:
            if isinstance(pump, DCPumpConfig) and pump.pin_type != "GPIO":
                required_i2c_boards.add((pump.pin_type, pump.board_number))

        # Get enabled I2C (device_type, board_number) pairs from I2C_CONFIG
        enabled_i2c_boards = {(cfg.device_type, cfg.board_number) for cfg in self.I2C_CONFIG if cfg.enabled}

        # Check that all required I2C boards have enabled devices
        missing_boards = required_i2c_boards - enabled_i2c_boards
        if missing_boards:
            readable = ", ".join(f"{t} board {n}" for t, n in missing_boards)
            error_msg = (
                f"PUMP_CONFIG uses I2C boards {readable} but I2C_CONFIG "
                "has no enabled devices for them. Add enabled entries to I2C_CONFIG."
            )
            _logger.error(f"Config Error: {error_msg}")
            if validate:
                raise ConfigError(error_msg)

    def _validate_waiter_payment(self, validate: bool) -> None:
        # Check that waiter mode is not enabled alongside CocktailBerry NFC payment
        if self.WAITER_MODE and self.payment_enabled:
            error_msg = "WAITER_MODE cannot be enabled when payment is also enabled"
            _logger.error(f"Config Error: {error_msg}")
            if validate:
                raise ConfigError(error_msg)

        if (self.WAITER_MODE or self.payment_enabled) and not self.nfc_enabled:
            error_msg = "NFC must be set when payment or waiter mode is active"
            _logger.error(f"Config Error: {error_msg}")
            if validate:
                raise ConfigError(error_msg)

    def _validate_scale_config(self, validate: bool) -> None:
        # Check that weight-based pumps have an enabled scale
        has_weight_pump = any(p.consumption_estimation == "weight" for p in self.PUMP_CONFIG)
        if has_weight_pump and not self.SCALE_CONFIG.enabled:
            error_msg = (
                "PUMP_CONFIG has pumps with consumption_estimation='weight' but SCALE_CONFIG is not enabled. "
                "Enable the scale or switch pumps to time-based estimation."
            )
            _logger.error(f"Config Error: {error_msg}")
            if validate:
                raise ConfigError(error_msg)

    def choose_bottle_number(self, get_all: bool = False, ignore_limits: bool = False) -> int:
        """Select the number of Bottles, limits by max supported count."""
        # for new app (no limits), this exists for legacy reason (QT)
        if ignore_limits:
            return self.MAKER_NUMBER_BOTTLES
        if get_all:
            return MAX_SUPPORTED_BOTTLES
        return min(self.MAKER_NUMBER_BOTTLES, MAX_SUPPORTED_BOTTLES)

    def add_config(
        self,
        config_name: str,
        default_value: str | float | bool | list[str] | list[int] | list[float],
        validation_function: list[Callable[[str, Any], None]] | None = None,
        list_validation_function: list[Callable[[str, Any], None]] | None = None,
        list_type: type[str | int | float] | None = None,
        min_length: int | Callable[[], int] = 0,
    ) -> None:
        """Add the configuration under the given name.

        Adds the default value, if it is currently not set in the config file.
        If validation functions for the value or the list values are given,
        they are also registered with the type.
        Currently supported types are str, int, float and bool.
        List cannot be nested, list types are str, int and float.
        List must contain the same type, no mixed types.
        If the default list is empty, please provide the list type,
        otherwise the fallback type will be string.
        """
        # Set validation to empty list if not given
        if validation_function is None:
            validation_function = []
        if list_validation_function is None:
            list_validation_function = []

        # if not exist, give default value
        if not hasattr(self, config_name):
            setattr(self, config_name, default_value)

        # Use internal type mapping for the config
        config_type_mapping: dict[type[str | int | float | bool], type[StringType | IntType | FloatType | BoolType]] = {
            str: StringType,
            int: IntType,
            float: FloatType,
            bool: BoolType,
        }

        # get the type of the config, define type and validation
        if isinstance(default_value, list):
            if list_type is None and len(default_value) == 0:
                list_type = str
            elif list_type is None:
                list_type = type(default_value[0])
            config_class = config_type_mapping[list_type]
            config_setting = ListType(config_class(list_validation_function), min_length)  # pyright: ignore[reportArgumentType]
        else:
            config_type = type(default_value)
            config_class = config_type_mapping[config_type]
            config_setting = config_class(validation_function)
        self.config_type[config_name] = config_setting

    def add_selection_config(
        self,
        config_name: str,
        options: list[str],
        default_value: str | None = None,
        validation_function: list[Callable[[str, Any], None]] | None = None,
    ) -> None:
        """Add a configuration value under the given name, which can only be from given options.

        This is used to create a dropdown selection for the user to prevent unintended values.
        Options must be string and have at least one element.
        Default value is first list element, or if given, the given value.
        """
        # If user did not provide the default value, use the first element of options as default
        if default_value is None:
            default_value = options[0]
        if validation_function is None:
            validation_function = []
        # Define default value if its not set
        if not hasattr(self, config_name):
            setattr(self, config_name, default_value)
        # Define a choose type for the add on
        addon_choose = ChooseType(options, validation_function)
        self.config_type[config_name] = addon_choose

    def add_complex_config(
        self,
        config_name: str,
        config_setting: DictType,
    ) -> None:
        """Add a complex DictType configuration under the given name.

        Sets the default value from the DictType's config class and registers the type.
        Used by hardware extensions to register their config at startup.
        """
        if not hasattr(self, config_name):
            setattr(self, config_name, config_setting.config_class())
        self.config_type[config_name] = config_setting


@api_dataclass
class StartupIssue:
    has_issue: bool = False
    ignored: bool = False
    message: str = ""

    def set_issue(self, message: str = "") -> None:
        self.has_issue = True
        self.message = message

    def set_ignored(self) -> None:
        self.ignored = True


class Shared:
    """Shared global variables which may dynamically change and are needed on different spaces."""

    def __init__(self) -> None:
        self.old_ingredient: list[str] = []
        self.selected_team = "No Team"
        self.team_member_name: str | None = None
        self.is_v1 = False
        self.restricted_mode_active = False
        self.cocktail_status = CocktailStatus()
        # Waiter mode state
        self.current_waiter_nfc_id: str | None = None
        self.current_waiter: WaiterResponse | None = None
        # those are used to display once the message after startup if there are some issues
        self.startup_need_time_adjustment = StartupIssue()
        self.startup_python_deprecated = StartupIssue()
        self.startup_config_issue = StartupIssue()
        self.startup_payment_issue = StartupIssue()
        self.startup_waiter_issue = StartupIssue()


def version_callback(value: bool) -> None:
    """Return the version of the program."""
    if value:
        typer.echo(f"{PROJECT_NAME} Version {__version__}. Created by Andre Wohnsland.")
        typer.echo(get_platform_data())
        typer.echo(r"For more information visit the docs: https://cocktailberry.readthedocs.io")
        typer.echo(r"Or the GitHub: https://github.com/AndreWohnsland/CocktailBerry.")
        raise typer.Exit()


def show_start_message(machine_name: str = PROJECT_NAME) -> None:
    """Show the starting message in both Figlet and normal font."""
    figlet = Figlet()
    start_message = f"{machine_name} Version {__version__}"
    print(figlet.renderText(start_message))
    _logger.info(start_message)
    _logger.info(str(get_platform_data()))


shared = Shared()
CONFIG = ConfigManager()
