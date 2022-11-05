import logging
from pathlib import Path
from typing import Union

# Grace period, will be switched once Python 3.8+ is mandatory
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

_DIRPATH = Path(__file__).parent.absolute()
_AceptedLogLevels = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class LogFiles():
    PRODUCTION = "production_logs"
    SERVICE = "service_logs"
    DEBUG = "debuglog"


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
