# pylint: disable=unused-argument,wrong-import-order,wrong-import-position,ungrouped-imports
from src.migrator import Migrator
# Migrations need to be made before imports, otherwise new needed packages will break the program
migrator = Migrator()
migrator.make_migrations()

import os
from typing import Optional
import typer

from src.config_manager import ConfigManager, version_callback, show_start_message
from src.programs.cocktailberry import run_cocktailberry
from src.programs.calibration import run_calibration


cli = typer.Typer(add_completion=False)


@cli.command()
def main(
    calibration: bool = typer.Option(False, "--calibration", "-c", help="Run the calibration program."),
    debug: bool = typer.Option(False, "--debug", "-d", help="Using debug instead of normal Endpoints."),
    version: Optional[bool] = typer.Option(None, "--version", callback=version_callback, help="Show current version.")
):
    """
    Starts the cocktail program. Optional, can start the calibration program.
    If you want to debug your microservice, you can use the --debug flag.

    For more information visit https://github.com/AndreWohnsland/CocktailBerry.
    """
    show_start_message()
    c_manager = ConfigManager()
    c_manager.sync_config_to_file()
    if debug:
        os.environ.setdefault('DEBUG_MS', 'True')
        print("Using debug mode")
    if calibration:
        run_calibration()
    run_cocktailberry()


if __name__ == "__main__":
    cli()
