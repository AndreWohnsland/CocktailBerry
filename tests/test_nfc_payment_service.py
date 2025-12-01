from __future__ import annotations

from unittest.mock import MagicMock, patch
import time

import pytest

from src.models import Cocktail
from src.programs.nfc_payment_service import CocktailBooking, NFCPaymentService, User


def create_test_user(
    uid: str = "TEST123",
    balance: float = 10.0,
    can_get_alcohol: bool = True,
) -> User:
    """Create a test user with specified attributes."""
    return User(uid=uid, balance=balance, can_get_alcohol=can_get_alcohol)


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


@pytest.fixture
def nfc_service():
    """Create a fresh NFCPaymentService instance for testing."""
    # Reset the singleton instance before each test
    NFCPaymentService._instance = None
    with patch("src.programs.nfc_payment_service.RFIDReader"):
        service = NFCPaymentService()
        yield service
        # Clean up after test - clear callbacks
        service._user_callbacks.clear()


class TestNFCPaymentServiceCallbacks:
    """Tests for NFC payment service callback functionality."""

    def test_add_callback(self, nfc_service: NFCPaymentService) -> None:
        """Test that add_callback adds a callback."""
        callback = MagicMock()
        nfc_service.add_callback(callback)
        
        assert callback in nfc_service._user_callbacks
        assert len(nfc_service._user_callbacks) == 1

    def test_add_multiple_callbacks(self, nfc_service: NFCPaymentService) -> None:
        """Test that multiple callbacks can be added."""
        callback1 = MagicMock()
        callback2 = MagicMock()
        
        nfc_service.add_callback(callback1)
        nfc_service.add_callback(callback2)
        
        assert callback1 in nfc_service._user_callbacks
        assert callback2 in nfc_service._user_callbacks
        assert len(nfc_service._user_callbacks) == 2

    def test_add_callback_prevents_duplicates(self, nfc_service: NFCPaymentService) -> None:
        """Test that the same callback is not added twice."""
        callback = MagicMock()
        
        nfc_service.add_callback(callback)
        nfc_service.add_callback(callback)
        
        # Should only have one instance of the callback
        assert len(nfc_service._user_callbacks) == 1

    def test_remove_callback(self, nfc_service: NFCPaymentService) -> None:
        """Test that remove_callback removes a callback."""
        callback = MagicMock()
        nfc_service.add_callback(callback)
        nfc_service.remove_callback(callback)
        
        assert callback not in nfc_service._user_callbacks
        assert len(nfc_service._user_callbacks) == 0

    def test_remove_callback_that_doesnt_exist(self, nfc_service: NFCPaymentService) -> None:
        """Test that removing a non-existent callback is safe."""
        callback = MagicMock()
        # Should not raise any exception
        nfc_service.remove_callback(callback)
        assert len(nfc_service._user_callbacks) == 0


class TestNFCPaymentServiceUserDetection:
    """Tests for user detection via NFC."""

    def test_handle_nfc_read_with_valid_user(self, nfc_service: NFCPaymentService) -> None:
        """Test that valid NFC read invokes callback with user."""
        callback = MagicMock()
        nfc_service._user_callbacks = [callback]
        
        # Simulate NFC read
        nfc_service._handle_nfc_read("", "CAD3B515")
        
        # Callback should be invoked with user and uid
        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] is not None  # user
        assert args[0].uid == "CAD3B515"
        assert args[1] == "CAD3B515"  # uid

    def test_handle_nfc_read_with_invalid_user(self, nfc_service: NFCPaymentService) -> None:
        """Test that invalid NFC read invokes callback with None user."""
        callback = MagicMock()
        nfc_service._user_callbacks = [callback]
        
        # Simulate NFC read with unknown ID
        nfc_service._handle_nfc_read("", "UNKNOWN_ID")
        
        # Callback should be invoked with None user
        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] is None  # user
        assert args[1] == "UNKNOWN_ID"  # uid

    def test_handle_nfc_read_with_multiple_callbacks(self, nfc_service: NFCPaymentService) -> None:
        """Test that NFC read invokes all registered callbacks."""
        callback1 = MagicMock()
        callback2 = MagicMock()
        nfc_service._user_callbacks = [callback1, callback2]
        
        # Simulate NFC read
        nfc_service._handle_nfc_read("", "CAD3B515")
        
        # Both callbacks should be invoked
        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_handle_nfc_read_without_callback(self, nfc_service: NFCPaymentService) -> None:
        """Test that NFC read without callback doesn't crash."""
        nfc_service._user_callbacks = []
        
        # Should not raise any exception
        nfc_service._handle_nfc_read("", "CAD3B515")
        assert nfc_service.uid == "CAD3B515"


class TestNFCPaymentServiceBooking:
    """Tests for cocktail booking functionality."""

    @patch("src.programs.nfc_payment_service.cfg.PAYMENT_PRICE_ROUNDING", 1)
    def test_book_cocktail_for_user_success(self, nfc_service: NFCPaymentService) -> None:
        """Test successful cocktail booking."""
        user = create_test_user(balance=50.0, can_get_alcohol=True)
        cocktail = create_test_cocktail(price_per_100_ml=5.0, amount=300)
        
        booking = nfc_service.book_cocktail_for_user(user, cocktail)
        
        assert booking.result == CocktailBooking.Result.SUCCESS
        assert user.balance == 35.0  # 50 - 15 (5.0 * 3)

    @patch("src.programs.nfc_payment_service.cfg.PAYMENT_PRICE_ROUNDING", 1)
    def test_book_cocktail_for_user_insufficient_balance(self, nfc_service: NFCPaymentService) -> None:
        """Test booking with insufficient balance."""
        user = create_test_user(balance=5.0, can_get_alcohol=True)
        cocktail = create_test_cocktail(price_per_100_ml=5.0, amount=300)
        
        booking = nfc_service.book_cocktail_for_user(user, cocktail)
        
        assert booking.result == CocktailBooking.Result.INSUFFICIENT_BALANCE
        assert user.balance == 5.0  # Balance unchanged

    @patch("src.programs.nfc_payment_service.cfg.PAYMENT_PRICE_ROUNDING", 1)
    def test_book_cocktail_for_user_no_alcohol_permission(self, nfc_service: NFCPaymentService) -> None:
        """Test booking without alcohol permission."""
        user = create_test_user(balance=50.0, can_get_alcohol=False)
        cocktail = create_test_cocktail(price_per_100_ml=5.0, amount=300)
        
        booking = nfc_service.book_cocktail_for_user(user, cocktail)
        
        assert booking.result == CocktailBooking.Result.NOT_ALLOWED_ALCOHOL
        assert user.balance == 50.0  # Balance unchanged

    @patch("src.programs.nfc_payment_service.cfg.PAYMENT_PRICE_ROUNDING", 1)
    def test_book_cocktail_for_none_user(self, nfc_service: NFCPaymentService) -> None:
        """Test booking with no user."""
        cocktail = create_test_cocktail(price_per_100_ml=5.0, amount=300)
        
        booking = nfc_service.book_cocktail_for_user(None, cocktail)
        
        assert booking.result == CocktailBooking.Result.NO_USER


class TestNFCPaymentServiceUserDatabase:
    """Tests for user database functionality."""

    def test_get_user_for_id_existing_user(self, nfc_service: NFCPaymentService) -> None:
        """Test retrieving an existing user."""
        user = nfc_service.get_user_for_id("CAD3B515")
        
        assert user is not None
        assert user.uid == "CAD3B515"
        assert user.balance == 5.0
        assert user.can_get_alcohol is False

    def test_get_user_for_id_nonexistent_user(self, nfc_service: NFCPaymentService) -> None:
        """Test retrieving a non-existent user."""
        user = nfc_service.get_user_for_id("UNKNOWN_ID")
        
        assert user is None
