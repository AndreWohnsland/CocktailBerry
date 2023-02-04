from dataclasses import dataclass
import time
from typing import List, Union
from PyQt5.QtWidgets import qApp

from src.config_manager import shared, CONFIG as cfg
from src.machine.generic_board import GenericController
from src.machine.interface import PinController
from src.machine.raspberry import RpiController


@dataclass
class _PreparationData:
    pin: int
    volume_flow: int
    flow_time: float
    consumption: float = 0.0
    closed: bool = False


class MachineController():
    """Controller Class for all Machine related Pin routines """

    def __init__(self):
        super().__init__()
        self._pin_controller = self.__chose_controller()

    def __chose_controller(self) -> PinController:
        """Selects the controller class for the Pin"""
        if cfg.MAKER_BOARD == "RPI":
            return RpiController()
        # In case none is found, fall back to generic using python-periphery
        return GenericController()

    def clean_pumps(self, w):
        """Clean the pumps for the defined time in the config.
        Activates all pumps for the given time
        """
        active_pins = cfg.PUMP_PINS[: cfg.MAKER_NUMBER_BOTTLES]
        _header_print("Start Cleaning")
        t_cleaned = 0.0
        w.open_progression_window("Cleaning")
        self._start_pumps(active_pins)
        # also using same button cancel from prepare cocktail
        shared.make_cocktail = True
        while t_cleaned < cfg.MAKER_CLEAN_TIME and shared.make_cocktail:
            _clean_print(t_cleaned)
            t_cleaned += cfg.MAKER_SLEEP_TIME
            t_cleaned = round(t_cleaned, 2)
            time.sleep(cfg.MAKER_SLEEP_TIME)
            w.change_progression_window(t_cleaned / cfg.MAKER_CLEAN_TIME * 100)
            qApp.processEvents()
        _clean_print(cfg.MAKER_CLEAN_TIME)
        print("")
        self._stop_pumps(active_pins)
        _header_print("Done Cleaning")
        w.close_progression_window()

    def make_cocktail(
        self,
        w,
        bottle_list: List[int],
        volume_list: list[Union[float, int]],
        recipe="",
        is_cocktail=True
    ):
        """RPI Logic to prepare the cocktail.
        Calculates needed time for each slot according to data and config.
        Updates Progressbar status. Returns data for DB updates.

        Args:
            w (QtMainWindow): MainWindow Object
            bottle_list (List[int]): Number of bottles to be used
            volume_list (List[float]): Corresponding Volume needed of bottles
            recipe (str, optional): Option to change the display text of Progress Screen. Defaults to "".

        Returns:
            tuple(List[int], float, float): Consumption of each bottle, taken time, max needed time
        """
        # Only show team dialog if it is enabled
        if cfg.TEAMS_ACTIVE and is_cocktail:
            w.open_team_window()
        shared.cocktail_started = True
        shared.make_cocktail = True
        if w is not None:
            w.open_progression_window(recipe)
        prep_data = self._build_preparation_data(bottle_list, volume_list)
        _header_print(f"Starting {recipe}")
        current_time, max_time = self._start_preparation(w, prep_data)
        consumption = [round(x.consumption) for x in prep_data]
        print("Total calculated consumption:", consumption)
        _header_print(f"Finished {recipe}")
        if w is not None:
            w.close_progression_window()
        return consumption, current_time, max_time

    def _start_preparation(self, w, prep_data: list[_PreparationData]):
        """Prepares the volumes of the given data"""
        current_time = 0.0
        # need to cut data into chunks
        chunk = cfg.MAKER_SIMULTANEOUSLY_PUMPS
        chunked_preparation = [
            prep_data[i:i + chunk] for i in range(0, len(prep_data), chunk)
        ]
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
            _print_time(current_time, max_time)
            self._start_pumps(pins)
            # iterate over each prep data
            while section_time < section_max and shared.make_cocktail:
                self._process_preparation_section(current_time, max_time, section, section_time)
                # Adjust needed data
                _consumption_print([x.consumption for x in prep_data], current_time, max_time)
                current_time = round(current_time + cfg.MAKER_SLEEP_TIME, 2)
                section_time = round(section_time + cfg.MAKER_SLEEP_TIME, 2)
                time.sleep(cfg.MAKER_SLEEP_TIME)
                if w is not None:
                    w.change_progression_window(current_time / max_time * 100)
                qApp.processEvents()
            _print_time(current_time, max_time)
            self._stop_pumps(pins)
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
                _print_time(current_time, max_time)
                self._stop_pumps([data.pin])
                data.closed = True

    def set_up_pumps(self):
        """Gets all used pins, prints pins and uses controller class to set up"""
        active_pins = cfg.PUMP_PINS[: cfg.MAKER_NUMBER_BOTTLES]
        print(f"Initializing Pins: {active_pins}")
        self._pin_controller.initialize_pin_list(active_pins)

    def _start_pumps(self, pin_list: List[int]):
        """Informs and opens all given pins"""
        print(f"Opening Pins: {pin_list}")
        self._pin_controller.activate_pin_list(pin_list)

    def close_all_pumps(self):
        """Close all pins connected to the pumps"""
        active_pins = cfg.PUMP_PINS[: cfg.MAKER_NUMBER_BOTTLES]
        self._stop_pumps(active_pins)

    def cleanup(self):
        """Cleanup for shutdown the machine"""
        self.close_all_pumps()
        self._pin_controller.cleanup_pin_list()

    def _stop_pumps(self, pin_list: List[int]):
        """Informs and closes all given pins"""
        print(f"Closing Pins: {pin_list}")
        self._pin_controller.close_pin_list(pin_list)

    def _build_preparation_data(
        self,
        bottle_list: List[int],
        volume_list: list[Union[float, int]]
    ) -> list[_PreparationData]:
        """Builds the data needed for machine preparation"""
        indexes = [x - 1 for x in bottle_list]
        pins = [cfg.PUMP_PINS[i] for i in indexes]
        volume_flows = [cfg.PUMP_VOLUMEFLOW[i] for i in indexes]
        pin_times = [round(volume / flow, 1) for volume, flow in zip(volume_list, volume_flows)]
        prep_data = []
        for pin, flow, pin_time in zip(pins, volume_flows, pin_times):
            prep_data.append(
                _PreparationData(pin, flow, pin_time)
            )
        return prep_data

    def _build_clean_data(self) -> list[_PreparationData]:
        """Builds a list of needed cleaning data objects"""
        active_pins = cfg.PUMP_PINS[: cfg.MAKER_NUMBER_BOTTLES]
        volume_flow = cfg.PUMP_VOLUMEFLOW[: cfg.MAKER_NUMBER_BOTTLES]
        prep_data = []
        for pin, flow in zip(active_pins, volume_flow):
            prep_data.append(
                _PreparationData(pin, flow, cfg.MAKER_CLEAN_TIME)
            )
        return prep_data


def _print_time(current_time: float, total_time: float):
    """Prints the current passed time in relation to total time"""
    print(f"{current_time: <4.1f} | {total_time: >4.1f} s:", end=" ")


def _consumption_print(consumption: List[float], current_time: float, max_time: float, interval=1):
    """Displays each interval seconds information for cocktail preparation"""
    if current_time % interval == 0 and current_time != 0:
        pretty_consumption = [round(x) for x in consumption]
        _print_time(current_time, max_time)
        print(f"Volumes: {pretty_consumption}")


def _clean_print(t_cleaned: float, interval=0.5):
    """Progress print for cleaning"""
    if t_cleaned % interval == 0:
        print(
            f"Cleaning, {t_cleaned:.1f}/{cfg.MAKER_CLEAN_TIME:.1f} s {'.' * int(t_cleaned*2)}", end="\r"
        )  # type: ignore


def _header_print(msg: str):
    """Formats the message with dashes around"""
    print(f"{' ' + msg + ' ':-^80}")


MACHINE = MachineController()
