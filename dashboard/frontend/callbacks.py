import dash
from dash.dependencies import Input, Output  # type: ignore
import datetime

from treemap import generate_treemap, get_plot_data
from app import app
from store import store


@app.callback(Output('treemap', 'figure'),
              Output('timeclock', "children"),
              Input('interval-component', 'n_intervals'),
              Input('url', 'pathname'))
def update_plot(n, pathname):
    routes = {
        "/n_today": 1,
        "/vol_today": 2,
        "/n_all": 3,
        "/vol_all": 4,
    }
    graphtype = routes.get(pathname, 1)
    store.current_graph_type = graphtype
    df = get_plot_data(store.current_graph_type)
    now_time = datetime.datetime.now().strftime('%H:%M')
    trigger_id = dash.callback_context.triggered[0]["prop_id"]
    triggered_by_time = trigger_id == "interval-component.n_intervals"
    if df.equals(store.last_data) and triggered_by_time:
        return [dash.no_update, now_time]
    store.last_data = df
    fig = generate_treemap(df)
    return [fig, now_time]
