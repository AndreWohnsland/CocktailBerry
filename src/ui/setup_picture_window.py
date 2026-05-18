from __future__ import annotations

from collections.abc import Callable

from PIL import Image
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap, QResizeEvent
from PyQt6.QtWidgets import QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.image_utils import find_default_cocktail_image, find_user_cocktail_image, process_image, save_image
from src.models import Cocktail
from src.ui.creation_utils import apply_responsive_layouts
from src.ui.icons import IconSetter
from src.ui_elements import Ui_PictureWindow


class PictureWindow(QMainWindow, Ui_PictureWindow):
    """Class for the Progress screen during Cocktail making."""

    def __init__(self, cocktail: Cocktail, refresh_cocktail_view: Callable) -> None:
        super().__init__()
        self.setupUi(self)
        self.cocktail = cocktail
        self.new_picture: Image.Image | None = None
        self.system_pixmap: QPixmap | None = None
        self.user_pixmap: QPixmap | None = None
        self.refresh_cocktail_view = refresh_cocktail_view
        DP_CONTROLLER.initialize_window_object(self)
        self.button_back.clicked.connect(self.close)
        self.button_enter.clicked.connect(self._set_picture)
        self.button_remove.clicked.connect(self._remove_picture)
        self.button_upload.clicked.connect(self._prepare_picture)
        icons = IconSetter()
        icons.set_picture_window_icons(self)
        UI_LANGUAGE.adjust_picture_window(self, cocktail.name)
        self._get_pictures()
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        """Flip layout_maker_detail based on window width and resize image to fit its container."""
        super().resizeEvent(a0)
        apply_responsive_layouts(self.width(), [self.layout_image])
        QTimer.singleShot(0, self._update_pixmaps)

    def _update_pixmaps(self) -> None:
        """Re-scale stored pixmaps to fit their labels while keeping aspect ratio."""
        if self.system_pixmap is not None:
            scaled = self.system_pixmap.scaled(
                self.picture_system.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.picture_system.setPixmap(scaled)
        if self.user_pixmap is not None:
            scaled = self.user_pixmap.scaled(
                self.picture_user.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.picture_user.setPixmap(scaled)

    def _set_picture(self) -> None:
        """Upload the picture to the user folder."""
        if self.new_picture is not None:
            save_image(self.new_picture, self.cocktail.id)
            # call the on close method (refresh the cocktail view)
            self.refresh_cocktail_view()
        self.close()

    def _remove_picture(self) -> None:
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

    def _prepare_picture(self) -> None:
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
        self.user_pixmap = pixmap
        self._update_pixmaps()

    def _get_pictures(self) -> None:
        """Populate the pictures for system and user."""
        self.system_image_path = find_default_cocktail_image(self.cocktail)
        # it should always exist, but just in case the user deleted it or some other weird thing happened
        if self.system_image_path.exists():
            self.system_pixmap = QPixmap(str(self.system_image_path))
        self.user_image_path = find_user_cocktail_image(self.cocktail)
        # no image provided by the user, or the image was deleted, return
        if self.user_image_path is not None and self.user_image_path.exists():
            self.user_pixmap = QPixmap(str(self.user_image_path))
        self._update_pixmaps()
