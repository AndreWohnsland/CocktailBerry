import sys

from src import FUTURE_PYTHON_VERSION
from src.config.config_manager import CONFIG as cfg
from src.updater import Updater
from src.utils import has_connection


def can_update() -> tuple[bool, str]:
    """Check if there is an update and it is possible."""
    if not cfg.MAKER_SEARCH_UPDATES:
        return False, "Update search is disabled."
    updater = Updater()
    return updater.check_for_updates()


def connection_okay() -> bool:
    """Check if there is an internet connection, if needed."""
    # only needed if microservice is also active
    if not cfg.MAKER_CHECK_INTERNET or not cfg.MICROSERVICE_ACTIVE:
        return True
    return has_connection()


def is_python_deprecated() -> bool:
    """Check if to display the deprecation warning for newer python version install."""
    sys_python = sys.version_info
    return sys_python < FUTURE_PYTHON_VERSION
