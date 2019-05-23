""" Special configs for the Logger """
import logging
import time


def basiclogger(loggername):
    """ This is a very basic logger, which logs every Level and writes the time
    and a Message.
    """
    logger = logging.getLogger('cocktail_application')
    logger.setLevel(logging.DEBUG)
    name_ = "Logfile_{}.log".format(loggername)
    fh = logging.FileHandler(name_)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(message)s', "%Y-%m-%d %H:%M")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    # Logging the Start of the Programm. If it runs a whole evening, each restart means a previous crash.
    template = "{:-^80}"
    logger.debug(template.format("Restarting the Programm",))
