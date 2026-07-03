from pathlib import Path

import pytest
from PIL import Image

from src import image_utils
from src.filepath import DEFAULT_COCKTAIL_IMAGE
from src.image_utils import (
    RANDOM_IMAGE_NAME,
    find_cocktail_image,
    find_user_cocktail_image,
    save_image,
)


def test_find_user_image_none_when_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(image_utils, "USER_IMAGE_FOLDER", tmp_path)
    assert find_user_cocktail_image(5) is None
    assert find_user_cocktail_image(RANDOM_IMAGE_NAME) is None


def test_random_falls_back_to_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(image_utils, "USER_IMAGE_FOLDER", tmp_path)
    # no user random.jpg -> default image
    assert find_cocktail_image(RANDOM_IMAGE_NAME) == DEFAULT_COCKTAIL_IMAGE


def test_user_image_wins_for_id_and_random(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(image_utils, "USER_IMAGE_FOLDER", tmp_path)
    img = Image.new("RGB", (10, 10))
    for identifier in (7, RANDOM_IMAGE_NAME):
        save_image(img, identifier)
        expected = tmp_path / f"{identifier}.jpg"
        assert expected.exists()
        assert find_cocktail_image(identifier) == expected
