import math
import json
import os
from pathlib import Path
from typing import Dict, List, Union
import yaml
import requests
import matplotlib
import matplotlib.pyplot as plt
from dotenv import load_dotenv

from pywaffle import Waffle

DIRPATH = Path(__file__).parent.absolute()
load_dotenv(DIRPATH / ".env")

# Getting the language file as dict
LANGUAGE_FILE = DIRPATH / "language.yaml"
with open(LANGUAGE_FILE, "r", encoding="UTF-8") as stream:
    LANGUAGE_DATA: Dict = yaml.safe_load(stream)

# Setting some plotting props
matplotlib.rcParams.update({'text.color': "white", 'axes.labelcolor': "white"})


def __choose_language(element: dict, **kwargs) -> Union[str, List[str]]:
    """Choose either the given language if exists, or english if not piping additional info into template"""
    language = os.getenv("UI_LANGUAGE")
    tmpl = element.get(language, element["en"])
    # Return the list and not apply template!
    if isinstance(tmpl, list):
        return tmpl
    return tmpl.format(**kwargs)


HEADER = __choose_language(LANGUAGE_DATA["header_label"])
DEFAULT_MESSAGE = __choose_language(LANGUAGE_DATA["default_message"])


def sort_dict_items(to_sort: dict):
    dictionary_items = to_sort.items()
    sorted_items = sorted(dictionary_items)
    return {x[0]: x[1] for x in sorted_items}


def extract_data(sort: bool, data: dict):
    if not data or sum(data.values()) < 3:
        waffle_data = {DEFAULT_MESSAGE: 3}
    else:
        waffle_data = {f"{x} ({y})": y for x, y in data.items()}
    if sort:
        waffle_data = sort_dict_items(waffle_data)
    return waffle_data


def generate_dimensions(total: float, count=True):
    proportion = 3
    threshold_upper = 1.2
    threshold_lower = 0.77
    one_row_until = 9
    # use fixed grid for non count variables
    if not count:
        return {"rows": 10, "columns": 25}
    # don't split until given dimension
    if total < one_row_until:
        return {"rows": 1}
    row = max(math.floor(math.sqrt(total / proportion)), 1)
    # calculate current proportion, add one if exceeds th
    column = math.ceil(total / row)
    real_prop = column / row
    if real_prop >= proportion * threshold_upper:
        row += 1
    # calculates adjusted proportion, rolls back if its too extreme
    column = math.ceil(total / row)
    adjusted_prop = column / row
    if adjusted_prop <= proportion * threshold_lower:
        row -= 1
    return {"rows": row}


def get_data(count: bool, hourrange: int, limit: int):
    headers = {"content-type": "application/json"}
    payload = {"limit": limit, "count": count, "hourrange": hourrange}
    payload = json.dumps(payload)
    res = requests.get("http://127.0.0.1:8080/leaderboard", data=payload, headers=headers)
    return json.loads(res.text)


def decide_data(datatype: int):
    index = datatype - 1
    count = [True, False, True, False][index]
    sort = [True, True, False, False][index]
    hourrange = [24, 24, None, None][index]
    limit = [5, 5, 4, 4][index]
    return (count, sort, hourrange, limit)


def generate_figure(datatype: int):
    """Generates the Waffle plot.
    Type is int from 1-4:
    1: Amount Today
    2: Volume Today
    3: Amount All Time
    4: Volume All Time
    """
    count, sort, hourrange, limit = decide_data(datatype)
    data = get_data(count, hourrange, limit)
    waffle_data = extract_data(sort, data)
    dims = generate_dimensions(sum(data.values()), count)
    # close current (old) figure, to avoid memory leak
    # this is needed because old figures will keep open until explicitly closed
    plt.close('all')
    fig = plt.figure(
        FigureClass=Waffle,
        **dims,
        values=waffle_data,
        title={
            'label': HEADER[datatype - 1],
            'fontdict': {
                'fontsize': 30
            }
        },
        facecolor=(0.054, 0.066, 0.090, 1),
        legend={'loc': 'upper center', 'bbox_to_anchor': (0.5, 0.0),
                'ncol': 2, 'framealpha': 0, 'fontsize': 18}
    )
    return fig
