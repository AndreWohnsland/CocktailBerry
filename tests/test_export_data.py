import datetime
from pathlib import Path
from typing import Any
from unittest.mock import call, mock_open, patch

from src.filepath import SAVE_FOLDER
from src.migration.export_data import migrate_csv_export_data_to_db


class TestExportData:
    """Test the export_data functionality."""

    def test_migrate_csv_export_data_to_db(self):
        """Test the migrate_csv_export_data_to_db function."""
        ingredient_csv_content = (
            "date,Fanta,Cola,Sprite,White Rum,Vodka,Gin\n2025-05-01,0,133,0,53,0,0\nlifetime,0,133,0,53,0,0\n"
        )
        recipe_csv_content = (
            "date,Cuba Libre,Tequila Sunrise,With Handadd,Black Sun,Blue Mara\n"
            "2025-05-01,5,0,3,1,2\n"
            "lifetime,5,0,3,1,2\n"
        )
        cost_csv_content = "date,Fanta,Cola,White Rum,Vodka\n2025-05-01,0,200,150,0\nlifetime,0,200,150,0\n"

        test_date = "20250501"
        recipe_file = Path(SAVE_FOLDER) / f"{test_date}_Recipe_export.csv"
        ingredient_file = Path(SAVE_FOLDER) / f"{test_date}_Ingredient_export.csv"
        cost_file = Path(SAVE_FOLDER) / f"{test_date}_Cost_export.csv"

        # Set up a custom file open mock that returns StringIO objects with the appropriate content
        mock_file_contents = {
            str(recipe_file): recipe_csv_content,
            str(ingredient_file): ingredient_csv_content,
            str(cost_file): cost_csv_content,
        }

        def mock_file_open(path: Any, *args: Any, **kwargs: Any):
            content = mock_file_contents.get(str(path), "")
            m = mock_open(read_data=content)
            return m()

        with (
            patch("pathlib.Path.glob") as mock_glob,
            patch("pathlib.Path.open", new=mock_file_open),
            patch("pathlib.Path.unlink") as mock_unlink,
            patch("pathlib.Path.exists", return_value=True),
            patch("src.migration.export_data.execute_raw_sql") as mock_execute_sql,
        ):
            # Configure mock_glob to return appropriate files for each pattern
            def glob_side_effect(pattern: str):
                if "_Recipe" in pattern:
                    return [recipe_file]
                if "_Ingredient" in pattern:
                    return [ingredient_file]
                if "_Cost" in pattern:
                    return [cost_file]
                return []

            mock_glob.side_effect = glob_side_effect

            migrate_csv_export_data_to_db()
            assert mock_unlink.call_count >= 3

            recipe_calls = [
                call(
                    "INSERT INTO CocktailExport (Export_Date, Recipe_Name, Counter) VALUES (?, ?, ?)",
                    (datetime.date(2025, 5, 1), "Cuba Libre", 5),
                ),
                call(
                    "INSERT INTO CocktailExport (Export_Date, Recipe_Name, Counter) VALUES (?, ?, ?)",
                    (datetime.date(2025, 5, 1), "With Handadd", 3),
                ),
                call(
                    "INSERT INTO CocktailExport (Export_Date, Recipe_Name, Counter) VALUES (?, ?, ?)",
                    (datetime.date(2025, 5, 1), "Black Sun", 1),
                ),
                call(
                    "INSERT INTO CocktailExport (Export_Date, Recipe_Name, Counter) VALUES (?, ?, ?)",
                    (datetime.date(2025, 5, 1), "Blue Mara", 2),
                ),
            ]

            ingredient_calls = [
                call(
                    """INSERT INTO IngredientExport (Export_Date, Ingredient_Name, Consumption, Cost_Consumption)
                    VALUES (?, ?, ?, ?)""",
                    (datetime.date(2025, 5, 1), "Cola", 133, 200),
                ),
                call(
                    """INSERT INTO IngredientExport (Export_Date, Ingredient_Name, Consumption, Cost_Consumption)
                    VALUES (?, ?, ?, ?)""",
                    (datetime.date(2025, 5, 1), "White Rum", 53, 150),
                ),
            ]

            # Verify that execute_raw_sql was called for each recipe and ingredient
            for recipe_call in recipe_calls:
                mock_execute_sql.assert_any_call(*recipe_call.args, **recipe_call.kwargs)

            for ingredient_call in ingredient_calls:
                mock_execute_sql.assert_any_call(*ingredient_call.args, **ingredient_call.kwargs)

            # Tequila Sunrise has 0 count, verify it wasn't inserted
            zero_recipe_call = call(
                "INSERT INTO CocktailExport (Export_Date, Recipe_Name, Counter) VALUES (?, ?, ?)",
                ("2025-05-01", "Tequila Sunrise", 0),
            )
            assert zero_recipe_call not in mock_execute_sql.call_args_list

            # Vodka has 0 consumption, verify it wasn't inserted
            zero_ingredient_call = call(
                """INSERT INTO IngredientExport (Export_Date, Ingredient_Name, Consumption, Cost_Consumption)
                    VALUES (?, ?, ?, ?)""",
                ("2025-05-01", "Vodka", 0, 0),
            )
            assert zero_ingredient_call not in mock_execute_sql.call_args_list

    def test_migrate_csv_export_data_without_cost_file(self):
        """Test migrating CSV export data without a cost file."""
        ingredient_csv_content = "date,Cola,Vodka,Tequila\n2025-05-02,200,150,75\nlifetime,200,150,75\n"
        recipe_csv_content = "date,Cuba Libre,Virgin Only Possible\n2025-05-02,10,5\nlifetime,10,5\n"

        test_date = "20250502"
        recipe_file = Path(SAVE_FOLDER) / f"{test_date}_Recipe_export.csv"
        ingredient_file = Path(SAVE_FOLDER) / f"{test_date}_Ingredient_export.csv"

        mock_file_contents = {
            str(recipe_file): recipe_csv_content,
            str(ingredient_file): ingredient_csv_content,
        }

        def mock_file_open(path: Any, *args: Any, **kwargs: Any):
            content = mock_file_contents.get(str(path), "")
            m = mock_open(read_data=content)
            return m()

        with (
            patch("pathlib.Path.glob") as mock_glob,
            patch("pathlib.Path.open", new=mock_file_open),
            patch("pathlib.Path.unlink") as mock_unlink,
            patch("pathlib.Path.exists", return_value=False),
            patch("src.migration.export_data.execute_raw_sql") as mock_execute_sql,
        ):
            # Cost file doesn't exist
            # Configure mock_glob to return appropriate files for each pattern
            def glob_side_effect(pattern: str):
                if "_Recipe" in pattern:
                    return [recipe_file]
                if "_Ingredient" in pattern:
                    return [ingredient_file]
                if "_Cost" in pattern:
                    return []  # No cost file
                return []

            mock_glob.side_effect = glob_side_effect

            migrate_csv_export_data_to_db()
            assert mock_unlink.call_count >= 2  # Only recipe and ingredient files

            recipe_calls = [
                call(
                    "INSERT INTO CocktailExport (Export_Date, Recipe_Name, Counter) VALUES (?, ?, ?)",
                    (datetime.date(2025, 5, 2), "Cuba Libre", 10),
                ),
                call(
                    "INSERT INTO CocktailExport (Export_Date, Recipe_Name, Counter) VALUES (?, ?, ?)",
                    (datetime.date(2025, 5, 2), "Virgin Only Possible", 5),
                ),
            ]

            ingredient_calls = [
                call(
                    """INSERT INTO IngredientExport (Export_Date, Ingredient_Name, Consumption, Cost_Consumption)
                    VALUES (?, ?, ?, ?)""",
                    (datetime.date(2025, 5, 2), "Cola", 200, 0),
                ),
                call(
                    """INSERT INTO IngredientExport (Export_Date, Ingredient_Name, Consumption, Cost_Consumption)
                    VALUES (?, ?, ?, ?)""",
                    (datetime.date(2025, 5, 2), "Vodka", 150, 0),
                ),
                call(
                    """INSERT INTO IngredientExport (Export_Date, Ingredient_Name, Consumption, Cost_Consumption)
                    VALUES (?, ?, ?, ?)""",
                    (datetime.date(2025, 5, 2), "Tequila", 75, 0),
                ),
            ]

            # Verify that execute_raw_sql was called for each recipe and ingredient
            for recipe_call in recipe_calls:
                mock_execute_sql.assert_any_call(*recipe_call.args, **recipe_call.kwargs)

            for ingredient_call in ingredient_calls:
                mock_execute_sql.assert_any_call(*ingredient_call.args, **ingredient_call.kwargs)

    def test_migrate_csv_export_data_with_time_suffix(self):
        """Test migrating CSV export data with time suffix in filenames."""
        ingredient_csv_content = "date,Cola,Orange Juice,Blue Curacao\n2025-05-03,100,250,30\nlifetime,100,250,30\n"
        recipe_csv_content = "date,With Handadd,Not Available\n2025-05-03,2,4\nlifetime,2,4\n"
        cost_csv_content = "date,Cola,Orange Juice,Blue Curacao\n2025-05-03,75,125,90\nlifetime,75,125,90\n"

        test_date = "20250503"
        recipe_file = Path(SAVE_FOLDER) / f"{test_date}_Recipe_export-173320.csv"
        ingredient_file = Path(SAVE_FOLDER) / f"{test_date}_Ingredient_export-173320.csv"
        cost_file = Path(SAVE_FOLDER) / f"{test_date}_Cost_export-173320.csv"

        mock_file_contents = {
            str(recipe_file): recipe_csv_content,
            str(ingredient_file): ingredient_csv_content,
            str(cost_file): cost_csv_content,
        }

        def mock_file_open(path: Any, *args: Any, **kwargs: Any):
            content = mock_file_contents.get(str(path), "")
            m = mock_open(read_data=content)
            return m()

        with (
            patch("pathlib.Path.glob") as mock_glob,
            patch("pathlib.Path.open", new=mock_file_open),
            patch("pathlib.Path.unlink"),
            patch("pathlib.Path.exists", return_value=True),
            patch("src.migration.export_data.execute_raw_sql") as mock_execute_sql,
        ):
            # Configure mock_glob to return appropriate files for each pattern
            def glob_side_effect(pattern: str):
                if "_Recipe" in pattern:
                    return [recipe_file]
                if "_Ingredient" in pattern:
                    return [ingredient_file]
                if "_Cost" in pattern:
                    return [cost_file]
                return []

            mock_glob.side_effect = glob_side_effect
            migrate_csv_export_data_to_db()

            recipe_calls = [
                call(
                    "INSERT INTO CocktailExport (Export_Date, Recipe_Name, Counter) VALUES (?, ?, ?)",
                    (datetime.date(2025, 5, 3), "With Handadd", 2),
                ),
                call(
                    "INSERT INTO CocktailExport (Export_Date, Recipe_Name, Counter) VALUES (?, ?, ?)",
                    (datetime.date(2025, 5, 3), "Not Available", 4),
                ),
            ]

            ingredient_calls = [
                call(
                    """INSERT INTO IngredientExport (Export_Date, Ingredient_Name, Consumption, Cost_Consumption)
                    VALUES (?, ?, ?, ?)""",
                    (datetime.date(2025, 5, 3), "Cola", 100, 75),
                ),
                call(
                    """INSERT INTO IngredientExport (Export_Date, Ingredient_Name, Consumption, Cost_Consumption)
                    VALUES (?, ?, ?, ?)""",
                    (datetime.date(2025, 5, 3), "Orange Juice", 250, 125),
                ),
                call(
                    """INSERT INTO IngredientExport (Export_Date, Ingredient_Name, Consumption, Cost_Consumption)
                    VALUES (?, ?, ?, ?)""",
                    (datetime.date(2025, 5, 3), "Blue Curacao", 30, 90),
                ),
            ]

            # Verify that execute_raw_sql was called for each recipe and ingredient
            for recipe_call in recipe_calls:
                mock_execute_sql.assert_any_call(*recipe_call.args, **recipe_call.kwargs)

            for ingredient_call in ingredient_calls:
                mock_execute_sql.assert_any_call(*ingredient_call.args, **ingredient_call.kwargs)
