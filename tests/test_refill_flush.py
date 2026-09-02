import asyncio
from typing import cast

import pytest
from fastapi import BackgroundTasks

from src.api.routers.bottles import refill_bottle
from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.database_commander import DatabaseCommander
from src.machine.controller import MachineController
from src.models import Ingredient, PrepareResult


@pytest.fixture
def _refill_setup(monkeypatch: pytest.MonkeyPatch, db_commander: DatabaseCommander) -> None:
    monkeypatch.setattr("src.api.routers.bottles.DatabaseCommander", lambda: db_commander)
    # bottle 1 holds an ingredient (White Rum) and gets a tube volume, so a flush is possible
    monkeypatch.setattr(cfg.PUMP_CONFIG[0], "tube_volume", 20)
    # other tests may leave a cocktail in progress in the shared state
    monkeypatch.setattr(shared.cocktail_status, "status", PrepareResult.FINISHED)


@pytest.mark.usefixtures("_refill_setup")
def test_refill_flushes_tubes_by_default() -> None:
    background_tasks = BackgroundTasks()
    asyncio.run(refill_bottle([1], background_tasks))
    assert len(background_tasks.tasks) == 1
    func, args = background_tasks.tasks[0].func, background_tasks.tasks[0].args
    assert func == MachineController().make_cocktail
    ingredients = cast("list[Ingredient]", args[1])
    assert [ing.amount for ing in ingredients] == [20]


@pytest.mark.usefixtures("_refill_setup")
def test_refill_skips_flush_when_disabled() -> None:
    background_tasks = BackgroundTasks()
    asyncio.run(refill_bottle([1], background_tasks, flush_tubes=False))
    assert background_tasks.tasks == []
