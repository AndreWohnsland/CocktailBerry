import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union


class PrepareResult(Enum):
    """Result of the prepare_cocktail function."""

    VALIDATION_OK = "VALIDATION_OK"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"
    CANCELED = "CANCELED"
    NOT_ENOUGH_INGREDIENTS = "NOT_ENOUGH_INGREDIENTS"
    COCKTAIL_NOT_FOUND = "COCKTAIL_NOT_FOUND"
    ADDON_ERROR = "ADDON_ERROR"


@dataclass
class CocktailStatus:
    progress: int = 0
    completed: bool = False
    message: Optional[str] = None
    status: PrepareResult = PrepareResult.FINISHED


@dataclass
class Ingredient:
    """Class to represent one ingredient."""

    id: int
    name: str
    alcohol: int
    bottle_volume: int
    fill_level: int
    hand: Union[bool, int]
    pump_speed: int
    amount: int = 0
    bottle: Optional[int] = None
    selected: Optional[str] = None
    cost: int = 0
    recipe_order: int = 2
    unit: str = "ml"

    def __post_init__(self):
        # limit fill level to [0, bottle_volume]
        self.fill_level = max(0, min(self.fill_level, self.bottle_volume))

    def __lt__(self, other):
        """Sort machine first, then highest amount and longest name."""
        self_compare = (int(self.bottle is None), -self.amount, -len(self.name))
        other_compare = (int(other.bottle is None), -other.amount, -len(other.name))
        return self_compare < other_compare


@dataclass
class Cocktail:
    """Class to represent one cocktail."""

    id: int
    name: str
    alcohol: int
    amount: int
    enabled: bool
    virgin_available: bool
    ingredients: list[Ingredient]
    adjusted_alcohol: float = 0
    adjusted_amount: int = 0
    adjusted_ingredients: list[Ingredient] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.ingredients.sort()
        # shallow copy will keep same Ingredients as references
        self.adjusted_ingredients = copy.deepcopy(self.ingredients)
        self.adjusted_alcohol = self.alcohol
        self.adjusted_amount = self.amount

    # also changes handadd to machine add if the handadd is currently at the machine
    # this way the user needs to add less, if it happens to be also on the machine
    @property
    def handadds(self):
        """Returns a list of all handadd Ingredients."""
        return [x for x in self.adjusted_ingredients if x.bottle is None]

    @property
    def machineadds(self):
        """Returns a list of all machine Ingredients."""
        return [x for x in self.adjusted_ingredients if x.bottle is not None]

    @property
    def is_virgin(self):
        """Returns if the cocktail is virgin."""
        return self.adjusted_alcohol == 0

    def is_possible(self, hand_available: list[int], max_hand_ingredients: int):
        """Return if the recipe is possible with given additional hand add ingredients."""
        machine = self.machineadds
        # If machine got not at least 1 add (=all handadd) return false
        # We don't want to let the user do all the work
        if len(machine) < 1:
            return False
        hand = self.handadds
        # if the number of hand adds is higher than the allowed hand adds, return false
        if len(hand) > max_hand_ingredients:
            return False
        for ing in machine:
            if ing.bottle is None:
                return False
        hand_id = {x.id for x in hand}
        return not hand_id - set(hand_available)

    def enough_fill_level(self) -> Optional[Ingredient]:
        """Check if the needed volume is there.

        Accepts if there is at least 80% of needed volume
        to be more efficient with the remainder volume in the bottle.
        """
        for ing in self.machineadds:
            if ing.amount * 0.8 > ing.fill_level:
                return ing
        return None

    def scale_cocktail(self, amount: int, alcohol_factor: float):
        """Scale the base cocktail recipe to given volume and alcohol factor.

        The scaling is saved in the adjusted_* properties.
        """
        scaled_amount = 0
        concentration = 0
        # reset adjusted to recipe values
        self.adjusted_ingredients = copy.deepcopy(self.ingredients)
        # scale alcoholic ingredients with factor
        for ing in self.adjusted_ingredients:
            factor = alcohol_factor if bool(ing.alcohol) else 1
            ing.amount *= factor  # type: ignore
            scaled_amount += ing.amount
            concentration += ing.amount * ing.alcohol
        self.adjusted_alcohol = round(concentration / scaled_amount, 1)
        # scale all to desired amount
        scaling = amount / scaled_amount
        for ing in self.adjusted_ingredients:
            ing.amount = round(ing.amount * scaling)
        self.adjusted_amount = amount
        self.adjusted_ingredients.sort()
