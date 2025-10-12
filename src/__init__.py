from typing import Literal

__version__ = "2.6.2"
PROJECT_NAME = "CocktailBerry"
MAX_SUPPORTED_BOTTLES = 24
SupportedLanguagesType = Literal["en", "de"]
SupportedThemesType = Literal["default", "bavaria", "alien", "berry", "tropical", "purple", "custom"]
SupportedRfidType = Literal["No", "MFRC522", "PiicoDev"]
NEEDED_PYTHON_VERSION = (3, 9)
FUTURE_PYTHON_VERSION = (3, 11)
