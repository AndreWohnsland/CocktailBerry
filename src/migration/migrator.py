from __future__ import annotations

from src.migration.version import Version
from src.python_vcheck import check_python_version

# Version check takes place before anything, else other imports may throw an error
check_python_version()

# pylint: disable=wrong-import-order,wrong-import-position,too-few-public-methods,ungrouped-imports
import configparser
import contextlib
import importlib.util
import platform
import shutil
import subprocess
import sys
from typing import Any, Callable, TypeVar

import yaml

from src import FUTURE_PYTHON_VERSION, __version__
from src.filepath import (
    BACKUP_FOLDER,
    CUSTOM_CONFIG_FILE,
    CUSTOM_STYLE_FILE,
    CUSTOM_STYLE_SCSS,
    VENV_FOLDER,
    VERSION_FILE,
)
from src.logger_handler import LoggerHandler
from src.migration.export_data import add_export_tables_to_db, migrate_csv_export_data_to_db
from src.migration.qt_migrator import roll_back_to_qt_script, script_entry_path
from src.migration.update_data import (
    add_cost_consumption_column_to_ingredients,
    add_foreign_keys,
    add_price_column_to_recipes,
    add_resource_usage_table,
    add_virgin_counters_to_recipes,
    clear_resource_log_file,
    fix_amount_in_recipe,
    remove_hand_from_recipe_data,
)
from src.migration.web_migrator import replace_backend_script

_logger = LoggerHandler("migrator_module")
T = TypeVar("T")


class Migrator:
    """Class to do all necessary migration locally for new versions."""

    def __init__(self) -> None:
        self.program_version = Version(__version__)
        self.config = configparser.ConfigParser()
        # if no file is found - assume we just installed (true for 99% of cases) - write latest version
        if not VERSION_FILE.exists():
            _logger.log_event("INFO", "No version file found, assuming fresh install, writing latest version")
            self._write_latest_to_local_version()
        self.config.read(VERSION_FILE)
        self.local_version = Version(self._get_local_version())

    def _get_local_version(self) -> str | None:
        try:
            local_version = self.config["DEFAULT"]["LOCALVERSION"]
        except KeyError:
            local_version = None
        return local_version

    def older_than_version(self, version: str | None) -> bool:
        """Check if the current version is below the given version."""
        return Version(version) > self.local_version

    def is_major_update(self, version: str) -> bool:
        """Check if the update to the given version is a major update."""
        new_version = Version(version)
        return new_version.major > self.local_version.major

    def older_than_version_with_logging(self, version: str) -> bool:
        """Check if the current version is below the given version."""
        is_older = Version(version) > self.local_version
        if is_older:
            self._migration_log(version)
        return is_older

    def _write_latest_to_local_version(self) -> None:
        """Write the latest version to the local version."""
        self.config["DEFAULT"]["LOCALVERSION"] = str(self.program_version.version)
        with VERSION_FILE.open("w", encoding="utf-8") as config_file:
            self.config.write(config_file)

    def make_migrations(self) -> None:
        """Make migration dependant on current local and program version."""
        _logger.log_event("INFO", f"Local version is: {self.local_version}, checking for necessary migrations")
        self._python_to_old_warning(FUTURE_PYTHON_VERSION)

        # define a version and the according list of actions to take
        version_actions = {
            "2.0.0": [
                lambda: self._install_pip_package("fastapi[standard]", "2.0.0"),
                lambda: self._install_pip_package("uvicorn", "2.0.0"),
                fix_amount_in_recipe,
            ],
            "2.1.0": [
                _install_uv,
                _check_and_replace_qt_launcher_script,
            ],
            "2.2.0": [
                add_foreign_keys,
                remove_hand_from_recipe_data,
            ],
            "2.2.2": [add_cost_consumption_column_to_ingredients],
            "2.3.0": [
                add_export_tables_to_db,
                migrate_csv_export_data_to_db,
            ],
            "2.4.0": [
                clear_resource_log_file,
                add_resource_usage_table,
            ],
            "2.6.0": [_add_maker_lock_value],
            "2.6.1": [add_virgin_counters_to_recipes],
            "2.6.2": [lambda: self._install_pip_package("pulp", "2.6.2")],
            "2.8.0": [_combine_led_setting_into_one_config],
            "3.0.0": [
                add_price_column_to_recipes,
                _install_pyqt6_over_apt,  # user running bookworm need this
            ],
        }

        for version, actions in version_actions.items():
            if self.older_than_version_with_logging(version):
                self._backup_config_file(version)
                for action in actions:
                    action()

        self._update_local_version_data()

    def _backup_config_file(self, suffix: str) -> None:
        """Save the config file at ~/cb_backup/custom_config_pre_{suffix}.yaml."""
        if not CUSTOM_CONFIG_FILE.exists():
            return
        save_path = BACKUP_FOLDER / f"custom_config_pre_{suffix}.yaml"
        _logger.log_event("INFO", f"Backing up config file to {save_path}")
        shutil.copy(CUSTOM_CONFIG_FILE, save_path)

    def _migration_log(self, version: str) -> None:
        """Log the migration message fro the version."""
        _logger.log_event("INFO", f"Making migrations for v{version}")

    def _python_to_old_warning(self, least_python: tuple[int, int]) -> None:
        """Log a warning that the future python is higher than system python."""
        sys_python = sys.version_info
        if sys_python < least_python:
            future_format = f"Python {least_python[0]}.{least_python[1]}"
            sys_format = f"{platform.python_version()}"
            _logger.log_event(
                "WARNING", f"Your used Python ({sys_format}) is deprecated, please upgrade to {future_format} or higher"
            )

    def _update_local_version_data(self) -> None:
        """Check to update the local version data."""
        if self.older_than_version(self.program_version.version):
            _logger.log_event("INFO", f"Local data migrated from {self.local_version} to {self.program_version}")
            self._update_custom_theme()
            self._write_latest_to_local_version()
        else:
            _logger.log_event("INFO", "Nothing to migrate")

    def _update_custom_theme(self) -> None:
        """Check and updates (compiles) the custom theme."""
        # skip if library is not installed, or file does not exist
        lib_not_installed = importlib.util.find_spec("qtsass") is None
        no_file = not CUSTOM_STYLE_SCSS.exists()
        if lib_not_installed or no_file:
            return
        import qtsass  # pylint:disable=import-outside-toplevel

        qtsass.compile_filename(CUSTOM_STYLE_SCSS, CUSTOM_STYLE_FILE)

    def _install_pip_package(self, package_name: str, version_to_migrate: str) -> None:
        """Try to install a python package over pip."""
        _logger.log_event("INFO", f"Trying to install {package_name}, it is needed since v{version_to_migrate}")
        if importlib.util.find_spec(package_name) is not None:
            _logger.log_event("INFO", f"Package {package_name} is already installed, skipping installation.")
            return
        # Check if uv is available
        uv_executable = shutil.which("uv")  # Find the uv executable in PATH
        pip_command = [sys.executable, "-m", "pip", "install", package_name]

        # Use uv install if uv is available
        if uv_executable:
            _logger.log_event("INFO", "Detected 'uv' command. Using 'uv pip install' for package installation.")
            pip_command = [uv_executable, "pip", "install", package_name]
        else:
            _logger.log_event("INFO", "'uv' not detected. Falling back to 'pip' for package installation.")

        try:
            subprocess.check_call(pip_command)
            _logger.log_event("INFO", f"Successfully installed {package_name}")
        except subprocess.CalledProcessError as err:
            err_msg = f"Could not install {package_name} using pip. Please install it manually!"
            err_msg += " See also debug logs for more information"
            _logger.log_event("ERROR", err_msg)
            _logger.log_exception(err)
            raise CouldNotMigrateException(version_to_migrate) from err


def _update_config_value_type(config_name: str, new_type: Callable[[Any], T], default_value: T) -> None:
    """Update the local config file, use the new given type.

    Uses the default if fails to convert.
    Also, if the given type is a list, it will try to convert the list elements.
    """
    configuration = _get_local_config(config_name)
    if configuration is None:
        return
    _logger.info(f"Converting config value for {config_name} to {new_type}")
    # get the value from the config, if not exists fall back to default
    local_config = configuration.get(config_name, default_value)
    # Try to convert, fall back to default if failure
    # also checks for a list, if so, convert each element
    if isinstance(local_config, list):
        new_values = []
        for element in local_config:
            new_values.append(_get_converted_value(new_type, default_value, element))
        configuration[config_name] = new_values
    else:
        configuration[config_name] = _get_converted_value(new_type, default_value, local_config)
    with CUSTOM_CONFIG_FILE.open("w", encoding="UTF-8") as stream:
        yaml.dump(configuration, stream, default_flow_style=False)


def _get_local_config(config_name: str) -> dict[str, Any] | None:
    if not CUSTOM_CONFIG_FILE.exists():
        _logger.info(f"No local config detected for {config_name}, skipping conversion")
        return None
    with CUSTOM_CONFIG_FILE.open(encoding="UTF-8") as stream:
        return yaml.safe_load(stream)


def _add_maker_lock_value() -> None:
    """Add the maker lock value to the config."""
    configuration = _get_local_config("UI_LOCKED_TABS")
    if configuration is None:
        return
    locked_tabs: list[bool] = configuration.get("UI_LOCKED_TABS", [False, True, True, True])
    if len(locked_tabs) == 3:  # noqa: PLR2004
        locked_tabs.insert(0, False)
    _logger.info(f"Using for migration: {locked_tabs=}")
    configuration["UI_LOCKED_TABS"] = locked_tabs
    with CUSTOM_CONFIG_FILE.open("w", encoding="UTF-8") as stream:
        yaml.dump(configuration, stream, default_flow_style=False)


def _get_converted_value(new_type: Callable[[Any], T], default_value: T, local_config: Any) -> T:
    try:
        new_value = new_type(local_config)
    except (ValueError, TypeError):
        new_value = default_value
    return new_value


def _install_uv() -> None:
    """Install uv for python dependency management."""
    _logger.info("Installing uv for python dependency management")
    uv_installed = shutil.which("uv")
    if uv_installed:
        _logger.info("uv is already installed, skipping installation")
        return
    platform_name = platform.system().lower()
    if platform_name == "windows":
        subprocess.run(
            'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"',
            check=False,
            shell=True,
        )
    else:
        subprocess.run("curl -LsSf https://astral.sh/uv/install.sh | sh", check=False, shell=True)


def _check_and_replace_qt_launcher_script() -> None:
    # check if the script has the basic python runme.py command without api
    needed_commands = ["runme.py"]
    with contextlib.suppress(FileNotFoundError):
        current_script_text = script_entry_path.read_text()
        _logger.info("Updating the launcher script to the new version with uv")
        if not all(command in current_script_text for command in needed_commands):
            replace_backend_script()
            return
        # need to also add uv venv on linux here if uv is already available
        # This is because we need the system site package for pyqt
        uv_executable = shutil.which("uv")
        platform_name = platform.system().lower()
        if not VENV_FOLDER.exists() and uv_executable and platform_name == "linux":
            subprocess.run(
                [uv_executable, "uv", "venv", "--system-site-packages", "--python", "$(python -V | awk '{print $2}')"],
                check=True,
            )
        roll_back_to_qt_script()


def _combine_led_setting_into_one_config() -> None:
    """Combine the LED settings into two separate configs based on LED type.

    Old settings (LED_PINS, LED_BRIGHTNESS, etc.) are migrated into either
    LED_NORMAL (for standard LEDs) or LED_WSLED (for WS281x LEDs).
    One config entry is created for each pin.
    """
    configuration = _get_local_config("convert LED settings")
    if configuration is None:
        return

    # Get the value from the config, if not exists fall back to default
    led_pins = configuration.get("LED_PINS", [])
    led_brightness = configuration.get("LED_BRIGHTNESS", 100)
    led_count = configuration.get("LED_COUNT", 24)
    led_number_rings = configuration.get("LED_NUMBER_RINGS", 1)
    led_default_on = configuration.get("LED_DEFAULT_ON", False)
    led_preparation_state = configuration.get("LED_PREPARATION_STATE", "Effect")
    led_is_ws = configuration.get("LED_IS_WS", True)

    _logger.info(
        f"Using for LED migration: {led_pins=}, {led_brightness=}, {led_count=}, "
        f"{led_number_rings=}, {led_default_on=}, {led_preparation_state=}, {led_is_ws=}"
    )

    # Create the appropriate config list based on LED type
    # Note: we keep dicts here since we just read in the plain dicts, not the classes
    if led_is_ws:
        # WS281x (addressable) LEDs
        led_wsled_config: list[dict] = []
        for pin in led_pins:
            led_wsled_config.append(
                {
                    "pin": pin,
                    "brightness": min(int(led_brightness / 255 * 100), 100),  # convert to percentage, old max was 255
                    "count": led_count,
                    "number_rings": led_number_rings,
                    "default_on": led_default_on,
                    "preparation_state": led_preparation_state,
                }
            )
        configuration["LED_WSLED"] = led_wsled_config
    else:
        # Normal (non-addressable) LEDs
        led_normal_config: list[dict] = []
        for pin in led_pins:
            led_normal_config.append(
                {
                    "pin": pin,
                    "default_on": led_default_on,
                    "preparation_state": led_preparation_state,
                }
            )
        configuration["LED_NORMAL"] = led_normal_config

    with CUSTOM_CONFIG_FILE.open("w", encoding="UTF-8") as stream:
        yaml.dump(configuration, stream, default_flow_style=False)


def _install_pyqt6_over_apt() -> None:
    """Check if apt is available and installs pyqt6 over apt."""
    apt_executable = shutil.which("apt")
    if not apt_executable:
        _logger.info("apt not found, skipping pyqt6 installation over apt")
        return
    _logger.info("Installing pyqt6 over apt")
    try:
        subprocess.run(["sudo", apt_executable, "update"], check=True)
        subprocess.run(["sudo", apt_executable, "install", "-y", "python3-pyqt6"], check=True)
        _logger.info("Successfully installed pyqt6 over apt")
    except subprocess.CalledProcessError as err:
        _logger.error("Could not install pyqt6 using apt. Please install it manually!")
        _logger.log_exception(err)


class CouldNotMigrateException(Exception):
    """Raised when there was an error with the migration."""

    def __init__(self, version: str) -> None:
        self.message = f"Error while migration to version: {version}"
        super().__init__(self.message)
