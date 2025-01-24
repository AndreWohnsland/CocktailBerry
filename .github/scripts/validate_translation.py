from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def github_error_print(
    message: str,
    file: str = "",
    line: int | None = None,
    col: int | None = None,
) -> None:
    """Print a GitHub Actions workflow command to annotate an error."""
    location = ""
    if file:
        location += f" file={file}"
    if line is not None:
        location += f",line={line}"
    if col is not None:
        location += f",col={col}"
    print(f"::error{location}::{message}")


def load_translations(base_path: Path) -> dict[str, Any]:
    translations = {}
    for language_folder in base_path.iterdir():
        lang_path = language_folder / "translation.json"
        if lang_path.is_file():
            with lang_path.open("r", encoding="utf-8") as file:
                translations[language_folder.name] = json.load(file)
    return translations


def flatten_json(nested_json: dict[str, Any], parent_key: str = "", sep: str = ".") -> dict[str, Any]:
    items = []
    for k, v in nested_json.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def find_missing_keys(translations: dict[str, Any]) -> dict[str, set[str]]:
    flattened_translations = {lang: flatten_json(content) for lang, content in translations.items()}
    all_keys = set().union(*flattened_translations.values())

    missing_keys = {}
    for lang, keys in flattened_translations.items():
        missing = all_keys - set(keys.keys())
        if missing:
            missing_keys[lang] = sorted(missing)
    return missing_keys


def main() -> int:
    base_path = Path("web_client/src/locales")
    if not base_path.exists():
        github_error_print(f"Error: Path '{base_path}' does not exist.")
        return 1

    translations = load_translations(base_path)
    missing_keys = find_missing_keys(translations)

    if missing_keys:
        msg = "Missing translation for keys detected:\n"
        for lang, keys in missing_keys.items():
            msg += f"  - Language: {lang}, Translation: {', '.join(keys)}\n"
        github_error_print(msg)
        return 1
    print("All translations are complete.")
    return 0


if __name__ == "__main__":
    exit(main())
