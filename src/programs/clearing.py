import typer

from src.database_commander import DB_COMMANDER as DBC
from src.logger_handler import LoggerHandler

_logger = LoggerHandler("clear_module")


def clear_local_database() -> None:
    """Remove the recipes, ingredients, links between them as well as entered bottles."""
    typer.confirm(
        "Delete local Database Data? This includes recipes and ingredients. A backup will be created before deletion.",
        abort=True,
    )
    DBC.create_backup()
    DBC.delete_database_data()
    _logger.log_event("INFO", "Data in local database was deleted by command.")
    typer.echo(typer.style("Local database is clean, time to enter new recipes", fg=typer.colors.GREEN, bold=True))
