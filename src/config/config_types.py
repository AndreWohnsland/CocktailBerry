"""Module for configuration types.

They are used to wrap the validation of different types and composition within the yaml config file.
Simply separating by build in types is not enough for dict or list types.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, ClassVar, get_args

from src import (
    SupportedBoardType,
    SupportedLanguagesType,
    SupportedRfidType,
    SupportedThemesType,
)
from src.config.errors import ConfigError

SUPPORTED_LANGUAGES = list(get_args(SupportedLanguagesType))
SUPPORTED_BOARDS = list(get_args(SupportedBoardType))
SUPPORTED_THEMES = list(get_args(SupportedThemesType))
SUPPORTED_RFID = list(get_args(SupportedRfidType))


class ChooseType:
    """Base Class for auto generated single select drop down."""

    allowed: ClassVar[list[str]] = []


class LanguageChoose(ChooseType):
    allowed = SUPPORTED_LANGUAGES


class BoardChoose(ChooseType):
    allowed = SUPPORTED_BOARDS


class ThemeChoose(ChooseType):
    allowed = SUPPORTED_THEMES


class RFIDChoose(ChooseType):
    allowed = SUPPORTED_RFID


@dataclass
class ConfigType:
    """Base class for configuration types."""

    config_type: type
    validator_functions: list[Callable[[str, Any], None]] = field(default_factory=list)

    def validate(self, configname: str, value: Any):
        """Validate the given value."""
        if value is not self.config_type:
            raise ConfigError(f"The value <{value}> for '{configname}' is not of type {self.config_type}")

    def ui_type(self):
        """Return the type for the UI."""
        return self.config_type


class ListType(ConfigType):
    """List configuration type."""

    def __init__(self, validator_functions: list[Callable[[str, Any], None]], list_type: ConfigType):
        self.config_type = list
        self.list_type = list_type
        self.validator_functions = validator_functions

    def validate(self, configname: str, value: Any):
        """Validate the given value."""
        super().validate(configname, value)
        for i, item in enumerate(value, 1):
            config_text = f"{configname} at position {i}"
            self.list_type.validate(config_text, item)

    def ui_type(self):
        """Return the type for the UI."""
        return type(self)


class DictType(ConfigType):
    """Dict configuration type."""

    def __init__(self, validator_functions: list[Callable[[str, Any], None]], dict_types: dict[str, ConfigType]):
        self.config_type = dict
        self.validator_functions = validator_functions
        self.dict_types = dict_types

    def validate(self, configname: str, config_dict: dict[str, Any]):
        """Validate the given value."""
        super().validate(configname, config_dict)
        for key_name, key_type in self.dict_types.items():
            key_value = config_dict.get(key_name)
            if key_value is None:
                raise ConfigError(f"Config value for '{key_name}' is missing in '{configname}'")
            key_text = f"{configname} key {key_name}"
            key_type.validate(key_text, key_value)

    def ui_type(self):
        """Return the type for the UI."""
        return type(self)
