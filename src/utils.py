import atexit
import datetime
import http.client as httplib
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
from collections import Counter
from dataclasses import dataclass
from typing import Literal

import distro
import psutil

from src.filepath import CUSTOM_STYLE_FILE, CUSTOM_STYLE_SCSS, LOG_FOLDER, ROOT_PATH, STYLE_FOLDER
from src.logger_handler import LogFiles, LoggerHandler

EXECUTABLE = ROOT_PATH / "runme.py"
logger = LoggerHandler("utils")
_DEBUG_FILE = "debuglog.log"


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


def set_system_datetime(datetime_string: str):
    """Set the system time to the given time, uses YYYY-MM-DD HH:MM:SS as format."""
    p_data = get_platform_data()
    # checking system, currently only setting on Linux (RPi), bc. its only one supported
    supported_os = ["Linux"]
    logger.log_event("INFO", f"Setting time to: {datetime_string}")
    if p_data.system not in supported_os:
        logger.log_event(
            "WARNING", f"Could not set time, your OS is: {p_data.system}. Currently supported OS are: {supported_os}"
        )
        return
    # need first disable timesyncd, otherwise you cannot set time
    time_commands = [
        "sudo systemctl stop systemd-timesyncd",
        f"sudo timedatectl set-time '{datetime_string}'",
        "sudo systemctl start systemd-timesyncd",
    ]
    try:
        # Use subprocess.run to capture the command's output and error
        for time_command in time_commands:
            subprocess.run(time_command, shell=True, check=True, capture_output=True, text=True)
        logger.log_event("INFO", "Time set successfully")

    except subprocess.CalledProcessError as err:
        # Log any exceptions that occurred during command execution
        err_msg = err.stderr.replace("\n", " ")
        logger.log_event("ERROR", f"Could not set time, error: {err_msg}")
        logger.log_exception(err)


def restart_program():
    """Restart the CocktailBerry application."""
    arguments = sys.argv[1:]
    # skip out if this is the dev program (will not work restart here)
    # This is because we run it with fastapi dev instead the python runme.py ...
    if len(arguments) != 0 and arguments[0] == "dev":
        time_print("Will not restart because of dev program.")
        return
    # trigger manually, since exec function will not trigger exit fun.
    atexit._run_exitfuncs()  # pylint: disable=protected-access
    # either run with uv or python (old setup)
    uv_executable = shutil.which("uv")
    python = sys.executable
    if uv_executable is not None:
        os.execl(uv_executable, "uv", "run", EXECUTABLE, *arguments)
    else:
        os.execl(python, "python", EXECUTABLE, *arguments)


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
        log_level: Literal["INFO", "WARNING", "CRITICAL"] = "INFO"
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


def update_os():
    distribution = distro.id().lower()

    if distribution in ["raspbian", "debian", "ubuntu"]:
        command = (
            "sudo DEBIAN_FRONTEND=noninteractive apt-get update && "
            "sudo DEBIAN_FRONTEND=noninteractive apt-get -y "
            '-o Dpkg::Options::="--force-confdef" '
            '-o Dpkg::Options::="--force-confold" full-upgrade'
        )
    elif distribution in ["fedora", "centos", "rhel"]:
        if subprocess.call(["command", "-v", "dnf"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0:
            command = "sudo dnf -y update"
        else:
            command = "sudo yum -y update"
    elif distribution in ["opensuse"]:
        command = "sudo zypper -n update"
    elif distribution in ["arch"]:
        command = "sudo pacman -Syu --noconfirm"
    else:
        logger.error(f"Unsupported Linux distribution: {distribution}")
        return

    try:
        subprocess.run(command, shell=True, check=True)
        logger.info("System updated successfully.")
    except subprocess.CalledProcessError as e:
        logger.error("Could not update system, see debug log for more information.")
        logger.log_exception(e)


def get_log_files() -> list[str]:
    """Check the logs folder for all existing log files."""
    return [file.name for file in LOG_FOLDER.glob("*.log")]


def read_log_file(log_name: str, warning_and_higher: bool) -> list[str]:
    """Read the current selected log file."""
    log_path = LOG_FOLDER / log_name
    log_text = log_path.read_text()
    # Handle debug logs differently, since they save error traces,
    # just display the read in text from log in this case
    if log_name == _DEBUG_FILE:
        return _parse_debug_logs(log_text)
    return _parse_log(log_text, warning_and_higher)


def _parse_log(log_text: str, warning_and_higher: bool) -> list[str]:
    """Parse all logs and return display object.

    Needs logs from new to old, if same message was already there, skip it.
    """
    data: dict[str, str] = {}
    counter: Counter[str] = Counter()
    for line in log_text.splitlines()[::-1]:
        date, message = _parse_log_line(line)
        if message not in data:
            data[message] = date
            counter[message] = 1
        else:
            counter[message] += 1
    log_list_data = [f"{key} ({counter[key]}x, latest: {value})" for key, value in data.items()]
    # Filter out DEBUG or INFO msgs
    if warning_and_higher:
        accepted = ["WARNING", "ERROR", "CRITICAL"]
        log_list_data = [x for x in log_list_data if any(a in x for a in accepted)]
    return log_list_data


def _parse_log_line(line: str) -> tuple[str, str]:
    """Parse the log message and return the timestamp + msg."""
    parts = line.split(" | ", maxsplit=1)
    parsed_date = parts[0]
    # usually, we only get 2 parts, due to the maxsplit
    parsed_message = " | ".join(parts[1::])
    return parsed_date, parsed_message


def _parse_debug_logs(log: str) -> list[str]:
    """Parse and invert the debug logs."""
    # having into group returns also the matched date
    # This needs to be joined before inverting.
    # Also, the first value is an empty string
    date_regex = r"(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2})"
    information_list = [x for x in re.split(date_regex, log) if x != ""]
    pairs = [" ".join(information_list[i : i + 2]) for i in range(0, len(information_list), 2)]
    return pairs[::-1]


def setup_wifi(ssid: str, password: str) -> bool:
    """Configure a WiFi network with the given SSID and password."""
    try:
        subprocess.run(["nmcli", "dev", "wifi", "connect", ssid, "password", password], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to connect to WiFi network: {ssid}: {e}")
        logger.log_exception(e)
        return False


def list_available_ssids() -> list[str]:
    """List all available WiFi networks."""
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "SSID", "dev", "wifi"], stdout=subprocess.PIPE, text=True, check=True
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"Failed to list available WiFi networks: {e}")
        logger.log_exception(e)
        return []


def create_ap(ssid: str = "CocktailBerry", password: str = "cocktailconnect"):
    commands = [
        "sudo iw dev wlan0 interface add wlan1 type __ap",
        f"sudo nmcli connection add type wifi ifname wlan1 con-name {ssid} ssid {ssid}",
        f"sudo nmcli connection modify {ssid} 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared",
        f'sudo nmcli connection modify {ssid} wifi-sec.key-mgmt wpa-psk wifi-sec.psk "{password}"',
        f"sudo nmcli con up id {ssid}",
    ]
    delete_ap(ssid)
    for command in commands:
        subprocess.run(command, shell=True, check=True)


def delete_ap(ssid: str = "CocktailBerry"):
    subprocess.run("sudo iw dev wlan1 del", shell=True, check=False)
    subprocess.run(f"sudo nmcli connection delete {ssid}", shell=True, check=False)
