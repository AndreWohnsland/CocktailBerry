""" Special configs for the Logger """
import logging
import time
from functools import wraps

import globals


def basiclogger(loggerobj, loggername, printline = False):
    """ This is a very basic logger, which logs every Level and writes the time
    and a Message.
    """
    logger = logging.getLogger(loggerobj)
    logger.setLevel(logging.DEBUG)
    name_ = "{}.log".format(loggername)
    fh = logging.FileHandler(name_)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(message)s', "%Y-%m-%d %H:%M")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    # Logging the Start of the Programm. If it runs a whole evening, each restart means a previous crash.
    if printline:
        template = "{:-^80}"
        logger.debug(template.format("Restarting the Programm",))


def logfunction(func):
    """ Logs every time the function name and time needed """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if globals.decoactivate:
            trigger = True
            logger_t = logging.getLogger('timing')
            t1 = time.time()
            try:
                func(*args, **kwargs)
            except Exception:
                logger_t.exception("The function {} could not be fully excecuted!".format(func.__name__))
                trigger = False
                print("The function {} could not be fully excecuted!".format(func.__name__))
            t2 = round((time.time() - t1) * 1000)
            if trigger:
                logger_t.info("The function {} took {} ms to complete".format(func.__name__, t2))
        else:
            func(*args, **kwargs)
    return wrapper

def logerror(func):
    """ Logs every time an error occours """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if globals.decoactivate:
            logger_t = logging.getLogger('timing')
            try:
                func(*args, **kwargs)
            except Exception:
                logger_t.exception
                logger_t.exception("The function {} could not be fully excecuted!".format(func.__name__))
                print("The function {} could not be fully excecuted!".format(func.__name__))
        else:
            func(*args, **kwargs)
    return wrapper
