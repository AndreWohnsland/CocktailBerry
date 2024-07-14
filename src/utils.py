import atexit
import datetime
import http.client as httplib
import os
import platform
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from typing import Literal

import psutil

from src.filepath import CUSTOM_STYLE_FILE, CUSTOM_STYLE_SCSS, ROOT_PATH, STYLE_FOLDER
from src.logger_handler import LogFiles, LoggerHandler

EXECUTABLE = ROOT_PATH / "runme.py"
_logger = LoggerHandler("utils")


def has_connection() -> bool:
    """Check if can connect to internet (google) and returns success."""
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
    platform: str  # eg. Windows-10-...
    machine: str  # eg. AMD64
    architecture: tuple[str, str]  # eg. ('64bit', 'WindowsPE')
    system: Literal["Linux", "Darwin", "Java", "Windows", ""]
    release: str  # eg. 10

    def __str__(self) -> str:
        return f"Running on {self.system}, {self.architecture[0]} rel. {self.release}, machine: {self.machine} ({self.platform})"  # noqa


def get_platform_data() -> PlatformData:
    """Return the specified platform data."""
    return PlatformData(
        platform.platform(),
        platform.machine(),
        platform.architecture(),
        platform.system(),  # type: ignore
        platform.release(),
    )


def set_system_time(time_string: str):
    """Set the system time to the given time, uses YYYY-MM-DD HH:MM:SS as format."""
    p_data = get_platform_data()
    # checking system, currently only setting on Linux (RPi), bc. its only one supported
    supported_os = ["Linux"]
    _logger.log_event("INFO", f"Setting time to: {time_string}")
    if p_data.system in supported_os:
        # need first disable timesyncd, otherwise you cannot set time
        time_commands = [
            "sudo systemctl stop systemd-timesyncd",
            f"sudo timedatectl set-time '{time_string}'",
            "sudo systemctl start systemd-timesyncd",
        ]
        try:
            # Use subprocess.run to capture the command's output and error
            for time_command in time_commands:
                subprocess.run(time_command, shell=True, check=True, capture_output=True, text=True)
            _logger.log_event("INFO", "Time set successfully")

        except subprocess.CalledProcessError as err:
            # Log any exceptions that occurred during command execution
            err_msg = err.stderr.replace("\n", " ")
            _logger.log_event("ERROR", f"Could not set time, error: {err_msg}")
            _logger.log_exception(err)
    else:
        _logger.log_event(
            "WARNING", f"Could not set time, your OS is: {p_data.system}. Currently supported OS are: {supported_os}"
        )


def restart_program():
    """Restart the CocktailBerry application."""
    # trigger manually, since exec function will not trigger exit fun.
    atexit._run_exitfuncs()  # pylint: disable=protected-access
    python = sys.executable
    os.execl(python, python, EXECUTABLE, *sys.argv[1:])


def generate_custom_style_file():
    """Generate the custom style file, if it does not exist."""
    default_style_file = STYLE_FOLDER / "default.scss"
    compiled_default = STYLE_FOLDER / "default.css"
    if not CUSTOM_STYLE_SCSS.exists():
        CUSTOM_STYLE_SCSS.write_text(default_style_file.read_text())
        CUSTOM_STYLE_FILE.write_text(compiled_default.read_text())


def time_print(msg: str, **kwargs):
    """Print the given string with a timestamp in the 'HH:MM:SS: ' prefix."""
    now = datetime.datetime.now()
    print(f"{now.strftime('%H:%M:%S')}:  {msg}", **kwargs)


def _resource_logger_thread(log_interval: int):
    # create an own logger + file for the resource tracker
    resource_logger = LoggerHandler("resource_tracker", LogFiles.RESOURCES)
    resource_logger.log_header("INFO", "Starting resource tracker")
    resource_logger.log_event("INFO", "CPU usage, RAM usage")
    sense_interval = 5
    while True:
        cpu_usage = psutil.cpu_percent(interval=sense_interval)
        ram_usage = psutil.virtual_memory().percent
        log_entry = f"{cpu_usage}%, {ram_usage}%"
        log_level = "INFO"
        if ram_usage > 80:
            log_level = "WARNING"
        elif ram_usage > 90:
            log_level = "CRITICAL"
        resource_logger.log_event(log_level, log_entry)
        time.sleep(log_interval - sense_interval)


def start_resource_tracker():
    """Start a thread that tracks the system resources."""
    log_thread = threading.Thread(target=_resource_logger_thread, args=(15,), daemon=True)
    log_thread.start()
