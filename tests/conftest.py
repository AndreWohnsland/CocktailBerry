import pytest

from src.database_commander import DatabaseCommander
from src.db_models import DbBottle


@pytest.fixture
def db_commander():
    """Fixture to create an in-memory SQLite database and populate it with test data."""
    db_commander = DatabaseCommander(db_url="sqlite:///:memory:")
    # Create ingredients
    db_commander.insert_new_ingredient("White Rum", 40, 1000, False, 100, 100, "ml")  # id 1
    db_commander.insert_new_ingredient("Cola", 0, 1000, False, 100, 50, "ml")  # id 2
    db_commander.insert_new_ingredient("Orange Juice", 0, 1000, False, 100, 50, "ml")  # id 3
    db_commander.insert_new_ingredient("Blue Curacao", 20, 700, True, 100, 150, "cl")  # id 4
    db_commander.insert_new_ingredient("Tequila", 38, 750, False, 100, 200, "ml")  # id 5
    # This one will not be added to the machine / available
    db_commander.insert_new_ingredient("Fanta", 0, 1000, False, 100, 50, "ml")  # id 6

    # create bottle 1-24
    with db_commander.session_scope() as session:
        session.add_all(DbBottle(number=i) for i in range(1, 25))

    # Create cocktails
    # we have 2 that can be made, 3 that would be possible (1 disabled) and 1 that is not possible
    # has all ingredients available added all via machine
    db_commander.insert_new_recipe("Cuba Libre", 11, 290, True, False, [(1, 80, 1), (2, 210, 2)])  # id 1
    # has all ingredients available, but is disabled
    db_commander.insert_new_recipe("Tequila Sunrise", 15, 250, False, False, [(5, 50, 1), (3, 200, 2)])  # id 2
    # has one available ingredient added via handadd
    db_commander.insert_new_recipe("With Handadd", 20, 250, True, False, [(1, 50, 1), (4, 200, 2)])  # id 3
    # not all ingredients are available
    db_commander.insert_new_recipe("Not Available", 10, 250, True, False, [(4, 50, 1), (6, 200, 2)])  # id 4

    # Assign ingredients to bottles
    db_commander.set_bottle_at_slot("White Rum", 1)
    # set rum fill level to max
    db_commander.set_bottle_volumelevel_to_max([1])
    db_commander.set_bottle_at_slot("Cola", 2)
    db_commander.set_bottle_at_slot("Orange Juice", 3)
    # explicitly let bottle 4 empty to test if it is properly handles (e.g. None by DB)
    db_commander.set_bottle_at_slot("Tequila", 5)

    # Add one ingredient to available table
    db_commander.insert_multiple_existing_handadd_ingredients(["Blue Curacao"])

    yield db_commander
