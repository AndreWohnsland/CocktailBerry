from pathlib import Path
from typing import List
import typer
import yaml

from src.models import Ingredient
from src import __version__, PROJECT_NAME


CONFIG_FILE = Path(__file__).parents[1].absolute() / "custom_config.yaml"


class ConfigManager:
    """Manager for all static configuration of the machine.
    The Settings defined here are the default settings and will be overritten by the config file"""

    # Activating some dev features like mouse cursor
    UI_DEVENVIRONMENT = True
    # Locks the recipe tab, making it impossible to acesss
    UI_PARTYMODE = False
    # Password to lock clean, delete and other critical operators
    UI_MASTERPASSWORD = "1337"
    # Language to use, use two chars look up documentation, if not provided fallback to en
    UI_LANGUAGE = "en"
    # Width and height of the touchscreen
    # Mainly used for dev and comparison for the desired touch dimesions
    # Used if UI_DEVENVIRONMENT is set to True
    UI_WIDTH = 800
    UI_HEIGHT = 480
    # RPi pins where pumps (ascending) are connected
    PUMP_PINS = [14, 15, 18, 23, 24, 25, 8, 7, 17, 27, 22, 10]
    # Volumeflow for the according pumps
    PUMP_VOLUMEFLOW = [30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]
    # Number of bottles possible at the machine
    MAKER_NUMBER_BOTTLES = 10
    # Time in seconds to execute clean programm
    MAKER_CLEAN_TIME = 20
    # time between each check loop when making cocktail
    MAKER_SLEEP_TIME = 0.05
    # If the maker should check automatically for updates
    MAKER_SEARCH_UPDATES = False
    # If to use microservice (mostly docker on same device) to handle external API calls and according url
    MICROSERVICE_ACTIVE = False
    MICROSERVICE_BASE_URL = "http://127.0.0.1:5000"
    # if to use the teams function and according options.
    # URL should be 'device_ip:8080' where dashboard container is running and in the same network
    # Button names must be two strings in the list
    TEAMS_ACTIVE = False
    TEAM_BUTTON_NAMES = ["Team 1", "Team 2"]
    TEAM_API_URL = "http://127.0.0.1:8080"

    def __init__(self) -> None:
        """Try to read in the custom configs. If the file is not there, ignores the error.
        At the initialisation of the programm the config is synced to the file, therefore creating it at the first start.
        The sync is not within the __init__ because the initialisation of the inheriting classes would also add their
        attributes within the config, which is not a desired behaviour. The sync will include all latest features within
        the config as well as allow custom settings without git overriding changes.
        """
        try:
            self.__read_config()
        except FileNotFoundError:
            pass

    def sync_config_to_file(self):
        """Writes the config attributes to the config file.
        Is used to sync new properties into the file"""
        attributes = [a for a in dir(self) if not (a.startswith('__') or a.startswith('_') or a.startswith('sync'))]
        config = {}
        for attribute in attributes:
            config[attribute] = getattr(self, attribute)
        with open(CONFIG_FILE, 'w', encoding="UTF-8") as stream:
            yaml.dump(config, stream, default_flow_style=False)

    def __read_config(self):
        with open(CONFIG_FILE, "r", encoding="UTF-8") as stream:
            configuration = yaml.safe_load(stream)
            for k, value in configuration.items():
                self.__validate_config_type(k, value)
                setattr(self, k, value)

    def __validate_config_type(self, configname, configvalue):
        config_type = {
            "UI_DEVENVIRONMENT": bool,
            "UI_PARTYMODE": bool,
            "UI_MASTERPASSWORD": str,
            "UI_LANGUAGE": str,
            "UI_WIDTH": int,
            "UI_HEIGHT": int,
            "PUMP_PINS": list,
            "PUMP_VOLUMEFLOW": list,
            "MAKER_NUMBER_BOTTLES": int,
            "MAKER_CLEAN_TIME": int,
            "MAKER_SLEEP_TIME": float,
            "MICROSERVICE_ACTIVE": bool,
            "MICROSERVICE_BASE_URL": str,
            "TEAMS_ACTIVE": bool,
            "TEAM_BUTTON_NAMES": list,
            "TEAM_API_URL": str,
        }
        datatype = config_type.get(configname)
        if datatype is None:
            return
        if isinstance(configvalue, datatype):
            if isinstance(configvalue, list):
                self.__validate_config_list_type(configname, configvalue)
            return
        raise ValueError(f"The config option {configname} is not of type {datatype}")

    def __validate_config_list_type(self, configname, configlist):
        config_type = {
            "PUMP_PINS": int,
            "PUMP_VOLUMEFLOW": int,
            "TEAM_BUTTON_NAMES": str,
        }
        datatype = config_type.get(configname)
        for i, config in enumerate(configlist, 1):
            if not isinstance(config, datatype):
                raise ValueError(f"The {i} position of {configname} is not of type {datatype}")


class Shared:
    """Shared global variables which may dynamically change and are needed on different spaces"""

    def __init__(self):
        self.cocktail_started = False
        self.make_cocktail = True
        self.old_ingredient: List[str] = []
        self.selected_team = "Nothing"
        self.handaddlist: List[Ingredient] = []


def version_callback(value: bool):
    if value:
        typer.echo(f"{PROJECT_NAME} Version {__version__}. Created by Andre Wohnsland.")
        typer.echo(r"For more information visit https://github.com/AndreWohnsland/CocktailBerry.")
        raise typer.Exit()


shared = Shared()
