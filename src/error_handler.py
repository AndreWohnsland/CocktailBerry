""" Wrapper function to suppress and instead only log error. Use with caution """
import sys
import re
import traceback
from functools import wraps
from typing import Callable

from src.logger_handler import LoggerHandler, LogFiles
from src.machine.controller import MACHINE
from src.utils import time_print


def logerror(func: Callable):
    """ Logs every time an error occurs """

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = LoggerHandler("error_logger", LogFiles.DEBUG)
        try:
            result = func(*args, **kwargs)
        # pylint: disable=broad-except
        except Exception:
            trb = sys.exc_info()[-1]
            stack = traceback.extract_tb(trb)
            fname = stack[-1][2]
            row = stack[-1][3]
            module = re.split(r"[\\/]", stack[-1][0])[-1]
            msg = f"The function {func.__name__} did run into an error at module: {module} function {fname} in row: {row}!"  # noqa
            logger.log_exception(msg)
            time_print(msg)
            MACHINE.close_all_pumps()
            raise
        return result
    return wrapper
