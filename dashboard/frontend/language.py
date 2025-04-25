import os
from pathlib import Path
from typing import Union

import yaml
from dotenv import load_dotenv

DIRPATH = Path(__file__).parent.absolute()
load_dotenv(DIRPATH / ".env")

# Getting the language file as dict
LANGUAGE_FILE = DIRPATH / "language.yaml"
with open(LANGUAGE_FILE, encoding="UTF-8") as stream:
    LANGUAGE_DATA: dict = yaml.safe_load(stream)


class Language:
    def __init__(self):
        self.HEADER = self._choose_language(LANGUAGE_DATA["header_label"])
        self.DEFAULT_MESSAGE = self._choose_language(LANGUAGE_DATA["default_message"])
        self.CALL_TO_ACTION = self._choose_language(LANGUAGE_DATA["call_to_action"])
        self.AMOUNT_TODAY = self._choose_language(LANGUAGE_DATA["amount_today"])
        self.VOLUME_TODAY = self._choose_language(LANGUAGE_DATA["volume_today"])
        self.AMOUNT_ALL = self._choose_language(LANGUAGE_DATA["amount_all"])
        self.VOLUME_ALL = self._choose_language(LANGUAGE_DATA["volume_all"])

    def _choose_language(self, element: dict, **kwargs) -> Union[str, list[str]]:
        """Choose either the given language if exists, or english if not piping additional info into template."""
        language = os.getenv("UI_LANGUAGE")
        tmpl = element.get(language, element["en"])
        # Return the list and not apply template!
        if isinstance(tmpl, list):
            return tmpl
        return tmpl.format(**kwargs)


language = Language()
