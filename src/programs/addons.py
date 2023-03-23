from importlib import import_module
from typing import Literal

from src.filepath import ADDON_PATH


class AddOnManager:
    """Class to handle the execution of all the addons"""

    def __init__(self) -> None:
        addon_names = ADDON_PATH.glob("*.py")
        addon_names = [x.stem for x in addon_names if "__init__" not in x.stem]
        self.addons = [import_module(f"addons.{x}") for x in addon_names]  # type: ignore | using if is better

    def init_addons(self):
        """Execute all the init function of the addons"""
        self._try_function_for_addons("init")

    def cleanup_addons(self):
        """Clean up all the addons"""
        self._try_function_for_addons("cleanup")

    def pre_cocktail(self):
        """Execute addon part before cocktail"""
        self._try_function_for_addons("start")

    def post_cocktail(self):
        """Execute addon part after cocktail"""
        self._try_function_for_addons("end")

    def _try_function_for_addons(
        self,
        function_name: Literal["init", "cleanup", "start", "end"]
    ):
        """Tries the according function for the list of addons
        Catches AttributeError (function was not defined)
        """
        for addon in self.addons:
            try:
                func = getattr(addon, function_name)
                func()
            except AttributeError:
                pass


ADDONS = AddOnManager()
