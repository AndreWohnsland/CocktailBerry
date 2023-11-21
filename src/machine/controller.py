from __future__ import annotations
from dataclasses import dataclass
import time
import atexit
from typing import List, Union, TYPE_CHECKING
from PyQt5.QtWidgets import qApp


from src.config_manager import shared, CONFIG as cfg
from src.models import Ingredient
from src.machine.generic_board import GenericController
from src.machine.interface import PinController
from src.machine.raspberry import RpiController
from src.machine.leds import LedController
from src.machine.reverter import Reverter
from src.utils import time_print

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


@dataclass
class _PreparationData:
    pin: int
    volume_flow: Union[int, float]
    flow_time: float
    consumption: float = 0.0
    closed: bool = False
    recipe_order: int = 1


class MachineController():
    """Controller Class for all Machine related Pin routines """

    def __init__(self):
        super().__init__()
        self.pin_controller = self._chose_controller()
        self._led_controller = LedController(self.pin_controller)
        self._reverter = Reverter(self.pin_controller)

    def _chose_controller(self) -> PinController:
        """Selects the controller class for the Pin"""
        if cfg.MAKER_BOARD == "RPI":
            return RpiController(cfg.MAKER_PINS_INVERTED)
        # In case none is found, fall back to generic using python-periphery
        return GenericController(cfg.MAKER_PINS_INVERTED)

    def clean_pumps(self, w: MainScreen, revert_pumps: bool = False):
        """Clean the pumps for the defined time in the config.
        Activates all pumps for the given time.
        """
        prep_data = _build_clean_data()
        w.open_progression_window("Cleaning")
        _header_print("Start Cleaning")
        if revert_pumps:
            self._reverter.revert_on()
        self._start_preparation(w, prep_data, False)
        if revert_pumps:
            self._reverter.revert_off()
        _header_print("Done Cleaning")
        w.close_progression_window()

    def make_cocktail(
        self,
        w: Union[MainScreen, None],
        ingredient_list: List[Ingredient],
        recipe="",
        is_cocktail=True,
        verbose=True,
    ):
        """RPI Logic to prepare the cocktail.
        Calculates needed time for each slot according to data and config.
        Updates Progressbar status. Returns data for DB updates.

        Args:
            w (QtMainWindow): MainWindow Object
            bottle_list (List[int]): Number of bottles to be used
            volume_list (List[float]): Corresponding Volume needed of bottles
            recipe (str, optional): Option to change the display text of Progress Screen. Defaults to "".
            is_cocktail (bool, optional): If the preparation is a cocktail. Default to True.

        Returns:
            tuple(List[int], float, float): Consumption of each bottle, taken time, max needed time
        """
        # Only show team dialog if it is enabled
        if cfg.TEAMS_ACTIVE and is_cocktail and w is not None:
            w.open_team_window()
        shared.cocktail_started = True
        if w is not None:
            w.open_progression_window(recipe)
        prep_data = _build_preparation_data(ingredient_list)
        _header_print(f"Starting {recipe}")
        if is_cocktail:
            self._led_controller.preparation_start()
        current_time, max_time = self._start_preparation(w, prep_data, verbose)
        if is_cocktail:
            self._led_controller.preparation_end()
        consumption = [round(x.consumption) for x in prep_data]
        time_print(f"Total calculated consumption: {consumption}")
        _header_print(f"Finished {recipe}")
        if w is not None:
            w.close_progression_window()
        shared.cocktail_started = False
        return consumption, current_time, max_time

    def _start_preparation(
        self,
        w: Union[MainScreen, None],
        prep_data: list[_PreparationData],
        verbose: bool = True
    ):
        """Prepares the volumes of the given data"""
        shared.make_cocktail = True
        current_time = 0.0
        # need to cut data into chunks
        chunk = cfg.MAKER_SIMULTANEOUSLY_PUMPS
        # also take the recipe order in consideration
        # first separate the preparation data into a list of lists,
        # where each list contains the data for one recipe order
        unique_orders = list({x.recipe_order for x in prep_data})
        # sort to ensure lowest order is first
        unique_orders.sort()
        chunked_preparation: list[list[_PreparationData]] = []
        for number in unique_orders:
            # get all the same order number
            order_chunk = [x for x in prep_data if x.recipe_order == number]
            # split the chunk again, if the size exceeds the chunk size
            chunked_preparation.extend(
                [order_chunk[i:i + chunk] for i in range(0, len(order_chunk), chunk)]
            )
        chunk_max = [max(x.flow_time for x in y) for y in chunked_preparation]
        max_time = round(sum(chunk_max), 2)
        # Iterate over each chunk
        for section in chunked_preparation:
            # interrupt loop if user interrupt cocktail
            if not shared.make_cocktail:
                break
            # Getting values for the section
            section_time = 0.0
            section_max = max(x.flow_time for x in section)
            pins = [x.pin for x in section]
            progress = _generate_progress(current_time, max_time)
            self._start_pumps(pins, progress)
            # iterate over each prep data
            while section_time < section_max and shared.make_cocktail:
                self._process_preparation_section(current_time, max_time, section, section_time)
                # Adjust needed data
                if verbose:
                    _consumption_print([x.consumption for x in prep_data], current_time, max_time)
                current_time = round(current_time + cfg.MAKER_SLEEP_TIME, 2)
                section_time = round(section_time + cfg.MAKER_SLEEP_TIME, 2)
                time.sleep(cfg.MAKER_SLEEP_TIME)
                if w is not None:
                    progress = int(current_time / max_time * 100)
                    w.change_progression_window(progress)
                qApp.processEvents()
            progress = _generate_progress(current_time, max_time)
            self._stop_pumps(pins, progress)
        return current_time, max_time

    def _process_preparation_section(
        self,
        current_time: float,
        max_time: float,
        section: list[_PreparationData],
        section_time: float,
    ):
        """Iterate over the data in each section and control pumps accordingly"""
        for data in section:
            if data.flow_time > section_time:
                data.consumption += data.volume_flow * cfg.MAKER_SLEEP_TIME
            elif not data.closed:
                progress = _generate_progress(current_time, max_time)
                self._stop_pumps([data.pin], progress)
                data.closed = True

    def set_up_pumps(self):
        """Gets all used pins, prints pins and uses controller class to set up"""
        active_pins = cfg.PUMP_PINS[: cfg.MAKER_NUMBER_BOTTLES]
        time_print(f"Initializing Pins: {active_pins}")
        self.pin_controller.initialize_pin_list(active_pins)
        self._reverter.initialize_pin()
        atexit.register(self.cleanup)

    def _start_pumps(self, pin_list: List[int], print_prefix: str = ""):
        """Informs and opens all given pins"""
        time_print(f"{print_prefix}Opening Pins: {pin_list}")
        self.pin_controller.activate_pin_list(pin_list)

    def close_all_pumps(self):
        """Close all pins connected to the pumps"""
        active_pins = cfg.PUMP_PINS[: cfg.MAKER_NUMBER_BOTTLES]
        self._stop_pumps(active_pins)

    def cleanup(self):
        """Cleanup for shutdown the machine"""
        self.close_all_pumps()
        self.pin_controller.cleanup_pin_list()

    def _stop_pumps(self, pin_list: List[int], print_prefix: str = ""):
        """Informs and closes all given pins"""
        time_print(f"{print_prefix}Closing Pins: {pin_list}")
        self.pin_controller.close_pin_list(pin_list)


def _build_preparation_data(
    ingredient_list: List[Ingredient],
) -> list[_PreparationData]:
    """Builds the data needed for machine preparation"""
    # build prep data for each ingredient
    prep_data = []
    for ing in ingredient_list:
        if ing.bottle is None:  # bottle should never be None at this point
            continue
        slow_factor = cfg.PUMP_SLOW_FACTOR if ing.slow else 1
        volume_flow = cfg.PUMP_VOLUMEFLOW[ing.bottle - 1] * slow_factor
        prep_data.append(
            _PreparationData(
                cfg.PUMP_PINS[ing.bottle - 1],
                volume_flow,
                round(ing.amount / volume_flow, 1),
                recipe_order=ing.recipe_order,
            )
        )
    return prep_data


def _build_clean_data() -> list[_PreparationData]:
    """Builds a list of needed cleaning data objects"""
    active_pins = cfg.PUMP_PINS[: cfg.MAKER_NUMBER_BOTTLES]
    volume_flow = cfg.PUMP_VOLUMEFLOW[: cfg.MAKER_NUMBER_BOTTLES]
    prep_data = []
    for pin, flow in zip(active_pins, volume_flow):
        prep_data.append(
            _PreparationData(pin, flow, cfg.MAKER_CLEAN_TIME)
        )
    return prep_data


def _generate_progress(current_time: float, total_time: float):
    """Prints the current passed time in relation to total time"""
    return f"{current_time: <4.1f} | {total_time: >4.1f} s: "


def _consumption_print(consumption: List[float], current_time: float, max_time: float, interval=1):
    """Displays each interval seconds information for cocktail preparation"""
    if current_time % interval == 0 and current_time != 0:
        pretty_consumption = [round(x) for x in consumption]
        progress = _generate_progress(current_time, max_time)
        time_print(f"{progress}Volumes: {pretty_consumption}")


def _header_print(msg: str):
    """Formats the message with dashes around"""
    time_print(f"{' ' + msg + ' ':-^80}")


MACHINE = MachineController()
