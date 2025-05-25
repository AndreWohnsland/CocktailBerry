from typing import Optional

import typer

from src.api.api import run_api
from src.config.config_manager import version_callback
from src.programs.common_cli import register_common_commands

cli = typer.Typer(add_completion=False)


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


register_common_commands(cli)
