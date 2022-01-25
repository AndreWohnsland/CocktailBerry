import sys
import typer
from PyQt5.QtWidgets import QApplication

from src.error_handler import logerror
from src.config_manager import ConfigManager
from src.migrator import Migrator
from src.ui.setup_mainwindow import MainScreen
from src.calibration import run_calibration


@logerror
def run_cocktailmaker():
    migrator = Migrator()
    migrator.make_migrations()
    c_manager = ConfigManager()
    c_manager.sync_config_to_file()
    app = QApplication(sys.argv)
    MainScreen()
    sys.exit(app.exec_())


@logerror
def main(calibration: bool = typer.Option(False, "--calibration", "-c", help="Run the calibration program.")):
    if calibration:
        run_calibration()
    run_cocktailmaker()


if __name__ == "__main__":
    typer.run(main)
