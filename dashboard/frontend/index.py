# pylint: disable=unused-import
import dash  # type: ignore
from dash import dcc  # type: ignore
from dash import html  # type: ignore

from language import language
import callbacks
from app import app


server = app.server
# Connect to your app pages
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(
        html.Div([
            html.Ul(
                [html.Li(dcc.Link(language.AMOUNT_TODAY, href='/n_today')),
                 html.Li(dcc.Link(language.VOLUME_TODAY, href='/vol_today')),
                 html.Li(dcc.Link(language.AMOUNT_ALL, href='/n_all')),
                 html.Li(dcc.Link(language.VOLUME_ALL, href='/vol_all'))]
            ),
            html.Div("00:00", id="timeclock", className="clock")
        ], className="container"), className="navbar"),
    html.Div(id='page-content', children=[
        html.Div([
            dcc.Interval(
                id='interval-component',
                interval=15 * 1000,  # in milliseconds
                n_intervals=0
            ),
            dcc.Graph(figure={}, className="treemap", config={"displayModeBar": False}, id="treemap")
        ], style={"textAlign": "center"})
    ])
], className="App")


if __name__ == '__main__':
    # app.run_server(debug=True)
    print("access the server on http://127.0.0.1:8050/ http://127.0.0.1 or your defined address")
    app.run_server(host="0.0.0.0", debug=False, port=8050)
