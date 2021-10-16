import math
import json
import requests
import matplotlib
import matplotlib.pyplot as plt

from pywaffle import Waffle

matplotlib.rcParams.update({'text.color': "white", 'axes.labelcolor': "white"})


NAMES = [
    "Anzahl (Heute)",
    "Volumen (Heute)",
    "Anzahl (Komplett)",
    "Volumen (Komplett)"
]


def sort_dict_items(to_sort: dict):
    dictionary_items = to_sort.items()
    sorted_items = sorted(dictionary_items)
    return {x[0]: x[1] for x in sorted_items}


def extract_data(sort: bool, data: dict):
    if not data or sum(data.values()) < 3:
        waffle_data = {"Cocktails trinken zum starten ...": 3}
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
    count = True
    sort = True
    hourrange = None
    if datatype in (1, 2):
        hourrange = 24
        limit = 5
    if datatype in (3, 4):
        sort = False
        limit = 10
    if datatype in (2, 4):
        count = False
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
    fig = plt.figure(
        FigureClass=Waffle,
        **dims,
        values=waffle_data,
        title={
            'label': NAMES[datatype - 1],
            'fontdict': {
                'fontsize': 50
            }
        },
        facecolor=(0.054, 0.066, 0.090, 1),
        legend={'loc': 'upper center', 'bbox_to_anchor': (0.5, 0.0),
                'ncol': 2, 'framealpha': 0, 'fontsize': 30}
    )
    return fig
