from typing import get_args

from src.dialog_handler import DIALOG_HANDLER, allowed_keys


def test_all_allowed_keys_have_translations() -> None:
    missing = set(get_args(allowed_keys)) - DIALOG_HANDLER.dialogs.keys()
    assert not missing, f"Keys allowed in get_translation but missing in language.yaml: {sorted(missing)}"
