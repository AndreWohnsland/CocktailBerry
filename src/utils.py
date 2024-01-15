import platform
import os
import subprocess
import sys
from typing import Tuple, Literal
from dataclasses import dataclass
import http.client as httplib
import atexit
import datetime

from src.filepath import ROOT_PATH, STYLE_FOLDER, CUSTOM_STYLE_FILE, CUSTOM_STYLE_SCSS
from src.logger_handler import LoggerHandler


EXECUTABLE = ROOT_PATH / "runme.py"
_logger = LoggerHandler("utils")


def has_connection() -> bool:
    """Checks if can connect to internet (google) and returns success"""
    conn = httplib.HTTPSConnection("8.8.8.8", timeout=3)
    try:
        conn.request("HEAD", "/")
        got_con = True
    # Will throw OSError on no connection
    except OSError:
        got_con = False
    finally:
        conn.close()
    return got_con


@dataclass
class PlatformData:
    platform: str   # eg. Windows-10-...
    machine: str    # eg. AMD64
    architecture: Tuple[str, str]   # eg. ('64bit', 'WindowsPE')
    system: Literal["Linux", "Darwin", "Java", "Windows", ""]
    release: str  # eg. 10

    def __str__(self) -> str:
        return f"Running on {self.system}, {self.architecture[0]} rel. {self.release}, machine: {self.machine} ({self.platform})"  # noqa


def get_platform_data() -> PlatformData:
    """Returns the specified platform data"""
    return PlatformData(
        platform.platform(),
        platform.machine(),
        platform.architecture(),
        platform.system(),  # type: ignore
        platform.release(),
    )


def set_system_time(time_string: str):
    """Sets the system time to the given time, uses YYYY-MM-DD HH:MM:SS as format"""
    p_data = get_platform_data()
    # checking system, currently only setting on Linux (RPi), bc. its only one supported
    supported_os = ["Linux"]
    _logger.log_event("INFO", f"Setting time to: {time_string}")
    if p_data.system in supported_os:
        time_command = f"sudo timedatectl set-time '{time_string}'"
        try:
            # Use subprocess.run to capture the command's output and error
            subprocess.run(
                time_command, shell=True, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True
            )
            _logger.log_event("INFO", "Time set successfully")

        except subprocess.CalledProcessError as e:
            # Log any exceptions that occurred during command execution
            err_msg = e.stderr.replace("\n", " ")
            _logger.log_event("ERROR", f"Could not set time, error: {err_msg}")
            _logger.log_exception(e)
    else:
        _logger.log_event(
            "WARNING",
            f"Could not set time, your OS is: {p_data.system}. Currently supported OS are: {supported_os}"
        )


def restart_program():
    """Restart the CocktailBerry application"""
    # trigger manually, since exec function will not trigger exit fun.
    atexit._run_exitfuncs()  # pylint: disable=protected-access
    python = sys.executable
    os.execl(python, python, EXECUTABLE, *sys.argv[1:])


def generate_custom_style_file():
    """Generates the custom style file, if it does not exist"""
    default_style_file = STYLE_FOLDER / "default.scss"
    compiled_default = STYLE_FOLDER / "default.css"
    if not CUSTOM_STYLE_SCSS.exists():
        CUSTOM_STYLE_SCSS.write_text(default_style_file.read_text())
        CUSTOM_STYLE_FILE.write_text(compiled_default.read_text())


def time_print(msg: str, **kwargs):
    """Prints the given string with a timestamp in the 'HH:MM:SS: ' prefix"""
    now = datetime.datetime.now()
    print(f"{now.strftime('%H:%M:%S')}:  {msg}", **kwargs)
