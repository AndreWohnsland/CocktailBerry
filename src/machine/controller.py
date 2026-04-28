from __future__ import annotations

import atexit
import contextlib
from typing import TYPE_CHECKING, Any, Self, TypeGuard

from src.logger_handler import LoggerHandler

# Only needed in v1
with contextlib.suppress(ModuleNotFoundError):
    from PyQt6.QtWidgets import QApplication

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.database_commander import DatabaseCommander
from src.machine.carriage import create_carriage
from src.machine.dispensers import create_dispenser
from src.machine.dispensers.base import BaseDispenser
from src.machine.dispensers.scheduler import DispenserScheduler, PreparationItem
from src.machine.hardware import HardwareContext
from src.machine.leds import LedController
from src.machine.pin_controller import PinController
from src.machine.reverter import Reverter
from src.machine.rfid import RFIDReader, create_rfid
from src.machine.scale import create_scale
from src.models import CocktailStatus, EventType, Ingredient, PreparationResult, PrepareResult
from src.programs.addons.hardware_extensions import HARDWARE_ADDONS

if TYPE_CHECKING:
    from src.machine.scale.base import ScaleInterface
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
        # Stage 1: core hardware + extensions (no dependencies)
        self.hardware = HardwareContext(
            pin_controller=PinController(),
            led_controller=LedController(),
            extra=HARDWARE_ADDONS.create_all(),
        )
        # Stage 2: scale can access pins, leds, extra
        self.hardware.scale = create_scale(cfg.SCALE_CONFIG, self.hardware)
        # Stage 3: carriage can access pins, leds, extra, AND scale
        # Note: referencing (find_reference()) can take seconds and is deliberately deferred —
        # call :meth:`find_carriage_reference` from the caller after the GUI/API is ready,
        # wrapping it in a spinner/progress indicator as appropriate for the version.
        self.hardware.carriage = create_carriage(cfg.CARRIAGE_CONFIG, self.hardware)
        # Stage 4: RFID can access pins, leds, extra, scale, AND carriage
        self.hardware.rfid = create_rfid(cfg.RFID_CONFIG, self.hardware)
        RFIDReader().attach(self.hardware.rfid)
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
        self._run_scheduler(w, items, use_carriage=cfg.CARRIAGE_CONFIG.move_during_cleaning)
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
        self._run_scheduler(w, items, verbose=verbose, use_carriage=True)
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

    def _run_scheduler(
        self,
        w: MainScreen | None,
        items: list[PreparationItem],
        verbose: bool = True,
        use_carriage: bool = False,
    ) -> None:
        """Create a scheduler and run the given items."""
        carriage = self.hardware.carriage if use_carriage else None
        home_position = cfg.CARRIAGE_CONFIG.home_position if carriage is not None else 0
        scheduler = DispenserScheduler(
            cfg.MAKER_SIMULTANEOUSLY_PUMPS,
            verbose=verbose,
            carriage=carriage,
            home_position=home_position,
        )

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
        HARDWARE_ADDONS.cleanup_all()
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
                    recipe_order=ing.recipe_order,
                    ingredient=ing,
                )
            )
        return items

    @property
    def has_scale(self) -> bool:
        """Check if a scale is available and initialized."""
        return self.hardware.scale is not None

    @property
    def has_carriage(self) -> bool:
        """Check if a carriage is available."""
        return self.hardware.carriage is not None

    def find_carriage_reference(self) -> None:
        """Drive the carriage to its reference sensor to establish position.

        Kept separate from :meth:`init_machine` because referencing can take
        several seconds and would block the main GUI / API startup. Callers
        decide when to run it (e.g. after the v1 GUI is visible — wrap in a
        spinner — or at the end of the v2 lifespan). Safe to call again at
        runtime. No-op if no carriage is configured.
        """
        if self.hardware.carriage is None:
            return
        self.hardware.carriage.find_reference()

    def _has_scale(self, scale: ScaleInterface | None) -> TypeGuard[ScaleInterface]:
        return scale is not None

    def _assure_scale(self) -> ScaleInterface:
        scale = self.hardware.scale
        if not self._has_scale(scale):
            raise RuntimeError("No scale available")
        return scale

    def scale_tare(self, samples: int = 3) -> int:
        """Tare (zero) the scale.

        Returns the raw offset value captured during tare.
        Raises RuntimeError if no scale is available.
        """
        return self._assure_scale().tare(samples)

    def scale_read_grams(self) -> float:
        """Read the calibrated weight in grams from the scale. Raises RuntimeError if no scale."""
        return self._assure_scale().read_grams()

    def is_glass_present(self) -> bool:
        """Return whether a glass is present on the scale.

        Returns True if no scale is configured, minimal_weight is 0 (feature disabled),
        or the gross weight reading (plus tolerance) meets the minimal_weight threshold.
        """
        _GLASS_WEIGHT_TOLERANCE = 1.0
        if self.hardware.scale is None:
            return True
        minimal_weight = cfg.SCALE_CONFIG.minimal_weight
        if minimal_weight == 0:
            return True
        return self.hardware.scale.get_gross_grams() + _GLASS_WEIGHT_TOLERANCE >= minimal_weight

    def scale_calibrate(self, known_weight_grams: float, zero_raw_offset: int, samples: int = 20) -> float:
        """Calibrate the scale using a known reference weight.

        Reads the raw ADC value (after tare) and computes the calibration factor.
        If zero_raw_offset is provided, it is also persisted to the scale and config.
        Both values are synced to config in one write. Returns the new calibration factor.
        Raises RuntimeError if no scale or if the reading is invalid.
        """
        scale = self._assure_scale()
        if known_weight_grams <= 0:
            raise ValueError("Known weight must be positive")
        factor = round(scale.calibrate_with_known_weight(known_weight_grams, zero_raw_offset, samples), 1)
        cfg.SCALE_CONFIG.calibration_factor = factor
        cfg.SCALE_CONFIG.zero_raw_offset = zero_raw_offset
        cfg.sync_config_to_file()
        return factor

    def default_led(self) -> None:
        """Turn the LED on."""
        self.hardware.led_controller.default_led()


def _header_print(msg: str) -> None:
    """Format the message with dashes around."""
    _logger.info(f"{' ' + msg + ' ':-^80}")


MACHINE = MachineController()
