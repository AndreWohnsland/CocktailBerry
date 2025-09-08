from __future__ import annotations

from collections.abc import Iterable

import pytest
from _pytest.monkeypatch import MonkeyPatch

from src.data_utils import select_optimal
from src.database_commander import DatabaseCommander


class TestSelectOptimalILP:
    def _ids(self, ingredients: Iterable) -> list[int]:
        return sorted([ing.id for ing in ingredients])

    def test_ilp_n3_selects_expected_set_and_cocktails(
        self, db_commander: DatabaseCommander, monkeypatch: MonkeyPatch
    ) -> None:
        """With k-pool fixed to {1,2,3,4,5}, ILP with n=3 should pick {1,2,4} and cover 3 cocktails.

        Cocktails considered (enabled and inside k-pool):
        - Cuba Libre (1,2)
        - With Handadd (1,4)
        - Rum Cola Curacao (1,2,4)  [inserted here]
        """
        # Insert a cocktail that forces a unique best solution when n=3
        db_commander.insert_new_recipe("Rum Cola Curacao", 10, 300, True, False, [(1, 60, 1), (2, 200, 2), (4, 20, 3)])

        # Ensure data_utils uses our in-memory DB commander
        monkeypatch.setattr("src.data_utils.DatabaseCommander", lambda: db_commander)
        # Control the k-pool deterministically
        monkeypatch.setattr(db_commander, "get_most_used_ingredient_ids", lambda k=None: [1, 2, 3, 4, 5])

        ingredients, cocktails = select_optimal(3, "ilp")

        assert self._ids(ingredients) == [1, 2, 4]
        assert {c.name for c in cocktails} == {"Cuba Libre", "With Handadd", "Rum Cola Curacao"}

    def test_ilp_n2_covers_one_cocktail(self, db_commander: DatabaseCommander, monkeypatch: MonkeyPatch) -> None:
        """With n=2, only one cocktail can be covered; accept either Cuba Libre or With Handadd."""
        monkeypatch.setattr("src.data_utils.DatabaseCommander", lambda: db_commander)
        monkeypatch.setattr(db_commander, "get_most_used_ingredient_ids", lambda k=None: [1, 2, 3, 4, 5])

        ingredients, cocktails = select_optimal(2, "ilp")

        # Exactly two ingredients selected, and exactly one cocktail covered
        assert len(ingredients) == 2
        assert len(cocktails) == 1
        covered = cocktails[0]
        chosen_ids = set(self._ids(ingredients))

        # Validate the single covered cocktail matches the chosen ingredient pair
        if covered.name == "Cuba Libre":
            assert chosen_ids == {1, 2}
        elif covered.name == "With Handadd":
            assert chosen_ids == {1, 4}
        else:
            pytest.fail(f"Unexpected covered cocktail: {covered.name}")
