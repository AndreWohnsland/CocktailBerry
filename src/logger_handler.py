import logging
from pathlib import Path
from typing import Literal, Union

_DIRPATH = Path(__file__).parent.absolute()
_AceptedLogLevels = Union[
    Literal["DEBUG"],
    Literal["INFO"],
    Literal["WARNING"],
    Literal["ERROR"],
    Literal["CRITICAL"]
]


class LoggerHandler:
    """Handler class for generating logger and logging events"""

    log_folder = _DIRPATH.parent / "logs"

    def __init__(self, loggername: str, filename: str = "production_logs"):
        self.loggername = loggername
        self.path = LoggerHandler.log_folder / f"{filename}.log"

        logger = logging.getLogger(loggername)
        logger.setLevel(logging.DEBUG)
        if not logger.hasHandlers():
            filehandler = logging.FileHandler(self.path)
            filehandler.setLevel(logging.DEBUG)
            formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s: %(message)s", "%Y-%m-%d %H:%M")
            filehandler.setFormatter(formatter)
            logger.addHandler(filehandler)

        self.logger = logging.getLogger(loggername)
        self.template = "{:-^80}"

    def log_event(self, level: _AceptedLogLevels, message: str):
        """Simply logs a message of given level"""
        self.logger.log(getattr(logging, level), message)

    def log_header(self, level: _AceptedLogLevels, message: str):
        """Logs a message of given level formated as header"""
        self.log_event(level, self.template.format(f" {message} ",))

    def log_start_program(self, program_type: str = "maker"):
        """Logs the start of the program, optionally can define program type"""
        self.log_header("INFO", f"Starting the {program_type} program")

    def log_exception(self, message: Union[str, object]):
        """Logs an exception with the given message"""
        self.logger.exception(message)
