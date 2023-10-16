import random
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, get_args
import typer
import yaml
from pyfiglet import Figlet

from src.logger_handler import LoggerHandler
from src.utils import get_platform_data
from src.filepath import CUSTOM_CONFIG_FILE
from src import (
    __version__,
    PROJECT_NAME,
    MAX_SUPPORTED_BOTTLES,
    SupportedLanguagesType,
    SupportedBoardType,
    SupportedThemesType,
    SupportedRfidType,
)


logger = LoggerHandler("config_manager")
SUPPORTED_LANGUAGES = list(get_args(SupportedLanguagesType))
SUPPORTED_BOARDS = list(get_args(SupportedBoardType))
SUPPORTED_THEMES = list(get_args(SupportedThemesType))
SUPPORTED_RFID = list(get_args(SupportedRfidType))


class ChooseType:
    """Base Class for auto generated single select drop down"""
    allowed: List[str] = []


class LanguageChoose(ChooseType):
    allowed = SUPPORTED_LANGUAGES


class BoardChoose(ChooseType):
    allowed = SUPPORTED_BOARDS


class ThemeChoose(ChooseType):
    allowed = SUPPORTED_THEMES


class RFIDChoose(ChooseType):
    allowed = SUPPORTED_RFID


class ConfigManager:
    """Manager for all static configuration of the machine.
    The Settings defined here are the default settings and will be overwritten by the config file"""

    # Activating some dev features like mouse cursor
    UI_DEVENVIRONMENT: bool = True
    # Password to lock clean, delete and other critical operators
    UI_MASTERPASSWORD: int = 0
    # Password to lock other tabs than maker tab
    UI_MAKER_PASSWORD: int = 0
    # Language to use, use two chars look up documentation, if not provided fallback to en
    UI_LANGUAGE: SupportedLanguagesType = "en"
    # Width and height of the touchscreen
    # Mainly used for dev and comparison for the desired touch dimensions
    # Used if UI_DEVENVIRONMENT is set to True
    UI_WIDTH: int = 800
    UI_HEIGHT: int = 480
    # Slow factor for eg sticky ingredients
    PUMP_SLOW_FACTOR = 1.0
    # RPi pins where pumps (ascending) are connected
    PUMP_PINS: list[int] = [14, 15, 18, 23, 24, 25, 8, 7, 17, 27, 22, 10]
    # Volume flow for the according pumps
    PUMP_VOLUMEFLOW: list[int] = [30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]
    # Custom name of the Maker
    MAKER_NAME: str = f"CocktailBerry (#{random.randint(0, 1000000):07})"
    # Number of bottles possible at the machine
    MAKER_NUMBER_BOTTLES: int = 8
    # Number of pumps parallel in production
    MAKER_SIMULTANEOUSLY_PUMPS: int = 16
    # Time in seconds to execute clean program
    MAKER_CLEAN_TIME: int = 20
    # Option to invert pump direction
    MAKER_PUMP_REVERSION: bool = False
    # Pin used for the pump direction
    MAKER_REVERSION_PIN: int = 0
    # time between each check loop when making cocktail
    MAKER_SLEEP_TIME: float = 0.05
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
    # Flag to check if internet is up at start
    MAKER_CHECK_INTERNET: bool = True
    # Volume to pump up if a bottle gets changed
    MAKER_TUBE_VOLUME: int = 0
    # Option to not scale the recipe volume but use always the defined one
    MAKER_USE_RECIPE_VOLUME: bool = False
    # List of LED pins for control
    LED_PINS: list[int] = []
    # Value for LED brightness
    LED_BRIGHTNESS: int = 100
    # Number of LEDs, only important for controllable
    LED_COUNT: int = 24
    # If there are multiple identical (ring) LEDs
    LED_NUMBER_RINGS: int = 1
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
    TEAM_BUTTON_NAMES: list[str] = ["Team 1", "Team 2"]
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
        self.config_type: Dict[str, Tuple[type, List[Callable[[str, Any], None]]]] = {
            "UI_DEVENVIRONMENT": (bool, []),
            "UI_MASTERPASSWORD": (int, []),
            "UI_MAKER_PASSWORD": (int, []),
            "UI_LANGUAGE": (LanguageChoose, []),
            "UI_WIDTH": (int, [_build_number_limiter(1, 10000)]),
            "UI_HEIGHT": (int, [_build_number_limiter(1, 3000)]),
            "PUMP_PINS": (list, []),
            "PUMP_SLOW_FACTOR": (float, [_build_number_limiter(0.01, 10)]),
            "PUMP_VOLUMEFLOW": (list, []),
            "MAKER_NAME": (str, [_validate_max_length]),
            "MAKER_NUMBER_BOTTLES": (int, [_build_number_limiter(1, MAX_SUPPORTED_BOTTLES)]),
            "MAKER_SIMULTANEOUSLY_PUMPS": (int, [_build_number_limiter(1, MAX_SUPPORTED_BOTTLES)]),
            "MAKER_CLEAN_TIME": (int, [_build_number_limiter()]),
            "MAKER_PUMP_REVERSION": (bool, []),
            "MAKER_REVERSION_PIN": (int, [self._validate_pin_numbers]),
            "MAKER_SLEEP_TIME": (float, [_build_number_limiter(0.01, 0.2)]),
            "MAKER_SEARCH_UPDATES": (bool, []),
            "MAKER_CHECK_BOTTLE": (bool, []),
            "MAKER_PINS_INVERTED": (bool, []),
            "MAKER_BOARD": (BoardChoose, []),
            "MAKER_THEME": (ThemeChoose, []),
            "MAKER_CHECK_INTERNET": (bool, []),
            "MAKER_TUBE_VOLUME": (int, [_build_number_limiter(0, 50)]),
            "MAKER_USE_RECIPE_VOLUME": (bool, []),
            "LED_PINS": (list, []),
            "LED_BRIGHTNESS": (int, [_build_number_limiter(1, 255)]),
            "LED_COUNT": (int, [_build_number_limiter(1, 500)]),
            "LED_NUMBER_RINGS": (int, [_build_number_limiter(1, 10)]),
            "LED_IS_WS": (bool, []),
            "RFID_READER": (RFIDChoose, []),
            "MICROSERVICE_ACTIVE": (bool, []),
            "MICROSERVICE_BASE_URL": (str, []),
            "TEAMS_ACTIVE": (bool, []),
            "TEAM_BUTTON_NAMES": (list, []),
            "TEAM_API_URL": (str, []),
            "EXP_MAKER_UNIT": (str, []),
            "EXP_MAKER_FACTOR": (float, [_build_number_limiter(0.01, 100)]),
        }
        # Dict of Format "configname": (type, List[CheckCallbacks]) for the single list elements
        # only needed if the above config type was defined as list type, rest is identical to top schema
        self.config_type_list: Dict[str, Tuple[type, List[Callable[[str, Any], None]]]] = {
            "PUMP_PINS": (int, [self._validate_pin_numbers]),
            "PUMP_VOLUMEFLOW": (float, [_build_number_limiter(0.1, 1000)]),
            "TEAM_BUTTON_NAMES": (str, []),
            "LED_PINS": (int, [_build_number_limiter(0, 200)]),
        }
        try:
            self._read_config()
        except FileNotFoundError:
            pass

    def sync_config_to_file(self):
        """Writes the config attributes to the config file.
        Is used to sync new properties into the file"""
        config = {}
        for attribute in self.config_type:
            config[attribute] = getattr(self, attribute)
        with open(CUSTOM_CONFIG_FILE, 'w', encoding="UTF-8") as stream:
            yaml.dump(config, stream, default_flow_style=False)

    def validate_and_set_config(self, configuration: Dict, lists_later=True):
        """Validates the config and set new values"""
        # Some lists may depend on other config variables like number of bottles
        # Therefore, by default, split list types from the rest and check them afterwards
        if lists_later:
            non_list_config = {k: value for k, value in configuration.items() if not isinstance(value, list)}
            self.validate_and_set_config(non_list_config, False)
            configuration = {k: value for k, value in configuration.items() if isinstance(value, list)}
        for k, value in configuration.items():
            self._validate_config_type(k, value)
            setattr(self, k, value)

    def _read_config(self):
        """Reads all the config data from the file and validates it"""
        with open(CUSTOM_CONFIG_FILE, "r", encoding="UTF-8") as stream:
            configuration = yaml.safe_load(stream)
            self.validate_and_set_config(configuration)

    def _validate_config_type(self, configname: str, configvalue: Any):
        """validates the configvalue if its fit the type / conditions"""
        config_setting = self.config_type.get(configname)
        if config_setting is None:
            return
        datatype, check_functions = config_setting
        # check first if type fits
        # if it's a choose type ignore typing for now, the function later will check if the value is in the list.
        if not isinstance(configvalue, datatype) and not issubclass(datatype, ChooseType):
            raise ConfigError(f"The value {configvalue} for {configname} is not of type {datatype}")

        # check if the right values for choose type is selected
        if issubclass(datatype, ChooseType):
            _build_support_checker(datatype.allowed)(configname, configvalue)

        # Additionally run all check functions provided
        for check_fun in check_functions:
            check_fun(configname, configvalue)

        # If it's a list, also run the list validation
        if isinstance(configvalue, list):
            self._validate_config_list_type(configname, configvalue)

    def _validate_config_list_type(self, configname: str, configlist: List[Any]):
        """Extra validation for list type in case len / types"""
        config_setting = self.config_type_list.get(configname)
        if config_setting is None:
            return
        datatype, check_functions = config_setting
        for i, config in enumerate(configlist, 1):
            if not isinstance(config, datatype):
                raise ConfigError(f"The value {config} at position {i} for {configname} is not of type {datatype}")
            for check_fun in check_functions:
                check_fun(configname, config)
        # additional len check of the list data,
        min_bottles = self.choose_bottle_number()
        min_len_config = {
            "PUMP_PINS": min_bottles,
            "PUMP_VOLUMEFLOW": min_bottles,
            "TEAM_BUTTON_NAMES": 2,
        }
        min_len = min_len_config.get(configname)
        if min_len is None:
            return
        _validate_list_length(configlist, configname, min_len)

    def choose_bottle_number(self, get_all=False):
        """Selects the number of Bottles, limits by max supported count"""
        if get_all:
            return MAX_SUPPORTED_BOTTLES
        return min(self.MAKER_NUMBER_BOTTLES, MAX_SUPPORTED_BOTTLES)

    def _validate_pin_numbers(self, configname: str, data: int):
        """Validates that the given pin numbers exists on the board"""
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
        default_value: Union[str, int, float, bool, list[str], list[int], list[float]],
        validation_function: Optional[list[Callable[[str, Any], None]]] = None,
        list_validation_function: Optional[list[Callable[[str, Any], None]]] = None,
        list_type: Optional[type] = None,
    ):
        """Adds the configuration under the given name.
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

        # get the type of the config, define type and validation
        config_type = type(default_value)
        self.config_type[config_name] = (config_type, validation_function)

        # Do the same for list, get either type if not provided, fall back to string if list is empty
        if isinstance(default_value, list):
            if list_type is None and len(default_value) == 0:
                list_type = str
            elif list_type is None:
                list_type = type(default_value[0])
            self.config_type_list[config_name] = (list_type, list_validation_function)

    def add_selection_config(
        self,
        config_name: str,
        options: list[str],
        default_value: Optional[str] = None,
        validation_function: Optional[list[Callable[[str, Any], None]]] = None,
    ):
        """Adds a configuration value under the given name, which can only be from given options
        This is used to create a dropdown selection for the user to prevent unintended values.
        Options must be string and have at least one element. 
        Default value is first list element, or if given, the given value
        """
        # Define a choose type for the add on
        class AddOnChoose(ChooseType):
            allowed = options

        # If user did not provide the default value, use the first element of options as default
        if default_value is None:
            default_value = options[0]
        if validation_function is None:
            validation_function = []
        # Define default value if its not set
        if not hasattr(self, config_name):
            setattr(self, config_name, default_value)

        # Set type and validation function
        self.config_type[config_name] = (AddOnChoose, validation_function)


def _validate_list_length(configlist: List[Any], configname: str, min_len: int):
    """Checks if the list is at least a given size"""
    actual_len = len(configlist)
    if actual_len < min_len:
        raise ConfigError(f"{configname} got only {actual_len} elements, but you need at least {min_len} elements")


def _build_support_checker(supported: List[Any]):
    """Builds the function: Check if the configvalue is within the supported List"""
    def check_if_supported(configname: str, configvalue: Any):
        if configvalue in supported:
            return
        raise ConfigError(f"Value '{configvalue}' for {configname} is not supported, please use any of {supported}")
    return check_if_supported


def _validate_max_length(configname: str, data: str, max_len=30):
    """Validates if data exceeds maximum length"""
    if len(data) <= max_len:
        return
    raise ConfigError(f"{configname} is longer than {max_len}, please reduce length")


def _build_number_limiter(min_val: Union[int, float] = 1, max_val: Union[int, float] = 100):
    """Builds the function: Check if the number is within the given limits"""
    def limit_number(configname: str, data: Union[int, float]):
        if data < min_val or data > max_val:
            raise ConfigError(f"{configname} must be between {min_val} and {max_val}.")
    return limit_number


class Shared:
    """Shared global variables which may dynamically change and are needed on different spaces"""

    def __init__(self):
        self.cocktail_started = False
        self.make_cocktail = True
        self.old_ingredient: List[str] = []
        self.selected_team = "No Team"
        self.team_member_name: Union[str, None] = None
        self.cocktail_volume: int = 200
        self.alcohol_factor: float = 1.0


class ConfigError(Exception):
    """Raised when there was an error with the configuration data"""


def version_callback(value: bool):
    """Returns the version of the program"""
    if value:
        typer.echo(f"{PROJECT_NAME} Version {__version__}. Created by Andre Wohnsland.")
        typer.echo(get_platform_data())
        typer.echo(r"For more information visit the docs: https://cocktailberry.readthedocs.io")
        typer.echo(r"Or the GitHub: https://github.com/AndreWohnsland/CocktailBerry.")
        raise typer.Exit()


def show_start_message(machine_name: str = PROJECT_NAME):
    """Shows the starting message in both Figlet and normal font"""
    figlet = Figlet()
    start_message = f"{machine_name} Version {__version__}"
    print(figlet.renderText(start_message))
    print(start_message)
    print(get_platform_data())


shared = Shared()
CONFIG = ConfigManager()
