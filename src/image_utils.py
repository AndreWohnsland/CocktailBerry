from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from src.filepath import DEFAULT_COCKTAIL_IMAGE, DEFAULT_IMAGE_FOLDER, USER_IMAGE_FOLDER
from src.models import Cocktail


def find_cocktail_image(cocktail: Cocktail) -> Path:
    """Find the image for the given cocktail."""
    # setting default cocktail image
    cocktail_image = find_default_cocktail_image(cocktail)
    # Now try to get the user defined image, if it exists
    user_cocktail_image = find_user_cocktail_image(cocktail)
    if user_cocktail_image is not None:
        cocktail_image = user_cocktail_image
    return cocktail_image


def find_default_cocktail_image(cocktail: Cocktail) -> Path:
    """Find the system defined image for the given cocktail."""
    # setting default cocktail image
    cocktail_image = DEFAULT_COCKTAIL_IMAGE
    # then try to get system cocktail image
    # provided cocktails will have a default image, user added will not
    specific_image_path = DEFAULT_IMAGE_FOLDER / f"{cocktail.id}.jpg"
    if specific_image_path.exists():
        cocktail_image = specific_image_path
    return cocktail_image


def find_user_cocktail_image(cocktail: Cocktail) -> Path | None:
    """Find the user defined image for the given cocktail.

    Returns None if not set.
    """
    cocktail_image = None
    # also allow cocktail name with underscores as image name
    image_paths = [
        USER_IMAGE_FOLDER / f"{cocktail.id}.jpg",
        USER_IMAGE_FOLDER / f"{cocktail.name.lower().replace(' ', '_')}.jpg",
    ]
    for path in image_paths:
        if path.exists():
            cocktail_image = path
            break
    return cocktail_image


def process_image(image_data: str | bytes | Path, resize_size: int = 500) -> Image.Image | None:
    """Resize and crop (1x1) the given image to the desired size."""
    # Open the image file
    try:
        img = Image.open(BytesIO(image_data)) if isinstance(image_data, bytes) else Image.open(image_data)
    # catch errors in file things
    except (FileNotFoundError, UnidentifiedImageError):
        return None
    # first check if the image needs to be rotated
    adjusted_img = check_picture_orientation(img)
    # Calculate dimensions for cropping
    width, height = adjusted_img.size
    if width > height:
        left = int((width - height) / 2)
        top = 0
        right = int((width + height) / 2)
        bottom = height
    else:
        top = int((height - width) / 2)
        left = 0
        bottom = int((height + width) / 2)
        right = width
    # Crop the image
    adjusted_img = adjusted_img.crop((left, top, right, bottom))
    # Resize the image
    adjusted_img = adjusted_img.resize((resize_size, resize_size), Image.Resampling.LANCZOS)
    # always convert to rgb
    return adjusted_img.convert("RGB")


def check_picture_orientation(img: Image.Image) -> Image.Image:
    # EXIF orientation tag values
    ORIENTATION_ROTATE_180 = 3
    ORIENTATION_ROTATE_90_CW = 6
    ORIENTATION_ROTATE_270_CW = 8

    # Check for EXIF orientation tag
    exif_data = img.getexif()
    orientation = exif_data.get(0x0112, 1)  # 0x0112 is the EXIF Orientation tag
    # rotate use counter clockwise, exif is clockwise, so don't be confused
    # Exif tags are, we currently only handle normal rotations here:
    # 1: Horizontal (normal)
    # 2: Mirror horizontal
    # 3: Rotate 180 <- is the same in rotate
    if orientation == ORIENTATION_ROTATE_180:
        img = img.rotate(180, expand=True)
    # 4: Mirror vertical
    # 5: Mirror horizontal and rotate 270 CW
    # 6: Rotate 90 CW <- is 270 counter CW
    elif orientation == ORIENTATION_ROTATE_90_CW:
        img = img.rotate(270, expand=True)
    # 7: Mirror horizontal and rotate 90 CW
    # 8: Rotate 270 CW <- is 90 counter CW
    elif orientation == ORIENTATION_ROTATE_270_CW:
        img = img.rotate(90, expand=True)
    return img


def save_image(image: Image.Image, save_id: int) -> None:
    """Save the given image to the user folder."""
    image.save(USER_IMAGE_FOLDER / f"{save_id}.jpg", "JPEG")
