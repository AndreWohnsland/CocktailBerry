# pylint: disable=unused-argument
import os
from typing import Optional

import typer

from src import PROJECT_NAME
from src.api.api import run_api
from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared, show_start_message, version_callback
from src.config.errors import ConfigError
from src.filepath import CUSTOM_CONFIG_FILE
from src.logger_handler import LoggerHandler
from src.machine.controller import MachineController
from src.programs.addons import ADDONS
from src.programs.calibration import run_calibration
from src.programs.cocktailberry import run_cocktailberry
from src.programs.common_cli import register_common_commands
from src.programs.config_window import run_config_window
from src.resource_stats import start_resource_tracker
from src.utils import generate_custom_style_file, time_print

_logger = LoggerHandler("cocktailberry")
cli = typer.Typer(add_completion=False)


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
    ADDONS.define_addon_configuration()
    # Load the config file and check for errors, update the config (sync new values if not present)
    try:
        cfg.read_local_config(update_config=True)
    except ConfigError as e:
        _logger.error(f"Config Error: {e}, check the config file. You can edit the file at: {CUSTOM_CONFIG_FILE}.")
        _logger.log_exception(e)
        time_print("Opening the config window to correct the error.")
        # just read in the config without validation
        cfg.read_local_config(validate=False)
        run_config_window(message=f"Config Error: {e}, please adjust this config!")
    if debug:
        os.environ.setdefault("DEBUG_MS", "True")
        _logger.info("Using debug mode")
    shared.is_v1 = True
    generate_custom_style_file()
    mc = MachineController()
    mc.init_machine()
    ADDONS.setup_addons()
    if calibration:
        run_calibration()
        return
    run_cocktailberry()


@cli.command()
def api(port: int = typer.Option(8000, "--port", "-p", help="Port for the FastAPI server")) -> None:
    """Run the FastAPI server.

    Can be used as an alternative way to control the machine, for example over an external program or a web ui.
    The FastAPI server will be started at the given port.
    See also https://docs.cocktailberry.org/web/.
    """
    run_api(port)


register_common_commands(cli)
