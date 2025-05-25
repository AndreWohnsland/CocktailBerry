import typer

from src.filepath import NGINX_SCRIPT, WEB_MIGRATION_SCRIPT
from src.migration.squeekboard import create_and_start_squeekboard_service, stop_and_disable_squeekboard_service
from src.migration.web_migrator import add_web_desktop_file, replace_backend_script
from src.utils import create_ap, delete_ap, get_platform_data


def register_common_commands(cli: typer.Typer) -> None:
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
