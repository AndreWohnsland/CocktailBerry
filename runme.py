import sys
from PyQt5.QtWidgets import QApplication

import src_ui.setup_mainwindow as setupui
from config.config_manager import ConfigManager


if __name__ == "__main__":
    c_manager = ConfigManager()
    c_manager.sync_config_to_file()
    app = QApplication(sys.argv)
    w = setupui.MainScreen()
    w.showFullScreen()
    w.setFixedSize(800, 480)
    sys.exit(app.exec_())
