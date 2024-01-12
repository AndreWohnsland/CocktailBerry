import json
import os
import warnings
import requests
import plotly.express as px
import pandas as pd
from language import language
from store import store

# something from plotly triggers pandas warning
warnings.filterwarnings("ignore")


DF_START = pd.DataFrame(
    [(language.DEFAULT_MESSAGE, language.CALL_TO_ACTION, 1), ],
    columns=["Team", "Person", "Amount"]
)
px_colors = px.colors.qualitative.Plotly


def __give_team_number(df: pd.DataFrame):
    """Adds the number to the team names"""
    stats = df.groupby("Team")["Amount"].sum()
    for team, amount in stats.items():
        df.Team.replace("^" + team + "$", f"{team} ({amount})", inplace=True, regex=True)


def __decide_data(datatype: int):
    index = datatype - 1
    count = [True, False, True, False][index]
    hour_range = [24, 24, None, None][index]
    limit = 5
    return (count, hour_range, limit)


def get_plot_data(datatype: int):
    count, hour_range, limit = __decide_data(datatype)
    headers = {"content-type": "application/json"}
    payload = {"limit": limit, "count": count, "hour_range": hour_range}
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
    # if its 1st or 2nd graph type (today data) add color mapping that team keeps
    # same color, even if the value changes
    additional_config = {}
    if store.current_graph_type in [1, 2]:
        team_names = sorted(df.Team.unique())
        color_discrete_map = dict(zip(team_names, px_colors))
        color_discrete_map["(?)"] = "darkgrey"
        additional_config = dict(color="Team", color_discrete_map=color_discrete_map)
    fig = px.treemap(df, path=[px.Constant("Teams"), 'Team', 'Person'], values='Amount', **additional_config)
    fig.update_traces(root_color="darkgrey", texttemplate="<b>%{label}</b><br>(%{value:.0f})")
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), hovermode=False, font=dict(size=24))
    fig.layout.plot_bgcolor = 'rgb(14, 17, 23)'
    fig.layout.paper_bgcolor = 'rgb(14, 17, 23)'
    return fig
