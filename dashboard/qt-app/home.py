"""View for welcome screen. Use layout in index.py"""

from dash import html   # type: ignore
from dash import dcc
from treemap import generate_treemap, get_plot_data


def gen_layout(graphtype: int):
    df = get_plot_data(graphtype)
    fig = generate_treemap(df)
    return html.Div([
        dcc.Graph(figure=fig, className="treemap")
    ], style={"textAlign": "center"})
