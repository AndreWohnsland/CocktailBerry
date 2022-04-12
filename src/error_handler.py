""" Wrapper function to suppress and instead only log error. Use with caution """
import sys
import re
import traceback
from functools import wraps
from typing import Callable

from src.logger_handler import LoggerHandler
from src.machine.controller import MACHINE


def logerror(func: Callable):
    """ Logs every time an error occours """

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = LoggerHandler("error_logger", "debuglog")
        try:
            func(*args, **kwargs)
        # pylint: disable=broad-except
        except Exception:
            trb = sys.exc_info()[-1]
            stack = traceback.extract_tb(trb)
            fname = stack[-1][2]
            row = stack[-1][3]
            module = re.split(r"[\\/]", stack[-1][0])[-1]
            msg = f"The function {func.__name__} did run into an error at module: {module} function {fname} in row: {row}!"
            logger.log_exception(msg)
            print(msg)
            MACHINE.close_all_pumps()
            raise
    return wrapper
