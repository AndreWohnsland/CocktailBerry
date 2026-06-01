"""Tests for the scale-assisted hand-add gating in ``maker.prepare_cocktail``.

The cocktail is finalized immediately; when the scale flow applies the hand-adds are attached to
``shared.cocktail_status.hand_adds`` so the UI can show the (non-blocking) guidance window.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.config.config_manager import CONFIG, shared
from src.config.errors import ConfigError
from src.models import Cocktail, HandAddMeasure, Ingredient, PrepareResult, PreparationResult


def _ingredient(id: int, name: str, *, bottle: int | None, amount: int, unit: str = "ml") -> Ingredient:
    return Ingredient(
        id=id,
        name=name,
        alcohol=0,
        bottle_volume=1000,
        fill_level=1000,
        hand=bottle is None,
        pump_speed=100,
        amount=amount,
        bottle=bottle,
        unit=unit,
    )


def _cocktail(ingredients: list[Ingredient]) -> Cocktail:
    return Cocktail(
        id=1,
        name="Test",
        alcohol=0,
        amount=sum(i.amount for i in ingredients),
        enabled=True,
        price_per_100_ml=0,
        virgin_available=False,
        ingredients=ingredients,
    )


def _run_prepare(cocktail: Cocktail, *, feature_on: bool, has_scale: bool) -> list[HandAddMeasure]:
    """Run prepare_cocktail with heavy collaborators mocked; return the resulting hand_adds list."""
    mc_instance = MagicMock()
    mc_instance.has_scale = has_scale
    # empty result -> completion_ratio 0, so the service hooks are skipped
    mc_instance.make_cocktail.return_value = PreparationResult(ingredients=[])
    with (
        patch("src.tabs.maker.MachineController", return_value=mc_instance),
        patch("src.tabs.maker.DatabaseCommander", return_value=MagicMock()),
        patch("src.tabs.maker.ADDONS"),
        patch("src.tabs.maker.SERVICE_HANDLER"),
        patch.object(CONFIG, "MAKER_SCALE_FOR_HAND_ADDS", feature_on),
    ):
        from src.tabs import maker

        shared.current_waiter_nfc_id = None
        result, _ = maker.prepare_cocktail(cocktail)
    assert result == PrepareResult.FINISHED
    return shared.cocktail_status.hand_adds


def test_ml_hand_add_is_measurable_with_feature_on_and_scale():
    cocktail = _cocktail(
        [
            _ingredient(1, "Gin", bottle=1, amount=40),
            _ingredient(2, "Lime", bottle=None, amount=10, unit="ml"),
        ]
    )
    hand_adds = _run_prepare(cocktail, feature_on=True, has_scale=True)
    assert [(h.name, h.measurable) for h in hand_adds] == [("Lime", True)]


def test_hand_adds_attached_but_not_measurable_when_feature_off():
    cocktail = _cocktail(
        [
            _ingredient(1, "Gin", bottle=1, amount=40),
            _ingredient(2, "Lime", bottle=None, amount=10, unit="ml"),
        ]
    )
    # the window still lists the hand-add, but it is a check (not a scale measure)
    hand_adds = _run_prepare(cocktail, feature_on=False, has_scale=True)
    assert [(h.name, h.measurable) for h in hand_adds] == [("Lime", False)]


def test_ml_hand_add_not_measurable_without_scale():
    cocktail = _cocktail(
        [
            _ingredient(1, "Gin", bottle=1, amount=40),
            _ingredient(2, "Lime", bottle=None, amount=10, unit="ml"),
        ]
    )
    hand_adds = _run_prepare(cocktail, feature_on=True, has_scale=False)
    assert [(h.name, h.measurable) for h in hand_adds] == [("Lime", False)]


def test_non_ml_hand_add_is_never_measurable():
    cocktail = _cocktail(
        [
            _ingredient(1, "Gin", bottle=1, amount=40),
            _ingredient(2, "Mint", bottle=None, amount=6, unit="pieces"),
        ]
    )
    hand_adds = _run_prepare(cocktail, feature_on=True, has_scale=True)
    assert [(h.name, h.measurable) for h in hand_adds] == [("Mint", False)]


def test_config_validation_requires_enabled_scale():
    original_feature = CONFIG.MAKER_SCALE_FOR_HAND_ADDS
    original_enabled = CONFIG.SCALE_CONFIG.enabled
    try:
        CONFIG.MAKER_SCALE_FOR_HAND_ADDS = True
        CONFIG.SCALE_CONFIG.enabled = False
        with pytest.raises(ConfigError):
            CONFIG._validate_scale_config(validate=True)
        CONFIG.SCALE_CONFIG.enabled = True
        # no error when the scale is enabled
        CONFIG._validate_scale_config(validate=True)
    finally:
        CONFIG.MAKER_SCALE_FOR_HAND_ADDS = original_feature
        CONFIG.SCALE_CONFIG.enabled = original_enabled
