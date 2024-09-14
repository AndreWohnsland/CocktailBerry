import platform
import sys

from src import NEEDED_PYTHON_VERSION
from src.utils import time_print

_needed_python_version_str = f"{NEEDED_PYTHON_VERSION[0]}.{NEEDED_PYTHON_VERSION[1]}"
_used_python_version = sys.version_info


class _PythonVersionTooLowError(Exception):
    """Raised when used Python version is too low."""

    def __init__(self) -> None:
        self.message = f"This program requires Python {_needed_python_version_str} or higher. You are using Python {platform.python_version()}"  # noqa
        super().__init__(self.message)


def check_python_version() -> None:
    """Raise an error if used Python version is too low."""
    if _used_python_version < NEEDED_PYTHON_VERSION:
        time_print(f"This program requires Python {_needed_python_version_str} or higher.")
        time_print(f"You are using Python {platform.python_version()}")
        time_print("Please install a correct version of Python.")
        raise _PythonVersionTooLowError()
