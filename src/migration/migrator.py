# pylint: disable=wrong-import-order,wrong-import-position,disable=too-few-public-methods
from src.python_vcheck import check_python_version
# Version check takes place before anything, else other imports may throw an error
check_python_version()

import configparser
import sys
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from src.logger_handler import LoggerHandler, LogFiles
from src.migration.updata_data import (
    rename_database_to_english,
    add_more_bottles_to_db,
    add_team_buffer_to_database,
    add_virgin_flag_to_db,
    remove_is_alcoholic_column
)
from src import __version__, FUTURE_PYTHON_VERSION

_DIRPATH = Path(__file__).parent.absolute()
_CONFIG_PATH = _DIRPATH.parents[1] / ".version.ini"
_logger = LoggerHandler("migrator_module", LogFiles.PRODUCTION)


class Migrator:
    """Class to do all neccecary migration locally for new versions"""

    def __init__(self) -> None:
        self.program_version = _Version(__version__)
        self.config = configparser.ConfigParser()
        self.config.read(_CONFIG_PATH)
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

    def _write_local_version(self):
        """Writes the latest version to the local version"""
        _logger.log_event("INFO", f"Local data migrated from {self.local_version} to {self.program_version}")
        self.config['DEFAULT']['LOCALVERSION'] = str(self.program_version.version)
        with open(_CONFIG_PATH, 'w', encoding="utf-8") as configfile:
            self.config.write(configfile)

    def make_migrations(self):
        """Make migration dependant on current local and program version"""
        _logger.log_event("INFO", f"Local version is: {self.local_version}, checking for necessary migrations")
        self._python_to_old_warning(FUTURE_PYTHON_VERSION)
        if self.older_than_version("1.5.0"):
            _logger.log_event("INFO", "Making migrations for v1.5.0")
            rename_database_to_english()
            add_team_buffer_to_database()
            self._install_pip_package("GitPython", "1.5.0")
        if self.older_than_version("1.5.3"):
            _logger.log_event("INFO", "Making migrations for v1.5.3")
            self._install_pip_package("typer", "1.5.3")
        if self.older_than_version("1.6.0"):
            _logger.log_event("INFO", "Making migrations for v1.6.0")
            self._change_git_repo()
            self._install_pip_package("pyfiglet", "1.6.0")
        if self.older_than_version("1.6.1"):
            _logger.log_event("INFO", "Making migrations for v1.6.1")
            add_more_bottles_to_db()
        if self.older_than_version("1.9.0"):
            _logger.log_event("INFO", "Making migrations for v1.9.0")
            add_virgin_flag_to_db()
            remove_is_alcoholic_column()
            self._install_pip_package("typing_extensions", "1.9.0")
        if self.older_than_version("1.11.0"):
            _logger.log_event("INFO", "Making migrations for v1.11.0")
            self._install_pip_package("qtawesome", "1.11.0")
        self._check_local_version_data()

    def _python_to_old_warning(self, least_python: Tuple[int, int]):
        if sys.version_info < least_python:
            pv_format = f"Python {least_python[0]}.{least_python[1]}"
            release_version_notes = f"v{self.program_version.major}.{self.program_version.minor}"
            _logger.log_event("WARNING", f"Your used Python is deprecated, please upgrade to {pv_format} or higher")
            _logger.log_event("WARNING", f"Please read the release notes {release_version_notes} for more information")

    def _check_local_version_data(self):
        """Checks to update the local version data"""
        if self.older_than_version(self.program_version.version):
            self._write_local_version()
        else:
            _logger.log_event("INFO", "Nothing to migrate")

    def _change_git_repo(self):
        """Sets the git source to the new named repo"""
        _logger.log_event("INFO", "Changing git origin to new repo name")
        try:
            subprocess.check_call(["git", "remote", "set-url", "origin",
                                   "https://github.com/AndreWohnsland/CocktailBerry.git"])
        except subprocess.CalledProcessError as err:
            _logger.log_event(
                "ERROR", "Could not change origin. Check if you made any local file changes / use 'git restore .'!")
            _logger.log_exception(err)
            raise CouldNotMigrateException("1.6.0") from err

    def _install_pip_package(self, packagename: str, version_to_migrate: str):
        """Try to install a python package over pip"""
        _logger.log_event("INFO", f"Trying to install {packagename}, it is needed since this version")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', packagename])
            _logger.log_event("INFO", f"Successfully installed {packagename}")
        except subprocess.CalledProcessError as err:
            _logger.log_event("ERROR", f"Could not install {packagename} using pip. Please install it manually!")
            _logger.log_exception(err)
            raise CouldNotMigrateException(version_to_migrate) from err


class _Version:
    """Class to compare semantic version numbers"""

    def __init__(self, version_number: Optional[str]) -> None:
        self.version = version_number
        # no verison was found, just asume the worst, so using first version
        if version_number is None:
            major = 1
            minor = 0
            patch = 0
        # otherwise split version for later comparison
        else:
            major, minor, *patch = version_number.split(".")
        self.major = int(major)
        self.minor = int(minor)
        # Some version like 1.0 or 1.1 dont got a patch property
        # List unpacking will return an empty list or a list of one
        # Future version should contain patch (e.g. 1.1.0) as well
        if patch:
            self.patch = int(patch[0])
        else:
            self.patch = 0

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
