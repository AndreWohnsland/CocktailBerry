from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import QSize, Qt, QMetaObject, Q_ARG
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFrame, QGridLayout, QSizePolicy, QVBoxLayout, QWidget

from src.config.config_manager import CONFIG as cfg
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.filepath import DEFAULT_COCKTAIL_IMAGE
from src.image_utils import find_cocktail_image
from src.models import Cocktail
from src.payment_utils import filter_cocktails_by_user
from src.programs.nfc_payment_service import NFCPaymentService
from src.ui.creation_utils import create_button, create_label
from src.ui.icons import IconSetter, PresetIcon
from src.ui_elements.clickable_label import ClickableLabel
from src.ui_elements.touch_scroll_area import TouchScrollArea
from src.utils import time_print

if TYPE_CHECKING:
    from src.programs.nfc_payment_service import User
    from src.ui.setup_mainwindow import MainScreen


def _n_columns() -> int:
    """Return calculated number of columns for the cocktail view."""
    # Need method, since config will be loaded in at runtime
    # default: roughly take 240 px for image dimensions
    n_columns = int(cfg.UI_WIDTH / cfg.UI_PICTURE_SIZE)
    # in some cases this value can be zero, so we need to make sure it's at least 1
    return max(n_columns, 1)


def _square_size() -> int:
    """Return calculated square size for the cocktail view."""
    # Need method, since config will be loaded in at runtime
    n_columns = _n_columns()
    # keep a 17% margin
    return int(cfg.UI_WIDTH / (n_columns * 1.17))


def generate_image_block(cocktail: Cocktail | None, mainscreen: MainScreen) -> QVBoxLayout:
    """Generate a image block for the given cocktail."""
    # those factors are taken from calculations based on the old static values
    square_size = _square_size()
    header_font_size = round(square_size / 15.8)
    header_height = round(square_size / 6.3)
    single_ingredient_label = UI_LANGUAGE.get_translation("label_single_ingredient", "main_window")
    name_label = single_ingredient_label if cocktail is None else cocktail.name
    button = create_button(
        name_label,
        font_size=header_font_size,
        min_h=0,
        max_h=header_height,
        max_w=square_size,
        css_class="btn-inverted btn-half-top",
    )
    icons = IconSetter()
    if cocktail is not None and cocktail.virgin_available:
        button.setText(f" {name_label}")
        icon = icons.generate_icon(PresetIcon.virgin, icons.color.background, border=cocktail.only_virgin)
        button.setIcon(icon)
        button.setIconSize(QSize(20, 20))
    label = ClickableLabel(name_label)
    label.setProperty("cssClass", "cocktail-picture-view")
    cocktail_image = DEFAULT_COCKTAIL_IMAGE if cocktail is None else find_cocktail_image(cocktail)
    pixmap = QPixmap(str(cocktail_image))
    label.setPixmap(pixmap)
    label.setScaledContents(True)
    label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)  # type: ignore
    label.setMinimumSize(square_size, square_size)
    label.setMaximumSize(square_size, square_size)
    layout = QVBoxLayout()
    layout.setSpacing(0)
    layout.addWidget(button)
    layout.addWidget(label)
    if cocktail is not None:
        # take care of the button overload thingy, otherwise the first element will be a bool
        button.clicked.connect(lambda _, c=cocktail: mainscreen.open_cocktail_detail(c))  # type: ignore[attr-defined]
        label.clicked.connect(lambda c=cocktail: mainscreen.open_cocktail_detail(c))
        button.setEnabled(cocktail.is_allowed)
        label.setEnabled(cocktail.is_allowed)
    else:
        button.clicked.connect(mainscreen.open_ingredient_window)  # type: ignore[attr-defined]
        label.clicked.connect(mainscreen.open_ingredient_window)
    return layout


class CocktailView(QWidget):
    def __init__(self, mainscreen: MainScreen) -> None:
        super().__init__()
        self.scroll_area = TouchScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setFrameShape(QFrame.NoFrame)  # type: ignore
        self.scroll_area.setFrameShadow(QFrame.Plain)  # type: ignore
        # no horizontal scroll bar
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # type: ignore

        self.grid = QGridLayout()
        self.grid.setVerticalSpacing(15)
        self.grid_widget = QWidget()
        self.grid_widget.setLayout(self.grid)
        self.scroll_area.setWidget(self.grid_widget)

        self.vertical_layout = QVBoxLayout()
        self.vertical_layout.addWidget(self.scroll_area)

        # Create NFC scan message label (hidden by default)
        self.info_label = create_label(
            text="",
            font_size=64,
            bold=True,
            centered=True,
            max_h=600,
            css_class="secondary",
            word_wrap=True,
        )
        self.info_label.hide()
        self.vertical_layout.addWidget(self.info_label)

        self.setLayout(self.vertical_layout)

        self.mainscreen = mainscreen

        # NFC polling timer for PyQt-safe threading
        self._nfc_poll_timer: QTimer | None = None
        self._last_known_user: User | None = None
        self.destroyed.connect(self._stop_nfc_polling)

    def _needs_nfc_user_protection(self) -> bool:
        """Check if NFC user protection is needed."""
        if not cfg.PAYMENT_ACTIVE:
            return False
        if not cfg.PAYMENT_LOCK_SCREEN_NO_USER:
            return False
        return self._last_known_user is None

    def _start_nfc_polling(self) -> None:
        """Start polling for NFC user login."""
        nfc_service = NFCPaymentService()
        # Stop any existing polling first, then start with our callback
        nfc_service.stop_polling()
        nfc_service.start_polling(self._on_user_change)

    def _stop_nfc_polling(self) -> None:
        """Stop the NFC polling."""
        nfc_service = NFCPaymentService()
        nfc_service.stop_polling()

    def _on_user_change(self, user: User | None, uid: str) -> None:
        """Callback when NFC user state changes.
        
        This callback may be invoked from a background thread, so we use
        QMetaObject.invokeMethod to ensure UI updates happen on the main thread.
        """
        # Use Qt's thread-safe mechanism to invoke the update on the main thread
        # Note: Q_ARG uses 'object' type as it's the correct Python type for Qt's marshalling
        QMetaObject.invokeMethod(
            self,
            "_on_user_change_impl",
            Qt.QueuedConnection,  # type: ignore
            Q_ARG(object, user),
            Q_ARG(str, uid),
        )
    
    def _on_user_change_impl(self, user: User | None, uid: str) -> None:
        """Implementation of user change handling (runs on main thread)."""
        if user == self._last_known_user:
            return
        time_print(f"NFC user state changed to {user} from {self._last_known_user}")
        self._last_known_user = user
        self._render_view()
        self.mainscreen.switch_to_cocktail_list()

    def _show_nfc_scan_message(self) -> None:
        """Show the NFC scan message and hide the cocktails grid."""
        self.scroll_area.hide()
        message = UI_LANGUAGE.get_translation("nfc_scan_to_proceed", "main_window")
        self.info_label.setText(message)
        self.info_label.show()

    def _populate_cocktails_grid(self) -> None:
        """Populate the cocktails grid (internal method)."""
        self.info_label.hide()
        self.scroll_area.show()

        n_columns = _n_columns()
        DP_CONTROLLER.delete_items_of_layout(self.grid)
        cocktails = DB_COMMANDER.get_possible_cocktails(cfg.MAKER_MAX_HAND_INGREDIENTS)
        # filter cocktails based on user criteria if payment is active
        if cfg.PAYMENT_ACTIVE:
            cocktails = filter_cocktails_by_user(self._last_known_user, cocktails)
            # remove if machine owner do not want to show not possible cocktails
            if not cfg.PAYMENT_SHOW_NOT_POSSIBLE:
                cocktails = [c for c in cocktails if c.is_allowed]
        # sort cocktails by name
        cocktails.sort(key=lambda x: x.name.lower())
        # fill the grid with n_columns columns, then go to another row
        for i in range(0, len(cocktails), n_columns):
            for j in range(n_columns):
                if i + j >= len(cocktails):
                    break
                block = generate_image_block(cocktails[i + j], self.mainscreen)
                self.grid.addLayout(block, i // n_columns, j)
        # Optionally add the single ingredient block after all cocktails
        if cfg.MAKER_ADD_SINGLE_INGREDIENT and not cfg.PAYMENT_ACTIVE:
            total = len(cocktails)
            row = total // n_columns
            col = total % n_columns
            block = generate_image_block(None, self.mainscreen)
            self.grid.addLayout(block, row, col)

    def _render_view(self) -> None:
        """Render the appropriate view based on current NFC user state."""
        if self._needs_nfc_user_protection():
            self._show_nfc_scan_message()
        else:
            self._populate_cocktails_grid()

    def populate_cocktails(self) -> None:
        """Add the given cocktails to the grid.

        If payment service is active and no user is logged in,
        shows a "Scan NFC to proceed" message instead of cocktails.
        Starts continuous polling to detect user login/logout/changes.
        """
        self._render_view()
        if cfg.PAYMENT_ACTIVE:
            self._start_nfc_polling()
