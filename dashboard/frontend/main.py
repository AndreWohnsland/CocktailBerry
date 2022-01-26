import math
import os
from pathlib import Path
import sqlite3
import warnings
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from pywaffle import Waffle
from dotenv import load_dotenv

st.set_page_config(
    page_title="Cocktail Dashboard",
    page_icon="🍸",
    layout="wide",
    initial_sidebar_state="collapsed",
)
warnings.filterwarnings("ignore", 'Starting a Matplotlib GUI outside of the main thread will likely fail.')
mpl.rcParams.update({'text.color': "white", 'axes.labelcolor': "white"})

DATABASE_NAME = "team"
DIRPATH = Path(__file__).parent.absolute()
load_dotenv(DIRPATH / ".env")
database_path = os.path.join(DIRPATH, "storage", f"{DATABASE_NAME}.db")


def __choose_language(element: dict) -> str:
    language = os.getenv("UI_LANGUAGE")
    return element.get(language, element["en"])


TIME_SELECT = __choose_language({
    "en": ("Today", "All time", ),
    "de": ("Heute", "All time", ),
})

TIME_HEADER = __choose_language({
    "en": "Select time",
    "de": "Zeit aussuchen",
})

TYPE_SELECT = __choose_language({
    "en": ("Amount", "Volume", ),
    "de": ("Anzahl", "Volumen", ),
})

TYPE_HEADER = __choose_language({
    "en": "Select aggregation",
    "de": "Aggregation aussuchen",
})

DEFAULT_MESSAGE = __choose_language({
    "en": "Drink cocktails to start ...",
    "de": "Cocktails trinken zum starten ...",
})


def get_leaderboard(hourrange=None, limit=2, count=True):
    addition = ""
    if hourrange is not None:
        addition = f" WHERE Date >= datetime('now','-{hourrange} hours')"
    agg = "count(*)" if count else "sum(Volume)"
    conn = sqlite3.connect(database_path)
    sql = f"SELECT Team, {agg} as amount FROM Team{addition} GROUP BY Team ORDER BY {agg} DESC LIMIT ?"
    board = pd.read_sql(sql, conn, params=(limit,))
    board.reset_index(drop=True, inplace=True)
    conn.close()
    return board


def sort_dict_items(to_sort: dict):
    dictionary_items = to_sort.items()
    sorted_items = sorted(dictionary_items)
    return {x[0]: x[1] for x in sorted_items}


def extract_data(sort: bool, df: pd.DataFrame):
    if df.empty or sum(df.amount.to_list()) < 3:
        waffle_data = {DEFAULT_MESSAGE: 3}
    else:
        waffle_data = {f"{x} ({y})": y for x, y in zip(df.Team.to_list(), df.amount.to_list())}
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


def generate_figure(title: str, hourrange: int = None, limit=5, sort=False, count=True):
    df = get_leaderboard(hourrange, limit, count)
    waffle_data = extract_data(sort, df)
    dims = generate_dimensions(sum(df.amount.to_list()), count)
    fig = plt.figure(
        FigureClass=Waffle,
        **dims,
        values=waffle_data,
        title={
            'label': title,
            'fontdict': {
                'fontsize': 20
            }
        },
        facecolor=(0.054, 0.066, 0.090, 1),
        legend={'loc': 'upper center', 'bbox_to_anchor': (0.5, 0.0), 'ncol': 2, 'framealpha': 0}
    )
    return fig


st_autorefresh(interval=15000, key="autorefresh")
st.markdown(""" <style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.block-container {padding: 1rem 1rem 1rem 1rem !important;}
</style> """, unsafe_allow_html=True)

st.sidebar.header(TIME_HEADER)
selected_display = st.sidebar.radio("", TIME_SELECT)
st.sidebar.header(TYPE_HEADER)
selected_type = st.sidebar.radio("", TYPE_SELECT)
use_count = selected_type == TYPE_SELECT[0]

if selected_display == TIME_SELECT[0]:
    st.pyplot(generate_figure(
        title=f"Leaderboard ({selected_type}, {selected_display})",
        hourrange=24, sort=True, count=use_count
    ))
else:
    st.pyplot(generate_figure(title=f"Leaderboard ({selected_type}, {selected_display})", limit=20, count=use_count))
