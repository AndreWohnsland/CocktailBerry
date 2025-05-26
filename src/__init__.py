from typing import Literal

__version__ = "2.4.1"
PROJECT_NAME = "CocktailBerry"
MAX_SUPPORTED_BOTTLES = 24
SupportedLanguagesType = Literal["en", "de"]
SupportedThemesType = Literal["default", "bavaria", "alien", "berry", "custom"]
SupportedRfidType = Literal["No", "MFRC522", "PiicoDev"]
NEEDED_PYTHON_VERSION = (3, 9)
FUTURE_PYTHON_VERSION = (3, 11)
