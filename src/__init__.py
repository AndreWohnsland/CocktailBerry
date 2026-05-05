import tomllib
from typing import Literal

from src.filepath import PYPROJECT_FILE


def _read_pyproject_version() -> str:
    with PYPROJECT_FILE.open("rb") as file:
        pyproject = tomllib.load(file)
    return str(pyproject["project"]["version"])


__version__ = _read_pyproject_version()
PROJECT_NAME = "CocktailBerry"
MAX_SUPPORTED_BOTTLES = 24
SupportedLanguagesType = Literal["en", "de"]
SupportedThemesType = Literal["default", "bavaria", "alien", "berry", "tropical", "purple", "custom"]
SupportedRfidType = Literal["MFRC522", "USB"]
SupportedPaymentOptions = Literal["Disabled", "CocktailBerry", "SumUp"]
SupportedLedStatesType = Literal["Effect", "On", "Off"]
I2CExpanderType = Literal["MCP23017", "PCF8574", "PCA9535"]
SupportedPinControlType = Literal["GPIO", "MCP23017", "PCF8574", "PCA9535"]
SupportedDispenserType = Literal["DC", "Stepper"]
SupportedStepperDriverType = Literal["A4988", "DRV8825", "LV8729"]
SupportedStepperStepType = Literal["Full", "Half", "1/4", "1/8", "1/16", "1/32"]
ConsumptionEstimationType = Literal["time", "weight"]
SupportedScaleDriverType = Literal["HX711", "NAU7802"]
SupportedCarriageType = Literal["NoCarriage"]
SupportedLedDriverType = Literal["Normal", "WSLED"]
NEEDED_PYTHON_VERSION = (3, 11)
FUTURE_PYTHON_VERSION = (3, 13)
