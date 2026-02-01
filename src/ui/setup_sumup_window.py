from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMainWindow
from sumup.readers import Reader

from src.config.config_manager import CONFIG as cfg
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.service.sumup_payment_service import Err, Result, SumupPaymentService
from src.ui.icons import IconSetter
from src.ui.qt_worker import CallableWorker, run_with_spinner
from src.ui.setup_keyboard_widget import KeyboardWidget
from src.ui_elements import Ui_SumupWindow

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class SumupWindow(QMainWindow, Ui_SumupWindow):
    """Creates the sumup window Widget."""

    def __init__(self, mainscreen: "MainScreen") -> None:
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
        self.setupUi(self)
        self.mainscreen = mainscreen
        self._sumup_service: SumupPaymentService | None = None
        self._fetch_worker: CallableWorker[list[Reader]] | None = None
        self._create_worker: CallableWorker[Result[Reader]] | None = None

        DP_CONTROLLER.initialize_window_object(self)
        self.button_back.clicked.connect(self.close)
        self.button_create.clicked.connect(self._create_reader)
        self.button_use.clicked.connect(self._use_selected_reader)
        self.button_delete.clicked.connect(self._delete_reader)

        self.input_code.clicked.connect(lambda: KeyboardWidget(self.mainscreen, self.input_code, 10))
        self.input_name.clicked.connect(lambda: KeyboardWidget(self.mainscreen, self.input_name, 100))

        # Disable buttons until readers are loaded
        self.button_use.setEnabled(False)
        self.button_create.setEnabled(False)

        icons = IconSetter()
        icons.set_icon(
            self.button_delete,
            icons.generate_icon(icons.presets.delete, icons.color.background),
            True,
        )

        UI_LANGUAGE.adjust_sumup_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

        # Start loading readers asynchronously
        self._load_readers()

    def _get_service(self) -> SumupPaymentService | None:
        """Get or create the SumUp service instance."""
        if self._sumup_service is not None:
            return self._sumup_service
        if not cfg.PAYMENT_SUMUP_API_KEY or not cfg.PAYMENT_SUMUP_MERCHANT_CODE:
            DP_CONTROLLER.standard_box("SumUp API key and merchant code must be configured first.")
            return None
        self._sumup_service = SumupPaymentService(
            api_key=cfg.PAYMENT_SUMUP_API_KEY,
            merchant_code=cfg.PAYMENT_SUMUP_MERCHANT_CODE,
        )
        return self._sumup_service

    def _load_readers(self) -> None:
        """Load readers asynchronously."""
        service = self._get_service()
        if service is None:
            return

        self._fetch_worker = run_with_spinner(
            service.get_all_readers,
            parent=self,
            on_finish=self._on_readers_loaded,
        )

    def _on_readers_loaded(self, readers: list[Reader]) -> None:
        """Populate the reader dropdown when readers are fetched."""
        self.input_reader.clear()

        current_reader_id = cfg.PAYMENT_SUMUP_TERMINAL_ID
        selected_index = -1

        for i, reader in enumerate(readers):
            # Display name, store ID as item data
            self.input_reader.addItem(reader.name, reader.id)
            if reader.id == current_reader_id:
                selected_index = i

        # Select currently configured reader if found
        if selected_index >= 0:
            self.input_reader.setCurrentIndex(selected_index)

        # Enable buttons now that we have data
        self.button_use.setEnabled(True)
        self.button_create.setEnabled(True)

    def _use_selected_reader(self) -> None:
        """Set the selected reader as the active terminal."""
        if self.input_reader.count() == 0:
            DP_CONTROLLER.standard_box("No readers available. Please create one first.")
            return

        reader_id = self.input_reader.currentData()
        reader_name = self.input_reader.currentText()

        if not reader_id:
            DP_CONTROLLER.standard_box("No reader selected.")
            return

        # Save to config
        cfg.PAYMENT_SUMUP_TERMINAL_ID = reader_id
        cfg.sync_config_to_file()

        DP_CONTROLLER.standard_box(f"Reader '{reader_name}' is now active.")

    def _create_reader(self) -> None:
        """Create a new SumUp reader with the provided name and pairing code."""
        service = self._get_service()
        if service is None:
            return

        name = self.input_name.text().strip()
        pairing_code = self.input_code.text().strip()

        if not name:
            DP_CONTROLLER.standard_box("Please enter a name for the reader.")
            return
        if not pairing_code:
            DP_CONTROLLER.standard_box("Please enter the pairing code from the reader.")
            return

        # Disable create button while working
        self.button_create.setEnabled(False)

        self._create_worker = run_with_spinner(
            lambda: service.create_reader(name, pairing_code),
            parent=self,
            on_finish=self._on_reader_created,
        )

    def _on_reader_created(self, result: Result[Reader]) -> None:
        """Handle the result of reader creation."""
        self.button_create.setEnabled(True)

        if isinstance(result, Err):
            DP_CONTROLLER.standard_box(f"Failed to create reader: {result.error}")
        else:
            reader = result.data
            # Add the new reader to the dropdown
            self.input_reader.addItem(reader.name, reader.id)
            # Select the newly created reader
            self.input_reader.setCurrentIndex(self.input_reader.count() - 1)
            # Clear inputs
            self.input_name.clear()
            self.input_code.clear()
            DP_CONTROLLER.standard_box(f"Reader '{reader.name}' created successfully!")

        self._use_selected_reader()

    def _delete_reader(self) -> None:
        """Delete the currently selected reader."""
        service = self._get_service()
        if service is None:
            return

        if self.input_reader.count() == 0:
            DP_CONTROLLER.standard_box("No readers available to delete.")
            return

        reader_id = self.input_reader.currentData()
        reader_name = self.input_reader.currentText()

        if not reader_id:
            DP_CONTROLLER.standard_box("No reader selected.")
            return

        if not DP_CONTROLLER.ask_to_delete_reader(reader_name):
            return

        result = service.delete_reader(reader_id)

        if isinstance(result, Err):
            DP_CONTROLLER.standard_box(f"Failed to delete reader: {result.error}")
            return

        # If the deleted reader was the configured one, clear the config
        if reader_id == cfg.PAYMENT_SUMUP_TERMINAL_ID:
            cfg.PAYMENT_SUMUP_TERMINAL_ID = ""
            cfg.sync_config_to_file()

        DP_CONTROLLER.standard_box(f"Reader '{reader_name}' deleted successfully!")
        self._load_readers()
