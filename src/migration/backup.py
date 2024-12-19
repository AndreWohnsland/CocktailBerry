from src.filepath import (
    CUSTOM_CONFIG_FILE,
    CUSTOM_STYLE_FILE,
    CUSTOM_STYLE_SCSS,
    DATABASE_PATH,
    USER_IMAGE_FOLDER,
    VERSION_FILE,
)

# the version.ini file is always required, as it pins the user version and possible needed migration on backup restore
NEEDED_BACKUP_FILES = [VERSION_FILE]
# version.ini will always be copied, so it is not needed to be in the list
OPTIONAL_BACKUP_FILES = [
    CUSTOM_STYLE_FILE,
    CUSTOM_STYLE_SCSS,
    CUSTOM_CONFIG_FILE,
    USER_IMAGE_FOLDER,
    DATABASE_PATH,
]
BACKUP_FILES = NEEDED_BACKUP_FILES + OPTIONAL_BACKUP_FILES


# A backup type (styles) may have more than one file, so a mapper is needed
# In addition, we need a translation for this
FILE_SELECTION_MAPPER = {
    "style": [CUSTOM_STYLE_FILE, CUSTOM_STYLE_SCSS],
    "config": [CUSTOM_CONFIG_FILE],
    "images": [USER_IMAGE_FOLDER],
    "database": [DATABASE_PATH],
}
