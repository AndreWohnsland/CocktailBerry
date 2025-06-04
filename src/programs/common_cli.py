import subprocess
from pathlib import Path
from typing import Optional

import typer

from src.filepath import NGINX_SCRIPT, QT_MIGRATION_SCRIPT, WEB_MIGRATION_SCRIPT
from src.migration.qt_migrator import roll_back_to_qt_script
from src.migration.squeekboard import create_and_start_squeekboard_service, stop_and_disable_squeekboard_service
from src.migration.web_migrator import add_web_desktop_file, replace_backend_script
from src.programs.addons import generate_addon_skeleton
from src.programs.clearing import clear_local_database
from src.programs.data_import import importer
from src.programs.microservice_setup import LanguageChoice, setup_service, setup_teams
from src.utils import create_ap, delete_ap, get_platform_data


def register_common_commands(cli: typer.Typer) -> None:  # noqa: C901, PLR0915
    _platform_data = get_platform_data()

    @cli.command()
    def setup_web(
        use_ssl: bool = typer.Option(False, "--ssl", "-s", help="Use SSL for the Nginx configuration"),
    ) -> None:
        """Set up the web interface."""
        if _platform_data.system == "Windows":
            print("Web setup is not supported on Windows")
            return
        replace_backend_script()
        add_web_desktop_file()
        import subprocess

        subprocess.run(["sudo", "python", str(WEB_MIGRATION_SCRIPT.absolute())], check=True)
        subprocess.run(["sudo", "python", str(NGINX_SCRIPT.absolute()), "--ssl" if use_ssl else "--no-ssl"], check=True)
        typer.echo(typer.style("Web setup was successful!", fg=typer.colors.GREEN, bold=True))

    @cli.command()
    def add_virtual_keyboard() -> None:
        """Add and start the virtual keyboard service."""
        create_and_start_squeekboard_service()
        typer.echo(typer.style("Virtual keyboard added and started successfully!", fg=typer.colors.GREEN, bold=True))

    @cli.command()
    def remove_virtual_keyboard() -> None:
        """Stop and disable the virtual keyboard service."""
        stop_and_disable_squeekboard_service()
        typer.echo(typer.style("Virtual keyboard stopped and disabled successfully!", fg=typer.colors.GREEN, bold=True))

    @cli.command()
    def setup_ap(
        ssid: str = typer.Option("CocktailBerry", "--ssid", help="SSID Name of the AP"),
        password: str = typer.Option("cocktailconnect", "--password", help="Password of the AP"),
    ) -> None:
        """Set up the access point."""
        required_password_chars = 8
        if len(password) < required_password_chars:
            typer.echo(typer.style("Password must be at least 8 characters long.", fg=typer.colors.RED, bold=True))
            raise typer.Exit(code=1)
        create_ap(ssid, password)
        msg = f"Access Point {ssid=} created with {password=} successfully!"
        typer.echo(typer.style(msg, fg=typer.colors.GREEN, bold=True))
        typer.echo("Within it, CocktailBerry is at: http://10.42.0.1 or https://10.42.0.1")

    @cli.command()
    def remove_ap(ssid: str = typer.Option("CocktailBerry", "--ssid", help="SSID Name of the AP")) -> None:
        """Remove the access point."""
        delete_ap(ssid)
        typer.echo(typer.style(f"Access Point {ssid=} removed successfully!", fg=typer.colors.GREEN, bold=True))
        delete_ap(ssid)
        typer.echo(typer.style(f"Access Point {ssid=} removed successfully!", fg=typer.colors.GREEN, bold=True))

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
        Within the prompts, you can reset the value to the default one, or skip this value if it should not be changed.
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
