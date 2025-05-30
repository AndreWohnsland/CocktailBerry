# pylint: disable=unused-argument
import os
import subprocess
from pathlib import Path
from typing import Optional

import typer

from src import PROJECT_NAME
from src.api.api import run_api
from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared, show_start_message, version_callback
from src.config.errors import ConfigError
from src.filepath import CUSTOM_CONFIG_FILE, QT_MIGRATION_SCRIPT
from src.logger_handler import LoggerHandler
from src.migration.qt_migrator import roll_back_to_qt_script
from src.programs.addons import ADDONS, generate_addon_skeleton
from src.programs.calibration import run_calibration
from src.programs.clearing import clear_local_database
from src.programs.cocktailberry import run_cocktailberry
from src.programs.common_cli import register_common_commands
from src.programs.config_window import run_config_window
from src.programs.data_import import importer
from src.programs.microservice_setup import LanguageChoice, setup_service, setup_teams
from src.resource_stats import start_resource_tracker
from src.utils import generate_custom_style_file, get_platform_data, time_print

_logger = LoggerHandler("cocktailberry")
cli = typer.Typer(add_completion=False)
_platform_data = get_platform_data()


@cli.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    displayed_name: str = typer.Option(PROJECT_NAME, "--name", "-n", help="Name to display at start."),
    calibration: bool = typer.Option(False, "--calibration", "-c", help="Run the calibration program."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Hide machine name, version and platform data."),
    debug: bool = typer.Option(False, "--debug", "-d", help="Using debug instead of normal Endpoints."),
    version: Optional[bool] = typer.Option(
        None, "--version", "-V", callback=version_callback, help="Show current version."
    ),
) -> None:
    """Start the cocktail program. Optional, can start the calibration program.

    If you want to debug your microservice, you can use the --debug flag.
    For more information visit https://docs.cocktailberry.org/ or https://github.com/AndreWohnsland/CocktailBerry.
    """
    if ctx.invoked_subcommand is not None:
        return
    if not quiet:
        show_start_message(displayed_name)
    start_resource_tracker()
    ADDONS.setup_addons()
    # Load the config file and check for errors, update the config (sync new values if not present)
    try:
        cfg.read_local_config(update_config=True)
    except ConfigError as e:
        _logger.error(f"Config Error: {e}")
        _logger.log_exception(e)
        time_print(f"Config Error: {e}, please check the config file. You can edit the file at: {CUSTOM_CONFIG_FILE}.")
        time_print("Opening the config window to correct the error.")
        # just read in the config without validation
        cfg.read_local_config(validate=False)
        run_config_window(message=f"Config Error: {e}, please adjust this config!")
    if debug:
        os.environ.setdefault("DEBUG_MS", "True")
        time_print("Using debug mode")
    shared.is_v1 = True
    generate_custom_style_file()
    if calibration:
        run_calibration()
        return
    run_cocktailberry()


@cli.command()
def data_import(
    path: Path,
    conversion: float = typer.Option(1.0, "--conversion", "-c", help="Conversion factor to ml"),
    no_unit: bool = typer.Option(False, "--no-unit", "-nu", help="Ingredient data got no unit text"),
) -> None:
    """Import the recipe data from a file.

    If the units are not in ml, please provide the conversion factor into ml.
    The file should contain the cocktail name, followed by ingredient data (amount, name).
    For further information regarding the file structure,
    please see https://docs.cocktailberry.org/commands/#importing-recipes-from-file.
    """
    importer(path, conversion, no_unit)


@cli.command()
def clear_database() -> None:
    """Clear the local database from the entered or default data.

    After this action, there will be no recipes or ingredients in your local CocktailBerry data.
    A backup of your local database is created before deleting.
    Use this if you want to build your own custom database and not use any of the supplied data.
    See also: https://docs.cocktailberry.org/commands/#clearing-local-database.
    """
    clear_local_database()


@cli.command()
def create_addon(addon_name: str) -> None:
    """Create the base file for an addon under the given name.

    The file is saved under the addons folder.
    File name will be the name converted to lower case, space are replaced with underscores
    and stripped of special characters.
    For more information see https://docs.cocktailberry.org/addons/#creating-addons.
    """
    generate_addon_skeleton(addon_name)


@cli.command()
def setup_microservice(
    api_key: Optional[str] = typer.Option(None, "--api-key", "-a", help="API key for dashboard"),
    hook_endpoint: Optional[str] = typer.Option(None, "--hook-endpoint", "-e", help="Custom hook endpoint"),
    hook_header: Optional[str] = typer.Option(None, "--hook-header", "-h", help="Custom hook headers"),
    use_v1: bool = typer.Option(False, "--old-compose", "-o", help="Use compose v1"),
) -> None:
    """Set up the microservice.

    If the API key, hook endpoint or hook header is not provided as an option, prompts the user for the values.
    Within the prompts, you can reset the value to the default one, or also skip this value if it should not be changed.
    A compose file will be created in the home directory, if this command was not already run once.
    If this file already exists, the values will be replaced with the provided ones.
    If you are using compose version 1, please specify the flag.
    For more context, see https://docs.cocktailberry.org/advanced/#installation-of-services.
    """
    setup_service(api_key, hook_endpoint, hook_header, use_v1)


@cli.command()
def setup_teams_service(
    language: LanguageChoice = typer.Option(
        LanguageChoice.ENGLISH, "--language", "-l", help="language for the teams service"
    ),
) -> None:
    """Set up the teams microservice.

    You can use english [en] or german [de] as language.
    Will run the frontend at localhost:8050 (http://localhost:8050), backend at localhost:8080 (http://localhost:8080).
    See also https://docs.cocktailberry.org/advanced/#dashboard-with-teams.
    """
    setup_teams(language)


@cli.command()
def api(port: int = typer.Option(8000, "--port", "-p", help="Port for the FastAPI server")) -> None:
    """Run the FastAPI server.

    Can be used as an alternative way to control the machine, for example over an external program or a web ui.
    The FastAPI server will be started at the given port.
    See also https://docs.cocktailberry.org/web/.
    """
    run_api(port)


@cli.command()
def switch_back() -> None:
    """Switch back to the Qt setup.

    This will switch back to the Qt setup for CocktailBerry.
    This is an alternative setup and overwrites the current app.
    The web interface will be removed.
    See also https://docs.cocktailberry.org/web/.
    """
    if _platform_data.system == "Windows":
        print("Web setup is not supported on Windows")
        return
    roll_back_to_qt_script()
    subprocess.run(["sudo", "python", str(QT_MIGRATION_SCRIPT.absolute())], check=True)
    typer.echo(typer.style("Switched back to Qt setup successfully!", fg=typer.colors.GREEN, bold=True))


register_common_commands(cli)
