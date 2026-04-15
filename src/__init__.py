from typing import Literal

__version__ = "3.3.0"
PROJECT_NAME = "CocktailBerry"
MAX_SUPPORTED_BOTTLES = 24
SupportedLanguagesType = Literal["en", "de"]
SupportedThemesType = Literal["default", "bavaria", "alien", "berry", "tropical", "purple", "custom"]
SupportedRfidType = Literal["No", "MFRC522", "USB"]
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
NEEDED_PYTHON_VERSION = (3, 11)
FUTURE_PYTHON_VERSION = (3, 13)
