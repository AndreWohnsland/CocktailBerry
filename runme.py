import sys
from PyQt5.QtWidgets import QApplication

from src.error_handler import logerror
from src.config_manager import ConfigManager
from src.migrator import Migrator
from src.ui.setup_mainwindow import MainScreen


@logerror
def main():
    migrator = Migrator()
    migrator.make_migrations()
    c_manager = ConfigManager()
    c_manager.sync_config_to_file()
    app = QApplication(sys.argv)
    MainScreen()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
