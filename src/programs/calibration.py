from dataclasses import dataclass

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QWidget

from src.config.config_manager import CONFIG as cfg
from src.dialog_handler import DIALOG_HANDLER as DH
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.tabs import maker
from src.ui.setup_numpad_widget import NumpadWidget
from src.ui_elements import Ui_CalibrationRealWidget, Ui_CalibrationTargetWidget, Ui_CalibrationWindow

MAX_DEVIATION_FACTOR = 20  # maximum allowed deviation factor for calibration


@dataclass
class CalibrationData:
    """Track calibration data."""

    pump_number: int
    target_volume: float = 0.0
    measured_volume: float = 0.0

    def reset(self) -> None:
        """Reset all calibration data."""
        self.target_volume = 0.0
        self.measured_volume = 0.0


class _CalibrationTargetWidget(QWidget, Ui_CalibrationTargetWidget):
    def __init__(self, calibration_data: CalibrationData) -> None:
        """Init the calibration Screen."""
        super().__init__()
        self.setupUi(self)
        self.calibration_data = calibration_data
        bottles = cfg.MAKER_NUMBER_BOTTLES
        self.button_start.clicked.connect(self.output_volume)
        self.channel_plus.clicked.connect(
            lambda: DP_CONTROLLER.change_input_value(self.input_pump_number, 1, bottles, 1)
        )
        self.channel_minus.clicked.connect(
            lambda: DP_CONTROLLER.change_input_value(self.input_pump_number, 1, bottles, -1)
        )
        self.amount_plus.clicked.connect(lambda: DP_CONTROLLER.change_input_value(self.input_amount, 10, 200, 10))
        self.amount_minus.clicked.connect(lambda: DP_CONTROLLER.change_input_value(self.input_amount, 10, 200, -10))

    def output_volume(self) -> None:
        """Output the set number of volume according to defined volume flow."""
        channel_number = int(self.input_pump_number.text())
        amount = int(self.input_amount.text())
        self.calibration_data.pump_number = channel_number
        self.calibration_data.target_volume += amount
        self.channel_plus.setEnabled(False)
        self.channel_minus.setEnabled(False)
        self.button_next.setEnabled(True)
        maker.calibrate(channel_number, amount)

    def reset(self) -> None:
        """Reset the calibration data."""
        self.channel_plus.setEnabled(True)
        self.channel_minus.setEnabled(True)
        self.button_next.setEnabled(False)


class _CalibrationRealWidget(QWidget, Ui_CalibrationRealWidget):
    def __init__(self, calibration_data: CalibrationData) -> None:
        super().__init__()
        self.setupUi(self)
        self.calibration_data = calibration_data

        self.input_measured_amount.clicked.connect(
            lambda: NumpadWidget(
                self,
                self.input_measured_amount,
                300,
                20,
                "Measured Amount",
                header_is_entered_number=True,
                use_float=True,
            )
        )
        self.input_measured_amount.textChanged.connect(self.on_entered_measured_amount)

    def on_entered_measured_amount(self, value: str) -> None:
        """Change the label if the entered amount is changed."""
        enter_amount_translation = UI_LANGUAGE._choose_language("enter_measured_amount", "calibration_window")
        if not value or value == "":
            self.label_new_flow.setText(enter_amount_translation)
            self.button_apply.setEnabled(False)
            return
        try:
            measured_value = float(value)
        except ValueError:
            self.label_new_flow.setText(enter_amount_translation)
            self.button_apply.setEnabled(False)
            return

        if measured_value <= 0 or self.calibration_data.target_volume <= 0:
            self.label_new_flow.setText(enter_amount_translation)
            self.button_apply.setEnabled(False)
            return

        # Get current flow from config for the selected channel
        channel_idx = self.calibration_data.pump_number - 1
        current_flow = cfg.PUMP_CONFIG[channel_idx].volume_flow

        # Calculate the deviation factor
        deviation_factor = self.calibration_data.target_volume / measured_value

        # Check if deviation is within acceptable bounds (factor of 20)
        if deviation_factor > MAX_DEVIATION_FACTOR or deviation_factor < 1 / MAX_DEVIATION_FACTOR:
            self.label_new_flow.setText(UI_LANGUAGE._choose_language("deviation_too_large", "calibration_window"))
            self.button_apply.setEnabled(False)
            return

        new_flow = round(current_flow * deviation_factor, 1)

        self.calibration_data.measured_volume = measured_value
        self.label_new_flow.setText(
            UI_LANGUAGE._choose_language("new_volume_flow", "calibration_window", flow=new_flow)
        )
        self.button_apply.setEnabled(True)

    def reset(self) -> None:
        """Reset the calibration data."""
        self.input_measured_amount.setText("")
        self.label_new_flow.setText(UI_LANGUAGE._choose_language("enter_measured_amount", "calibration_window"))
        self.button_apply.setEnabled(False)


class CalibrationScreen(QMainWindow, Ui_CalibrationWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)  # type: ignore

        self.button_exit.clicked.connect(self.close)
        self.button_reset.clicked.connect(self.reset)
        self.calibration_data = CalibrationData(1)
        self.page_target = _CalibrationTargetWidget(self.calibration_data)
        self.page_real = _CalibrationRealWidget(self.calibration_data)

        self.stack.addWidget(self.page_target)
        self.stack.addWidget(self.page_real)
        self.stack.setCurrentWidget(self.page_target)

        # Initialize button states
        self.page_target.button_next.setEnabled(False)
        self.page_real.button_apply.setEnabled(False)

        # we need some "shared" management of the pages, otherwise we would need to pass a lot between them
        self.page_target.button_next.clicked.connect(self.show_real_page)
        self.page_real.button_apply.clicked.connect(self.apply_new_flow)

        # translations
        UI_LANGUAGE.adjust_calibration_window(self)
        UI_LANGUAGE.adjust_calibration_target(self.page_target)
        UI_LANGUAGE.adjust_calibration_real(self.page_real)

        self.showFullScreen()
        DP_CONTROLLER.inject_stylesheet(self)
        DP_CONTROLLER.set_display_settings(self)

    def show_real_page(self) -> None:
        self.page_real.label_spend_volume.setText(
            UI_LANGUAGE._choose_language(
                "target_amount", "calibration_window", amount=self.calibration_data.target_volume
            )
        )
        self.stack.setCurrentWidget(self.page_real)

    def show_target_page(self) -> None:
        self.stack.setCurrentWidget(self.page_target)

    def reset(self) -> None:
        """Reset all calibration data and return to target page."""
        self.calibration_data.reset()
        self.page_target.reset()
        self.page_real.reset()
        self.show_target_page()

    def apply_new_flow(self) -> None:
        """Apply the new calculated flow rate to the config and save to file."""
        if self.calibration_data.measured_volume <= 0 or self.calibration_data.target_volume <= 0:
            return
        channel_idx = self.calibration_data.pump_number - 1
        current_flow = cfg.PUMP_CONFIG[channel_idx].volume_flow
        new_flow = round(
            current_flow * (self.calibration_data.target_volume / self.calibration_data.measured_volume), 1
        )
        cfg.PUMP_CONFIG[channel_idx].volume_flow = new_flow
        cfg.sync_config_to_file()
        self.reset()
        DH.say_volume_flow_adjusted(self.calibration_data.pump_number, new_flow)
