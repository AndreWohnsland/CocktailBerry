from typing import Callable

from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QMainWindow

from src.config_manager import CONFIG as cfg
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.image_utils import find_default_cocktail_image, find_user_cocktail_image, process_image, save_image
from src.models import Cocktail
from src.ui.icons import ICONS
from src.ui_elements import Ui_PictureWindow

PICTURE_SIZE = int(min(cfg.UI_WIDTH * 0.5, cfg.UI_HEIGHT * 0.65))


class PictureWindow(QMainWindow, Ui_PictureWindow):
    """Class for the Progress screen during Cocktail making."""

    def __init__(self, cocktail: Cocktail, refresh_cocktail_view: Callable):
        super().__init__()
        self.setupUi(self)
        self.cocktail = cocktail
        self.new_picture = None
        self.refresh_cocktail_view = refresh_cocktail_view
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
        """Upload the picture to the user folder."""
        if self.new_picture is not None:
            save_image(self.new_picture, self.cocktail.id)
            # call the on close method (refresh the cocktail view)
            self.refresh_cocktail_view()
        self.close()

    def _remove_picture(self):
        """Remove the picture from the user folder."""
        if not DP_CONTROLLER.ask_to_remove_picture():
            return
        if self.user_image_path is None:
            return
        # remove the pixmap from picture_user
        self.picture_user.clear()
        # remove the file from the user folder
        self.user_image_path.unlink()
        self.picture_user.setText("No Image\nAvailable")
        self.refresh_cocktail_view()

    def _prepare_picture(self):
        """Crops and show the picture."""
        selected_path = DP_CONTROLLER.ask_for_image_location()
        if selected_path is None:
            return
        image = process_image(selected_path)
        if image is None:
            DP_CONTROLLER.say_image_processing_failed()
            return
        self.new_picture = image
        q_image = QImage(
            image.tobytes("raw", "RGB"),
            image.width,
            image.height,
            QImage.Format.Format_RGB888,
        )
        pixmap = QPixmap.fromImage(q_image)
        self.picture_user.setPixmap(pixmap)

    def _get_pictures(self):
        """Populate the pictures for system and user."""
        self.system_image_path = find_default_cocktail_image(self.cocktail)
        # it should always exist, but just in case the user deleted it or some other weird thing happened
        if self.system_image_path.exists():
            default_pixmap = QPixmap(str(self.system_image_path))
            self.picture_system.setPixmap(default_pixmap)
        self.user_image_path = find_user_cocktail_image(self.cocktail)
        # no image provided by the user, or the image was deleted, return
        if self.user_image_path is None or not self.user_image_path.exists():
            return
        user_pixmap = QPixmap(str(self.user_image_path))
        self.picture_user.setPixmap(user_pixmap)
