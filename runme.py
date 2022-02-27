# pylint: disable=unused-argument,wrong-import-order,wrong-import-position,ungrouped-imports
from src.migrator import Migrator

# Migrations need to be made before imports, otherwise new needed packages will break the program
migrator = Migrator()
migrator.make_migrations()

import sys
from typing import Optional
import typer
from PyQt5.QtWidgets import QApplication
from pyfiglet import Figlet

from src.error_handler import logerror
from src.config_manager import ConfigManager, version_callback
from src.ui.setup_mainwindow import MainScreen
from src.calibration import run_calibration
from src import __version__, PROJECT_NAME


cli = typer.Typer(add_completion=False)


@logerror
def run_cocktailmaker():
    """Executes the cocktail maker"""
    c_manager = ConfigManager()
    c_manager.sync_config_to_file()
    app = QApplication(sys.argv)
    MainScreen()
    sys.exit(app.exec_())


@cli.command()
def main(
    calibration: bool = typer.Option(False, "--calibration", "-c", help="Run the calibration program."),
    version: Optional[bool] = typer.Option(None, "--version", callback=version_callback, help="Show current version.")
):
    """
    Starts the cocktail maker. Optional, can start the calibration program.
    For more information visit https://github.com/AndreWohnsland/Cocktailmaker_AW.
    """
    figlet = Figlet()
    start_message = f"{PROJECT_NAME} Version {__version__}"
    print(figlet.renderText(start_message))
    print(start_message)
    if calibration:
        run_calibration()
    run_cocktailmaker()


if __name__ == "__main__":
    cli()
