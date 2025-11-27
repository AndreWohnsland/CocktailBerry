from typing import Literal

__version__ = "2.9.0"
PROJECT_NAME = "CocktailBerry"
MAX_SUPPORTED_BOTTLES = 24
SupportedLanguagesType = Literal["en", "de"]
SupportedThemesType = Literal["default", "bavaria", "alien", "berry", "tropical", "purple", "custom"]
SupportedRfidType = Literal["No", "MFRC522", "PiicoDev", "USB"]
SupportedLedStatesType = Literal["Effect", "On", "Off"]
NEEDED_PYTHON_VERSION = (3, 11)
FUTURE_PYTHON_VERSION = (3, 11)
