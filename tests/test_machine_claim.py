"""The machine must never run two preparations at once and must not stay busy after a crash."""

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from src.config.config_manager import shared
from src.machine.controller import MachineController
from src.models import Cocktail, CocktailStatus, Ingredient, PrepareResult
from src.tabs import maker


@pytest.fixture(autouse=True)
def _idle_machine() -> Iterator[None]:
    shared.cocktail_status = CocktailStatus()
    yield
    shared.cocktail_status = CocktailStatus()


def _cocktail() -> Cocktail:
    gin = Ingredient(
        id=1,
        name="Gin",
        alcohol=40,
        bottle_volume=1000,
        fill_level=1000,
        hand=False,
        pump_speed=100,
        amount=40,
        bottle=1,
    )
    return Cocktail(
        id=1,
        name="Test",
        alcohol=40,
        amount=40,
        enabled=True,
        price_per_100_ml=0,
        virgin_available=False,
        ingredients=[gin],
    )


@pytest.mark.parametrize("first", [PrepareResult.IN_PROGRESS, PrepareResult.WAITING_FOR_PAYMENT])
def test_second_claim_is_refused_while_busy(first: PrepareResult):
    assert maker.claim_machine(first)
    assert not maker.claim_machine(PrepareResult.IN_PROGRESS)
    assert shared.cocktail_status.status == first


@pytest.mark.parametrize("done", [PrepareResult.FINISHED, PrepareResult.CANCELED])
def test_claim_is_granted_after_preparation_ended(done: PrepareResult):
    shared.cocktail_status = CocktailStatus(status=done)
    assert maker.claim_machine(PrepareResult.IN_PROGRESS)


def test_crashed_preparation_frees_the_machine():
    mc = MagicMock()
    mc.make_cocktail.side_effect = RuntimeError("pump driver died")
    with patch("src.tabs.maker.MachineController", return_value=mc), pytest.raises(RuntimeError):
        maker.prepare_cocktail(_cocktail())
    assert shared.cocktail_status.status == PrepareResult.CANCELED
    assert maker.claim_machine(PrepareResult.IN_PROGRESS)


def test_scheduler_crash_stops_all_pumps():
    mc = MachineController()
    dispenser = MagicMock()
    hardware = MagicMock()
    with (
        patch.object(mc, "dispensers", {1: dispenser}),
        patch.object(mc, "hardware", hardware, create=True),
        patch.object(mc, "_build_preparation_items", return_value=[]),
        patch.object(mc, "_run_scheduler", side_effect=RuntimeError("scheduler died")),
        pytest.raises(RuntimeError),
    ):
        mc.make_cocktail(None, [], recipe="Test")
    dispenser.stop.assert_called_once()
    hardware.led_controller.preparation_end.assert_called_once()
