import sys

import pytest
from fastapi.testclient import TestClient

from src.database_commander import DatabaseCommander


@pytest.fixture
def client(db_commander: DatabaseCommander, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from src.api.api import app

    # every module aliases the global as DBC, so swap it in all of them at once
    for module in [m for name, m in sys.modules.items() if name.startswith("src.") and hasattr(m, "DBC")]:
        monkeypatch.setattr(module, "DBC", db_commander)
    # no context manager: the lifespan would start hardware and background services
    return TestClient(app)


def test_ingredient_create_update_delete_round_trip(client: TestClient) -> None:
    body = {
        "name": "Gin",
        "alcohol": 40,
        "bottle_volume": 700,
        "fill_level": 0,
        "cost": 1,
        "pump_speed": 100,
        "hand": False,
        "unit": "ml",
        "disallow_pump_back": False,
    }
    created = client.post("/api/ingredients", json=body)
    assert created.status_code == 200
    ingredient_id = created.json()["data"]["id"]

    updated = client.put(f"/api/ingredients/{ingredient_id}", json={**body, "alcohol": 37})
    assert updated.status_code == 200
    assert client.get(f"/api/ingredients/{ingredient_id}").json()["alcohol"] == 37

    assert client.delete(f"/api/ingredients/{ingredient_id}").status_code == 200
    assert client.get(f"/api/ingredients/{ingredient_id}").status_code == 404


def test_ingredient_listing_filters_hand_ingredients(client: TestClient) -> None:
    names = {i["name"] for i in client.get("/api/ingredients").json()}
    assert "Blue Curacao" in names
    machine_only = {i["name"] for i in client.get("/api/ingredients", params={"hand": False}).json()}
    assert "Blue Curacao" not in machine_only


def test_cocktail_servings_carry_the_charged_prices(
    client: TestClient, db_commander: DatabaseCommander, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.config.config_manager import CONFIG as cfg

    cuba_libre = db_commander.get_cocktail(1)
    assert cuba_libre is not None

    def set_price(price: float, virgin: bool) -> None:
        ingredients = [(i.id, i.amount, i.recipe_order) for i in cuba_libre.ingredients]
        db_commander.set_recipe(1, cuba_libre.name, 0, cuba_libre.amount, price, True, virgin, ingredients)

    set_price(3.67, virgin=False)
    monkeypatch.setattr(cfg, "MAKER_USE_RECIPE_VOLUME", False)
    monkeypatch.setattr(cfg, "MAKER_PREPARE_VOLUME", [250, 150])
    monkeypatch.setattr(cfg, "PAYMENT_PRICE_ROUNDING", 0.25)
    monkeypatch.setattr(cfg, "PAYMENT_VIRGIN_MULTIPLIER", 50)

    monkeypatch.setattr(cfg, "PAYMENT_TYPE", "SumUp")
    servings = client.get("/api/cocktails/1").json()["servings"]
    # 150 ml is 5.505 raw: half cents round up, so the step lifts it to 5.75 and not 5.50
    assert servings == [
        {"amount": 150, "price": 5.75, "virgin_price": None},
        {"amount": 250, "price": 9.25, "virgin_price": None},
    ]

    set_price(3.67, virgin=True)
    servings = client.get("/api/cocktails/1").json()["servings"]
    assert [s["virgin_price"] for s in servings] == [2.75, 4.75]

    monkeypatch.setattr(cfg, "PAYMENT_TYPE", "Disabled")
    servings = client.get("/api/cocktails/1").json()["servings"]
    assert servings == [
        {"amount": 150, "price": None, "virgin_price": None},
        {"amount": 250, "price": None, "virgin_price": None},
    ]


def test_cocktail_detail_and_bottle_assignment(client: TestClient) -> None:
    cocktail = client.get("/api/cocktails/1").json()
    assert cocktail["name"] == "Cuba Libre"
    assert {i["name"] for i in cocktail["ingredients"]} == {"White Rum", "Cola"}
    assert client.get("/api/cocktails/999").status_code == 404

    bottles = client.get("/api/bottles").json()
    assert bottles[0]["ingredient"]["name"] == "White Rum"


def test_role_cannot_be_deleted_while_a_waiter_uses_it(client: TestClient) -> None:
    role_id = client.post("/api/roles", json={"name": "Bar"}).json()["id"]
    assert client.post("/api/waiters", json={"nfc_id": "nfc-1", "name": "Sam", "role_id": role_id}).status_code == 200

    assert client.delete(f"/api/roles/{role_id}").status_code == 409
    assert client.delete("/api/waiters/nfc-1").status_code == 200
    assert client.delete(f"/api/roles/{role_id}").status_code == 200
    assert client.delete(f"/api/roles/{role_id}").status_code == 404
