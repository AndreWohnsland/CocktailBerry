from __future__ import annotations

# pylint: disable=wrong-import-order,wrong-import-position,too-few-public-methods,ungrouped-imports
from src.python_vcheck import check_python_version

# Version check takes place before anything, else other imports may throw an error
check_python_version()


import configparser
import importlib.util
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from src import FUTURE_PYTHON_VERSION, __version__
from src.filepath import CUSTOM_CONFIG_FILE, CUSTOM_STYLE_FILE, CUSTOM_STYLE_SCSS, VERSION_FILE
from src.logger_handler import LoggerHandler
from src.migration.update_data import (
    add_cost_column_to_ingredients,
    add_more_bottles_to_db,
    add_order_column_to_ingredient_data,
    add_slower_ingredient_flag_to_db,
    add_team_buffer_to_database,
    add_unit_column_to_ingredients,
    add_virgin_flag_to_db,
    change_slower_flag_to_pump_speed,
    fix_amount_in_recipe,
    remove_is_alcoholic_column,
    remove_old_recipe_columns,
    rename_database_to_english,
)

_logger = LoggerHandler("migrator_module")


class Migrator:
    """Class to do all necessary migration locally for new versions."""

    def __init__(self) -> None:
        self.program_version = _Version(__version__)
        self.config = configparser.ConfigParser()
        self.config.read(VERSION_FILE)
        self.local_version = _Version(self._get_local_version())

    def _get_local_version(self):
        try:
            local_version = self.config["DEFAULT"]["LOCALVERSION"]
        except KeyError:
            local_version = None
        return local_version

    def older_than_version(self, version: str | None) -> bool:
        """Check if the current version is below the given version."""
        return _Version(version) > self.local_version

    def older_than_version_with_logging(self, version: str) -> bool:
        """Check if the current version is below the given version."""
        is_older = _Version(version) > self.local_version
        if is_older:
            self._migration_log(version)
        return is_older

    def _write_local_version(self):
        """Write the latest version to the local version."""
        _logger.log_event("INFO", f"Local data migrated from {self.local_version} to {self.program_version}")
        self.config["DEFAULT"]["LOCALVERSION"] = str(self.program_version.version)
        with open(VERSION_FILE, "w", encoding="utf-8") as config_file:
            self.config.write(config_file)

    def make_migrations(self):
        """Make migration dependant on current local and program version."""
        _logger.log_event("INFO", f"Local version is: {self.local_version}, checking for necessary migrations")
        self._python_to_old_warning(FUTURE_PYTHON_VERSION)

        # define a version and the according list of actions to take
        version_actions = {
            "1.5.0": [
                rename_database_to_english,
                add_team_buffer_to_database,
                lambda: self._install_pip_package("GitPython", "1.5.0"),
            ],
            "1.5.3": [lambda: self._install_pip_package("typer", "1.5.3")],
            "1.6.0": [
                self._change_git_repo,
                lambda: self._install_pip_package("pyfiglet", "1.6.0"),
            ],
            "1.6.1": [add_more_bottles_to_db],
            "1.9.0": [
                add_virgin_flag_to_db,
                remove_is_alcoholic_column,
                lambda: self._install_pip_package("typing_extensions", "1.9.0"),
            ],
            "1.11.0": [lambda: self._install_pip_package("qtawesome", "1.11.0")],
            "1.17.0": [lambda: self._install_pip_package("pyqtspinner", "1.17.0")],
            "1.18.0": [remove_old_recipe_columns],
            "1.19.3": [lambda: _update_config_value_type("UI_MASTERPASSWORD", int, 0)],
            "1.22.0": [add_slower_ingredient_flag_to_db],
            "1.23.1": [lambda: _update_config_value_type("PUMP_SLOW_FACTOR", float, 1.0)],
            "1.26.1": [lambda: _update_config_value_type("PUMP_VOLUMEFLOW", float, 1.0)],
            "1.29.0": [add_cost_column_to_ingredients],
            "1.30.0": [
                add_order_column_to_ingredient_data,
                lambda: self._install_pip_package("pillow", "1.30.0"),
            ],
            "1.30.1": [add_unit_column_to_ingredients],
            "1.33.0": [_move_slow_factor_to_db],
            "1.35.0": [lambda: self._install_pip_package("psutil", "1.35.0")],
            "1.36.0": [
                _combine_pump_setting_into_one_config,
                lambda: self._install_pip_package("distro", "1.36.0"),
            ],
            "2.0.0": [
                lambda: self._install_pip_package("fastapi[standard]", "2.0.0"),
                lambda: self._install_pip_package("uvicorn", "2.0.0"),
                fix_amount_in_recipe,
            ],
        }

        for version, actions in version_actions.items():
            if self.older_than_version_with_logging(version):
                self._backup_config_file(version)
                for action in actions:
                    action()

        self._check_local_version_data()

    def _backup_config_file(self, suffix):
        """Save the config file at ~/cb_backup/custom_config_pre_{suffix}.yaml."""
        if not CUSTOM_CONFIG_FILE.exists():
            return
        save_path = Path.home() / "cb_backup" / f"custom_config_pre_{suffix}.yaml"
        _logger.log_event("INFO", f"Backing up config file to {save_path}")
        # Ensure the backup directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(CUSTOM_CONFIG_FILE, save_path)

    def _migration_log(self, version: str):
        """Log the migration message fro the version."""
        _logger.log_event("INFO", f"Making migrations for v{version}")

    def _python_to_old_warning(self, least_python: tuple[int, int]):
        """Log a warning that the future python is higher than system python."""
        sys_python = sys.version_info
        if sys_python < least_python:
            future_format = f"Python {least_python[0]}.{least_python[1]}"
            sys_format = f"{platform.python_version()}"
            _logger.log_event(
                "WARNING", f"Your used Python ({sys_format}) is deprecated, please upgrade to {future_format} or higher"
            )

    def _check_local_version_data(self):
        """Check to update the local version data."""
        if self.older_than_version(self.program_version.version):
            self._update_custom_theme()
            self._write_local_version()
        else:
            _logger.log_event("INFO", "Nothing to migrate")

    def _update_custom_theme(self):
        """Check and updates (compiles) the custom theme."""
        # skip if library is not installed, or file does not exist
        lib_not_installed = importlib.util.find_spec("qtsass") is None
        no_file = not CUSTOM_STYLE_SCSS.exists()
        if lib_not_installed or no_file:
            return
        import qtsass  # pylint:disable=import-outside-toplevel

        qtsass.compile_filename(CUSTOM_STYLE_SCSS, CUSTOM_STYLE_FILE)

    def _change_git_repo(self):
        """Set the git source to the new named repo."""
        _logger.log_event("INFO", "Changing git origin to new repo name")
        try:
            subprocess.check_call(
                ["git", "remote", "set-url", "origin", "https://github.com/AndreWohnsland/CocktailBerry.git"]
            )
        except subprocess.CalledProcessError as err:
            err_msg = "Could not change origin. Check if you made any local file changes / use 'git restore .'!"
            err_msg += " See also debug logs for more information"
            _logger.log_event("ERROR", err_msg)
            _logger.log_exception(err)
            raise CouldNotMigrateException("1.6.0") from err

    def _install_pip_package(self, package_name: str, version_to_migrate: str):
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


def _update_config_value_type(config_name: str, new_type: type, default_value: Any):
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
    with open(CUSTOM_CONFIG_FILE, "w", encoding="UTF-8") as stream:
        yaml.dump(configuration, stream, default_flow_style=False)


def _get_local_config(config_name) -> dict[str, Any] | None:
    if not CUSTOM_CONFIG_FILE.exists():
        _logger.info(f"No local config detected for {config_name}, skipping conversion")
        return None
    with open(CUSTOM_CONFIG_FILE, encoding="UTF-8") as stream:
        return yaml.safe_load(stream)


def _combine_pump_setting_into_one_config():
    """Combine the pump settings into one config.

    The pump settings were split into two different configs, now they will be combined.
    """
    configuration = _get_local_config("convert pum settings")
    if configuration is None:
        return
    # get the value from the config, if not exists fall back to default
    pump_pins = configuration.get("PUMP_PINS")
    if pump_pins is None:
        pump_pins = [14, 15, 18, 23, 24, 25, 8, 7, 17, 27]
        _logger.info("No pump pins found in config, using fallback pins")
    pump_volume_flow = configuration.get("PUMP_VOLUMEFLOW")
    if pump_volume_flow is None:
        pump_volume_flow = [30.0] * len(pump_pins)
        _logger.info("No pump volume flow found in config, using fallback volume flow")
    tube_volume = configuration.get("MAKER_TUBE_VOLUME", 0)
    _logger.info(f"Using for migration: {tube_volume=}, {pump_pins=}, {pump_volume_flow=}")
    pump_config: list[dict] = []
    # we just read in the plain dict but not the classes in the migrator, so keep this in mind.
    for pin, volume_flow in zip(pump_pins, pump_volume_flow):
        pump_config.append({"pin": pin, "volume_flow": volume_flow, "tube_volume": tube_volume})
    configuration["PUMP_CONFIG"] = pump_config
    with open(CUSTOM_CONFIG_FILE, "w", encoding="UTF-8") as stream:
        yaml.dump(configuration, stream, default_flow_style=False)


def _move_slow_factor_to_db():
    """Convert the slow factor from the config to the database.

    Will use the slow flag and the config value to calculate the pump speed,
    others will be 100%.
    """
    if not CUSTOM_CONFIG_FILE.exists():
        slow_factor = 1.0
    else:
        configuration: dict[str, Any] = {}
        with open(CUSTOM_CONFIG_FILE, encoding="UTF-8") as stream:
            configuration = yaml.safe_load(stream)
        slow_factor = configuration.get("PUMP_SLOW_FACTOR", 1.0)
    change_slower_flag_to_pump_speed(slow_factor)


def _get_converted_value(new_type: type, default_value: Any, local_config: Any):
    try:
        new_value = new_type(local_config)
    except ValueError:
        new_value = default_value
    return new_value


class _Version:
    """Class to compare semantic version numbers."""

    def __init__(self, version_number: str | None) -> None:
        self.version = version_number
        # no version was found, just assume the worst, so using first version
        if version_number is None:
            major = 1
            minor = 0
            patch = 0
        # otherwise split version for later comparison
        else:
            major_str, minor_str, *patch_str = version_number.split(".")
            major = int(major_str)
            minor = int(minor_str)
            # Some version like 1.0 or 1.1 don't got a patch property
            # List unpacking will return an empty list or a list of one
            # Future version should contain patch (e.g. 1.1.0) as well
            patch = int(patch_str[0]) if patch_str else 0
        self.major = major
        self.minor = minor
        self.patch = patch

    def __gt__(self, __o: object) -> bool:
        return (self.major, self.minor, self.patch) > (__o.major, __o.minor, __o.patch)  # type: ignore

    def __eq__(self, __o: object) -> bool:
        return self.version == __o.version  # type: ignore

    def __str__(self) -> str:
        if self.version is None:
            return "No defined Version"
        return f"v{self.version}"

    def __repr__(self) -> str:
        if self.version is None:
            return "Version(not defined)"
        return f"Version({self.version})"


class CouldNotMigrateException(Exception):
    """Raised when there was an error with the migration."""

    def __init__(self, version):
        self.message = f"Error while migration to version: {version}"
        super().__init__(self.message)
