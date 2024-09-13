from __future__ import annotations

import atexit
import re
from importlib import import_module
from typing import Any, Callable, Literal, Protocol

import typer
from PyQt5.QtWidgets import QVBoxLayout

from src import __version__
from src.filepath import ADDON_FOLDER, ADDON_SKELTON
from src.logger_handler import LoggerHandler
from src.utils import time_print

_SupportedActions = Literal["setup", "cleanup", "before_cocktail", "after_cocktail"]
_logger = LoggerHandler("AddonManager")


class AddonInterface(Protocol):
    def setup(self):
        """Init the addon."""

    def cleanup(self):
        """Clean up the addon."""

    def before_cocktail(self, data: dict[str, Any]):
        """Logic to be executed before the cocktail."""

    def after_cocktail(self, data: dict[str, Any]):
        """Logic to be executed after the cocktail."""

    def build_gui(
        self,
        container: QVBoxLayout,
        button_generator: Callable[[str, Callable[[], None]], None],
    ) -> bool:
        """Logic to build up the addon GUI."""
        return False


class AddOnManager:
    """Class to handle the execution of all the addons."""

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
                    "ERROR", f"Could not get Addon class from {name}, please check addon or contact provider."
                )
                continue
            addon = getattr(module, "Addon")
            self.addons[name] = addon()

    def setup_addons(self):
        """Execute all the setup function of the addons."""
        if self.addons:
            addon_string = ", ".join(list(self.addons.keys()))
            time_print(f"Used Addons: {addon_string}")
        self._try_function_for_addons("setup")
        atexit.register(self.cleanup_addons)

    def cleanup_addons(self):
        """Clean up all the addons."""
        self._try_function_for_addons("cleanup")

    def before_cocktail(self, data: dict[str, Any]):
        """Execute addon part before cocktail."""
        self._try_function_for_addons("before_cocktail", data)

    def after_cocktail(self, data: dict[str, Any]):
        """Execute addon part after cocktail."""
        self._try_function_for_addons("after_cocktail", data)

    def _try_function_for_addons(
        self,
        function_name: _SupportedActions,
        data: dict[str, Any] | None = None,
    ):
        """Try the according function for the list of addons.

        Catches AttributeError (function was not defined).
        """
        for addon in self.addons.values():
            try:
                func = getattr(addon, function_name)
                if data is None:
                    func()
                else:
                    func(data)
            # In case of an interface change in base app, this error will occur
            except TypeError:
                _logger.error(
                    f"Could not execute {function_name} for {addon.__module__}. "
                    + "This is probably due to a change in CocktailBerry that the addon currently did not adapt to."
                )
            # If the function is not found (should usually not happen), ignore it
            except AttributeError:
                pass

    def build_addon_gui(
        self,
        addon_name: str,
        container: QVBoxLayout,
        button_generator: Callable[[str, Callable[[], None]], None],
    ) -> bool:
        """Build the gui for the selected addon.

        If method is not provided, return false.
        """
        addon = self.addons[addon_name]
        if hasattr(addon, "build_gui"):
            return addon.build_gui(container, button_generator)
        return False


def generate_addon_skeleton(name: str):
    """Create an base addon file unter the given name."""
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
