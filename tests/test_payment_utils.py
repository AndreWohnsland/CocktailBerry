from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any
from unittest.mock import patch

import pytest

from src.models import Cocktail
from src.payment_utils import filter_cocktails_by_user
from src.programs.nfc_payment_service import User

# Type alias for the patch_cfg fixture return type
PatchCfgType = Callable[..., AbstractContextManager[dict[str, Any]]]


def create_test_cocktail(
    cocktail_id: int = 1,
    name: str = "Test Cocktail",
    alcohol: int = 10,
    amount: int = 300,
    price_per_100_ml: float = 5.0,
    virgin_available: bool = False,
) -> Cocktail:
    """Create a minimal test cocktail with only required attributes."""
    return Cocktail(
        id=cocktail_id,
        name=name,
        alcohol=alcohol,
        amount=amount,
        enabled=True,
        price_per_100_ml=price_per_100_ml,
        virgin_available=virgin_available,
        ingredients=[],
    )


def create_test_user(
    uid: str = "TEST123",
    balance: float = 10.0,
    can_get_alcohol: bool = True,
) -> User:
    """Create a test user with specified attributes."""
    return User(nfc_id=uid, balance=balance, is_adult=can_get_alcohol)


@pytest.fixture
def mock_cfg() -> dict[str, Any]:
    """Provide default config values for testing."""
    return {
        "MAKER_PREPARE_VOLUME": [150, 250, 350],
        "MAKER_USE_RECIPE_VOLUME": True,
        "PAYMENT_PRICE_ROUNDING": 1,
        "PAYMENT_VIRGIN_MULTIPLIER": 80,
    }


@pytest.fixture
def patch_cfg(mock_cfg: dict[str, Any]) -> PatchCfgType:
    """Fixture to patch cfg attributes for tests."""

    def _patch(**overrides: Any) -> AbstractContextManager[dict[str, Any]]:
        config = {**mock_cfg, **overrides}
        return patch.multiple("src.payment_utils.cfg", **config)

    return _patch


class TestFilterCocktailsNoUser:
    """Tests for filter_cocktails_by_user when no user is logged in."""

    def test_returns_empty_list_when_user_is_none(self, patch_cfg: PatchCfgType) -> None:
        """When user is None, should return input."""
        cocktails = [create_test_cocktail()]
        with patch_cfg():
            result = filter_cocktails_by_user(None, cocktails)
        assert result == cocktails

    def test_returns_empty_list_for_multiple_cocktails_when_user_is_none(self, patch_cfg: PatchCfgType) -> None:
        """When user is None, should return input regardless of cocktails."""
        cocktails = [
            create_test_cocktail(cocktail_id=1, name="Cocktail 1"),
            create_test_cocktail(cocktail_id=2, name="Cocktail 2"),
        ]
        with patch_cfg():
            result = filter_cocktails_by_user(None, cocktails)
        assert result == cocktails


class TestFilterCocktailsAlcoholPermission:
    """Tests for alcohol permission filtering."""

    def test_user_with_alcohol_permission_gets_all_cocktails(self, patch_cfg: PatchCfgType) -> None:
        """User who can get alcohol should have access to all affordable cocktails."""
        user = create_test_user(balance=100.0, can_get_alcohol=True)
        cocktails = [
            create_test_cocktail(cocktail_id=1, name="Alcoholic", alcohol=10, virgin_available=False),
            create_test_cocktail(cocktail_id=2, name="Non-Alcoholic", alcohol=0, virgin_available=False),
        ]
        with patch_cfg():
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 2
        assert {c.name for c in result} == {"Alcoholic", "Non-Alcoholic"}
        assert all(c.is_allowed for c in result)

    def test_user_without_alcohol_permission_excluded_from_alcoholic_only(self, patch_cfg: PatchCfgType) -> None:
        """User who cannot get alcohol should have alcoholic-only cocktails marked as not allowed."""
        user = create_test_user(balance=100.0, can_get_alcohol=False)
        cocktails = [
            create_test_cocktail(cocktail_id=1, name="Alcoholic Only", alcohol=15, virgin_available=False),
        ]
        with patch_cfg():
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is False

    def test_user_without_alcohol_permission_gets_virgin_available_cocktails(self, patch_cfg: PatchCfgType) -> None:
        """User who cannot get alcohol should have virgin cocktails marked as allowed."""
        user = create_test_user(balance=100.0, can_get_alcohol=False)
        cocktails = [
            create_test_cocktail(cocktail_id=1, name="Virgin Available", alcohol=10, virgin_available=True),
        ]
        with patch_cfg():
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].name == "Virgin Available"
        assert result[0].only_virgin is True
        assert result[0].is_allowed is True

    def test_user_without_alcohol_mixed_cocktails(self, patch_cfg: PatchCfgType) -> None:
        """User who cannot get alcohol should have appropriate is_allowed flags set."""
        user = create_test_user(balance=100.0, can_get_alcohol=False)
        cocktails = [
            create_test_cocktail(cocktail_id=1, name="Alcoholic Only", alcohol=15, virgin_available=False),
            create_test_cocktail(cocktail_id=2, name="Virgin Available", alcohol=10, virgin_available=True),
            create_test_cocktail(cocktail_id=3, name="Already Virgin", alcohol=0, virgin_available=True),
        ]
        with patch_cfg():
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 3
        # Alcoholic only should not be allowed
        alcoholic_only = next(c for c in result if c.name == "Alcoholic Only")
        assert alcoholic_only.is_allowed is False
        # Virgin available cocktails should be allowed and marked as only_virgin
        allowed = [c for c in result if c.is_allowed]
        assert len(allowed) == 2
        assert {c.name for c in allowed} == {"Virgin Available", "Already Virgin"}
        for cocktail in allowed:
            assert cocktail.only_virgin is True


class TestFilterCocktailsBalance:
    """Tests for balance/price filtering."""

    def test_user_can_afford_cocktail(self, patch_cfg: PatchCfgType) -> None:
        """User with sufficient balance should have cocktail marked as allowed."""
        user = create_test_user(balance=20.0, can_get_alcohol=True)
        cocktails = [create_test_cocktail(price_per_100_ml=5.0, amount=300)]
        with patch_cfg():
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is True

    def test_user_cannot_afford_cocktail(self, patch_cfg: PatchCfgType) -> None:
        """User with insufficient balance should have cocktail marked as not allowed."""
        user = create_test_user(balance=10.0, can_get_alcohol=True)
        cocktails = [create_test_cocktail(price_per_100_ml=5.0, amount=300)]
        with patch_cfg():
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is False

    def test_user_balance_exactly_matches_price(self, patch_cfg: PatchCfgType) -> None:
        """User with balance exactly matching price should have cocktail allowed."""
        user = create_test_user(balance=15.0, can_get_alcohol=True)
        cocktails = [create_test_cocktail(price_per_100_ml=5.0, amount=300)]
        with patch_cfg():
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is True

    def test_user_balance_just_below_price(self, patch_cfg: PatchCfgType) -> None:
        """User with balance just below price should have cocktail not allowed."""
        user = create_test_user(balance=14.9, can_get_alcohol=True)
        cocktails = [create_test_cocktail(price_per_100_ml=5.0, amount=300)]
        with patch_cfg():
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is False

    def test_filters_to_affordable_cocktails_only(self, patch_cfg: PatchCfgType) -> None:
        """Should mark unaffordable cocktails as not allowed."""
        user = create_test_user(balance=10.0, can_get_alcohol=True)
        cocktails = [
            create_test_cocktail(cocktail_id=1, name="Cheap", price_per_100_ml=2.0, amount=300),  # 6.0
            create_test_cocktail(cocktail_id=2, name="Expensive", price_per_100_ml=10.0, amount=300),  # 30.0
        ]
        with patch_cfg():
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 2
        cheap = next(c for c in result if c.name == "Cheap")
        expensive = next(c for c in result if c.name == "Expensive")
        assert cheap.is_allowed is True
        assert expensive.is_allowed is False


class TestFilterCocktailsVirginPricing:
    """Tests for virgin cocktail pricing with the multiplier."""

    def test_virgin_price_is_cheaper_with_multiplier(self, patch_cfg: PatchCfgType) -> None:
        """Virgin cocktails should use the virgin multiplier for pricing."""
        # Regular price = 10.0 / 100 * 300 = 30.0
        # Virgin price = 30.0 * 0.8 = 24.0
        user = create_test_user(balance=25.0, can_get_alcohol=False)
        cocktails = [
            create_test_cocktail(
                name="Virgin Available",
                price_per_100_ml=10.0,
                amount=300,
                virgin_available=True,
            ),
        ]
        with patch_cfg(PAYMENT_VIRGIN_MULTIPLIER=80):
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is True

    def test_cannot_afford_regular_but_can_afford_virgin(self, patch_cfg: PatchCfgType) -> None:
        """User who cannot afford regular price but can afford virgin price should have it allowed."""
        # Regular price = 10.0 / 100 * 300 = 30.0
        # Virgin price = 30.0 * 0.5 = 15.0
        user = create_test_user(balance=20.0, can_get_alcohol=False)
        cocktails = [
            create_test_cocktail(
                name="Expensive But Virgin Cheap",
                price_per_100_ml=10.0,
                amount=300,
                virgin_available=True,
            ),
        ]
        with patch_cfg(PAYMENT_VIRGIN_MULTIPLIER=50):
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].only_virgin is True
        assert result[0].is_allowed is True

    def test_cannot_afford_even_virgin(self, patch_cfg: PatchCfgType) -> None:
        """User who cannot afford even virgin price should have cocktail not allowed."""
        # Regular price = 10.0 / 100 * 300 = 30.0
        # Virgin price = 30.0 * 0.8 = 24.0
        user = create_test_user(balance=20.0, can_get_alcohol=False)
        cocktails = [
            create_test_cocktail(
                name="Too Expensive",
                price_per_100_ml=10.0,
                amount=300,
                virgin_available=True,
            ),
        ]
        with patch_cfg(PAYMENT_VIRGIN_MULTIPLIER=80):
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is False


class TestFilterCocktailsVolumeConfig:
    """Tests for volume configuration affecting prices."""

    def test_uses_recipe_volume_when_configured(self, patch_cfg: PatchCfgType) -> None:
        """When MAKER_USE_RECIPE_VOLUME is True, should use cocktail's own amount."""
        user = create_test_user(balance=20.0, can_get_alcohol=True)
        # 5.0 / 100 * 300 = 15.0
        cocktails = [create_test_cocktail(price_per_100_ml=5.0, amount=300)]
        with patch_cfg(MAKER_USE_RECIPE_VOLUME=True, MAKER_PREPARE_VOLUME=[150]):
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is True

    def test_uses_lowest_prepare_volume_when_not_using_recipe_volume(self, patch_cfg: PatchCfgType) -> None:
        """When MAKER_USE_RECIPE_VOLUME is False, should use lowest prepare volume."""
        # With lowest volume 150: price = 5.0 / 100 * 150 = 7.5
        user = create_test_user(balance=10.0, can_get_alcohol=True)
        cocktails = [create_test_cocktail(price_per_100_ml=5.0, amount=300)]
        with patch_cfg(MAKER_USE_RECIPE_VOLUME=False, MAKER_PREPARE_VOLUME=[150, 250, 350]):
            result = filter_cocktails_by_user(user, cocktails)
        # With lowest volume of 150, price should be 7.5 which is <= 10.0
        assert len(result) == 1
        assert result[0].is_allowed is True

    def test_cannot_afford_with_recipe_volume_but_can_with_lowest(self, patch_cfg: PatchCfgType) -> None:
        """User cannot afford recipe volume but can afford lowest prepare volume."""
        # Recipe volume 300: price = 5.0 / 100 * 300 = 15.0
        # Lowest volume 150: price = 5.0 / 100 * 150 = 7.5
        user = create_test_user(balance=10.0, can_get_alcohol=True)
        cocktails = [create_test_cocktail(price_per_100_ml=5.0, amount=300)]

        # With recipe volume, cannot afford
        with patch_cfg(MAKER_USE_RECIPE_VOLUME=True, MAKER_PREPARE_VOLUME=[150, 250, 350]):
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is False

        # With lowest prepare volume, can afford
        with patch_cfg(MAKER_USE_RECIPE_VOLUME=False, MAKER_PREPARE_VOLUME=[150, 250, 350]):
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is True

    def test_empty_prepare_volume_uses_recipe_amount(self, patch_cfg: PatchCfgType) -> None:
        """When MAKER_PREPARE_VOLUME is empty, should use recipe amount."""
        user = create_test_user(balance=20.0, can_get_alcohol=True)
        cocktails = [create_test_cocktail(price_per_100_ml=5.0, amount=300)]
        with patch_cfg(MAKER_USE_RECIPE_VOLUME=False, MAKER_PREPARE_VOLUME=[]):
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is True

    def test_unordered_prepare_volume_uses_smallest(self, patch_cfg: PatchCfgType) -> None:
        """When MAKER_PREPARE_VOLUME is unordered, should still use smallest volume."""
        # With smallest volume 200: price = 5.0 / 100 * 200 = 10.0
        # With first element 300: price = 5.0 / 100 * 300 = 15.0
        # User balance 10.0 should only afford the 200ml price
        user = create_test_user(balance=10.0, can_get_alcohol=True)
        cocktails = [create_test_cocktail(price_per_100_ml=5.0, amount=400)]
        # MAKER_PREPARE_VOLUME is unordered with 300 as first element
        with patch_cfg(MAKER_USE_RECIPE_VOLUME=False, MAKER_PREPARE_VOLUME=[300, 200]):
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        # Should be allowed because smallest volume (200) gives price 10.0 == balance
        assert result[0].is_allowed is True


class TestFilterCocktailsPriceRounding:
    """Tests for price rounding behavior."""

    def test_price_rounding_to_nearest_integer(self, patch_cfg: PatchCfgType) -> None:
        """Price rounding with step 1 should round up to nearest integer."""
        # price = 3.33 / 100 * 300 = 9.99, rounded up to 10
        user = create_test_user(balance=10.0, can_get_alcohol=True)
        cocktails = [create_test_cocktail(price_per_100_ml=3.33, amount=300)]
        with patch_cfg(PAYMENT_PRICE_ROUNDING=1):
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is True

    def test_price_rounding_to_quarter(self, patch_cfg: PatchCfgType) -> None:
        """Price rounding with step 0.25 should round up to nearest quarter."""
        # price = 4.0 / 100 * 300 = 12.0, no rounding needed
        # price = 4.1 / 100 * 300 = 12.3, rounded up to 12.5
        user = create_test_user(balance=12.5, can_get_alcohol=True)
        cocktails = [create_test_cocktail(price_per_100_ml=4.1, amount=300)]
        with patch_cfg(PAYMENT_PRICE_ROUNDING=0.25):
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is True

    def test_price_rounding_to_half(self, patch_cfg: PatchCfgType) -> None:
        """Price rounding with step 0.5 should round up to nearest half."""
        # price = 2.9 / 100 * 300 = 8.7, rounded up to 9.0
        user = create_test_user(balance=9.0, can_get_alcohol=True)
        cocktails = [create_test_cocktail(price_per_100_ml=2.9, amount=300)]
        with patch_cfg(PAYMENT_PRICE_ROUNDING=0.5):
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is True

    def test_price_rounding_user_cannot_afford_rounded_price(self, patch_cfg: PatchCfgType) -> None:
        """User cannot afford price after rounding up."""
        # price = 2.9 / 100 * 300 = 8.7, rounded up to 9.0
        user = create_test_user(balance=8.7, can_get_alcohol=True)
        cocktails = [create_test_cocktail(price_per_100_ml=2.9, amount=300)]
        with patch_cfg(PAYMENT_PRICE_ROUNDING=0.5):
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is False


class TestFilterCocktailsEdgeCases:
    """Edge case tests for filter_cocktails_by_user."""

    def test_empty_cocktail_list(self, patch_cfg: PatchCfgType) -> None:
        """Should return empty list when no cocktails provided."""
        user = create_test_user(balance=100.0)
        with patch_cfg():
            result = filter_cocktails_by_user(user, [])
        assert result == []

    def test_zero_balance_user(self, patch_cfg: PatchCfgType) -> None:
        """User with zero balance should have cocktails marked as not allowed."""
        user = create_test_user(balance=0.0, can_get_alcohol=True)
        cocktails = [create_test_cocktail(price_per_100_ml=1.0, amount=100)]
        with patch_cfg():
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is False

    def test_free_cocktail_zero_price(self, patch_cfg: PatchCfgType) -> None:
        """User with zero balance should have free cocktails allowed."""
        user = create_test_user(balance=0.0, can_get_alcohol=True)
        cocktails = [create_test_cocktail(price_per_100_ml=0.0, amount=300)]
        with patch_cfg():
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].is_allowed is True

    def test_virgin_only_flag_not_set_for_alcohol_user(self, patch_cfg: PatchCfgType) -> None:
        """Cocktails should not have only_virgin set for users who can get alcohol."""
        user = create_test_user(balance=100.0, can_get_alcohol=True)
        cocktails = [
            create_test_cocktail(name="Virgin Available", virgin_available=True),
        ]
        with patch_cfg():
            result = filter_cocktails_by_user(user, cocktails)
        assert len(result) == 1
        assert result[0].only_virgin is False
        assert result[0].is_allowed is True

    def test_preserves_cocktail_order(self, patch_cfg: PatchCfgType) -> None:
        """Should preserve the order of cocktails in the result."""
        user = create_test_user(balance=100.0, can_get_alcohol=True)
        cocktails = [
            create_test_cocktail(cocktail_id=3, name="C"),
            create_test_cocktail(cocktail_id=1, name="A"),
            create_test_cocktail(cocktail_id=2, name="B"),
        ]
        with patch_cfg():
            result = filter_cocktails_by_user(user, cocktails)
        assert [c.name for c in result] == ["C", "A", "B"]
        assert all(c.is_allowed for c in result)
