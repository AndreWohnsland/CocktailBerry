import threading
import time
from datetime import datetime

import psutil

from src.database_commander import DatabaseCommander
from src.logger_handler import LogFiles, LoggerHandler

_logger = LoggerHandler("resource_tracker", LogFiles.RESOURCES)


def save_resource_usage(cpu_usage: float, ram_usage: float, session: int, timestamp: datetime | None = None) -> None:
    DBC = DatabaseCommander()
    DBC.save_resource_usage(cpu_usage, ram_usage, session, timestamp)


def _resource_logger_thread(log_interval: int, session_number: int) -> None:
    _logger.log_header("INFO", "Starting resource tracker, will only log if RAM usage is above 90%")
    _logger.info("The whole data points will be saved in the Database and can be accessed via the GUI.")
    sense_interval = 5
    while True:
        cpu_usage = psutil.cpu_percent(interval=sense_interval)
        ram_usage = psutil.virtual_memory().percent
        save_resource_usage(cpu_usage, ram_usage, session_number)
        if ram_usage > 90:
            _logger.critical(f"Machine ressources are on the limit: CPU: {cpu_usage}%, RAM: {ram_usage}%")
        time.sleep(log_interval - sense_interval)


def start_resource_tracker() -> None:
    """Start a thread that tracks the system resources."""
    session_number = DatabaseCommander().get_highest_session_number() + 1
    log_thread = threading.Thread(target=_resource_logger_thread, args=(15, session_number), daemon=True)
    log_thread.start()
