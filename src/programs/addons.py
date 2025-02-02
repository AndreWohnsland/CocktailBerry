from __future__ import annotations

import atexit
import contextlib
import re
import threading
import time
from importlib import import_module
from typing import TYPE_CHECKING, Any, Callable, Literal, Protocol, runtime_checkable

import typer

from src import __version__
from src.api.internal.preparation import api_addon_prepare_flow
from src.filepath import ADDON_FOLDER, ADDON_SKELTON
from src.logger_handler import LoggerHandler
from src.models import Cocktail
from src.utils import time_print

with contextlib.suppress(ModuleNotFoundError):
    from PyQt5.QtWidgets import QVBoxLayout

    from src.ui.shared import qt_prepare_flow

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

_SupportedActions = Literal["setup", "cleanup", "before_cocktail", "after_cocktail", "cocktail_trigger"]
_logger = LoggerHandler("AddonManager")
_check_addon = "please check addon or contact provider"


@runtime_checkable
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

    def cocktail_trigger(self, prepare: Callable[[Cocktail], tuple[bool, str]]):
        """Will be executed in the background loop and can trigger a cocktail preparation.

        Use the prepare function to start a cocktail preparation with prepare(cocktail).
        Return if cocktail preparation was successful and a message.
        """


class AddOnManager:
    """Class to handle the execution of all the addons."""

    def __init__(self) -> None:
        addon_files = ADDON_FOLDER.glob("*.py")
        filenames = [x.stem for x in addon_files if "__init__" not in x.stem]
        self.addons: dict[str, AddonInterface] = {}
        for filename in filenames:
            try:
                module = import_module(f"addons.{filename}")
            except ModuleNotFoundError as e:
                message = f"Could not import addon: {filename} due to <{e}>, {_check_addon}."
                _logger.log_event("ERROR", message)
                time_print(message)
                continue
            name = filename
            if hasattr(module, "ADDON_NAME"):
                name = module.ADDON_NAME
            # Check if the module implemented the addon class, otherwise log error and skip module
            if not hasattr(module, "Addon"):
                _logger.log_event("WARNING", f"Could not get Addon class from {name}, {_check_addon}.")
                continue
            addon = getattr(module, "Addon")
            if not issubclass(addon, AddonInterface):
                _logger.log_event(
                    "WARNING",
                    f"Addon class in {name} does not implement the AddonInterface, {_check_addon}.",
                )
                continue
            self.addons[name] = addon()

    def setup_addons(self):
        """Execute all the setup function of the addons."""
        if self.addons:
            addon_string = ", ".join(list(self.addons.keys()))
            time_print(f"Used Addons: {addon_string}")
        self._try_function_for_addons("setup")
        atexit.register(self.cleanup_addons)

    def _create_cocktail_preparation(self, w: MainScreen | None = None) -> Callable[[Cocktail], tuple[bool, str]]:
        """Build the cocktail prepare function for the addon based on v1 (Qt) or v2."""
        if w is not None:
            return lambda cocktail: qt_prepare_flow(w, cocktail)
        # Caution, this currently does not work properly, because QT needs to be run on the main thread
        # We can neither run this on a tread, nor a QThread, because it will not work
        return api_addon_prepare_flow

    def start_trigger_loop(self, w: MainScreen | None = None):
        """Start the trigger loop for all addons.

        This will start a thread for each addon that will call the cocktail_trigger function.
        The function is used to prepare a cocktail over a programmed condition from the addon.
        """
        prepare_function = self._create_cocktail_preparation(w)

        def run_in_background(addon, prepare_function):
            while True:
                time.sleep(0.5)
                try:
                    func: Callable = getattr(addon, "cocktail_trigger")
                    func(prepare_function)
                # In case of an interface change in base app, this error will occur
                except TypeError:
                    _logger.error(
                        f"Could not execute cocktail_trigger for {addon.__module__}. "
                        + "This is probably due to a change in CocktailBerry that the addon currently did not adapt to."
                    )
                    break
                # If the function is not found (should usually not happen), ignore it
                except AttributeError:
                    break

        # Start threads, need to use QThread for GUI to work in case of QT (does not work, currently no GUI support)
        for addon in self.addons.values():
            thread = threading.Thread(target=run_in_background, args=(addon, prepare_function))
            thread.daemon = True
            thread.start()

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
