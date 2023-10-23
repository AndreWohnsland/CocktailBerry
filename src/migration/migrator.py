# pylint: disable=wrong-import-order,wrong-import-position,too-few-public-methods,ungrouped-imports
import platform

import yaml
from src.python_vcheck import check_python_version
# Version check takes place before anything, else other imports may throw an error
check_python_version()

import configparser
import sys
import subprocess
from typing import Any, Optional, Tuple
import importlib.util

from src.filepath import CUSTOM_CONFIG_FILE, VERSION_FILE, CUSTOM_STYLE_FILE, CUSTOM_STYLE_SCSS
from src import __version__, FUTURE_PYTHON_VERSION
from src.logger_handler import LoggerHandler
from src.migration.update_data import (
    rename_database_to_english,
    add_more_bottles_to_db,
    add_team_buffer_to_database,
    add_virgin_flag_to_db,
    remove_is_alcoholic_column,
    remove_old_recipe_columns,
    add_slower_ingredient_flag_to_db,
)

_logger = LoggerHandler("migrator_module")


class Migrator:
    """Class to do all necessary migration locally for new versions"""

    def __init__(self) -> None:
        self.program_version = _Version(__version__)
        self.config = configparser.ConfigParser()
        self.config.read(VERSION_FILE)
        self.local_version = _Version(self._get_local_version())

    def _get_local_version(self):
        try:
            local_version = self.config['DEFAULT']['LOCALVERSION']
        except KeyError:
            local_version = None
        return local_version

    def older_than_version(self, version: Optional[str]) -> bool:
        """Checks if the current version is below the given version"""
        return _Version(version) > self.local_version

    def older_than_version_with_logging(self, version: str) -> bool:
        """Checks if the current version is below the given version"""
        is_older = _Version(version) > self.local_version
        if is_older:
            self._migration_log(version)
        return is_older

    def _write_local_version(self):
        """Writes the latest version to the local version"""
        _logger.log_event("INFO", f"Local data migrated from {self.local_version} to {self.program_version}")
        self.config['DEFAULT']['LOCALVERSION'] = str(self.program_version.version)
        with open(VERSION_FILE, 'w', encoding="utf-8") as config_file:
            self.config.write(config_file)

    def make_migrations(self):
        """Make migration dependant on current local and program version"""
        _logger.log_event("INFO", f"Local version is: {self.local_version}, checking for necessary migrations")
        self._python_to_old_warning(FUTURE_PYTHON_VERSION)
        if self.older_than_version_with_logging("1.5.0"):
            rename_database_to_english()
            add_team_buffer_to_database()
            self._install_pip_package("GitPython", "1.5.0")
        if self.older_than_version_with_logging("1.5.3"):
            self._install_pip_package("typer", "1.5.3")
        if self.older_than_version_with_logging("1.6.0"):
            self._change_git_repo()
            self._install_pip_package("pyfiglet", "1.6.0")
        if self.older_than_version_with_logging("1.6.1"):
            add_more_bottles_to_db()
        if self.older_than_version_with_logging("1.9.0"):
            add_virgin_flag_to_db()
            remove_is_alcoholic_column()
            self._install_pip_package("typing_extensions", "1.9.0")
        if self.older_than_version_with_logging("1.11.0"):
            self._install_pip_package("qtawesome", "1.11.0")
        if self.older_than_version_with_logging("1.17.0"):
            self._install_pip_package("pyqtspinner", "1.17.0")
        if self.older_than_version_with_logging("1.18.0"):
            remove_old_recipe_columns()
        if self.older_than_version_with_logging("1.19.3"):
            _update_config_value_type("UI_MASTERPASSWORD", int, 0)
        if self.older_than_version_with_logging("1.22.0"):
            add_slower_ingredient_flag_to_db()
        if self.older_than_version_with_logging("1.23.1"):
            _update_config_value_type("PUMP_SLOW_FACTOR", float, 1.0)
        if self.older_than_version_with_logging("1.26.1"):
            _update_config_value_type("PUMP_VOLUMEFLOW", float, 1.0)
        self._check_local_version_data()

    def _migration_log(self, version: str):
        """Logs the migration message fro the version"""
        _logger.log_event("INFO", f"Making migrations for v{version}")

    def _python_to_old_warning(self, least_python: Tuple[int, int]):
        """Logs a warning that the future python is higher than system python"""
        sys_python = sys.version_info
        if sys_python < least_python:
            future_format = f"Python {least_python[0]}.{least_python[1]}"
            sys_format = f"{platform.python_version()}"
            _logger.log_event(
                "WARNING",
                f"Your used Python ({sys_format}) is deprecated, please upgrade to {future_format} or higher"
            )

    def _check_local_version_data(self):
        """Checks to update the local version data"""
        if self.older_than_version(self.program_version.version):
            self._update_custom_theme()
            self._write_local_version()
        else:
            _logger.log_event("INFO", "Nothing to migrate")

    def _update_custom_theme(self):
        """Checks and updates (compiles) the custom theme"""
        # skip if library is not installed, or file does not exist
        lib_not_installed = importlib.util.find_spec("qtsass") is None
        no_file = not CUSTOM_STYLE_SCSS.exists()
        if lib_not_installed or no_file:
            return
        import qtsass  # pylint:disable=import-outside-toplevel
        qtsass.compile_filename(CUSTOM_STYLE_SCSS, CUSTOM_STYLE_FILE)

    def _change_git_repo(self):
        """Sets the git source to the new named repo"""
        _logger.log_event("INFO", "Changing git origin to new repo name")
        try:
            subprocess.check_call([
                "git", "remote", "set-url", "origin",
                "https://github.com/AndreWohnsland/CocktailBerry.git"
            ])
        except subprocess.CalledProcessError as err:
            _logger.log_event(
                "ERROR", "Could not change origin. Check if you made any local file changes / use 'git restore .'!")
            _logger.log_exception(err)
            raise CouldNotMigrateException("1.6.0") from err

    def _install_pip_package(self, package_name: str, version_to_migrate: str):
        """Try to install a python package over pip"""
        _logger.log_event("INFO", f"Trying to install {package_name}, it is needed since v{version_to_migrate}")
        if importlib.util.find_spec(package_name) is not None:
            _logger.log_event("INFO", f"Package {package_name} is already installed, skipping installation.")
            return
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])
            _logger.log_event("INFO", f"Successfully installed {package_name}")
        except subprocess.CalledProcessError as err:
            _logger.log_event("ERROR", f"Could not install {package_name} using pip. Please install it manually!")
            _logger.log_exception(err)
            raise CouldNotMigrateException(version_to_migrate) from err


def _update_config_value_type(config_name: str, new_type: type, default_value: Any):
    """Updates the local config file, use the new given type
    Uses the default if fails to convert.
    Also, if the given type is a list, it will try to convert the list elements
    """
    if not CUSTOM_CONFIG_FILE.exists():
        return
    _logger.info(f"Converting config value for {config_name} to {new_type}")
    configuration: dict[str, Any] = {}
    with open(CUSTOM_CONFIG_FILE, "r", encoding="UTF-8") as stream:
        configuration = yaml.safe_load(stream)
    # get the password from the config, if not exists fall back to default
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
    with open(CUSTOM_CONFIG_FILE, 'w', encoding="UTF-8") as stream:
        yaml.dump(configuration, stream, default_flow_style=False)


def _get_converted_value(new_type: type, default_value: Any, local_config: Any):
    try:
        new_value = new_type(local_config)
    except ValueError:
        new_value = default_value
    return new_value


class _Version:
    """Class to compare semantic version numbers"""

    def __init__(self, version_number: Optional[str]) -> None:
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
            if patch_str:
                patch = int(patch_str[0])
            else:
                patch = 0
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
    """Raised when there was an error with the migration"""

    def __init__(self, version):
        self.message = f"Error while migration to version: {version}"
        super().__init__(self.message)
