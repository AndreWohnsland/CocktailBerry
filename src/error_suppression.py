""" Special configs for the Logger """
import logging
import time
from functools import wraps
import os

import globalvars


def logerror(func):
    """ Logs every time an error occours """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if globalvars.SUPPRESS_ERROR:
            logger = logging.getLogger("debuglog")
            try:
                func(*args, **kwargs)
            except Exception:
                logger.exception(f"The function {func.__name__} could not be fully excecuted!")
                print("The function {} could not be fully excecuted!".format(func.__name__))
        else:
            func(*args, **kwargs)

    return wrapper
