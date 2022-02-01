import dash  # type: ignore # pylint: disable=unused-import
from dash import dcc  # type: ignore
from dash import html  # type: ignore
from dash.dependencies import Input, Output  # type: ignore
import datetime

import home

from app import app
from app import server  # pylint: disable=unused-import


# Connect to your app pages
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(
        html.Div([
            html.Ul(
                [html.Li(dcc.Link('Amount Today', href='/n_today')),
                 html.Li(dcc.Link('Volume Today', href='/vol_today')),
                 html.Li(dcc.Link('Amout All Time', href='/n_all')),
                 html.Li(dcc.Link('Volume All Time', href='/vol_all'))]
            ),
            html.Div(datetime.datetime.now().strftime('%H:%M'), id="timeclock", className="clock")
        ], className="container"), className="navbar"),
    html.Div(id='page-content', children=[])
], className="App")


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    """Routes the path to the according page layout

    Args:
        pathname (str): name of the path

    Returns:
        dcc Layout: Layout of dash core / html elements
    """
    routes = {
        "/n_today": 1,
        "/vol_today": 2,
        "/n_all": 3,
        "/vol_all": 4,
    }
    graphtype = routes.get(pathname, 1)
    return home.gen_layout(graphtype)


if __name__ == '__main__':
    # app.run_server(debug=True)
    print("access the server on http://127.0.0.1:8050/ http://127.0.0.1 or your defined address")
    app.run_server(host="0.0.0.0", debug=True, port=8050)
