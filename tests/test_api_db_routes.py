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
