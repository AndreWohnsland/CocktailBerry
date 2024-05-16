# pylint: disable=wrong-import-order,wrong-import-position,ungrouped-imports
from src.migration.migrator import Migrator

# Migrations need to be made before imports, otherwise new needed packages will break the program
migrator = Migrator()
migrator.make_migrations()

from src.programs.cli import cli


if __name__ == "__main__":
    cli()
