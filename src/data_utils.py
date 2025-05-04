import json
from typing import Union

import requests
from requests.exceptions import ConnectionError as ReqConnectionError

from src.database_commander import DatabaseCommander
from src.filepath import ADDON_FOLDER
from src.logger_handler import LoggerHandler
from src.models import AddonData, ConsumeData
from src.programs.addons import ADDONS

ALL_TIME = "ALL"
SINCE_RESET = "AT RESET"
_GITHUB_ADDON_SOURCE = "https://raw.githubusercontent.com/AndreWohnsland/CocktailBerry-Addons/main/addon_data.json"


_logger = LoggerHandler("DataUtils")


class CouldNotInstallAddonError(Exception):
    pass


def _extract_data(data: list[list]):
    """Extract the needed data from the exported data.

    Since DB method and exported files are similar in the core,
    We can use it on both returned data to have just one method.
    """
    # The data has three rows:
    # first is the Names, with the first column being the date
    names = data[0][1::]
    # second is resettable data
    # data comes from csv, so it is str, need to convert to float
    since_reset = data[1][1::]
    since_reset = [float(x) for x in since_reset]
    # third is life time data
    all_time = data[2][1::]
    all_time = [float(x) for x in all_time]

    # Extract both into a dict containing name: quant
    # using only quantities greater than zero
    extracted = {}
    extracted[ALL_TIME] = {x: y for x, y in zip(names, all_time) if y > 0}
    extracted[SINCE_RESET] = {x: y for x, y in zip(names, since_reset) if y > 0}
    return extracted


def generate_consume_data() -> dict[str, ConsumeData]:
    """Get data from database, assigns objects and fill dropdown."""
    DBC = DatabaseCommander()
    consume_data: dict[str, ConsumeData] = {}

    # Get current data in DB (since reset and all time)
    recipe_db = _extract_data(DBC.get_consumption_data_lists_recipes())
    ingredient_db = _extract_data(DBC.get_consumption_data_lists_ingredients())
    cost_db = _extract_data(DBC.get_cost_data_lists_ingredients())
    consume_data[SINCE_RESET] = ConsumeData(recipe_db[SINCE_RESET], ingredient_db[SINCE_RESET], cost_db[SINCE_RESET])
    consume_data[ALL_TIME] = ConsumeData(recipe_db[ALL_TIME], ingredient_db[ALL_TIME], cost_db[ALL_TIME])

    # Get historical export data from database and merge it with current data
    consume_data.update(DBC.get_export_data())

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
