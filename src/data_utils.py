import csv
import json
from pathlib import Path
from typing import Optional, Union

import requests
from pydantic.dataclasses import dataclass
from requests.exceptions import ConnectionError as ReqConnectionError

from src import __version__
from src.database_commander import DatabaseCommander
from src.filepath import ADDON_FOLDER, SAVE_FOLDER
from src.logger_handler import LoggerHandler
from src.migration.migrator import _Version
from src.programs.addons import ADDONS

ALL_TIME = "ALL"
SINCE_RESET = "AT RESET"
_GITHUB_ADDON_SOURCE = "https://raw.githubusercontent.com/AndreWohnsland/CocktailBerry-Addons/main/addon_data.json"
_NOT_SET = "Not Set"

_logger = LoggerHandler("DataUtils")


@dataclass
class ConsumeData:
    recipes: dict[str, int]
    ingredients: dict[str, int]
    cost: Optional[dict[str, int]]


@dataclass
class AddonData:
    name: str = _NOT_SET
    description: str = _NOT_SET
    url: str = _NOT_SET
    disabled_since: str = ""
    is_installable: bool = True
    file_name: str = ""
    installed: bool = False
    official: bool = True

    def __post_init__(self):
        if self.file_name:
            return
        self.file_name = self.url.rsplit("/", maxsplit=1)[-1]
        if self.disabled_since != "":
            local_version = _Version(__version__)
            self.is_installable = local_version < _Version(self.disabled_since.replace("v", ""))


class CouldNotInstallAddonError(Exception):
    pass


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


def get_addon_data() -> list[AddonData]:
    """Get all the addon data from source and locally installed ones, build the data objects."""
    # get the addon data from the source
    # This should provide name, description and url
    installed_addons = ADDONS.addons
    official_addons: list[AddonData] = []
    try:
        req = requests.get(_GITHUB_ADDON_SOURCE, allow_redirects=True, timeout=5)
        if req.ok:
            gh_data = json.loads(req.text)
            official_addons = [AddonData(**data) for data in gh_data]
    except ReqConnectionError:
        _logger.log_event("WARNING", "Could not fetch addon data from source, is there an internet connection?")

    # Check if the addon is installed
    lower_case_installed_addons = [x.lower() for x in installed_addons]
    for addon in official_addons:
        if addon.name.lower() in lower_case_installed_addons:
            addon.installed = True

    # also add local addons, which are not official ones to the list
    possible_addons = official_addons
    for local_addon_name, addon_class in installed_addons.items():
        if local_addon_name.lower() not in [a.name.lower() for a in possible_addons]:
            file_name = f"{addon_class.__module__.split('.')[-1]}.py"
            possible_addons.append(
                AddonData(
                    name=local_addon_name,
                    description="Installed addon is not in list of official ones. Please manage over file system.",
                    url=file_name,
                    disabled_since="",
                    is_installable=False,
                    file_name=file_name,
                    installed=True,
                    official=False,
                )
            )
    return possible_addons


def _estimate_addon(addon_name: str) -> AddonData:
    """Fallback in cases where we cannot provide the addon object, but only the name."""
    possible_addon = get_addon_data()
    found_addon = next((a for a in possible_addon if a.name == addon_name), None)
    if found_addon is None:
        raise CouldNotInstallAddonError(f"Addon {addon_name} not found in the list of addons.")
    return found_addon


def install_addon(addon: Union[AddonData, str]):
    """Try to install addon, log if req is not ok or no connection."""
    if isinstance(addon, str):
        addon = _estimate_addon(addon)

    addon_file = ADDON_FOLDER / addon.file_name
    try:
        req = requests.get(addon.url, allow_redirects=True, timeout=5)
        if req.ok:
            addon_file.write_bytes(req.content)
        else:
            raise CouldNotInstallAddonError(
                f"Could not get {addon.name} from {addon.url}: {req.status_code} {req.reason}"
            )
    except ReqConnectionError:
        raise CouldNotInstallAddonError(f"Could not get {addon.name} from {addon.url}: No internet connection")


def remove_addon(addon: Union[AddonData, str]):
    """Remove the addon from the system."""
    if isinstance(addon, str):
        addon = _estimate_addon(addon)
    addon_file = ADDON_FOLDER / addon.file_name
    addon_file.unlink(missing_ok=True)
