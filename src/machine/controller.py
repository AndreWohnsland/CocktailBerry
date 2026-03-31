from __future__ import annotations

import atexit
import contextlib
from typing import TYPE_CHECKING, Any, Self

from src.logger_handler import LoggerHandler

# Only needed in v1
with contextlib.suppress(ModuleNotFoundError):
    from PyQt6.QtWidgets import QApplication

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.database_commander import DatabaseCommander
from src.machine.dispensers import create_dispenser
from src.machine.dispensers.base import BaseDispenser
from src.machine.dispensers.scheduler import DispenserScheduler, PreparationItem
from src.machine.hardware import HardwareContext
from src.machine.leds import LedController
from src.machine.pin_controller import PinController
from src.machine.reverter import Reverter
from src.models import CocktailStatus, EventType, Ingredient, PreparationResult, PrepareResult

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

_logger = LoggerHandler("MachineController")


class MachineController:
    """Controller Class for all Machine related Pin routines."""

    _instance = None

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self.dispensers: dict[int, BaseDispenser] = {}
        self._initialized = True

    def init_machine(self) -> None:
        self.hardware = HardwareContext(
            pin_controller=PinController(),
            led_controller=LedController(),
        )
        self.reverter = Reverter(cfg.MAKER_PUMP_REVERSION_CONFIG)
        self.set_up_pumps()
        self.default_led()
        atexit.register(self.cleanup)

    def clean_pumps(self, w: MainScreen | None, revert_pumps: bool = False) -> None:
        """Clean the pumps for the defined time in the config.

        Activates all pumps for the given time.
        """
        shared.cocktail_status = CocktailStatus(0, status=PrepareResult.IN_PROGRESS)
        items = self._build_clean_items()
        if w is not None:
            w.open_progression_window("Cleaning")
        _header_print("Start Cleaning")
        if revert_pumps:
            self.reverter.revert_on()
        self._run_scheduler(w, items)
        if revert_pumps:
            self.reverter.revert_off()
        _header_print("Done Cleaning")
        if w is not None:
            w.close_progression_window()
        shared.cocktail_status.status = PrepareResult.FINISHED
        DatabaseCommander().save_event(EventType.CLEANING)

    def make_cocktail(
        self,
        w: MainScreen | None,
        ingredient_list: list[Ingredient],
        recipe: str = "",
        is_cocktail: bool = True,
        verbose: bool = True,
        finish_message: str = "",
    ) -> PreparationResult:
        """RPI Logic to prepare the cocktail.

        Calculates needed time for each slot according to data and config.
        Updates Progressbar status. Returns data for DB updates.
        """
        shared.cocktail_status = CocktailStatus(0, status=PrepareResult.IN_PROGRESS)
        if w is not None:
            w.open_progression_window(recipe)
        items = self._build_preparation_items(ingredient_list)
        _header_print(f"Starting {recipe}")
        if is_cocktail:
            self.hardware.led_controller.preparation_start()
        self._run_scheduler(w, items, verbose=verbose)
        if is_cocktail:
            self.hardware.led_controller.preparation_end()
        # Write consumption back to ingredient objects
        for item in items:
            if item.ingredient is not None:
                item.ingredient.consumption = item.consumption
        machine_ingredients = [item.ingredient for item in items if item.ingredient is not None]
        _logger.info(f"Total calculated consumption: {[round(i.consumption) for i in machine_ingredients]}")
        _header_print(f"Finished {recipe}")
        if w is not None:
            w.close_progression_window()
        if shared.cocktail_status.status != PrepareResult.CANCELED:
            shared.cocktail_status.status = PrepareResult.FINISHED
            shared.cocktail_status.message = finish_message
        return PreparationResult(
            ingredients=machine_ingredients,
        )

    def _run_scheduler(self, w: MainScreen | None, items: list[PreparationItem], verbose: bool = True) -> None:
        """Create a scheduler and run the given items."""
        scheduler = DispenserScheduler(cfg.MAKER_SIMULTANEOUSLY_PUMPS, verbose=verbose)

        def on_progress(progress: int, consumption: list[float]) -> None:
            shared.cocktail_status.progress = progress
            if w is not None:
                w.change_progression_window(progress)
                QApplication.processEvents()

        def is_cancelled() -> bool:
            return shared.cocktail_status.status == PrepareResult.CANCELED

        scheduler.run(items, on_progress, is_cancelled)

    def set_up_pumps(self) -> None:
        """Initialize dispensers for all configured pump slots."""
        used_config = cfg.PUMP_CONFIG[: cfg.MAKER_NUMBER_BOTTLES]
        self.dispensers = {}
        for slot, pump_cfg in enumerate(used_config, start=1):
            dispenser = create_dispenser(slot, pump_cfg, self.hardware)
            dispenser.setup()
            self.dispensers[slot] = dispenser
        _logger.info(f"<i> Initialized {len(self.dispensers)} dispensers")
        self.reverter.initialize_pin()

    def close_all_pumps(self) -> None:
        """Stop all active dispensers."""
        for dispenser in self.dispensers.values():
            dispenser.stop()

    def cleanup(self) -> None:
        """Cleanup for shutdown the machine."""
        self.close_all_pumps()
        self.hardware.cleanup()

    def _build_clean_items(self) -> list[PreparationItem]:
        """Build cleaning items for all active dispensers."""
        items = []
        for dispenser in self.dispensers.values():
            amount_ml = dispenser.volume_flow * cfg.MAKER_CLEAN_TIME
            items.append(
                PreparationItem(
                    dispenser=dispenser,
                    amount_ml=amount_ml,
                    pump_speed=100,
                    estimated_time=float(cfg.MAKER_CLEAN_TIME),
                )
            )
        return items

    def _build_preparation_items(self, ingredient_list: list[Ingredient]) -> list[PreparationItem]:
        """Build the preparation items from ingredients and dispensers."""
        items = []
        for ing in ingredient_list:
            if ing.bottle is None:
                continue
            dispenser = self.dispensers[ing.bottle]
            items.append(
                PreparationItem(
                    dispenser=dispenser,
                    amount_ml=float(ing.amount),
                    pump_speed=ing.pump_speed,
                    estimated_time=dispenser.estimated_time(ing.amount, ing.pump_speed),
                    recipe_order=ing.recipe_order,
                    ingredient=ing,
                )
            )
        return items

    def default_led(self) -> None:
        """Turn the LED on."""
        self.hardware.led_controller.default_led()


def _header_print(msg: str) -> None:
    """Format the message with dashes around."""
    _logger.info(f"{' ' + msg + ' ':-^80}")


MACHINE = MachineController()
