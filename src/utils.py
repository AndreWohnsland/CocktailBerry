import platform
import os
import sys
from pathlib import Path
from typing import Tuple, Literal
from dataclasses import dataclass
import http.client as httplib

from src.logger_handler import LoggerHandler


FILE_PATH = Path(__file__).parents[0].absolute()
EXECUTABLE = FILE_PATH.parents[0].absolute() / "runme.py"
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
        platform.system(),  # type: ignore | this usually only gives the literals specified
        platform.release(),
    )


def set_system_time(time_string: str):
    """Sets the system time to the given time, uses YYYY-MM-DD HH:MM:SS as format"""
    p_data = get_platform_data()
    # checking system, currently only setting on Linux (RPi), bc. its only one supported
    supported_os = ["Linux"]
    _logger.log_event("INFO", f"Setting time to: {time_string}")
    if p_data.system == "Linux":
        time_command = f"timedatectl set-time {time_string}"
        os.system(time_command)
    else:
        _logger.log_event(
            "WARNING",
            f"Could not set time, your OS is: {p_data.system} currently supported OS are: {supported_os}"
        )


def restart_program():
    os.execl(sys.executable, "python", EXECUTABLE, *sys.argv[1:])
