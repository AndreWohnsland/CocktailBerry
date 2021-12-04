import sys
from PyQt5.QtWidgets import QApplication
from src.error_handler import logerror

from src_ui.setup_mainwindow import MainScreen
from config.config_manager import ConfigManager


@logerror
def main():
    c_manager = ConfigManager()
    c_manager.sync_config_to_file()
    app = QApplication(sys.argv)
    MainScreen()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
