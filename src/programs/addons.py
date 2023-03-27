from importlib import import_module
import re
from typing import Callable, Literal, Protocol

import typer
from PyQt5.QtWidgets import QVBoxLayout

from src.filepath import ADDON_FOLDER, ADDON_SKELTON
from src.logger_handler import LoggerHandler
from src import __version__

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
        addon_files = ADDON_FOLDER.glob("*.py")
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
        if self.addons:
            addon_string = ", ".join(list(self.addons.keys()))
            print(f"Used Addons: {addon_string}")
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
        button_generator: Callable[[str, Callable[[], None]], None],
    ) -> bool:
        """Builds the gui for the selected addon
        If method is not provided, return false.
        """
        addon = self.addons[addon_name]
        if hasattr(addon, "build_gui"):
            return addon.build_gui(container, button_generator)
        return False


def generate_addon_skeleton(name: str):
    """Creates an base addon file unter the given name"""
    # Converts space into underscores
    file_name = name.replace(" ", "_")
    # strips all other unwanted things
    file_name = re.sub(r"\W", "", file_name.lower())
    addon_path = ADDON_FOLDER / f"{file_name}.py"
    if addon_path.exists():
        msg = f"There is already an addon created under the {name=} in {file_name}.py"
        typer.echo(typer.style(f"{msg}, aborting...", fg=typer.colors.RED, bold=True))
        raise typer.Exit()
    addon_path.write_text(
        (
            ADDON_SKELTON.read_text(encoding="utf-8")
            .replace("ADDON_NAME_HOLDER", name)
            .replace("VERSION_HOLDER", __version__)
        ),
        encoding="utf-8",
    )
    msg = f"Addon file was create at {addon_path}"
    typer.echo(typer.style(msg, fg=typer.colors.GREEN, bold=True))


ADDONS = AddOnManager()
