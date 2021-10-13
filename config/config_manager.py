class ConfigManager:
    """Manager for all static configuration of the machine """

    # Password to lock clean, delete and other critical operators
    MASTERPASSWORD = "1337"
    # RPi pins where pumps (ascending) are connected
    USEDPINS = [14, 15, 18, 23, 24, 25, 8, 7, 17, 27, 22, 20]
    # Volumeflow for the according pumps
    PUMP_VOLUMEFLOW = [30, 30, 25, 30, 30, 30, 25, 30, 30, 23, 30, 30]
    # Number of bottles possible at the machine
    NUMBER_BOTTLES = 10
    # Time in seconds to execute clean programm
    CLEAN_TIME = 20
    # time between each check loop when making cocktail
    SLEEP_TIME = 0.05
    # Locks the recipe tab, making it impossible to acesss
    PARTYMODE = False
    # Names for the according logger files
    LOGGERNAME = "cocktaillogger"
    LOGGERNAME_DEBUG = "debuglogger"
    # If to use microservice (mostly docker on same device) to handle external API calls and according url
    USE_MICROSERVICE = False
    MICROSERVICE_BASE_URL = "http://127.0.0.1:5000"
    # if to use the teams function and according options.
    # URL should be 'device_ip:8080' where dashboard container is running and in the same network
    USE_TEAMS = True
    TEAM_BUTTON_NAMES = ["Team 1", "Team 2"]
    TEAM_API_URL = "http://127.0.0.1:8080"
    # Activating some dev features like mouse cursor
    DEVENVIRONMENT = True


class Shared:
    """Shared global variables which may dynamically change and are needed on different spaces"""

    def __init__(self):
        self.cocktail_started = False
        self.make_cocktail = True
        self.supress_error = False
        self.old_ingredient = []


shared = Shared()
