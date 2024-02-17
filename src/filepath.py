"""Holds all the path location of the project"""

from pathlib import Path

# Root Path
ROOT_PATH = Path(__file__).parents[1].absolute()
CUSTOM_CONFIG_FILE = ROOT_PATH / "custom_config.yaml"
VERSION_FILE = ROOT_PATH / ".version.ini"
LOG_FOLDER = ROOT_PATH / "logs"
SAVE_FOLDER = ROOT_PATH / "saves"
ADDON_FOLDER = ROOT_PATH / "addons"
SCRIPTS_FOLDER = ROOT_PATH / "scripts"
USER_IMAGE_FOLDER = ROOT_PATH / "display_images_user"
DEFAULT_IMAGE_FOLDER = ROOT_PATH / "default_cocktail_images"
DEFAULT_COCKTAIL_IMAGE = DEFAULT_IMAGE_FOLDER / "default.jpg"
DATABASE_PATH = ROOT_PATH / "Cocktail_database.db"
DEFAULT_DATABASE_PATH = ROOT_PATH / "Cocktail_database_default.db"

# src path
SRC_PATH = ROOT_PATH / "src"
STYLE_FOLDER = SRC_PATH / "ui" / "styles"
CUSTOM_STYLE_FILE = STYLE_FOLDER / "custom.css"
CUSTOM_STYLE_SCSS = STYLE_FOLDER / "custom.scss"
LANGUAGE_FILE = SRC_PATH / "language.yaml"
APP_ICON_FILE = SRC_PATH / "ui_elements" / "Cocktail-icon.png"
ADDON_SKELTON = SRC_PATH / "programs" / "addon_skeleton.py"

# other
LOCAL_MICROSERVICE_FILE = Path.home().absolute() / "ms-docker-compose.yaml"
DEFAULT_MICROSERVICE_FILE = SCRIPTS_FOLDER / "ms-docker-compose.yaml"
TEAMS_DOCKER_FILE = ROOT_PATH / "dashboard" / "docker-compose.both.yaml"
