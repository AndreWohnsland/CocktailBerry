from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QVBoxLayout

# Auto created by CocktailBerry CLI version VERSION_HOLDER
# Imports are automatically generated for all the examples from the docs
# You can delete the imports you don't need
# For more information see: https://cocktailberry.readthedocs.io/addons/
# Use the cfg to add your config / validation
from src.config.config_manager import CONFIG as cfg
from src.config.errors import ConfigError

# You can access the default database with help of the dbc
from src.database_commander import DatabaseCommander

# Use the uil to add description and according translation
from src.dialog_handler import UI_LANGUAGE as uil

# Use the dpc to display dialogues or prompts to the user
from src.display_controller import DP_CONTROLLER as dpc

# Use the LoggerHandler class for your logger
from src.logger_handler import LoggerHandler
from src.models import Cocktail

# The addon interface will provide intellisense for all possible methods
from src.programs.addons import AddonInterface

ADDON_NAME = "ADDON_NAME_HOLDER"
_logger = LoggerHandler("ADDON: ADDON_NAME_HOLDER")


# The class needs to be called Addon and inherit from the AddonInterface
class Addon(AddonInterface):
    def setup(self):
        """Init the addon, executed at program start."""

    def cleanup(self):
        """Clean up the addon, executed a program end."""

    def before_cocktail(self, data: dict[str, Any]):
        """Run this method before the cocktail preparation.

        In case of a RuntimeError, the cocktail will not be prepared
        and the message will be shown to the user.
        """

    def after_cocktail(self, data: dict[str, Any]):
        """Run this method after the cocktail preparation."""

    def cocktail_trigger(self, prepare: Callable[[Cocktail], tuple[bool, str]]):
        """Will be executed in the background loop and can trigger a cocktail preparation.

        Use the prepare function to start a cocktail preparation with prepare(cocktail).
        It will return True, if the cocktail preparation was successful, otherwise False.
        In addition, there is a message, which can contain further information.
        """

    def build_gui(self, container: "QVBoxLayout", button_generator: Callable[[str, Callable[[], None]], None]) -> bool:
        """Build up the GUI to do additional things on command.

        Returns
        -------
            True, if you want to build an interface / GUI
            False, if you don't provide an interface / GUI

        """
        # Change to True, if you build your own GUI
        # Otherwise, an information will be shown, that the addon do not provide a GUI
        return False
