"""Pin type enumeration and abstractions for hybrid GPIO/I2C control."""

from enum import Enum


class PinType(str, Enum):
    """Types of pin controllers supported by the system."""

    GPIO = "GPIO"
    MCP23017 = "MCP23017"
    PCF8574 = "PCF8574"
