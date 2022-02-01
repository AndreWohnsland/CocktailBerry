import pandas as pd


class Store:
    last_data: pd.DataFrame = pd.DataFrame([])
    current_graph_type = 1


store = Store()
