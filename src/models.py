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
    selected: str = None


@dataclass
class IngredientData():
    """Class to represent the data of one ingredient of a recipe/cocktail"""
    id: int
    name: str
    alcohol: int
    amount: int
    hand: bool


@dataclass
class Cocktail():
    """Class to represent one cocktail"""
    id: int
    name: str
    alcohol: int
    amount: int
    comment: str
    enabled: bool
    ingredients: List[IngredientData]
