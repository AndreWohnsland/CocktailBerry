import os
import yaml

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "custom_config.yaml")


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
    UI_LANGUAGE = "de"
    # RPi pins where pumps (ascending) are connected
    PUMP_PINS = [14, 15, 18, 23, 24, 25, 8, 7, 17, 27, 22, 20]
    # Volumeflow for the according pumps
    PUMP_VOLUMEFLOW = [30, 30, 25, 30, 30, 30, 25, 30, 30, 23, 30, 30]
    # Number of bottles possible at the machine
    MAKER_NUMBER_BOTTLES = 10
    # Time in seconds to execute clean programm
    MAKER_CLEAN_TIME = 20
    # time between each check loop when making cocktail
    MAKER_SLEEP_TIME = 0.05
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
        attributes = [a for a in dir(self) if not (a.startswith('__') or a.startswith('_') or a.startswith('sync'))]
        config = {}
        for attribute in attributes:
            config[attribute] = getattr(self, attribute)
        with open(CONFIG_FILE, 'w', encoding="UTF-8") as stream:
            yaml.dump(config, stream, default_flow_style=False)
        # with open(CONFIG_FILE, 'w', encoding="UTF-8") as stream:
        #     data = json.dumps(config, indent=2)
        #     stream.write(data)

    def __read_config(self):
        with open(CONFIG_FILE, "r", encoding="UTF-8") as stream:
            configuration = yaml.safe_load(stream)
            for k, value in configuration.items():
                setattr(self, k, value)


class Shared:
    """Shared global variables which may dynamically change and are needed on different spaces"""

    def __init__(self):
        self.cocktail_started = False
        self.make_cocktail = True
        self.suppress_error = False
        self.old_ingredient = []
        self.selected_team = "Nothing"
        self.handaddlist = []


shared = Shared()
