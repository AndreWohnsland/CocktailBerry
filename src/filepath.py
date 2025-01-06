"""Holds all the path location of the project."""

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
APP_ICON_FILE = SRC_PATH / "ui_elements" / "cocktailberry.png"
ADDON_SKELTON = SRC_PATH / "programs" / "addon_skeleton.py"
QT_MIGRATION_SCRIPT = SRC_PATH / "migration" / "qt_migrator.py"
WEB_MIGRATION_SCRIPT = SRC_PATH / "migration" / "web_migrator.py"
NGINX_SCRIPT = SRC_PATH / "migration" / "setup_web.py"

# other
LOCAL_MICROSERVICE_FILE = Path.home().absolute() / "ms-docker-compose.yaml"
DEFAULT_MICROSERVICE_FILE = SCRIPTS_FOLDER / "ms-docker-compose.yaml"
NGINX_CONFIG_FILE = SCRIPTS_FOLDER / "cocktailberry_web_client"
TEAMS_DOCKER_FILE = ROOT_PATH / "dashboard" / "docker-compose.both.yaml"

# API
API_FOLDER = SRC_PATH / "api"
STATIC_API_FOLDER = API_FOLDER / "static"
WEB_APP_FOLDER = API_FOLDER / "webapp"
COCKTAIL_WEB_DESKTOP = SCRIPTS_FOLDER / "cocktail_web.desktop"
