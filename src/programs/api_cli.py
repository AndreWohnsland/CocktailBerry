import subprocess
from typing import Optional

import typer

from src.api.api import run_api
from src.config.config_manager import version_callback
from src.filepath import NGINX_SCRIPT, WEB_MIGRATION_SCRIPT
from src.migration.squeekboard import create_and_start_squeekboard_service, stop_and_disable_squeekboard_service
from src.migration.web_migrator import add_web_desktop_file, replace_backend_script
from src.utils import create_ap, delete_ap, get_platform_data

cli = typer.Typer(add_completion=False)
_platform_data = get_platform_data()


@cli.callback(invoke_without_command=True)
def api(
    ctx: typer.Context,
    port: int = typer.Option(8000, "--port", "-p", help="Port for the FastAPI server"),
    version: Optional[bool] = typer.Option(
        None, "--version", "-V", callback=version_callback, help="Show current version."
    ),
) -> None:
    """Run the FastAPI server.

    Can be used as an alternative way to control the machine, for example over an external program or a web ui.
    The FastAPI server will be started at the given port.
    See also https://docs.cocktailberry.org/web/.
    """
    if ctx.invoked_subcommand is not None:
        return
    run_api(port)


@cli.command()
def setup_web(use_ssl: bool = typer.Option(False, "--ssl", "-s", help="Use SSL for the Nginx configuration")) -> None:
    """Set up the web interface.

    This will set up the web interface for CocktailBerry.
    This is an alternative setup and overwrites the current app.
    The web interface will be available at http://localhost or proxy it with Nginx to just localhost/the ip.
    The api will be available at http://localhost:8000.
    See also https://docs.cocktailberry.org/web/.
    """
    if _platform_data.system == "Windows":
        print("Web setup is not supported on Windows")
        return
    replace_backend_script()
    add_web_desktop_file()
    subprocess.run(["sudo", "python", str(WEB_MIGRATION_SCRIPT.absolute())], check=True)
    subprocess.run(["sudo", "python", str(NGINX_SCRIPT.absolute()), "--ssl" if use_ssl else "--no-ssl"], check=True)
    typer.echo(typer.style("Web setup was successful!", fg=typer.colors.GREEN, bold=True))


@cli.command()
def add_virtual_keyboard() -> None:
    """Add and start the virtual keyboard service.

    This will create, enable, and start the Squeekboard virtual keyboard service.
    The service will be set up to start automatically on boot.
    This enables the virtual keyboard as soon as you click on an input field.
    """
    create_and_start_squeekboard_service()
    typer.echo(typer.style("Virtual keyboard added and started successfully!", fg=typer.colors.GREEN, bold=True))


@cli.command()
def remove_virtual_keyboard() -> None:
    """Stop and disable the virtual keyboard service.

    This will stop and disable the Squeekboard virtual keyboard service.
    The service will no longer start automatically on boot.
    """
    stop_and_disable_squeekboard_service()
    typer.echo(typer.style("Virtual keyboard stopped and disabled successfully!", fg=typer.colors.GREEN, bold=True))


@cli.command()
def setup_ap(
    ssid: str = typer.Option("CocktailBerry", "--ssid", help="SSID Name of the AP"),
    password: str = typer.Option("cocktailconnect", "--password", help="Password of the AP"),
) -> None:
    """Set up the access point.

    The access point will be created on a virtual wlan1 interface.
    So you can still use the wlan0 interface for your normal network connection.
    This requires that you can have a virtual interface on your chip, for example the Raspberry Pi 3B+.
    """
    if len(password) < 8:
        typer.echo(typer.style("Password must be at least 8 characters long.", fg=typer.colors.RED, bold=True))
        raise typer.Exit(code=1)
    create_ap(ssid, password)
    msg = f"Access Point {ssid=} created with {password=} successfully!"
    typer.echo(typer.style(msg, fg=typer.colors.GREEN, bold=True))
    typer.echo("Within it, CocktailBerry is at: http://10.42.0.1 or https://10.42.0.1")


@cli.command()
def remove_ap(ssid: str = typer.Option("CocktailBerry", "--ssid", help="SSID Name of the AP")) -> None:
    """Remove the access point.

    Remove the given config for this access point and remove virtual wlan1 interface.
    """
    delete_ap(ssid)
    typer.echo(typer.style(f"Access Point {ssid=} removed successfully!", fg=typer.colors.GREEN, bold=True))
