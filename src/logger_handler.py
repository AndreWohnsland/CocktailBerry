import logging
from pathlib import Path

DIRPATH = Path(__file__).parent.absolute()


class LoggerHandler:
    """Handler class for generating logger and logging events"""

    log_folder = DIRPATH.parent / "logs"

    def __init__(self, loggername: str, filename: str):
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

    def log_event(self, level, message: str):
        """Simply logs a message of given level"""
        self.logger.log(getattr(logging, level), message)

    def log_header(self, level, message: str):
        """Logs a message of given level formated as header"""
        self.log_event(level, self.template.format(f" {message} ",))

    def log_start_program(self):
        """Logs the start of the program"""
        self.log_header("INFO", "Starting the program")

    def log_exception(self, message: str):
        """Logs an exception with the given message"""
        self.logger.exception(message)
