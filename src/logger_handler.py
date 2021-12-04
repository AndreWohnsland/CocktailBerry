import os
import logging

dirpath = os.path.dirname(os.path.abspath(__file__))


class LoggerHandler:
    """Handler Class for Generating Logger and Logging events"""

    log_folder = os.path.join(dirpath, "..", "logs")

    def __init__(self, loggername, filename):
        self.loggername = loggername
        self.path = os.path.join(LoggerHandler.log_folder, f"{filename}.log")

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

    def log_event(self, level, message):
        self.logger.log(getattr(logging, level), message)

    def log_header(self, level, message):
        self.log_event(level, self.template.format(f" {message} ",))

    def log_start_program(self):
        self.log_header("INFO", "Starting the Programm")

    def log_exception(self, message):
        self.logger.exception(message)
