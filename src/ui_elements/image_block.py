from pathlib import Path
from typing import Union
from PIL import Image, UnidentifiedImageError

from PyQt5.QtWidgets import QVBoxLayout, QPushButton
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSizePolicy

from src.filepath import DEFAULT_IMAGE_FOLDER, USER_IMAGE_FOLDER
from src.models import Cocktail
from src.ui_elements.clickable_label import ClickableLabel
from src.config_manager import CONFIG as cfg

# roughly take 240 px for image dimensions
N_COLUMNS = int(cfg.UI_WIDTH / 240)
# keep a 15% margin
SQUARE_SIZE = int(cfg.UI_WIDTH / (N_COLUMNS * 1.15))


def generate_image_block(cocktail: Cocktail):
    """Generates a image block for the given cocktail"""
    button = QPushButton(cocktail.name)
    label = ClickableLabel(cocktail.name)
    # setting default cocktail image
    cocktail_image = DEFAULT_IMAGE_FOLDER / 'default.jpg'
    # first try the user image folder, then the default image folder, then use the default image if nothing exists
    # allow name or id to be used for cocktail, but prefer id
    # also prefer user before system delivered ones
    image_paths = [
        USER_IMAGE_FOLDER / f'{cocktail.id}.jpg',
        USER_IMAGE_FOLDER / f'{cocktail.name.lower()}.jpg',
        DEFAULT_IMAGE_FOLDER / f'{cocktail.id}.jpg',
    ]
    for path in image_paths:
        if path.exists():
            cocktail_image = path
            break
    pixmap = QPixmap(str(cocktail_image))
    label.setPixmap(pixmap)
    label.setScaledContents(True)
    label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)  # type: ignore
    label.setMinimumSize(SQUARE_SIZE, SQUARE_SIZE)
    label.setMaximumSize(SQUARE_SIZE, SQUARE_SIZE)
    layout = QVBoxLayout()
    layout.setSpacing(0)
    layout.addWidget(button)
    layout.addWidget(label)
    # TODO: add functionality to the buttons
    button.clicked.connect(lambda: print(cocktail.name))
    label.clicked.connect(lambda: print(cocktail.name))
    return layout


def process_image(image_path: Union[str, bytes, Path], resize_size: int = 500, save_id: int = -1):
    """Resize and crop (1x1) the given image to the desired size"""
    if save_id == -1:
        return False
    # Open the image file
    try:
        img = Image.open(image_path)
    # catch errors in file things
    except (FileNotFoundError, UnidentifiedImageError):
        return False
    # Calculate dimensions for cropping
    width, height = img.size
    if width > height:
        left = (width - height) / 2
        top = 0
        right = (width + height) / 2
        bottom = height
    else:
        top = (height - width) / 2
        left = 0
        bottom = (height + width) / 2
        right = width
    # Crop the image
    img = img.crop((left, top, right, bottom))  # type: ignore
    # Resize the image
    img = img.resize((resize_size, resize_size), Image.LANCZOS)
    img.save(USER_IMAGE_FOLDER / f'{save_id}.jpg', "JPEG")
    return True
