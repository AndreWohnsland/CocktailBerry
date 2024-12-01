import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.database_commander import DatabaseCommander
from src.filepath import SAVE_FOLDER

ALL_TIME = "ALL"
SINCE_RESET = "AT RESET"


@dataclass
class ConsumeData:
    recipes: dict[str, int]
    ingredients: dict[str, int]
    cost: Optional[dict[str, int]]


def _generate_consumption_from_file(date_string: str):
    # we need to get the pattern of the files, the are date_string_xxx-increasing number
    recipe_files = sorted(SAVE_FOLDER.glob(f"{date_string}_Recipe*.csv"), key=lambda f: int(f.stem.split("-")[-1]))
    ingredient_files = sorted(
        SAVE_FOLDER.glob(f"{date_string}_Ingredient*.csv"), key=lambda f: int(f.stem.split("-")[-1])
    )
    cost_files = sorted(SAVE_FOLDER.glob(f"{date_string}_Cost*.csv"), key=lambda f: int(f.stem.split("-")[-1]))

    # Select the oldest file (lowest last number)
    recipe_file = recipe_files[0]
    ingredient_file = ingredient_files[0]
    cost_file = cost_files[0] if cost_files else None
    recipe_data = _read_csv_file(SAVE_FOLDER / recipe_file)[SINCE_RESET]
    ingredient_data = _read_csv_file(SAVE_FOLDER / ingredient_file)[SINCE_RESET]
    cost_data = None
    if cost_file:
        cost_data = _read_csv_file(SAVE_FOLDER / cost_file)[SINCE_RESET]
    return ConsumeData(recipe_data, ingredient_data, cost_data)


def _read_csv_file(to_read: Path):
    """Read and extracts the given csv file."""
    data = []
    with to_read.open(encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file, delimiter=",")
        for row in reader:
            data.append(row)
    return _extract_data(data)


def _extract_data(data: list[list]):
    """Extract the needed data from the exported data.

    Since DB method and exported files are similar in the core,
    We can use it on both returned data to have just one method.
    """
    # The data has three rows:
    # first is the Names, with the first column being the date
    names = data[0][1::]
    # second is resettable data
    # data comes from csv, so it is str, need to convert to int
    since_reset = data[1][1::]
    since_reset = [int(x) for x in since_reset]
    # third is life time data
    all_time = data[2][1::]
    all_time = [int(x) for x in all_time]

    # Extract both into a dict containing name: quant
    # using only quantities greater than zero
    extracted = {}
    extracted[ALL_TIME] = {x: y for x, y in zip(names, all_time) if y > 0}
    extracted[SINCE_RESET] = {x: y for x, y in zip(names, since_reset) if y > 0}
    return extracted


def get_saved_dates() -> list[str]:
    """Extract the timestamp pattern from the file."""
    # pattern is something like "20241201_Recipe_export-155942"
    recipes_files = [file.name for file in SAVE_FOLDER.glob("*Recipe*.csv")]
    dates = set()
    for file_name in recipes_files:
        date_str = file_name.split("_")[0]
        dates.add(date_str)
    return list(dates)


def generate_consume_data() -> dict[str, ConsumeData]:
    """Get data from files and db, assigns objects and fill dropdown."""
    dates = get_saved_dates()
    # first get things from database
    DBC = DatabaseCommander()
    consume_data: dict[str, ConsumeData] = {}
    recipe_db = _extract_data(DBC.get_consumption_data_lists_recipes())
    ingredient_db = _extract_data(DBC.get_consumption_data_lists_ingredients())
    cost_db = _extract_data(DBC.get_cost_data_lists_ingredients())
    consume_data[SINCE_RESET] = ConsumeData(recipe_db[SINCE_RESET], ingredient_db[SINCE_RESET], cost_db[SINCE_RESET])
    consume_data[ALL_TIME] = ConsumeData(recipe_db[ALL_TIME], ingredient_db[ALL_TIME], cost_db[ALL_TIME])
    # then iterate over dates and get data there
    for d in dates:
        consume_data[d] = _generate_consumption_from_file(d)
    return consume_data
