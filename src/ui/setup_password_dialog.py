from typing import Literal

from PyQt5.QtCore import QEventLoop
from PyQt5.QtWidgets import QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements.passworddialog import Ui_PasswordDialog


class PasswordDialog(QMainWindow, Ui_PasswordDialog):
    """Password dialog that blocks until closed and returns success/failure."""

    def __init__(self, right_password: int, header_type: Literal["master", "maker"] = "master") -> None:
        super().__init__()
        self.setupUi(self)
        self.right_password = right_password
        self._result = False
        self._loop: QEventLoop | None = None

        DP_CONTROLLER.initialize_window_object(self)

        # Buttons
        self.enter_button.clicked.connect(self._enter_clicked)
        self.cancel_button.clicked.connect(self._cancel_clicked)
        self.PBdel.clicked.connect(self._del_clicked)

        # Connect number buttons dynamically
        for number in range(10):
            getattr(self, f"PB{number}").clicked.connect(lambda _, n=number: self._number_clicked(n))

        UI_LANGUAGE.adjust_password_window(self, header_type)

    def _finish(self, result: bool) -> None:
        """Store result, exit event loop, close window."""
        self._result = result
        if self._loop is not None:
            self._loop.quit()
        self.close()

    def _number_clicked(self, number: int) -> None:
        """Append clicked number to line edit."""
        self.password_field.setText(self.password_field.text() + str(number))

    def _enter_clicked(self) -> None:
        """Check entered password and finish if correct, otherwise reset."""
        password_string = self.password_field.text()
        password = int(password_string) if password_string else 0
        if password == self.right_password:
            self._finish(True)
        else:
            DP_CONTROLLER.say_wrong_password()
            self.password_field.clear()

    def _cancel_clicked(self) -> None:
        """Cancel password entry."""
        self._finish(False)

    def _del_clicked(self) -> None:
        """Delete the last digit."""
        self.password_field.setText(self.password_field.text()[:-1])

    def exec(self) -> bool:
        """Block until user confirms or cancels. Returns True if password correct, False otherwise."""
        self._loop = QEventLoop()
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)
        self._loop.exec_()
        return self._result
