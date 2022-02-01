import json
import os
import warnings
from pathlib import Path
from typing import Dict, List, Union
import yaml
import requests
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv

# something from plotly triggers pandas warnign
warnings.filterwarnings("ignore")


DIRPATH = Path(__file__).parent.absolute()
load_dotenv(DIRPATH / ".env")

# Getting the language file as dict
LANGUAGE_FILE = DIRPATH / "language.yaml"
with open(LANGUAGE_FILE, "r", encoding="UTF-8") as stream:
    LANGUAGE_DATA: Dict = yaml.safe_load(stream)


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
CALL_TO_ACTION = __choose_language(LANGUAGE_DATA["call_to_action"])
DF_START = pd.DataFrame([(DEFAULT_MESSAGE, CALL_TO_ACTION, 1), ], columns=["Team", "Person", "Amount"])


def __give_team_number(df: pd.DataFrame):
    """Adds the number to the team names"""
    stats = df.groupby("Team")["Amount"].sum()
    for team, amount in stats.iteritems():
        df.Team.replace("^" + team + "$", f"{team} ({amount})", inplace=True, regex=True)


def __decide_data(datatype: int):
    index = datatype - 1
    count = [True, False, True, False][index]
    hourrange = [24, 24, None, None][index]
    limit = 5
    return (count, hourrange, limit)


def get_plot_data(datatype: int):
    count, hourrange, limit = __decide_data(datatype)
    headers = {"content-type": "application/json"}
    payload = {"limit": limit, "count": count, "hourrange": hourrange}
    payload = json.dumps(payload)
    url = "http://127.0.0.1:8080/teamdata"
    if os.getenv("EXECUTOR") is not None:
        url = "http://backend:8080/teamdata"
    res = requests.get(url, data=payload, headers=headers)
    data = pd.DataFrame(json.loads(res.text), columns=["Team", "Person", "Amount"])
    if data.empty:
        return DF_START
    __give_team_number(data)
    return data


def generate_treemap(df: pd.DataFrame):
    """Generates a treemap out of the df"""
    fig = px.treemap(df, path=[px.Constant("Teams"), 'Team', 'Person'], values='Amount')
    fig.update_traces(root_color="darkgrey", texttemplate="<b>%{label}</b><br>(%{value:.0f})")
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), hovermode=False, font=dict(size=24))
    fig.layout.plot_bgcolor = 'rgb(14, 17, 23)'
    fig.layout.paper_bgcolor = 'rgb(14, 17, 23)'
    return fig
