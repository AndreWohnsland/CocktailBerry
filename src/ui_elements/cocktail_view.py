from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QGridLayout, QFrame
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSizePolicy

from src.database_commander import DB_COMMANDER
from src.display_controller import DP_CONTROLLER
from src.models import Cocktail
from src.ui_elements.clickable_label import ClickableLabel
from src.ui_elements.touch_scroll_area import TouchScrollArea
from src.image_utils import find_cocktail_image
from src.config_manager import CONFIG as cfg
from src.ui.creation_utils import create_button
from src.ui.icons import ICONS, PresetIcon

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

# roughly take 240 px for image dimensions
N_COLUMNS = int(cfg.UI_WIDTH / 240)
# keep a 17% margin
SQUARE_SIZE = int(cfg.UI_WIDTH / (N_COLUMNS * 1.17))


def generate_image_block(cocktail: Cocktail, mainscreen: MainScreen):
    """Generates a image block for the given cocktail"""
    button = create_button(
        cocktail.name, font_size=14, min_h=0, max_h=35,
        max_w=SQUARE_SIZE, css_class="btn-inverted btn-half-top"
    )
    if cocktail.virgin_available:
        icon = ICONS.generate_icon(PresetIcon.virgin, ICONS.color.background)
        button.setIcon(icon)
        button.setIconSize(QSize(20, 20))
    label = ClickableLabel(cocktail.name)
    label.setProperty("cssClass", "cocktail-picture-view")
    cocktail_image = find_cocktail_image(cocktail)
    pixmap = QPixmap(str(cocktail_image))
    label.setPixmap(pixmap)
    label.setScaledContents(True)
    label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)  # type: ignore
    label.setMinimumSize(SQUARE_SIZE, SQUARE_SIZE)
    label.setMaximumSize(SQUARE_SIZE, SQUARE_SIZE)
    layout = QVBoxLayout()
    layout.setSpacing(0)
    layout.addWidget(button)
    layout.addWidget(label)
    # take care of the button overload thingy, otherwise the first element will be a bool
    button.clicked.connect(
        lambda _, c=cocktail: mainscreen.open_cocktail_selection(c)
    )
    label.clicked.connect(
        lambda c=cocktail: mainscreen.open_cocktail_selection(c)
    )
    return layout


class CocktailView(QWidget):
    def __init__(self, mainscreen: MainScreen):
        super().__init__()
        self.scroll_area = TouchScrollArea()  # Create a QScrollArea
        self.scroll_area.setWidgetResizable(True)  # Make it resizable
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setFrameShape(QFrame.NoFrame)  # type: ignore
        self.scroll_area.setFrameShadow(QFrame.Plain)  # type: ignore

        self.grid = QGridLayout()
        self.grid.setVerticalSpacing(15)
        self.gridWidget = QWidget()  # Create a QWidget
        self.gridWidget.setLayout(self.grid)  # Set its layout to grid
        self.scroll_area.setWidget(self.gridWidget)  # Set the scroll area's widget to the QWidget with the grid layout

        self.vLayout = QVBoxLayout()
        self.vLayout.addWidget(self.scroll_area)
        self.setLayout(self.vLayout)

        self.mainscreen = mainscreen

    def populate_cocktails(self):
        """Adds the given cocktails to the grid"""
        DP_CONTROLLER.delete_items_of_layout(self.grid)
        cocktails = DB_COMMANDER.get_possible_cocktails()
        # sort cocktails by name
        cocktails.sort(key=lambda x: x.name.lower())
        # fill the grid with N_COLUMNS columns, then go to another row
        for i in range(0, len(cocktails), N_COLUMNS):
            for j in range(N_COLUMNS):
                if i + j >= len(cocktails):
                    break
                block = generate_image_block(
                    cocktails[i + j],
                    self.mainscreen,
                )
                self.grid.addLayout(block, i // N_COLUMNS, j)
