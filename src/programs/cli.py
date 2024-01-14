# pylint: disable=unused-argument
import os
from typing import Optional
from pathlib import Path
import typer

from src import PROJECT_NAME
from src.config_manager import CONFIG as cfg, version_callback, show_start_message
from src.migration.update_data import add_new_recipes_from_default_db
from src.programs.microservice_setup import setup_service, setup_teams, LanguageChoice
from src.utils import generate_custom_style_file
from src.programs.cocktailberry import run_cocktailberry
from src.programs.calibration import run_calibration
from src.programs.data_import import importer
from src.programs.clearing import clear_local_database
from src.programs.addons import ADDONS, generate_addon_skeleton


cli = typer.Typer(add_completion=False)


@cli.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    displayed_name: str = typer.Option(PROJECT_NAME, "--name", "-n", help="Name to display at start."),
    calibration: bool = typer.Option(False, "--calibration", "-c", help="Run the calibration program."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Hide machine name, version and platform data."),
    debug: bool = typer.Option(False, "--debug", "-d", help="Using debug instead of normal Endpoints."),
    version: Optional[bool] = typer.Option(
        None, "--version", "-V", callback=version_callback, help="Show current version.")
):
    """
    Starts the cocktail program. Optional, can start the calibration program.
    If you want to debug your microservice, you can use the --debug flag.

    For more information visit https://cocktailberry.readthedocs.io/ or https://github.com/AndreWohnsland/CocktailBerry.
    """
    if ctx.invoked_subcommand is not None:
        return
    if not quiet:
        show_start_message(displayed_name)
    ADDONS.setup_addons()
    cfg.sync_config_to_file()
    if debug:
        os.environ.setdefault('DEBUG_MS', 'True')
        print("Using debug mode")
    generate_custom_style_file()
    if calibration:
        run_calibration()
    run_cocktailberry()


@cli.command()
def data_import(
    path: Path,
    conversion: float = typer.Option(1.0, "--conversion", "-c", help="Conversion factor to ml"),
    no_unit: bool = typer.Option(False, "--no-unit", "-nu", help="Ingredient data got no unit text"),
):
    """
    Imports the recipe data from a file.
    If the units are not in ml, please provide the conversion factor into ml.

    The file should contain the cocktail name, followed by ingredient data (amount, name).
    For further information regarding the file structure,
    please see https://cocktailberry.readthedocs.io/commands/#importing-recipes-from-file.
    """
    importer(path, conversion, no_unit)


@cli.command()
def update_database():
    """
    Using the default provided database to check for newly added recipes due to new updates.
    Adds the new recipes including missing ingredients to the local database.
    Ignore recipes that collide with names of your self-added recipes.
    Creates a backup before doing the update,
    see also https://cocktailberry.readthedocs.io/troubleshooting/#restoring-database

    Please take note that the ingredients are in german, so if you renamed your ingredients,
    this will most likely add all ingredients from the new recipes in german to your local database.
    If you are not satisfied the result, consult the documentation how to use the backup.
    You can also create a own backup with the build in CocktailBerry backup function over the program interface.
    More information also at https://cocktailberry.readthedocs.io/commands/#updating-local-database
    """
    add_new_recipes_from_default_db()


@cli.command()
def clear_database():
    """
    Clears the local database from the entered or default data.
    After this action, there will be no recipes or ingredients in your local CocktailBerry data.
    A backup of your local database is created before deleting.
    Use this if you want to build your own custom database and not use any of the supplied data.
    See also: https://cocktailberry.readthedocs.io/commands/#clearing-local-database
    """
    clear_local_database()


@cli.command()
def create_addon(addon_name: str):
    """
    Creates the base file for an addon under the given name.
    The file is saved under the addons folder.
    File name will be the name converted to lower case, space are replaced with underscores
    and stripped of special characters.
    """
    generate_addon_skeleton(addon_name)


@cli.command()
def setup_microservice(
    api_key: Optional[str] = typer.Option(None, "--api-key", "-a", help="API key for dashboard"),
    hook_endpoint: Optional[str] = typer.Option(None, "--hook-endpoint", "-e", help="Custom hook endpoint"),
    hook_header: Optional[str] = typer.Option(None, "--hook-header", "-h", help="Custom hook headers"),
    use_v1: bool = typer.Option(False, "--old-compose", "-o", help="Use compose v1"),
):
    """
    Set up the microservice.
    If the API key, hook endpoint or hook header is not provided as an option, prompts the user for the values.
    Within the prompts, you can reset the value to the default one, or also skip this value if it should not be changed.
    A compose file will be created in the home directory, if this command was not already run once.
    If this file already exists, the values will be replaced with the provided ones.
    If you are using compose version 1, please specify the flag.
    """
    setup_service(api_key, hook_endpoint, hook_header, use_v1)


@cli.command()
def setup_teams_service(
    language: LanguageChoice = typer.Option(LanguageChoice.ENGLISH, "--language",
                                            "-l", help="language for the teams service"),
):
    """
    Set up the teams microservice.
    You can use english [en] or german [de] as language.
    Will run the frontend at localhost:8050 (http://localhost:8050), backend at localhost:8080 (http://localhost:8080).
    """
    setup_teams(language)
