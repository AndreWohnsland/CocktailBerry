from dataclasses import dataclass

from PyQt5.QtWidgets import QMainWindow, QWidget

from src.config.config_manager import CONFIG as cfg
from src.database_commander import DatabaseCommander
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

    @property
    def factor(self) -> float:
        """Get the calibration factor."""
        if self.target_volume <= 0 or self.measured_volume <= 0:
            return 0.0
        return self.measured_volume / self.target_volume


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
        self.populate_ingredient_dropdown()
        self.prompt_for_measured_amount()

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
        self.input_ingredient.currentTextChanged.connect(self.on_ingredient_changed)

    def prompt_for_measured_amount(self) -> None:
        enter_amount_translation = UI_LANGUAGE._choose_language("enter_measured_amount", "calibration_window")
        self.label_new_flow.setText(enter_amount_translation)
        self.button_apply.setEnabled(False)

    def on_ingredient_changed(self, _: str) -> None:
        # just propagate the change since the calculation is the same
        self.on_entered_measured_amount(self.input_measured_amount.text())

    def on_entered_measured_amount(self, value: str) -> None:
        """Change the label if the entered amount is changed."""
        if not value or value == "":
            self.prompt_for_measured_amount()
            return
        try:
            measured_value = float(value)
        except ValueError:
            self.prompt_for_measured_amount()
            return

        if measured_value <= 0 or self.calibration_data.target_volume <= 0:
            self.prompt_for_measured_amount()
            return

        # Get current flow from config for the selected channel
        channel_idx = self.calibration_data.pump_number - 1
        current_flow = cfg.PUMP_CONFIG[channel_idx].volume_flow
        self.calibration_data.measured_volume = measured_value

        # Check if deviation is within acceptable bounds (factor of 20)
        if 1 / MAX_DEVIATION_FACTOR > self.calibration_data.factor > MAX_DEVIATION_FACTOR:
            self.label_new_flow.setText(UI_LANGUAGE._choose_language("deviation_too_large", "calibration_window"))
            self.button_apply.setEnabled(False)
            return

        self.button_apply.setEnabled(True)

        # in case of selected ingredient, show ingredient speed instead of volume flow
        if self.is_ingredient_selected:
            self.label_new_flow.setText(
                UI_LANGUAGE._choose_language(
                    "new_ingredient_speed", "calibration_window", speed=int(self.calibration_data.factor * 100)
                )
            )
            return

        new_flow = round(current_flow * self.calibration_data.factor, 1)
        self.label_new_flow.setText(
            UI_LANGUAGE._choose_language("new_volume_flow", "calibration_window", flow=new_flow)
        )

    def reset(self) -> None:
        """Reset the calibration data."""
        self.input_measured_amount.setText("")
        self.label_new_flow.setText(UI_LANGUAGE._choose_language("enter_measured_amount", "calibration_window"))
        self.button_apply.setEnabled(False)
        self.populate_ingredient_dropdown()

    def populate_ingredient_dropdown(self) -> None:
        """Populate the ingredient dropdown with available ingredients."""
        DBC = DatabaseCommander()
        ingredients = DBC.get_all_ingredients(get_hand=False)
        DP_CONTROLLER.fill_single_combobox(self.input_ingredient, [i.name for i in ingredients], clear_first=True)

    @property
    def is_ingredient_selected(self) -> bool:
        """Check if an ingredient is selected."""
        return self.input_ingredient.currentText() != ""


class CalibrationScreen(QMainWindow, Ui_CalibrationWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)

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

        if self.page_real.is_ingredient_selected:
            # adjust ingredient speed instead of volume flow
            new_speed = int(100 * self.calibration_data.factor)
            DBC = DatabaseCommander()
            ingredient_name = self.page_real.input_ingredient.currentText()
            ingredient = DBC.get_ingredient(ingredient_name)
            if ingredient is None:
                return
            DBC.set_ingredient_data(
                ingredient_name=ingredient.name,
                alcohol_level=ingredient.alcohol,
                volume=ingredient.bottle_volume,
                new_level=ingredient.fill_level,
                only_hand=ingredient.hand,
                pump_speed=new_speed,
                ingredient_id=ingredient.id,
                cost=ingredient.cost,
                unit=ingredient.unit,
            )
            DH.say_ingredient_speed_adjusted(ingredient.name, new_speed)
            self.reset()
            return

        new_flow = round(current_flow * self.calibration_data.factor, 1)
        cfg.PUMP_CONFIG[channel_idx].volume_flow = new_flow
        cfg.sync_config_to_file()
        self.reset()
        DH.say_volume_flow_adjusted(self.calibration_data.pump_number, new_flow)
