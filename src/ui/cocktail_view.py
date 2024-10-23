from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFrame, QGridLayout, QSizePolicy, QVBoxLayout, QWidget

from src.config.config_manager import CONFIG as cfg
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.filepath import DEFAULT_COCKTAIL_IMAGE
from src.image_utils import find_cocktail_image
from src.models import Cocktail
from src.ui.creation_utils import create_button
from src.ui.icons import ICONS, PresetIcon
from src.ui_elements.clickable_label import ClickableLabel
from src.ui_elements.touch_scroll_area import TouchScrollArea

if TYPE_CHECKING:
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


def generate_image_block(cocktail: Cocktail | None, mainscreen: MainScreen):
    """Generate a image block for the given cocktail."""
    # those factors are taken from calculations based on the old static values
    square_size = _square_size()
    header_font_size = round(square_size / 15.8)
    header_height = round(square_size / 6.3)
    single_ingredient_label = UI_LANGUAGE.get_translation("label_single_ingredient", "main_window")
    name_label = cocktail.name if cocktail is not None else single_ingredient_label
    button = create_button(
        name_label,
        font_size=header_font_size,
        min_h=0,
        max_h=header_height,
        max_w=square_size,
        css_class="btn-inverted btn-half-top",
    )
    if cocktail is not None and cocktail.virgin_available:
        icon = ICONS.generate_icon(PresetIcon.virgin, ICONS.color.background)
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
        button.clicked.connect(lambda _, c=cocktail: mainscreen.open_cocktail_selection(c))
        label.clicked.connect(lambda c=cocktail: mainscreen.open_cocktail_selection(c))
    else:
        button.clicked.connect(mainscreen.open_ingredient_window)
        label.clicked.connect(mainscreen.open_ingredient_window)
    return layout


class CocktailView(QWidget):
    def __init__(self, mainscreen: MainScreen):
        super().__init__()
        self.scroll_area = TouchScrollArea()  # Create a QScrollArea
        self.scroll_area.setWidgetResizable(True)  # Make it resizable
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setFrameShape(QFrame.NoFrame)  # type: ignore
        self.scroll_area.setFrameShadow(QFrame.Plain)  # type: ignore
        # no horizontal scroll bar
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # type: ignore

        self.grid = QGridLayout()
        self.grid.setVerticalSpacing(15)
        self.grid_widget = QWidget()  # Create a QWidget
        self.grid_widget.setLayout(self.grid)  # Set its layout to grid
        self.scroll_area.setWidget(self.grid_widget)  # Set the scroll area's widget to the QWidget with the grid layout

        self.vertical_layout = QVBoxLayout()
        self.vertical_layout.addWidget(self.scroll_area)
        self.setLayout(self.vertical_layout)

        self.mainscreen = mainscreen

    def populate_cocktails(self):
        """Add the given cocktails to the grid."""
        n_columns = _n_columns()
        DP_CONTROLLER.delete_items_of_layout(self.grid)
        cocktails = DB_COMMANDER.get_possible_cocktails(cfg.MAKER_MAX_HAND_INGREDIENTS)
        # sort cocktails by name
        cocktails.sort(key=lambda x: x.name.lower())
        # add last "filler" element, this is for the single ingredient element
        if cfg.MAKER_ADD_SINGLE_INGREDIENT:
            cocktails = [*cocktails, None]
        # fill the grid with n_columns columns, then go to another row
        for i in range(0, len(cocktails), n_columns):
            for j in range(n_columns):
                if i + j >= len(cocktails):
                    break
                block = generate_image_block(
                    cocktails[i + j],
                    self.mainscreen,
                )
                self.grid.addLayout(block, i // n_columns, j)
