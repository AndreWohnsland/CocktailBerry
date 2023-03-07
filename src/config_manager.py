import random
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Union
import typer
import yaml
from pyfiglet import Figlet

from src.logger_handler import LoggerHandler
from src.models import Ingredient
from src.utils import get_platform_data
from src import (
    __version__,
    PROJECT_NAME,
    MAX_SUPPORTED_BOTTLES,
    SUPPORTED_LANGUAGES,
    SUPPORTED_BOARDS,
    SUPPORTED_THEMES
)


CONFIG_FILE = Path(__file__).parents[1].absolute() / "custom_config.yaml"
logger = LoggerHandler("config_manager")


class ChooseType:
    allowed: List[str] = []


class LanguageChoose(ChooseType):
    allowed = SUPPORTED_LANGUAGES


class BoardChoose(ChooseType):
    allowed = SUPPORTED_BOARDS


class ThemeChoose(ChooseType):
    allowed = SUPPORTED_THEMES


class ConfigManager:
    """Manager for all static configuration of the machine.
    The Settings defined here are the default settings and will be overwritten by the config file"""

    # Activating some dev features like mouse cursor
    UI_DEVENVIRONMENT = True
    # Locks the recipe tab, making it impossible to access
    UI_PARTYMODE = False
    # Password to lock clean, delete and other critical operators
    UI_MASTERPASSWORD = "1234"
    # Language to use, use two chars look up documentation, if not provided fallback to en
    UI_LANGUAGE = "en"
    # Width and height of the touchscreen
    # Mainly used for dev and comparison for the desired touch dimensions
    # Used if UI_DEVENVIRONMENT is set to True
    UI_WIDTH = 800
    UI_HEIGHT = 480
    # RPi pins where pumps (ascending) are connected
    PUMP_PINS = [14, 15, 18, 23, 24, 25, 8, 7, 17, 27, 22, 10]
    # Volume flow for the according pumps
    PUMP_VOLUMEFLOW = [30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]
    # Custom name of the Maker
    MAKER_NAME = f"CocktailBerry (#{random.randint(0, 1000000):07})"
    # Number of bottles possible at the machine
    MAKER_NUMBER_BOTTLES = 10
    # Number of pumps parallel in production
    MAKER_SIMULTANEOUSLY_PUMPS = 16
    # Time in seconds to execute clean program
    MAKER_CLEAN_TIME = 20
    # time between each check loop when making cocktail
    MAKER_SLEEP_TIME = 0.05
    # If the maker should check automatically for updates
    MAKER_SEARCH_UPDATES = False
    # Inverts the pin signal (on is low, off is high)
    MAKER_PINS_INVERTED = True
    # Possibility to use different boards to control Pins
    MAKER_BOARD = "RPI"
    # Theme Setting to load according qss file
    MAKER_THEME = "default"
    # Flag to check if internet is up at start
    MAKER_CHECK_INTERNET = True
    # Volume to pump up if a bottle gets changed
    MAKER_TUBE_VOLUME = 0
    # List of LED pins for control
    LED_PINS = []
    # Value for LED brightness
    LED_BRIGHTNESS = 255
    # Number of LEDs, only important for controllable
    LED_COUNT = 24
    # If there are multiple identical (ring) LEDs
    LED_NUMBER_RINGS = 1
    # If the led is as ws-x series (and controllable)
    LED_IS_WS = True
    # if a RFID reader exists
    RFID_EXISTS = False
    # If to use microservice (mostly docker on same device) to handle external API calls and according url
    MICROSERVICE_ACTIVE = False
    MICROSERVICE_BASE_URL = "http://127.0.0.1:5000"
    # if to use the teams function and according options.
    # URL should be 'device_ip:8080' where dashboard container is running and in the same network
    # Button names must be two strings in the list
    TEAMS_ACTIVE = False
    TEAM_BUTTON_NAMES = ["Team 1", "Team 2"]
    TEAM_API_URL = "http://127.0.0.1:8080"
    # Config to change the displayed values in the maker to another unit
    EXP_MAKER_UNIT = "ml"
    EXP_MAKER_FACTOR = 1.0

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
            "UI_PARTYMODE": (bool, []),
            "UI_MASTERPASSWORD": (str, []),
            "UI_LANGUAGE": (LanguageChoose, [_build_support_checker(SUPPORTED_LANGUAGES)]),
            "UI_WIDTH": (int, [_build_number_limiter(1, 10000)]),
            "UI_HEIGHT": (int, [_build_number_limiter(1, 3000)]),
            "PUMP_PINS": (list, [self._validate_config_list_type]),
            "PUMP_VOLUMEFLOW": (list, [self._validate_config_list_type]),
            "MAKER_NAME": (str, [_validate_max_length]),
            "MAKER_NUMBER_BOTTLES": (int, [_build_number_limiter(1, MAX_SUPPORTED_BOTTLES)]),
            "MAKER_SIMULTANEOUSLY_PUMPS": (int, [_build_number_limiter(1, MAX_SUPPORTED_BOTTLES)]),
            "MAKER_CLEAN_TIME": (int, [_build_number_limiter()]),
            "MAKER_SLEEP_TIME": (float, [_build_number_limiter(0.01, 0.2)]),
            "MAKER_SEARCH_UPDATES": (bool, []),
            "MAKER_PINS_INVERTED": (bool, []),
            "MAKER_BOARD": (BoardChoose, [_build_support_checker(SUPPORTED_BOARDS)]),
            "MAKER_THEME": (ThemeChoose, [_build_support_checker(SUPPORTED_THEMES)]),
            "MAKER_CHECK_INTERNET": (bool, []),
            "MAKER_TUBE_VOLUME": (int, [_build_number_limiter(0, 50)]),
            "LED_PINS": (list, [self._validate_config_list_type]),
            "LED_BRIGHTNESS": (int, [_build_number_limiter(1, 255)]),
            "LED_COUNT": (int, [_build_number_limiter(1, 500)]),
            "LED_NUMBER_RINGS": (int, [_build_number_limiter(1, 10)]),
            "LED_IS_WS": (bool, []),
            "RFID_EXISTS": (bool, []),
            "MICROSERVICE_ACTIVE": (bool, []),
            "MICROSERVICE_BASE_URL": (str, []),
            "TEAMS_ACTIVE": (bool, []),
            "TEAM_BUTTON_NAMES": (list, [self._validate_config_list_type]),
            "TEAM_API_URL": (str, []),
            "EXP_MAKER_UNIT": (str, []),
            "EXP_MAKER_FACTOR": (float, [_build_number_limiter(0.01, 100)]),
        }
        # Dict of Format "configname": (type, List[CheckCallbacks]) for the single list elements
        # only needed if the above config type was defined as list type, rest is identical to top schema
        self.config_type_list: Dict[str, Tuple[type, List[Callable[[str, Any], None]]]] = {
            "PUMP_PINS": (int, [self._validate_pin_numbers]),
            "PUMP_VOLUMEFLOW": (int, [_build_number_limiter(1, 1000)]),
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
        with open(CONFIG_FILE, 'w', encoding="UTF-8") as stream:
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
        with open(CONFIG_FILE, "r", encoding="UTF-8") as stream:
            configuration = yaml.safe_load(stream)
            self.validate_and_set_config(configuration)

    def _validate_config_type(self, configname: str, configvalue: Any):
        """validates the configvalue if its fit the type / conditions"""
        config_setting = self.config_type.get(configname)
        if config_setting is None:
            return
        datatype, check_functions = config_setting
        # check first if type fits, if list, also check list elements.
        # Additionally run all check functions provided
        # if it's a choose type ignore typing for now, the function will check if the value is in the list.
        if isinstance(configvalue, datatype) or issubclass(datatype, ChooseType):
            for check_fun in check_functions:
                check_fun(configname, configvalue)
            return
        raise ConfigError(f"The value {configvalue} for {configname} is not of type {datatype}")

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
        self.handaddlist: List[Ingredient] = []
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


def show_start_message():
    """Shows the starting message in both Figlet and normal font"""
    figlet = Figlet()
    start_message = f"{PROJECT_NAME} Version {__version__}"
    print(figlet.renderText(start_message))
    print(start_message)
    print(get_platform_data())


shared = Shared()
CONFIG = ConfigManager()
