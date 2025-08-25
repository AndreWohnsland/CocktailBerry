from src.database_commander import DatabaseCommander
from src.models import ConsumeData

ALL_TIME = "ALL"
SINCE_RESET = "AT RESET"


def _extract_data(data: list[list]) -> dict[str, dict[str, int]]:
    """Extract the needed data from the exported data.

    Since DB method and exported files are similar in the core,
    We can use it on both returned data to have just one method.
    """
    # The data has three rows:
    # first is the Names, with the first column being the date
    names = [str(x) for x in data[0][1::]]  # explicitly convert to str (only for typing)
    # second is resettable data
    # data comes from csv, so it is str, need to convert to float
    since_reset = data[1][1::]
    since_reset = [int(x) for x in since_reset]
    # third is life time data
    all_time = data[2][1::]
    all_time = [int(x) for x in all_time]

    # Extract both into a dict containing name: quant
    # using only quantities greater than zero
    extracted: dict[str, dict[str, int]] = {}
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
