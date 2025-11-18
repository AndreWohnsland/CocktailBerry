from __future__ import annotations

import atexit
import contextlib
import importlib
import json
import re
import sys
import threading
import time
from dataclasses import fields
from importlib import import_module
from typing import TYPE_CHECKING, Any, Callable, Literal, Protocol, runtime_checkable

import requests
import typer
from requests.exceptions import ConnectionError as ReqConnectionError

from src import __version__
from src.filepath import ADDON_FOLDER, ADDON_SKELTON
from src.logger_handler import LoggerHandler
from src.models import AddonData, Cocktail
from src.utils import time_print

with contextlib.suppress(ModuleNotFoundError):
    from PyQt5.QtWidgets import QVBoxLayout

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

_SupportedActions = Literal[
    "define_configuration",
    "setup",
    "cleanup",
    "before_cocktail",
    "after_cocktail",
    "cocktail_trigger",
]
_logger = LoggerHandler("AddonManager")
_check_addon = "please check addon or contact provider"
_GITHUB_ADDON_SOURCE = "https://raw.githubusercontent.com/AndreWohnsland/CocktailBerry-Addons/main/addon_data_v2.json"


class CouldNotInstallAddonError(Exception):
    pass


@runtime_checkable
class AddonInterface(Protocol):
    def version(self) -> str:
        """Return the version of the addon."""
        return getattr(self, "ADDON_VERSION", "1.0.0")

    def define_configuration(self) -> None:
        """Define configuration for the addon."""

    def setup(self) -> None:
        """Init the addon."""

    def cleanup(self) -> None:
        """Clean up the addon."""

    def before_cocktail(self, data: dict[str, Any]) -> None:
        """Logic to be executed before the cocktail."""

    def after_cocktail(self, data: dict[str, Any]) -> None:
        """Logic to be executed after the cocktail."""

    def build_gui(
        self,
        container: QVBoxLayout,
        button_generator: Callable[[str, Callable[[], None]], None],
    ) -> bool:
        """Logic to build up the addon GUI."""
        return False

    def cocktail_trigger(self, prepare: Callable[[Cocktail], tuple[bool, str]]) -> None:
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
        self.addon_thread_ids: dict[str, int] = {}
        for filename in filenames:
            self._load_in_addon(filename)

    def _load_in_addon(self, filename: str) -> None | tuple[str, AddonInterface]:
        """Load an addon from a file."""
        try:
            module = import_module(f"addons.{filename}")
        except ImportError as e:
            message = f"Could not import addon: {filename} due to <{e}>, {_check_addon}."
            _logger.log_event("ERROR", message)
            time_print(message)
            return None
        name = getattr(module, "ADDON_NAME", filename)
        # Check if the module implemented the addon class, otherwise log error and skip module
        if not hasattr(module, "Addon"):
            _logger.log_event("WARNING", f"Could not get Addon class from {name}, {_check_addon}.")
            return None
        addon = getattr(module, "Addon")
        if not issubclass(addon, AddonInterface):
            _logger.log_event(
                "WARNING",
                f"Addon class in {name} does not implement the AddonInterface, {_check_addon}.",
            )
            return None
        addon_instance = addon()
        self.addons[name] = addon_instance
        return name, addon_instance

    def define_addon_configuration(self) -> None:
        """Define configuration for all addons."""
        for addon in self.addons.values():
            self._try_function_for_addon(addon, "define_configuration")

    def setup_addons(self) -> None:
        """Execute all the setup function of the addons."""
        if self.addons:
            addon_string = ", ".join(list(self.addons.keys()))
            time_print(f"Used Addons: {addon_string}")
        for addon in self.addons.values():
            self._try_function_for_addon(addon, "setup")
        atexit.register(self.cleanup_addons)

    def _create_cocktail_preparation(self, w: MainScreen | None = None) -> Callable[[Cocktail], tuple[bool, str]]:
        """Build the cocktail prepare function for the addon based on v1 (Qt) or v2."""
        from src.api.internal.preparation import api_addon_prepare_flow

        with contextlib.suppress(ModuleNotFoundError):
            from src.ui.shared import qt_prepare_flow

        if w is not None:
            return lambda cocktail: qt_prepare_flow(w, cocktail)
        # Caution, this currently does not work properly, because QT needs to be run on the main thread
        # We can neither run this on a tread, nor a QThread, because it will not work
        return api_addon_prepare_flow

    def _run_in_background(
        self,
        addon_name: str,
        addon: AddonInterface,
        prepare_function: Callable[[Cocktail], tuple[bool, str]],
        thread_id: int,
    ) -> None:
        self.addon_thread_ids[addon_name] = thread_id
        while True:
            time.sleep(0.5)
            # if there was a new thread for the addon started, or this one removed, exit
            if self.addon_thread_ids.get(addon_name, -1) != thread_id:
                break
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

    def start_trigger_loop(self, w: MainScreen | None = None) -> None:
        """Start the trigger loop for all addons.

        This will start a thread for each addon that will call the cocktail_trigger function.
        The function is used to prepare a cocktail over a programmed condition from the addon.
        """
        prepare_function = self._create_cocktail_preparation(w)

        # Start threads, need to use QThread for GUI to work in case of QT (does not work, currently no GUI support)
        for addon_name, addon in self.addons.items():
            thread = threading.Thread(
                target=self._run_in_background,
                args=(
                    addon_name,
                    addon,
                    prepare_function,
                    int(time.time()),
                ),
            )
            thread.daemon = True
            thread.start()

    def cleanup_addons(self) -> None:
        """Clean up all the addons."""
        for addon in self.addons.values():
            self._try_function_for_addon(addon, "cleanup")

    def before_cocktail(self, data: dict[str, Any]) -> None:
        """Execute addon part before cocktail."""
        for addon in self.addons.values():
            self._try_function_for_addon(addon, "before_cocktail", data)

    def after_cocktail(self, data: dict[str, Any]) -> None:
        """Execute addon part after cocktail."""
        for addon in self.addons.values():
            self._try_function_for_addon(addon, "after_cocktail", data)

    def _try_function_for_addon(
        self,
        addon: AddonInterface,
        function_name: _SupportedActions,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Try the according function for the list of addons.

        Catches AttributeError (function was not defined).
        """
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

    def install_addon(self, addon: AddonData) -> None:
        """Add a new addon to the manager."""
        addon_file = ADDON_FOLDER / addon.file_name
        try:
            req = requests.get(addon.url, allow_redirects=True, timeout=5)
            if req.ok:
                addon_file.write_bytes(req.content)
            else:
                raise CouldNotInstallAddonError(
                    f"Could not get {addon.name} from {addon.url}: {req.status_code} {req.reason}"
                )
        except ReqConnectionError:
            raise CouldNotInstallAddonError(f"Could not get {addon.name} from {addon.url}: No internet connection")
        addon_init = self._load_in_addon(addon_file.stem)
        if addon_init is None:
            return
        name, addon_instance = addon_init
        time_print(f"Setting up newly added addon {name}")
        self._try_function_for_addon(addon_instance, "setup")

        # Do not support V1 for now
        thread = threading.Thread(
            target=self._run_in_background,
            args=(name, addon_instance, self._create_cocktail_preparation(None), int(time.time())),
        )
        thread.daemon = True
        thread.start()

    def remove_addon(self, addon: AddonData) -> None:
        """Remove an addon from the manager."""
        if addon.name in self.addons:
            addon_instance = self.addons[addon.name]
            self._try_function_for_addon(addon_instance, "cleanup")
            del self.addons[addon.name]
            time_print(f"Removed addon {addon.name}")
        if addon.name in self.addon_thread_ids:
            del self.addon_thread_ids[addon.name]
        addon_file = ADDON_FOLDER / addon.file_name

        addon_file.unlink(missing_ok=True)

        # Remove the module from sys.modules to allow fresh import
        module_name = f"addons.{addon_file.stem}"
        if module_name in sys.modules:
            del sys.modules[module_name]
        importlib.invalidate_caches()

    def reload_addon(self, addon_data: AddonData) -> None:
        """Reload an addon in the manager."""
        self.remove_addon(addon_data)
        self.install_addon(addon_data)

    def _addon_from_json_data(self, data: dict) -> AddonData:
        """Filter JSON dict to only supported AddonData fields, using dataclass fields dynamically."""
        supported_fields = {f.name for f in fields(AddonData)}
        return AddonData(**{k: v for k, v in data.items() if k in supported_fields})

    def get_addon_data(self) -> list[AddonData]:
        """Get all the addon data from source and locally installed ones, build the data objects."""
        # get the addon data from the source
        # This should provide name, description and url
        installed_addons_lowercase_key = {k.lower(): v for k, v in ADDONS.addons.items()}
        official_addons: list[AddonData] = []
        try:
            req = requests.get(_GITHUB_ADDON_SOURCE, allow_redirects=True, timeout=5)
            if req.ok:
                gh_data = json.loads(req.text)
                official_addons = [self._addon_from_json_data(data) for data in gh_data]
        except ReqConnectionError:
            _logger.log_event("WARNING", "Could not fetch addon data from source, is there an internet connection?")

        # Check if the addon is installed
        for addon in official_addons:
            if addon.name.lower() in installed_addons_lowercase_key:
                addon.installed = True
                addon.local_version = installed_addons_lowercase_key[addon.name.lower()].version()

        # also add local addons, which are not official ones to the list
        possible_addons = official_addons
        for local_addon_name, addon_class in ADDONS.addons.items():
            if local_addon_name.lower() in [a.name.lower() for a in possible_addons]:
                continue
            file_name = f"{addon_class.__module__.split('.')[-1]}.py"
            possible_addons.append(
                AddonData(
                    name=local_addon_name,
                    description="Installed addon is not in list of official ones. Please manage over file system.",
                    url=file_name,
                    disabled_since="",
                    version=addon_class.version(),
                    local_version=addon_class.version(),
                    file_name=file_name,
                    installed=True,
                    official=False,
                )
            )
        return possible_addons


def generate_addon_skeleton(name: str) -> None:
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
