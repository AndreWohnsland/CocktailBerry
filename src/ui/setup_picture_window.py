from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QPixmap

from src.ui_elements import Ui_PictureWindow

from src.models import Cocktail
from src.display_controller import DP_CONTROLLER
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE
from src.ui.icons import ICONS
from src.config_manager import CONFIG as cfg
from src.image_utils import find_user_cocktail_image, find_default_cocktail_image

PICTURE_SIZE = int(min(cfg.UI_WIDTH * 0.5, cfg.UI_HEIGHT * 0.65))


class PictureWindow(QMainWindow, Ui_PictureWindow):
    """ Class for the Progress screen during Cocktail making. """

    def __init__(self, cocktail: Cocktail):
        super().__init__()
        self.setupUi(self)
        self.cocktail = cocktail
        DP_CONTROLLER.initialize_window_object(self)
        self.button_back.clicked.connect(self.close)
        self.button_enter.clicked.connect(self._set_picture)
        self.button_remove.clicked.connect(self._remove_picture)
        self.button_upload.clicked.connect(self._prepare_picture)
        ICONS.set_picture_window_icons(self)
        UI_LANGUAGE.adjust_picture_window(self, cocktail.name)
        self._get_pictures()
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _set_picture(self):
        """Uploads the picture to the user folder"""
        # TODO: Implement

    def _remove_picture(self):
        """Removes the picture from the user folder"""
        # TODO: Implement
        if not DP_CONTROLLER.ask_to_remove_picture():
            return

    def _prepare_picture(self):
        """Crops and show the picture"""
        # TODO: Implement

    def _get_pictures(self):
        """Populates the pictures for system and user"""
        self.system_image_path = find_default_cocktail_image(self.cocktail)
        default_pixmap = QPixmap(str(self.system_image_path))
        self.picture_system.setPixmap(default_pixmap)
        self.user_image_path = find_user_cocktail_image(self.cocktail)
        if self.user_image_path is None:
            return
        user_pixmap = QPixmap(str(self.user_image_path))
        self.picture_user.setPixmap(user_pixmap)
