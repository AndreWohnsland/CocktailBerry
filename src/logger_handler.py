import logging
from pathlib import Path
from typing import Union, Literal


_DIRPATH = Path(__file__).parent.absolute()
_AcceptedLogLevels = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class LogFiles():
    PRODUCTION = "production_logs"
    SERVICE = "service_logs"
    DEBUG = "debuglog"


class LoggerHandler:
    """Handler class for generating logger and logging events"""

    log_folder = _DIRPATH.parent / "logs"

    def __init__(self, logger_name: str, filename: str = LogFiles.PRODUCTION):
        self.logger_name = logger_name
        self.path = LoggerHandler.log_folder / f"{filename}.log"

        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        if not logger.hasHandlers():
            file_handler = logging.FileHandler(self.path)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s: %(message)s", "%Y-%m-%d %H:%M")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        self.logger = logging.getLogger(logger_name)
        self.template = "{:-^80}"

    def log_event(self, level: _AcceptedLogLevels, message: str):
        """Simply logs a message of given level"""
        self.logger.log(getattr(logging, level), message)

    def log_header(self, level: _AcceptedLogLevels, message: str):
        """Logs a message of given level formatted as header"""
        self.log_event(level, self.template.format(f" {message} ",))

    def log_start_program(self, program_type: str = "maker"):
        """Logs the start of the program, optionally can define program type"""
        self.log_header("INFO", f"Starting the {program_type} program")

    def log_exception(self, message: Union[str, object]):
        """Logs an exception with the given message"""
        self.logger.exception(message)
