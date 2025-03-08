import pytest

from src.database_commander import DatabaseCommander


@pytest.fixture
def db_commander():
    """Fixture to create an in-memory SQLite database and populate it with test data."""
    db_commander = DatabaseCommander(db_url="sqlite:///:memory:")
    db_commander.copy_default_data_to_current_db()
    yield db_commander


def test_get_cocktail(db_commander: DatabaseCommander):
    """Test the get_cocktail method."""
    cocktail = db_commander.get_cocktail(1)
    assert cocktail is not None
    assert cocktail.name == "Cuba Libre"
    assert cocktail.alcohol == 11
    assert cocktail.amount == 290
    assert cocktail.enabled is True
    assert cocktail.virgin_available is False
    assert len(cocktail.ingredients) == 3

    ingredient = cocktail.ingredients[0]
    assert ingredient.name == "Weißer Rum"
    assert ingredient.alcohol == 40
    assert ingredient.amount == 80
