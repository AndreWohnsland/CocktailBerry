"""Wrapper function to suppress and instead only log error. Use with caution."""

import re
import sys
import traceback
from functools import wraps
from typing import Any, Callable

from src.logger_handler import LogFiles, LoggerHandler
from src.machine.controller import MACHINE
from src.utils import time_print

_logger = LoggerHandler("error_logger", LogFiles.DEBUG)


def logerror(func: Callable):
    """Wrap a function, execute it and log the exception.

    Close the machine pump, then re-raise the exception.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
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
            _logger.log_exception(msg)
            time_print(msg)
            try:
                MACHINE.close_all_pumps()
            except Exception as e:
                _logger.log_exception(f"Error while closing the pumps: {e}")
            raise
        return result

    return wrapper
