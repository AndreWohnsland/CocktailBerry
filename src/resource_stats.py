from __future__ import annotations

import threading
import time

import psutil

from src.database_commander import DatabaseCommander
from src.logger_handler import LogFiles, LoggerHandler

_logger = LoggerHandler("resource_tracker", LogFiles.RESOURCES)


def _resource_logger_thread(log_interval: int, session_number: int) -> None:
    _logger.log_header("INFO", f"Starting resource tracker, session number: {session_number}")
    _logger.info("The data will be saved in the database and can be accessed via the GUI")
    sense_interval = 5
    critical_usage = 90
    DBC = DatabaseCommander()
    while True:
        cpu_usage = psutil.cpu_percent(interval=sense_interval)
        ram_usage = psutil.virtual_memory().percent
        DBC.save_resource_usage(cpu_usage, ram_usage, session_number)
        if ram_usage > critical_usage:
            _logger.critical(f"Machine ressources are on the limit: CPU: {cpu_usage}%, RAM: {ram_usage}%")
        time.sleep(log_interval - sense_interval)


def start_resource_tracker() -> None:
    """Clean up the stored resource data, then start a thread that tracks the system resources.

    The cleanup runs before the tracker and before anything else in the app touches the database:
    the vacuum locks the whole file, so the boot stalls here instead of failing a query elsewhere.
    """
    dbc = DatabaseCommander()
    dbc.cleanup_resource_stats()
    deleted = dbc.compact_resource_stats()
    _logger.info(f"Compacted the stored resource data, removed {deleted} data points")
    try:
        dbc.vacuum_if_fragmented()
    # a full disk must not keep the app from starting
    except Exception as err:
        _logger.error("Could not rebuild the database, it stays at its current size")
        _logger.log_exception(err)
    session_number = dbc.get_highest_session_number() + 1
    log_thread = threading.Thread(target=_resource_logger_thread, args=(30, session_number), daemon=True)
    log_thread.start()
