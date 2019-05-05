""" Special configs for the Logger """
import logging
import time


def basiclogger():
    """ This is a very basic logger, which logs every Level and writes the time
    and a Message.
    """
    logger = logging.getLogger('cocktail_application')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('Party_2019_03_30.log')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(message)s', "%Y-%m-%d %H:%M")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Test the logger
    template = "{:-^80}"
    logger.debug(template.format("Restarting the Programm",))