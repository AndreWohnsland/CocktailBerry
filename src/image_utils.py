from typing import Union
from pathlib import Path
from PIL import Image, UnidentifiedImageError

from src.filepath import DEFAULT_IMAGE_FOLDER, USER_IMAGE_FOLDER
from src.models import Cocktail


def find_cocktail_image(cocktail: Cocktail):
    """Find the image for the given cocktail"""
    # setting default cocktail image
    cocktail_image = find_default_cocktail_image(cocktail)
    # Now try to get the user defined image, if it exists
    user_cocktail_image = find_user_cocktail_image(cocktail)
    if user_cocktail_image is not None:
        cocktail_image = user_cocktail_image
    return cocktail_image


def find_default_cocktail_image(cocktail: Cocktail):
    """Find the system defined image for the given cocktail"""
    # setting default cocktail image
    cocktail_image = DEFAULT_IMAGE_FOLDER / 'default.jpg'
    # then try to get system cocktail image
    # provided cocktails will have a default image, user added will not
    specific_image_path = DEFAULT_IMAGE_FOLDER / f'{cocktail.id}.jpg'
    if specific_image_path.exists():
        cocktail_image = specific_image_path
    return cocktail_image


def find_user_cocktail_image(cocktail: Cocktail):
    """Finds the user defined image for the given cocktail
    Returns None if not set"""
    cocktail_image = None
    image_paths = [
        USER_IMAGE_FOLDER / f'{cocktail.id}.jpg',
        USER_IMAGE_FOLDER / f'{cocktail.name.lower()}.jpg',
    ]
    for path in image_paths:
        if path.exists():
            cocktail_image = path
            break
    return cocktail_image


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
    img = img.resize((resize_size, resize_size), Image.LANCZOS)  # pylint: disable=E1101
    img.save(USER_IMAGE_FOLDER / f'{save_id}.jpg', "JPEG")
    return True
