import os
import logging
from pathlib import Path

dirpath = os.path.dirname(__file__)


class LoggerHandler:
    """Handler Class for Generating Logger and Logging events"""

    log_folder = os.path.join(dirpath, "..", "logs")

    def __init__(self, loggername, filename):
        self.path = os.path.join(LoggerHandler.log_folder, f"{filename}.log")
        logging.basicConfig(
            level=logging.DEBUG, format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M", filename=self.path, filemode="a",
        )
        self.logger = logging.getLogger(loggername)
        self.TEMPLATE = "{:-^80}"

    def log_event(self, level, message):
        self.logger.log(getattr(logging, level), message)

    def log_header(self, level, message):
        self.log_event(level, self.TEMPLATE.format(message,))

    def log_start_program(self):
        self.logger.info(self.TEMPLATE.format("Starting the Programm",))
