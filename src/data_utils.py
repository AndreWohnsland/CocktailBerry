from __future__ import annotations

from typing import Literal

import pulp

from src.database_commander import DatabaseCommander
from src.models import Cocktail, ConsumeData, Ingredient

ALL_TIME = "ALL"
SINCE_RESET = "AT RESET"


def _extract_data(data: list[list]) -> dict[str, dict[str, int]]:
    """Extract the needed data from the exported data.

    Since DB method and exported files are similar in the core,
    We can use it on both returned data to have just one method.
    """
    # The data has three rows:
    # first is the Names, with the first column being the date
    names = [str(x) for x in data[0][1::]]  # explicitly convert to str (only for typing)
    # second is resettable data
    # data comes from csv, so it is str, need to convert to float
    since_reset = data[1][1::]
    since_reset = [int(x) for x in since_reset]
    # third is life time data
    all_time = data[2][1::]
    all_time = [int(x) for x in all_time]

    # Extract both into a dict containing name: quant
    # using only quantities greater than zero
    extracted: dict[str, dict[str, int]] = {}
    extracted[ALL_TIME] = {x: y for x, y in zip(names, all_time) if y > 0}
    extracted[SINCE_RESET] = {x: y for x, y in zip(names, since_reset) if y > 0}
    return extracted


def generate_consume_data() -> dict[str, ConsumeData]:
    """Get data from database, assigns objects and fill dropdown."""
    DBC = DatabaseCommander()
    consume_data: dict[str, ConsumeData] = {}

    # Get current data in DB (since reset and all time)
    recipe_db = _extract_data(DBC.get_consumption_data_lists_recipes())
    ingredient_db = _extract_data(DBC.get_consumption_data_lists_ingredients())
    cost_db = _extract_data(DBC.get_cost_data_lists_ingredients())
    consume_data[SINCE_RESET] = ConsumeData(recipe_db[SINCE_RESET], ingredient_db[SINCE_RESET], cost_db[SINCE_RESET])
    consume_data[ALL_TIME] = ConsumeData(recipe_db[ALL_TIME], ingredient_db[ALL_TIME], cost_db[ALL_TIME])

    # Get historical export data from database and merge it with current data
    consume_data.update(DBC.get_export_data())

    return consume_data


def load_data(k: int | None = None) -> tuple[set[int], list[Cocktail]]:
    """Load selection snapshot from the database.

    Returns a tuple of (top_ing_ids, cocktails).
    """
    dbc = DatabaseCommander()
    ingredient_ids = dbc.get_most_used_ingredient_ids(k=k)
    cocktails = dbc.get_all_cocktails(status="enabled")
    cocktails = [c for c in cocktails if all(ing.id in ingredient_ids for ing in c.ingredients)]
    return set(ingredient_ids), cocktails


def greedy_selection(top_ing_ids: set[int], cocktails: list[Cocktail], n: int) -> tuple[set[int], int]:
    chosen: set[int] = set()

    # Precompute ingredient id sets per cocktail for speed
    cocktail_ing_sets = [(c.id, {ing.id for ing in c.ingredients}) for c in cocktails]

    def score(chosen: set[int]) -> int:
        return sum(1 for _, ing_set in cocktail_ing_sets if ing_set.issubset(chosen))

    for _ in range(n):
        best_ing, best_gain = None, -1
        for ing in top_ing_ids - chosen:
            candidate = chosen | {ing}
            gain = score(candidate)
            if gain > best_gain:
                best_ing, best_gain = ing, gain
        if best_ing is not None:
            chosen.add(best_ing)

    return chosen, score(chosen)


def greedy_local_selection(
    top_ing_ids: set[int], cocktails: list[Cocktail], n: int, max_iters: int = 100
) -> tuple[set[int], int]:
    # Precompute sets once and pass along
    cocktail_ing_sets = [(c.id, {ing.id for ing in c.ingredients}) for c in cocktails]

    def score(chosen: set[int]) -> int:
        return sum(1 for _, ing_set in cocktail_ing_sets if ing_set.issubset(chosen))

    # Start with a greedy solution
    chosen, best_score = greedy_selection(top_ing_ids, cocktails, n)

    improved, iterations = True, 0
    while improved and iterations < max_iters:
        improved = False
        iterations += 1

        for ing_out in chosen:
            for ing_in in top_ing_ids - chosen:
                candidate = (chosen - {ing_out}) | {ing_in}
                new_score = score(candidate)
                if new_score > best_score:
                    chosen, best_score = candidate, new_score
                    improved = True
                    break
            if improved:
                break

    return chosen, best_score


def ilp_selection(top_ing_ids: set[int], cocktails: list[Cocktail], n: int) -> tuple[set[int], int]:
    """Solve exact problem with ILP using pulp."""
    ing_ids = list(top_ing_ids)

    # ILP model
    model = pulp.LpProblem("Cocktail_Selection", pulp.LpMaximize)

    x = {i: pulp.LpVariable(f"x_{i}", cat="Binary") for i in ing_ids}  # ingredient chosen
    # Cocktail possible variables keyed by cocktail id
    y = {c.id: pulp.LpVariable(f"y_{c.id}", cat="Binary") for c in cocktails}

    # Constraint: choose exactly n ingredients
    model += pulp.lpSum(x[i] for i in ing_ids) == n

    # Cocktail only possible if all its ingredients chosen
    for c in cocktails:
        for ing in {ing.id for ing in c.ingredients}:
            model += y[c.id] <= x[ing]

    # Objective: maximize number of cocktails possible
    model += pulp.lpSum(y[c.id] for c in cocktails)

    model.solve(pulp.PULP_CBC_CMD(msg=False))

    chosen = {i for i in ing_ids if pulp.value(x[i]) == 1}
    score = sum(1 for c in cocktails if pulp.value(y[c.id]) == 1)

    return chosen, score


def select_optimal(
    n: int,
    algorithm: Literal["greedy", "local", "ilp"],
    k: int = 30,
) -> tuple[list[Ingredient], list[Cocktail]]:
    """Select n ingredients using the requested algorithm and return covered cocktails.

    Returns a tuple (ingredient_ids, cocktails), where ingredient_ids is a list of the n selected
    ingredient IDs (sorted), and cocktails contains all enabled cocktails that can be made using
    only the selected ingredients.
    """
    dbc = DatabaseCommander()
    top_ing_ids = dbc.get_most_used_ingredient_ids(k=k)
    cocktails = dbc.get_all_cocktails(status="enabled")
    cocktails = [c for c in cocktails if all(ing.id in top_ing_ids for ing in c.ingredients)]
    n = max(0, min(n, len(top_ing_ids)))

    if algorithm == "greedy":
        chosen, _ = greedy_selection(top_ing_ids, cocktails, n)
    elif algorithm == "local":
        chosen, _ = greedy_local_selection(top_ing_ids, cocktails, n)
    elif algorithm == "ilp":
        chosen, _ = ilp_selection(top_ing_ids, cocktails, n)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    # Filter cocktails that are possible with the chosen ingredients
    chosen_set = set(chosen)
    covered = [c for c in cocktails if {ing.id for ing in c.ingredients}.issubset(chosen_set)]
    ingredients = [x for x in [dbc.get_ingredient(ing_id) for ing_id in chosen_set] if x is not None]

    return ingredients, covered
