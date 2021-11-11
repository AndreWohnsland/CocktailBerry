""" Wrapper function to suppress and instead only log error. Use with caution """
from functools import wraps

from config.config_manager import shared
from src.logger_handler import LoggerHandler


def logerror(func):
    """ Logs every time an error occours """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if shared.suppress_error:
            logger = LoggerHandler("error_suppressor", "debuglog")
            try:
                func(*args, **kwargs)
            except Exception:
                msg = f"The function {func.__name__} could not be fully excecuted!"
                logger.log_event("ERROR", msg)
                print(msg)
        else:
            func(*args, **kwargs)

    return wrapper
