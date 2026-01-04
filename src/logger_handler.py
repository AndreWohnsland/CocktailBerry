import logging
import os
import sys
from typing import Literal

from src.filepath import LOG_FOLDER

_AcceptedLogLevels = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class LogFiles:
    PRODUCTION = "production_logs"
    SERVICE = "service_logs"
    DEBUG = "debuglog"
    RESOURCES = "resource_usage"


class LoggerHandler:
    """Handler class for generating logger and logging events."""

    log_folder = LOG_FOLDER

    def __init__(self, logger_name: str, filename: str = LogFiles.PRODUCTION) -> None:
        self.logger_name = logger_name
        self.path = LoggerHandler.log_folder / f"{filename}.log"

        requested_log_level = os.getenv("COCKTAILBERRY_LOG_LEVEL", "INFO").upper()
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        used_log_level = level_map.get(requested_log_level, logging.INFO)
        logger = logging.getLogger(logger_name)
        logger.setLevel(used_log_level)
        if not logger.hasHandlers():
            # Add file handler
            file_handler = logging.FileHandler(self.path)
            file_handler.setLevel(used_log_level)
            formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s [%(name)s]", "%Y-%m-%d %H:%M:%S")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            # Add console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(used_log_level)
            console_formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", "%H:%M:%S")
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        self.logger = logging.getLogger(logger_name)
        self.template = "{:-^80}"

        # build internal debug logger if its not the debug logger itself
        # this is used to not log the exception in to the debug log
        # the exception got another format and must be parsed differently
        self._debug_logger = None
        if filename != LogFiles.DEBUG:
            self._debug_logger = LoggerHandler(f"{logger_name}_debug", LogFiles.DEBUG)

    def log_event(self, level: _AcceptedLogLevels, message: str) -> None:
        """Simply logs a message of given level."""
        self.logger.log(getattr(logging, level), message)

    def log_header(self, level: _AcceptedLogLevels, message: str) -> None:
        """Log a message of given level formatted as header."""
        self.log_event(
            level,
            self.template.format(
                f" {message} ",
            ),
        )

    def log_start_program(self, program_type: str = "maker") -> None:
        """Log the start of the program, optionally can define program type."""
        self.log_header("INFO", f"Starting the {program_type} program")

    def log_exception(self, message: str | object) -> None:
        """Log an exception with the given message."""
        if self._debug_logger is None:
            self.logger.exception(message)
        else:
            self._debug_logger.log_exception(message)

    def debug(self, message: object, *args: object, **kwargs: object) -> None:
        """Log the message under the debug level."""
        self.logger.debug(message, *args, **kwargs)  # type: ignore

    def info(self, message: object, *args: object, **kwargs: object) -> None:
        """Log the message under the info level."""
        self.logger.info(message, *args, **kwargs)  # type: ignore

    def warning(self, message: object, *args: object, **kwargs: object) -> None:
        """Log the message under the warning level."""
        self.logger.warning(message, *args, **kwargs)  # type: ignore

    def error(self, message: object, *args: object, **kwargs: object) -> None:
        """Log the message under the error level."""
        self.logger.error(message, *args, **kwargs)  # type: ignore

    def critical(self, message: object, *args: object, **kwargs: object) -> None:
        """Log the message under the critical level."""
        self.logger.critical(message, *args, **kwargs)  # type: ignore
