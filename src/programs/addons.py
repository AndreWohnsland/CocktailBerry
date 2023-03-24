from importlib import import_module
from typing import Callable, Literal, Protocol

from PyQt5.QtWidgets import QVBoxLayout

from src.filepath import ADDON_PATH
from src.logger_handler import LoggerHandler

_SupportedActions = Literal[
    "setup", "cleanup",
    "before_cocktail", "after_cocktail"
]
_logger = LoggerHandler("AddonManager")


class AddonInterface(Protocol):
    def setup(self):
        """Init the addon"""

    def cleanup(self):
        """Clean up the addon"""

    def before_cocktail(self):
        """Logic to be executed before the cocktail"""

    def after_cocktail(self):
        """Logic to be executed after the cocktail"""

    def build_gui(
        self,
        container: QVBoxLayout,
        button_generator: Callable[[str, Callable[[], None]], None],
    ) -> bool:
        """Logic to build up the addon GUI."""
        return False


class AddOnManager:
    """Class to handle the execution of all the addons"""

    def __init__(self) -> None:
        addon_files = ADDON_PATH.glob("*.py")
        filenames = [x.stem for x in addon_files if "__init__" not in x.stem]
        self.addons: dict[str, AddonInterface] = {}
        for filename in filenames:
            module = import_module(f"addons.{filename}")
            name = filename
            if hasattr(module, "ADDON_NAME"):
                name = module.ADDON_NAME
            # Check if the module implemented the addon class, otherwise log error and skip module
            if not hasattr(module, "Addon"):
                _logger.log_event(
                    "ERROR",
                    f"Could not get Addon class from {name}, please check addon or contact provider."
                )
                continue
            addon = getattr(module, "Addon")
            self.addons[name] = addon()

    def setup_addons(self):
        """Execute all the setup function of the addons"""
        self._try_function_for_addons("setup")

    def cleanup_addons(self):
        """Clean up all the addons"""
        self._try_function_for_addons("cleanup")

    def before_cocktail(self):
        """Execute addon part before cocktail"""
        self._try_function_for_addons("before_cocktail")

    def after_cocktail(self):
        """Execute addon part after cocktail"""
        self._try_function_for_addons("after_cocktail")

    def _try_function_for_addons(
        self,
        function_name: _SupportedActions,
    ):
        """Tries the according function for the list of addons
        Catches AttributeError (function was not defined)
        """
        for addon in self.addons.values():
            try:
                func = getattr(addon, function_name)
                func()
            except AttributeError:
                pass

    def build_addon_gui(
        self,
        addon_name: str,
        container: QVBoxLayout,
        button_generator: Callable[[str, Callable], None],
    ) -> bool:
        """Builds the gui for the selected addon
        If method is not provided, return false.
        """
        addon = self.addons[addon_name]
        if hasattr(addon, "build_gui"):
            addon.build_gui(container, button_generator)
            return True
        return False


ADDONS = AddOnManager()
