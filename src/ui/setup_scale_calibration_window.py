from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.machine.controller import MachineController
from src.ui.creation_utils import FontSize, create_button, create_label, create_spacer
from src.ui.setup_numpad_widget import NumpadWidget
from src.ui_elements.clickablelineedit import ClickableLineEdit


class ScaleCalibrationScreen(QMainWindow):
    """Scale calibration wizard with tare -> calibrate flow."""

    def __init__(self) -> None:
        super().__init__()
        self.mc = MachineController()
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self._zero_offset: int = 0

        header_row = QHBoxLayout()
        self.header_label = create_label(
            UI_LANGUAGE._choose_language("header", "scale_calibration_window"),
            FontSize.HEADER,
            bold=True,
            centered=True,
            css_class="secondary",
        )
        header_row.addWidget(self.header_label)
        self.button_back = create_button("X", min_w=60, max_w=60, min_h=50, css_class="destructive btn-inverted")
        self.button_back.clicked.connect(self.close)
        header_row.addWidget(self.button_back)
        self.main_layout.addLayout(header_row)

        if not self.mc.has_scale:
            self._build_no_scale_view()
        else:
            self._build_calibration_view()

        DP_CONTROLLER.initialize_window_object(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _build_no_scale_view(self) -> None:
        """Show a message that scale is not available and a back button."""
        self.main_layout.addStretch()
        not_available_label = create_label(
            UI_LANGUAGE._choose_language("not_available", "scale_calibration_window"),
            FontSize.LARGE,
            centered=True,
        )
        self.main_layout.addWidget(not_available_label)
        self.main_layout.addStretch()

    def _build_calibration_view(self) -> None:
        """Build the stacked widget with tare and calibrate pages."""
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        self._build_tare_page()
        self._build_calibrate_page()

        self.stack.setCurrentWidget(self.tare_page)

    def _build_tare_page(self) -> None:
        """Page 1: instruct user to clear the scale, then tare."""
        self.tare_page = QWidget()
        layout = QVBoxLayout(self.tare_page)
        layout.addStretch()

        self.tare_instruction = create_label(
            UI_LANGUAGE._choose_language("tare_instruction", "scale_calibration_window"),
            FontSize.MEDIUM,
            centered=True,
        )
        layout.addWidget(self.tare_instruction)
        layout.addStretch()

        self.button_tare = create_button(
            UI_LANGUAGE._choose_language("tare", "scale_calibration_window"),
            css_class="btn-inverted",
        )
        self.button_tare.clicked.connect(self._do_tare)
        layout.addWidget(self.button_tare)

        self.stack.addWidget(self.tare_page)

    def _build_calibrate_page(self) -> None:
        """Page 2: enter known weight, read current, apply calibration."""
        self.calibrate_page = QWidget()
        layout = QVBoxLayout(self.calibrate_page)
        layout.addStretch()

        self.place_instruction = create_label(
            UI_LANGUAGE._choose_language("place_weight_instruction", "scale_calibration_window"),
            FontSize.MEDIUM,
            centered=True,
        )
        layout.addWidget(self.place_instruction)
        layout.addItem(create_spacer(10))

        # Known weight input
        weight_label = create_label(
            UI_LANGUAGE._choose_language("known_weight", "scale_calibration_window"),
            FontSize.MEDIUM,
            centered=True,
        )
        layout.addWidget(weight_label)

        self.input_known_weight = ClickableLineEdit("100")
        self.input_known_weight.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_known_weight.setStyleSheet("font-size: 24pt; font-weight: bold;")
        self.input_known_weight.setMinimumHeight(50)
        self.input_known_weight.setReadOnly(True)
        self.input_known_weight.clicked.connect(
            lambda: NumpadWidget(
                self,
                self.input_known_weight,
                1000,
                1,
                UI_LANGUAGE._choose_language("known_weight", "scale_calibration_window"),
                header_is_entered_number=True,
            )
        )
        layout.addWidget(self.input_known_weight)
        layout.addItem(create_spacer(10))

        # Status label for feedback
        self.label_status = create_label("", FontSize.MEDIUM, centered=True)
        layout.addWidget(self.label_status)

        layout.addStretch()

        row = QHBoxLayout()
        self.button_read_weight = create_button(UI_LANGUAGE._choose_language("read_weight", "scale_calibration_window"))
        self.button_read_weight.clicked.connect(self._do_read_weight)
        row.addWidget(self.button_read_weight)

        self.button_back_to_tare = create_button(
            UI_LANGUAGE._choose_language("back_to_tare", "scale_calibration_window")
        )
        self.button_back_to_tare.clicked.connect(self._reset_to_tare)
        row.addWidget(self.button_back_to_tare)
        layout.addLayout(row)

        self.button_calibrate = create_button(
            UI_LANGUAGE._choose_language("calibrate", "scale_calibration_window"),
            css_class="btn-inverted",
        )
        self.button_calibrate.clicked.connect(self._do_calibrate)
        layout.addWidget(self.button_calibrate)

        self.stack.addWidget(self.calibrate_page)

    def _do_tare(self) -> None:
        """Execute tare, store offset, and move to calibrate page."""
        self._zero_offset = self.mc.scale_tare(5)
        self.stack.setCurrentWidget(self.calibrate_page)

    def _do_read_weight(self) -> None:
        """Read current weight from scale and display in status label."""
        try:
            weight = self.mc.scale_read_grams()
        except RuntimeError:
            return
        self.label_status.setText(
            UI_LANGUAGE._choose_language("current_reading", "scale_calibration_window", weight=f"{weight:.1f}")
        )

    def _do_calibrate(self) -> None:
        """Read scale, compute factor, save config."""
        try:
            known_weight = float(self.input_known_weight.text())
        except ValueError:
            return
        if known_weight <= 0:
            return
        try:
            factor = self.mc.scale_calibrate(known_weight, zero_raw_offset=self._zero_offset)
        except RuntimeError:
            self.label_status.setText(UI_LANGUAGE._choose_language("calibration_error", "scale_calibration_window"))
            return
        text = UI_LANGUAGE._choose_language(
            "calibration_done",
            "scale_calibration_window",
            factor=f"{factor:.4f}",
            offset=f"{self._zero_offset:.2f}",
        )
        self.label_status.setText(text)

    def _reset_to_tare(self) -> None:
        """Go back to tare page and reset."""
        self.label_status.setText("")
        self.stack.setCurrentWidget(self.tare_page)
