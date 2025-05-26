from __future__ import annotations

import csv
import datetime
from pathlib import Path

from src.filepath import SAVE_FOLDER
from src.logger_handler import LoggerHandler
from src.migration.update_data import _try_execute_db_commands, execute_raw_sql

_logger = LoggerHandler("export_tables_migration")


def add_export_tables_to_db() -> None:
    """Add tables for storing export data in the database instead of CSV files."""
    _logger.log_event("INFO", "Adding export tables to database")
    commands = [
        """CREATE TABLE IF NOT EXISTS CocktailExport (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Export_Date DATE NOT NULL DEFAULT (date('now')),
            Recipe_Name TEXT NOT NULL,
            Counter INTEGER NOT NULL
        );""",
        """CREATE TABLE IF NOT EXISTS IngredientExport (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Export_Date DATE NOT NULL DEFAULT (date('now')),
            Ingredient_Name TEXT NOT NULL,
            Consumption INTEGER NOT NULL,
            Cost_Consumption INTEGER NOT NULL
        );""",
        "CREATE INDEX IF NOT EXISTS idx_cocktail_export_date ON CocktailExport (Export_Date);",
        "CREATE INDEX IF NOT EXISTS idx_cocktail_export_recipe ON CocktailExport (Recipe_Name);",
        "CREATE INDEX IF NOT EXISTS idx_ingredient_export_date ON IngredientExport (Export_Date);",
        "CREATE INDEX IF NOT EXISTS idx_ingredient_export_ingredient ON IngredientExport (Ingredient_Name);",
    ]
    _try_execute_db_commands(commands)


def migrate_csv_export_data_to_db() -> None:
    """Migrate existing CSV export data to the database tables."""
    _logger.log_event("INFO", "Migrating existing CSV export data to database")
    recipe_files = list(SAVE_FOLDER.glob("*_Recipe*.csv"))

    if not recipe_files:
        _logger.log_event("INFO", "No export files found, skipping migration")
        return

    # Extract dates from recipe files (which should always exist)
    export_dates = set()
    for file_path in recipe_files:
        date_str = file_path.name.split("_")[0]
        try:
            datetime.datetime.strptime(date_str, "%Y%m%d")
            export_dates.add(date_str)
        except ValueError:
            _logger.log_event("WARNING", f"Could not parse date from filename: {file_path.name}")
            continue

    migrated_csv_count = 0
    for date_str in sorted(export_dates):
        # Find the earliest export for this date (to handle multiple exports on same day)
        date_recipe_files = sorted([f for f in recipe_files if f.name.startswith(f"{date_str}_Recipe")])

        if not date_recipe_files:
            continue

        recipe_file = date_recipe_files[0]
        ingredient_files = sorted(SAVE_FOLDER.glob(f"{date_str}_Ingredient*.csv"))
        cost_files = sorted(SAVE_FOLDER.glob(f"{date_str}_Cost*.csv"))
        ingredient_file = ingredient_files[0] if ingredient_files else None
        cost_file = cost_files[0] if cost_files else None

        if not ingredient_file:
            _logger.log_event("WARNING", f"Missing ingredient file for date {date_str}, skipping")
            continue

        try:
            export_date = datetime.datetime.strptime(date_str, "%Y%m%d").date()
        except ValueError:
            _logger.log_event("ERROR", f"Invalid date format in {date_str}, skipping")
            continue

        _migrate_recipe_export_file(recipe_file, export_date)
        _migrate_ingredient_export_file(ingredient_file, cost_file, export_date)

        migrated_csv_count += 1
    _logger.log_event("INFO", f"Migrated {migrated_csv_count} csv export files")


def _migrate_recipe_export_file(recipe_file: Path, export_date: datetime.date) -> None:
    """Migrate a single recipe export file to the database."""
    needed_document_rows = 2
    try:
        with recipe_file.open(encoding="utf-8") as csv_file:
            reader = csv.reader(csv_file)
            rows = list(reader)

            if len(rows) < needed_document_rows:
                return

            # First row contains headers with recipe names
            recipe_names = rows[0][1:]
            # Second row contains consumption values
            consumption_values = rows[1][1:]

            for recipe_name, consumption in zip(recipe_names, consumption_values):
                ing_consumption = int(float(consumption))
                if ing_consumption <= 0:
                    continue

                execute_raw_sql(
                    "INSERT INTO CocktailExport (Export_Date, Recipe_Name, Counter) VALUES (?, ?, ?)",
                    (export_date, recipe_name, ing_consumption),
                )

        recipe_file.unlink()
    except Exception as e:
        _logger.log_event("ERROR", f"Error migrating recipe export file {recipe_file}: {e!s}")


def _migrate_ingredient_export_file(
    ingredient_file: Path, cost_file_path: Path | None, export_date: datetime.date
) -> None:
    """Migrate a single ingredient export file with its cost data to the database."""
    needed_document_rows = 2
    document_with_cost_rows = 3
    try:
        with ingredient_file.open(encoding="utf-8") as csv_file:
            reader = csv.reader(csv_file)
            rows = list(reader)

            if len(rows) < needed_document_rows:
                return

            # First row contains headers with ingredient names
            ingredient_names = rows[0][1:]
            # Second row contains consumption values
            consumption_values = rows[1][1:]

            # Read cost data if available
            cost_data = {}
            if cost_file_path and cost_file_path.exists():
                with cost_file_path.open(encoding="utf-8") as cost_file:
                    cost_reader = csv.reader(cost_file)
                    cost_rows = list(cost_reader)

                    if len(cost_rows) >= document_with_cost_rows:
                        cost_names = cost_rows[0][1:]
                        cost_values = cost_rows[1][1:]

                        for cost_name, cost_value in zip(cost_names, cost_values):
                            cost_data[cost_name] = int(float(cost_value))
                cost_file_path.unlink()

            for ingredient_name, consumption in zip(ingredient_names, consumption_values):
                int_consumption = int(float(consumption))
                if int_consumption <= 0:
                    continue

                cost_consumption = cost_data.get(ingredient_name, 0)

                execute_raw_sql(
                    """INSERT INTO IngredientExport (Export_Date, Ingredient_Name, Consumption, Cost_Consumption)
                    VALUES (?, ?, ?, ?)""",
                    (export_date, ingredient_name, int_consumption, cost_consumption),
                )

        ingredient_file.unlink()
    except Exception as e:
        _logger.log_event("ERROR", f"Error migrating ingredient export file {ingredient_file}: {e!s}")
