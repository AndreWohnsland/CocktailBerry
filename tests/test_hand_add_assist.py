from src.config.config_manager import CONFIG, shared
from src.hand_add_assist import build_hand_add_assist_items, should_use_hand_add_scale_assist
from src.models import Cocktail, Ingredient, PreparationResult, PrepareResult
from src.tabs import maker


def _build_cocktail() -> Cocktail:
    return Cocktail(
        id=1,
        name="Assist Test",
        alcohol=10,
        amount=110,
        enabled=True,
        price_per_100_ml=4.0,
        virgin_available=False,
        ingredients=[
            Ingredient(
                id=1,
                name="Rum",
                alcohol=40,
                bottle_volume=700,
                fill_level=700,
                hand=False,
                pump_speed=100,
                amount=100,
                bottle=1,
            ),
            Ingredient(
                id=2,
                name="Lime Juice",
                alcohol=0,
                bottle_volume=1000,
                fill_level=0,
                hand=True,
                pump_speed=100,
                amount=10,
                bottle=None,
            ),
            Ingredient(
                id=3,
                name="Mint Leaves",
                alcohol=0,
                bottle_volume=1000,
                fill_level=0,
                hand=True,
                pump_speed=100,
                amount=6,
                bottle=None,
                unit="leaves",
            ),
        ],
    )


def test_build_hand_add_assist_items_formats_measureable_items(monkeypatch):
    monkeypatch.setattr(CONFIG, "EXP_MAKER_UNIT", "oz")
    monkeypatch.setattr(CONFIG, "EXP_MAKER_FACTOR", 2.0)

    items = build_hand_add_assist_items(_build_cocktail())

    assert [item.name for item in items] == ["Mint Leaves", "Lime Juice"]
    assert items[0].display_amount == 12
    assert items[0].display_unit == "leaves"
    assert items[0].measurable is False
    assert items[0].target_weight_grams is None
    assert items[1].display_amount == 10
    assert items[1].display_unit == "oz"
    assert items[1].measurable is True
    assert items[1].target_weight_grams == 10.0


def test_should_use_hand_add_scale_assist_requires_flag_and_scale(monkeypatch):
    cocktail = _build_cocktail()
    monkeypatch.setattr(CONFIG, "MAKER_HANDADD_SCALE_ASSIST", True)

    assert should_use_hand_add_scale_assist(cocktail, has_scale=True) is True
    assert should_use_hand_add_scale_assist(cocktail, has_scale=False) is False


def test_prepare_cocktail_sets_hand_add_status(monkeypatch):
    cocktail = _build_cocktail()
    monkeypatch.setattr(CONFIG, "MAKER_HANDADD_SCALE_ASSIST", True)
    monkeypatch.setattr(CONFIG, "WAITER_LOGOUT_AFTER_COCKTAIL", False)

    class DummyMachineController:
        has_scale = True

        def make_cocktail(self, _w, ingredient_list, _recipe, finish_message=""):
            for ingredient in ingredient_list:
                ingredient.consumption = float(ingredient.amount)
            shared.cocktail_status.status = PrepareResult.FINISHED
            shared.cocktail_status.message = finish_message
            return PreparationResult(ingredients=ingredient_list)

    class DummyDatabaseCommander:
        def increment_recipe_counter(self, *_args):
            return None

        def set_multiple_ingredient_consumption(self, *_args):
            return None

        def save_event(self, *_args):
            return None

        def log_waiter_cocktail(self, *_args):
            return None

    monkeypatch.setattr(maker, "MachineController", DummyMachineController)
    monkeypatch.setattr(maker, "DatabaseCommander", lambda: DummyDatabaseCommander())
    monkeypatch.setattr(maker.ADDONS, "after_cocktail", lambda _data: None)
    monkeypatch.setattr(maker.SERVICE_HANDLER, "post_team_data", lambda *_args: None)
    monkeypatch.setattr(maker.SERVICE_HANDLER, "post_cocktail_to_hook", lambda *_args: None)

    result, message = maker.prepare_cocktail(cocktail)

    assert result == PrepareResult.FINISHED
    assert message == ""
    assert [item.name for item in shared.cocktail_status.hand_adds] == ["Mint Leaves", "Lime Juice"]
