from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from PyQt6.QtCore import QEventLoop, pyqtSignal
from PyQt6.QtWidgets import QMainWindow

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.service.waiter_service import WaiterService
from src.ui_elements.passworddialog import Ui_PasswordDialog

if TYPE_CHECKING:
    from src.api.models import PermissionKey


class PasswordDialog(QMainWindow, Ui_PasswordDialog):
    """Password dialog that blocks until closed and returns success/failure."""

    _waiter_accepted = pyqtSignal()

    def __init__(
        self,
        right_password: int,
        header_type: Literal["master", "maker"] = "master",
        permission_key: PermissionKey | None = None,
    ) -> None:
        super().__init__()
        self.setupUi(self)
        self.right_password = right_password
        self._result = False
        self._loop: QEventLoop | None = None
        self._permission_key = permission_key
        self._waiter_callback_name: str | None = None

        DP_CONTROLLER.initialize_window_object(self)

        # Buttons
        self.enter_button.clicked.connect(self._enter_clicked)
        self.cancel_button.clicked.connect(self._cancel_clicked)
        self.PBdel.clicked.connect(self._del_clicked)

        # Connect number buttons dynamically
        for number in range(10):
            getattr(self, f"PB{number}").clicked.connect(lambda _, n=number: self._number_clicked(n))

        UI_LANGUAGE.adjust_password_window(self, header_type)

        # Bridge signal for thread-safe waiter NFC callback
        self._waiter_accepted.connect(lambda: self._finish(True))
        self._register_waiter_callback()

    def _register_waiter_callback(self) -> None:
        """Register a WaiterService callback to auto-accept on NFC scan with sufficient permissions."""
        if self._permission_key is None or not cfg.waiter_mode_active:
            return
        self._waiter_callback_name = "password_dialog"
        WaiterService().add_callback(self._waiter_callback_name, self._on_waiter_scan)

    def _unregister_waiter_callback(self) -> None:
        """Remove the WaiterService callback if registered."""
        if self._waiter_callback_name is None:
            return
        WaiterService().remove_callback(self._waiter_callback_name)
        self._waiter_callback_name = None

    def _on_waiter_scan(self) -> None:
        """Check waiter permissions on NFC scan and emit accept signal if sufficient."""
        if shared.current_waiter is None or self._permission_key is None:
            return

        # Explicitly map, in case attributes get renamed
        permissions = shared.current_waiter.permissions
        permission_mapping: dict[str | None, bool] = {
            "maker": permissions.maker,
            "ingredients": permissions.ingredients,
            "recipes": permissions.recipes,
            "bottles": permissions.bottles,
            "options": permissions.options,
            None: False,
        }

        if permission_mapping.get(self._permission_key, False):
            self._waiter_accepted.emit()

    def _finish(self, result: bool) -> None:
        """Store result, exit event loop, close window."""
        self._unregister_waiter_callback()
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
        self._loop.exec()
        return self._result
