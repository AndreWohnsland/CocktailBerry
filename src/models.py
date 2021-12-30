import copy
from dataclasses import dataclass
from typing import List, Union


@dataclass
class Ingredient():
    """Class to represent one ingredient"""
    id: int
    name: str
    alcohol: int
    bottle_volume: int
    fill_level: int
    hand: Union[bool, int]
    amount: int = 0
    recipe_hand: Union[bool, int, None] = None
    bottle: Union[int, None] = None
    selected: Union[str, None] = None

    def __lt__(self, other):
        """Sort machine first, then highest amount and longest name"""
        self_hand = self.recipe_hand if self.recipe_hand is not None else self.hand
        other_hand = other.recipe_hand if other.recipe_hand is not None else other.hand
        return (int(self_hand), -self.amount, -len(self.name)) < (int(other_hand), -other.amount, -len(other.name))


@dataclass
class Cocktail():
    """Class to represent one cocktail"""
    id: int
    name: str
    alcohol: int
    amount: int
    comment: str
    enabled: bool
    ingredients: List[Ingredient]
    adjusted_ingredients: Union[List[Ingredient], None] = None
    adjusted_alcohol: int = 0
    adjusted_amount: int = 0

    def __post_init__(self):
        self.ingredients.sort()
        # shallow copy will keep same Ingredients as references
        self.adjusted_ingredients = copy.deepcopy(self.ingredients)
        self.adjusted_alcohol = self.alcohol
        self.adjusted_amount = self.amount

    def get_handadds(self):
        """Returns a list of all handadd Ingredients"""
        return [x for x in self.adjusted_ingredients if x.recipe_hand]

    def get_machineadds(self):
        """Returns a list of all machine Ingredients"""
        return [x for x in self.adjusted_ingredients if not x.recipe_hand]

    def is_possible(self, hand_available: List[int]):
        """Returns if the recipe is possible with given aditional hand add ingredients"""
        machine = self.get_machineadds()
        for ing in machine:
            if ing.bottle is None:
                return False
        hand = self.get_handadds()
        hand_id = {x.id for x in hand}
        if hand_id - set(hand_available):
            return False
        return True

    def enough_fill_level(self):
        """Checks if the needed volume is there
        Accepts if there is at least 80% of needed volume
        to be more efficient with the remainder volume in the bottle"""
        for ing in self.get_machineadds():
            if ing.amount * 0.8 > ing.fill_level:
                return [ing.name, ing.fill_level, ing.amount]
        return None

    def scale_cocktail(self, amount: int, alcohol_facor: float):
        """Scales the base cocktail recipe to given volume and alcohol factor
        The scaling is saved in the adjusted_* properties"""
        scaled_amount = 0
        concentration = 0
        # reset adjusted to recipe values
        self.adjusted_ingredients = copy.deepcopy(self.ingredients)
        # scale alcoholic ingredients with factor
        for ing in self.adjusted_ingredients:
            factor = alcohol_facor if bool(ing.alcohol) else 1
            ing.amount *= factor
            scaled_amount += ing.amount
            concentration += ing.amount * ing.alcohol
        self.adjusted_alcohol = round(concentration / scaled_amount)
        # scale all to desired amount
        scaling = amount / scaled_amount
        for ing in self.adjusted_ingredients:
            ing.amount = round(ing.amount * scaling)
        self.adjusted_amount = amount
        self.adjusted_ingredients.sort()
