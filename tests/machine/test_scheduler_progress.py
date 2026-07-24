"""Progress emitted by the scheduler must never decrease or go negative.

Lifting the glass off the scale mid-preparation makes the raw reading (and thus
item consumption) drop far below zero; the displayed progress must hold its
high-water mark instead of flickering back or showing negative values.
"""

from __future__ import annotations

from typing import cast

from src.machine.dispensers.base import BaseDispenser
from src.machine.dispensers.scheduler import DispenserScheduler, PreparationItem


def _item(amount_ml: float) -> PreparationItem:
    # progress math never touches the dispenser, so None stands in for it
    dispenser = cast("BaseDispenser", None)
    return PreparationItem(dispenser=dispenser, amount_ml=amount_ml, pump_speed=100, estimated_time=1.0)


def test_progress_is_monotonic_and_never_negative():
    scheduler = DispenserScheduler(max_concurrent=2)
    item = _item(100)
    emitted: list[int] = []
    # simulated scale readings: pour, glass lifted (negative), put back, finish
    for consumption in [-5.0, 30.0, 60.0, -180.0, 20.0, 70.0, 100.0]:
        item.consumption = consumption
        scheduler._emit_progress([item], emitted.append)
    assert emitted == [0, 30, 60, 60, 60, 70, 100]
