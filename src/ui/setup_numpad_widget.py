from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QDialog, QLineEdit, QWidget

from src.display_controller import DP_CONTROLLER
from src.ui_elements.numpad import Ui_NumpadWindow

if TYPE_CHECKING:
    from src.ui.create_config_window import ConfigWindow
    from src.ui.setup_mainwindow import MainScreen


class NumpadWidget(QDialog, Ui_NumpadWindow):
    """Creates the Numpad screen."""

    def __init__(
        self,
        parent: "MainScreen | ConfigWindow | QWidget",
        le_to_write: QLineEdit,
        x_pos: int = 0,
        y_pos: int = 0,
        header_text: str = "Password",
        use_float: bool = False,
        allow_negative: bool = False,
        overwrite_number: bool = False,
        header_is_entered_number: bool = False,
    ) -> None:
        """Init. Connect all the buttons and set window policy."""
        super().__init__(parent)
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self, x_pos, y_pos)
        # Connect all the buttons, generates a list of the numbers an object names to do that
        self.PBenter.clicked.connect(self.enter_clicked)
        self.PBdel.clicked.connect(self.del_clicked)
        self.number_list = list(range(10))
        self.overwrite_number = overwrite_number
        self.attribute_numbers = [getattr(self, "PB" + str(x)) for x in self.number_list]
        for obj, number in zip(self.attribute_numbers, self.number_list):
            obj.clicked.connect(lambda _, n=number: self.number_clicked(number=n))
        self.mainscreen = parent
        self.setWindowTitle(header_text)
        self.header_is_entered_number = header_is_entered_number
        if header_is_entered_number:
            self.LHeader.setText(le_to_write.text())
        else:
            self.LHeader.setText(header_text)
        self.source_line_edit = le_to_write
        self._add_float(use_float)
        self._add_minus(allow_negative)
        self.show()
        DP_CONTROLLER.set_display_settings(self, resize=False)

    def minus_toggled(self, checked: bool) -> None:
        """Add or remove minus sign in front based on PBminus state."""
        text = self.source_line_edit.text()
        new_text = f"-{text}" if checked else text.lstrip("-")
        self.change_text(new_text)

    def number_clicked(self, number: int) -> None:
        """Add the clicked number to the lineedit."""
        text = str(number) if self.overwrite_number else f"{self.source_line_edit.text()}{number}"
        self.change_text(text)

    def enter_clicked(self) -> None:
        """Enters/Closes the Dialog."""
        self.close()

    def del_clicked(self) -> None:
        """Delete the last digit in the lineedit."""
        current_string = self.source_line_edit.text()[:-1]
        self.change_text(current_string)

    def _add_float(self, use_float: bool) -> None:
        if not use_float:
            self.PBdot.deleteLater()
            return
        self.PBdot.clicked.connect(self._dot_clicked)

    def _add_minus(self, allow_negative: bool) -> None:
        if not allow_negative:
            self.PBminus.deleteLater()
            return
        if self.source_line_edit.text().startswith("-"):
            self.PBminus.setChecked(True)
        self.PBminus.toggled.connect(self.minus_toggled)

    def _dot_clicked(self) -> None:
        """Add a dot if its not the first letter or a dot already exists."""
        current_string = self.source_line_edit.text()
        if "." in current_string or len(current_string) == 0:
            return
        self.change_text(f"{self.source_line_edit.text()}.")

    def change_text(self, new_text: str) -> None:
        """Change the text in the lineedit and header."""
        self.source_line_edit.setText(new_text)
        if self.header_is_entered_number:
            self.LHeader.setText(new_text)
