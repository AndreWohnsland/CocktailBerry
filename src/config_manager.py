from __future__ import annotations

import contextlib
import random
from typing import Any, Callable, ClassVar

import typer
import yaml
from pyfiglet import Figlet

from src import (
    MAX_SUPPORTED_BOTTLES,
    PROJECT_NAME,
    SupportedBoardType,
    SupportedLanguagesType,
    SupportedRfidType,
    SupportedThemesType,
    __version__,
)
from src.config.config_types import (
    BoolType,
    ChooseOptions,
    ChooseType,
    ConfigInterface,
    DictType,
    FloatType,
    IntType,
    ListType,
    PumpConfig,
    StringType,
)
from src.config.errors import ConfigError
from src.config.validators import build_number_limiter, validate_max_length
from src.filepath import CUSTOM_CONFIG_FILE
from src.logger_handler import LoggerHandler
from src.utils import get_platform_data

logger = LoggerHandler("config_manager")


_default_pins = [14, 15, 18, 23, 24, 25, 8, 7, 17, 27]
_default_volume_flow = [30.0] * 10


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
    UI_LOCKED_TABS: ClassVar[list[bool]] = [True, True, True]
    # Language to use, use two chars look up documentation, if not provided fallback to en
    UI_LANGUAGE: SupportedLanguagesType = "en"
    # Width and height of the touchscreen
    # Mainly used for dev and comparison for the desired touch dimensions
    # Used if UI_DEVENVIRONMENT is set to True
    UI_WIDTH: int = 800
    UI_HEIGHT: int = 480
    UI_PICTURE_SIZE: int = 240
    PUMP_CONFIG: ClassVar[list[PumpConfig]] = [
        PumpConfig(pin, flow, 0) for pin, flow in zip(_default_pins, _default_volume_flow)
    ]
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
    # Option to invert pump direction
    MAKER_PUMP_REVERSION: bool = False
    # Pin used for the pump direction
    MAKER_REVERSION_PIN: int = 0
    # If the maker should check automatically for updates
    MAKER_SEARCH_UPDATES: bool = True
    # If the maker should check if there is enough in the bottle before making a cocktail
    MAKER_CHECK_BOTTLE: bool = True
    # Inverts the pin signal (on is low, off is high)
    MAKER_PINS_INVERTED: bool = True
    # Possibility to use different boards to control Pins
    MAKER_BOARD: SupportedBoardType = "RPI"
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
    # List of LED pins for control
    LED_PINS: ClassVar[list[int]] = []
    # Value for LED brightness
    LED_BRIGHTNESS: int = 100
    # Number of LEDs, only important for controllable
    LED_COUNT: int = 24
    # If there are multiple identical (ring) LEDs
    LED_NUMBER_RINGS: int = 1
    # Turns the led always on to a white when not doing anything else
    LED_DEFAULT_ON: bool = False
    # If the led is as ws-x series (and controllable)
    LED_IS_WS: bool = True
    # if a RFID reader exists
    RFID_READER: SupportedRfidType = "No"
    # If to use microservice (mostly docker on same device) to handle external API calls and according url
    MICROSERVICE_ACTIVE: bool = False
    MICROSERVICE_BASE_URL: str = "http://127.0.0.1:5000"
    # if to use the teams function and according options.
    # URL should be 'device_ip:8080' where dashboard container is running and in the same network
    # Button names must be two strings in the list
    TEAMS_ACTIVE: bool = False
    TEAM_BUTTON_NAMES: ClassVar[list[str]] = ["Team 1", "Team 2"]
    TEAM_API_URL: str = "http://127.0.0.1:8080"
    # Config to change the displayed values in the maker to another unit
    EXP_MAKER_UNIT: str = "ml"
    EXP_MAKER_FACTOR: float = 1.0

    def __init__(self) -> None:
        """Try to read in the custom configs. If the file is not there, ignores the error.

        At the initialization of the program the config is synced to the file, therefore creating it at the first start.
        The sync is not within the __init__ because the initialization of the inheriting classes would also add their
        attributes within the config, which is not a desired behavior. The sync will include all latest features within
        the config as well as allow custom settings without git overriding changes.
        """
        # Dict of Format "configname": (type, List[CheckCallbacks])
        # The check function needs to be a callable with interface fn(configname, configvalue)
        self.config_type: dict[str, ConfigInterface] = {
            "UI_DEVENVIRONMENT": BoolType(),
            "UI_MASTERPASSWORD": IntType(),
            "UI_MAKER_PASSWORD": IntType(),
            "UI_LOCKED_TABS": ListType(BoolType(), 3, immutable=True),
            "UI_LANGUAGE": ChooseOptions.language,
            "UI_WIDTH": IntType([build_number_limiter(1, 10000)]),
            "UI_HEIGHT": IntType([build_number_limiter(1, 3000)]),
            "UI_PICTURE_SIZE": IntType([build_number_limiter(100, 1000)]),
            "PUMP_CONFIG": ListType(
                DictType(
                    {
                        "pin": IntType([self._validate_pin_numbers], prefix="Pin:"),
                        "volume_flow": FloatType([build_number_limiter(0.1, 1000)], suffix="ml/s"),
                        "tube_volume": IntType([build_number_limiter(0, 100)], suffix="ml"),
                    },
                    PumpConfig,
                ),
                self.choose_bottle_number,
            ),
            "MAKER_NAME": StringType([validate_max_length]),
            "MAKER_NUMBER_BOTTLES": IntType([build_number_limiter(1, MAX_SUPPORTED_BOTTLES)]),
            "MAKER_PREPARE_VOLUME": ListType(IntType([build_number_limiter(25, 1000)], suffix="ml"), 1),
            "MAKER_SIMULTANEOUSLY_PUMPS": IntType([build_number_limiter(1, MAX_SUPPORTED_BOTTLES)]),
            "MAKER_CLEAN_TIME": IntType([build_number_limiter()], suffix="s"),
            "MAKER_PUMP_REVERSION": BoolType(),
            "MAKER_REVERSION_PIN": IntType([self._validate_pin_numbers]),
            "MAKER_SEARCH_UPDATES": BoolType(),
            "MAKER_CHECK_BOTTLE": BoolType(),
            "MAKER_PINS_INVERTED": BoolType(),
            "MAKER_BOARD": ChooseOptions.board,
            "MAKER_THEME": ChooseOptions.theme,
            "MAKER_MAX_HAND_INGREDIENTS": IntType([build_number_limiter(0, 10)]),
            "MAKER_CHECK_INTERNET": BoolType(),
            "MAKER_USE_RECIPE_VOLUME": BoolType(),
            "MAKER_ADD_SINGLE_INGREDIENT": BoolType(),
            "LED_PINS": ListType(IntType([build_number_limiter(0, 200)]), 0),
            "LED_BRIGHTNESS": IntType([build_number_limiter(1, 255)]),
            "LED_COUNT": IntType([build_number_limiter(1, 500)]),
            "LED_NUMBER_RINGS": IntType([build_number_limiter(1, 10)]),
            "LED_DEFAULT_ON": BoolType(),
            "LED_IS_WS": BoolType(),
            "RFID_READER": ChooseOptions.rfid,
            "MICROSERVICE_ACTIVE": BoolType(),
            "MICROSERVICE_BASE_URL": StringType(),
            "TEAMS_ACTIVE": BoolType(),
            "TEAM_BUTTON_NAMES": ListType(StringType(), 2),
            "TEAM_API_URL": StringType(),
            "EXP_MAKER_UNIT": StringType(),
            "EXP_MAKER_FACTOR": FloatType([build_number_limiter(0.01, 100)]),
        }
        with contextlib.suppress(FileNotFoundError):
            self._read_config()

    def sync_config_to_file(self):
        """Write the config attributes to the config file.

        Is used to sync new properties into the file.
        """
        config = {}
        for name, setting in self.config_type.items():
            config[name] = setting.to_config(getattr(self, name))
        with open(CUSTOM_CONFIG_FILE, "w", encoding="UTF-8") as stream:
            yaml.dump(config, stream, default_flow_style=False)

    def validate_and_set_config(self, configuration: dict):
        """Validate the config and set new values."""
        # Some lists may depend on other config variables like number of bottles
        # Therefore, by default, split list types from the rest and check them afterwards
        no_list_or_dict = {k: value for k, value in configuration.items() if not isinstance(value, (list, dict))}
        self._validate_and_set_config(no_list_or_dict)
        list_or_dict = {k: value for k, value in configuration.items() if isinstance(value, (list, dict))}
        self._validate_and_set_config(list_or_dict)

    def _validate_and_set_config(self, configuration: dict):
        for config_name, config_value in configuration.items():
            config_setting = self.config_type.get(config_name)
            # old or user added configs will not be validated
            if config_setting is None:
                continue
            config_setting.validate(config_name, config_value)
            setattr(self, config_name, config_setting.from_config(config_value))

    def _read_config(self):
        """Read all the config data from the file and validates it."""
        with open(CUSTOM_CONFIG_FILE, encoding="UTF-8") as stream:
            configuration = yaml.safe_load(stream)
            self.validate_and_set_config(configuration)

    def _validate_config_type(self, configname: str, configvalue: Any):
        """Validate the configvalue if its fit the type / conditions."""
        config_setting = self.config_type.get(configname)
        # old or user added configs will not be validated
        if config_setting is None:
            return
        config_setting.validate(configname, configvalue)

    def choose_bottle_number(self, get_all=False):
        """Select the number of Bottles, limits by max supported count."""
        if get_all:
            return MAX_SUPPORTED_BOTTLES
        return min(self.MAKER_NUMBER_BOTTLES, MAX_SUPPORTED_BOTTLES)

    def _validate_pin_numbers(self, configname: str, data: int):
        """Validate that the given pin numbers exists on the board."""
        # RPI
        rpi_allowed = list(range(0, 28))
        # Generic Pins, 200 should probably be enough, RockPi got numbers up to 160
        allowed_pins = list(range(0, 201))
        if self.MAKER_BOARD == "RPI":
            allowed_pins = rpi_allowed
        if data not in allowed_pins:
            raise ConfigError(f"{configname} must be one of the values: {allowed_pins}")

    def add_config(
        self,
        config_name: str,
        default_value: str | int | float | bool | list[str] | list[int] | list[float],
        validation_function: list[Callable[[str, Any], None]] | None = None,
        list_validation_function: list[Callable[[str, Any], None]] | None = None,
        list_type: type | None = None,
        min_length: int | Callable[[], int] = 0,
    ):
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
        config_type_mapping = {
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
            config_setting = ListType(config_class(list_type, list_validation_function), min_length)
        else:
            config_type = type(default_value)
            config_class = config_type_mapping[config_type]
            config_setting = config_class(config_type, validation_function)
        self.config_type[config_name] = config_setting

    def add_selection_config(
        self,
        config_name: str,
        options: list[str],
        default_value: str | None = None,
        validation_function: list[Callable[[str, Any], None]] | None = None,
    ):
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


class Shared:
    """Shared global variables which may dynamically change and are needed on different spaces."""

    def __init__(self):
        self.cocktail_started = False
        self.make_cocktail = True
        self.old_ingredient: list[str] = []
        self.selected_team = "No Team"
        self.team_member_name: str | None = None
        self.alcohol_factor: float = 1.0


def version_callback(value: bool):
    """Return the version of the program."""
    if value:
        typer.echo(f"{PROJECT_NAME} Version {__version__}. Created by Andre Wohnsland.")
        typer.echo(get_platform_data())
        typer.echo(r"For more information visit the docs: https://cocktailberry.readthedocs.io")
        typer.echo(r"Or the GitHub: https://github.com/AndreWohnsland/CocktailBerry.")
        raise typer.Exit()


def show_start_message(machine_name: str = PROJECT_NAME):
    """Show the starting message in both Figlet and normal font."""
    figlet = Figlet()
    start_message = f"{machine_name} Version {__version__}"
    print(figlet.renderText(start_message))
    print(start_message)
    print(get_platform_data())


shared = Shared()
CONFIG = ConfigManager()
