"""A card that is booked next to a cancel has already paid, so the cocktail must still be made."""

import asyncio
import threading
import time
from collections.abc import Callable

import pytest

from src.api.internal import nfc_payment
from src.api.internal.nfc_payment import NFCPaymentHandler
from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.models import Cocktail, CocktailStatus, PrepareResult
from src.service.booking import CocktailBooking
from src.service.nfc_payment_service import NFCPaymentService, User, UserLookup

_COCKTAIL = Cocktail(
    id=1,
    name="Test",
    alcohol=10,
    amount=300,
    enabled=True,
    price_per_100_ml=5.0,
    virgin_available=False,
    ingredients=[],
)
_USER = UserLookup.found(User(nfc_id="CARD", balance=20.0, is_adult=True))


@pytest.fixture
def prepared(monkeypatch: pytest.MonkeyPatch) -> list[Cocktail]:
    made: list[Cocktail] = []

    def fake_prepare(cocktail: Cocktail, additional_message: str) -> None:
        made.append(cocktail)

    monkeypatch.setattr(nfc_payment.maker, "prepare_cocktail", fake_prepare)
    return made


@pytest.fixture
def handler(monkeypatch: pytest.MonkeyPatch) -> NFCPaymentHandler:
    monkeypatch.setattr(NFCPaymentService, "_instance", None)
    monkeypatch.setattr(shared, "cocktail_status", CocktailStatus(status=PrepareResult.WAITING_FOR_PAYMENT))
    monkeypatch.setattr(cfg, "PAYMENT_TIMEOUT_S", 0.2)
    monkeypatch.setattr(cfg, "PAYMENT_AUTO_LOGOUT_TIME_S", 0)
    monkeypatch.setattr(cfg, "PAYMENT_LOGOUT_AFTER_PREPARATION", False)
    handler = NFCPaymentHandler()
    monkeypatch.setattr(handler.nfc_service, "get_user_for_id", lambda _id: _USER)
    monkeypatch.setattr(
        handler.nfc_service, "book_cocktail_for_user", lambda lookup, cocktail: CocktailBooking.successful_booking(15.0)
    )
    return handler


def _run(handler: NFCPaymentHandler, *during_wait: Callable[[], object]) -> None:
    async def flow() -> None:
        task = asyncio.create_task(handler.start_payment_flow(_COCKTAIL))
        await asyncio.sleep(0)  # let the flow register its card callback
        for action in during_wait:
            action()
        await task

    asyncio.run(flow())


def test_booking_landing_with_cancel_still_prepares(handler: NFCPaymentHandler, prepared: list[Cocktail]) -> None:
    _run(handler, lambda: handler.nfc_service._handle_nfc_read("", "CARD"), handler.cancel_payment)
    assert prepared == [_COCKTAIL]


def test_cancel_during_booking_request_waits_for_the_debit(
    handler: NFCPaymentHandler, prepared: list[Cocktail], monkeypatch: pytest.MonkeyPatch
) -> None:
    def slow_booking(lookup: UserLookup, cocktail: Cocktail) -> CocktailBooking:
        handler.cancel_payment()  # the cancel lands while the payment service request is still running
        time.sleep(0.3)
        return CocktailBooking.successful_booking(15.0)

    monkeypatch.setattr(handler.nfc_service, "book_cocktail_for_user", slow_booking)
    _run(handler, lambda: threading.Thread(target=handler.nfc_service._handle_nfc_read, args=("", "CARD")).start())
    assert prepared == [_COCKTAIL]


def test_cancel_without_card_prepares_nothing(handler: NFCPaymentHandler, prepared: list[Cocktail]) -> None:
    _run(handler, handler.cancel_payment)
    assert prepared == []
    assert shared.cocktail_status.status == PrepareResult.CANCELED
    assert shared.cocktail_status.message == CocktailBooking.canceled().message


def test_timeout_without_card_prepares_nothing(handler: NFCPaymentHandler, prepared: list[Cocktail]) -> None:
    _run(handler)
    assert prepared == []
    assert shared.cocktail_status.status == PrepareResult.CANCELED
