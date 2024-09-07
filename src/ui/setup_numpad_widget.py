from PyQt5.QtWidgets import QDialog, QLineEdit

from src.display_controller import DP_CONTROLLER
from src.ui_elements.numpad import Ui_NumpadWindow


class NumpadWidget(QDialog, Ui_NumpadWindow):
    """Creates the Numpad screen."""

    def __init__(
        self,
        parent,
        le_to_write: QLineEdit,
        x_pos: int = 0,
        y_pos: int = 0,
        header_text: str = "Password",
        use_float=False,
        overwrite_number: bool = False,
        header_is_entered_number: bool = False,
    ):
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
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
        self.show()
        DP_CONTROLLER.set_display_settings(self, resize=False)

    def number_clicked(self, number: int):
        """Add the clicked number to the lineedit."""
        text = str(number) if self.overwrite_number else f"{self.source_line_edit.text()}{number}"
        self.source_line_edit.setText(text)
        if self.header_is_entered_number:
            self.LHeader.setText(text)

    def enter_clicked(self):
        """Enters/Closes the Dialog."""
        self.close()

    def del_clicked(self):
        """Delete the last digit in the lineedit."""
        current_string = self.source_line_edit.text()[:-1]
        self.source_line_edit.setText(current_string)
        if self.header_is_entered_number:
            self.LHeader.setText(current_string)

    def _add_float(self, use_float: bool):
        if not use_float:
            self.PBdot.deleteLater()
            return
        self.PBdot.clicked.connect(self._dot_clicked)

    def _dot_clicked(self):
        """Add a dot if its not the first letter or a dot already exists."""
        current_string = self.source_line_edit.text()
        if "." in current_string or len(current_string) == 0:
            return
        self.source_line_edit.setText(f"{self.source_line_edit.text()}.")
