from pathlib import Path

# Root Path
ROOT_PATH = Path(__file__).parents[1].absolute()
CUSTOM_CONFIG_FILE = ROOT_PATH / "custom_config.yaml"
VERSION_FILE = ROOT_PATH / ".version.ini"
LOG_FOLDER = ROOT_PATH / "logs"
SAVE_FOLDER = ROOT_PATH / "saves"
ADDON_PATH = ROOT_PATH / "addons"

# src path
SRC_PATH = ROOT_PATH / "src"
STYLE_FOLDER = SRC_PATH / "ui" / "styles"
LANGUAGE_FILE = SRC_PATH / "language.yaml"
APP_ICON_FILE = SRC_PATH / "ui_elements" / "Cocktail-icon.png"
