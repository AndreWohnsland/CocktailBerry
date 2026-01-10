"""Tests for UserLookup and UserLookupResult classes."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from src.programs.nfc_payment_service import User, UserLookup, UserLookupResult


def create_test_user(
    uid: str = "TEST123",
    balance: float = 10.0,
    is_adult: bool = True,
) -> User:
    """Create a test user with specified attributes."""
    return User(nfc_id=uid, balance=balance, is_adult=is_adult)


class TestUserLookupResult:
    """Tests for UserLookupResult enum."""

    def test_user_found_value(self) -> None:
        """Test USER_FOUND has correct value."""
        assert UserLookupResult.USER_FOUND == "user_found"

    def test_user_not_found_value(self) -> None:
        """Test USER_NOT_FOUND has correct value."""
        assert UserLookupResult.USER_NOT_FOUND == "user_not_found"

    def test_service_unavailable_value(self) -> None:
        """Test SERVICE_UNAVAILABLE has correct value."""
        assert UserLookupResult.SERVICE_UNAVAILABLE == "service_unavailable"

    def test_user_removed_value(self) -> None:
        """Test USER_REMOVED has correct value."""
        assert UserLookupResult.USER_REMOVED == "user_removed"


class TestUserLookupFactoryMethods:
    """Tests for UserLookup factory methods."""

    def test_found_creates_lookup_with_user(self) -> None:
        """Test found() creates a UserLookup with user and USER_FOUND result."""
        user = create_test_user()
        lookup = UserLookup.found(user)

        assert lookup.user == user
        assert lookup.result == UserLookupResult.USER_FOUND

    def test_not_found_creates_lookup_without_user(self) -> None:
        """Test not_found() creates a UserLookup with None user and USER_NOT_FOUND result."""
        lookup = UserLookup.not_found()

        assert lookup.user is None
        assert lookup.result == UserLookupResult.USER_NOT_FOUND

    def test_service_unavailable_creates_lookup_without_user(self) -> None:
        """Test service_unavailable() creates a UserLookup with None user and SERVICE_UNAVAILABLE result."""
        lookup = UserLookup.service_unavailable()

        assert lookup.user is None
        assert lookup.result == UserLookupResult.SERVICE_UNAVAILABLE

    def test_removed_creates_lookup_without_user(self) -> None:
        """Test removed() creates a UserLookup with None user and USER_REMOVED result."""
        lookup = UserLookup.removed()

        assert lookup.user is None
        assert lookup.result == UserLookupResult.USER_REMOVED


class TestUserLookupBehavior:
    """Tests for UserLookup behavior and usage patterns."""

    def test_user_lookup_is_dataclass(self) -> None:
        """Test UserLookup can be instantiated directly."""
        user = create_test_user()
        lookup = UserLookup(user=user, result=UserLookupResult.USER_FOUND)

        assert lookup.user == user
        assert lookup.result == UserLookupResult.USER_FOUND

    def test_user_lookup_with_none_user(self) -> None:
        """Test UserLookup can have None user."""
        lookup = UserLookup(user=None, result=UserLookupResult.USER_NOT_FOUND)

        assert lookup.user is None
        assert lookup.result == UserLookupResult.USER_NOT_FOUND

    def test_user_found_has_user_data(self) -> None:
        """Test that USER_FOUND lookup contains valid user data."""
        user = create_test_user(uid="NFC123", balance=50.0, is_adult=False)
        lookup = UserLookup.found(user)

        assert lookup.user is not None
        assert lookup.user.nfc_id == "NFC123"
        assert lookup.user.balance == 50.0
        assert lookup.user.is_adult is False

    @pytest.mark.parametrize(
        "factory_method,expected_result",
        [
            (UserLookup.not_found, UserLookupResult.USER_NOT_FOUND),
            (UserLookup.service_unavailable, UserLookupResult.SERVICE_UNAVAILABLE),
            (UserLookup.removed, UserLookupResult.USER_REMOVED),
        ],
    )
    def test_error_states_have_no_user(
        self,
        factory_method: Callable[[], UserLookup],
        expected_result: UserLookupResult,
    ) -> None:
        """Test that error state lookups have no user."""
        lookup = factory_method()

        assert lookup.user is None
        assert lookup.result == expected_result
