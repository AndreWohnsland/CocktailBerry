import os
import logging
from pathlib import Path

dirpath = os.path.dirname(__file__)


class LoggerHandler:
    """Handler Class for Generating Logger and Logging events"""

    log_folder = os.path.join(dirpath, "..", "logs")

    def __init__(self, loggername, filename):
        self.loggername = loggername
        self.path = os.path.join(LoggerHandler.log_folder, f"{filename}.log")

        logger = logging.getLogger(loggername)
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(self.path)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s: %(message)s", "%Y-%m-%d %H:%M")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        self.logger = logging.getLogger(loggername)
        self.TEMPLATE = "{:-^80}"

    def log_event(self, level, message):
        self.logger.log(getattr(logging, level), message)

    def log_header(self, level, message):
        self.log_event(level, self.TEMPLATE.format(message,))

    def log_start_program(self):
        self.logger.info(self.TEMPLATE.format("Starting the Programm",))
