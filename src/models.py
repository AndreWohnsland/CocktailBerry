import copy
import math
from dataclasses import field
from enum import Enum

from pydantic import computed_field
from pydantic.dataclasses import dataclass as pydantic_dataclass

from src import __version__
from src.migration.version import Version

_NOT_SET = "Not Set"


class PrepareResult(Enum):
    """Result of the prepare_cocktail function."""

    VALIDATION_OK = "VALIDATION_OK"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"
    CANCELED = "CANCELED"
    NOT_ENOUGH_INGREDIENTS = "NOT_ENOUGH_INGREDIENTS"
    ADDON_ERROR = "ADDON_ERROR"
    WAITING_FOR_PAYMENT = "WAITING_FOR_PAYMENT"


@pydantic_dataclass
class CocktailStatus:
    progress: int = 0
    message: str | None = None
    status: PrepareResult = PrepareResult.FINISHED


@pydantic_dataclass
class Ingredient:
    """Class to represent one ingredient."""

    id: int
    name: str
    alcohol: int
    bottle_volume: int
    fill_level: int
    hand: bool
    pump_speed: int
    amount: int = 0
    bottle: int | None = None
    selected: str | None = None
    cost: int = 0
    recipe_order: int = 2
    unit: str = "ml"

    def __post_init__(self) -> None:
        # limit fill level to [0, bottle_volume]
        self.fill_level = max(0, min(self.fill_level, self.bottle_volume))

    def __lt__(self, other: "Ingredient") -> bool:
        """Sort machine first, then highest amount and longest name."""
        self_compare = (int(self.bottle is None), -self.amount, -len(self.name))
        other_compare = (int(other.bottle is None), -other.amount, -len(other.name))
        return self_compare < other_compare


@pydantic_dataclass
class Cocktail:
    """Class to represent one cocktail."""

    id: int
    name: str
    alcohol: int
    amount: int
    enabled: bool
    price_per_100_ml: float
    virgin_available: bool
    ingredients: list[Ingredient]
    is_allowed: bool = True
    only_virgin: bool = False
    adjusted_alcohol: float = 0
    adjusted_amount: int = 0
    adjusted_ingredients: list[Ingredient] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.ingredients.sort()
        # shallow copy will keep same Ingredients as references
        self.adjusted_ingredients = copy.deepcopy(self.ingredients)
        self.adjusted_alcohol = self.alcohol
        self.adjusted_amount = self.amount

    # also changes handadd to machine add if the handadd is currently at the machine
    # this way the user needs to add less, if it happens to be also on the machine
    @property
    def handadds(self) -> list[Ingredient]:
        """Returns a list of all handadd Ingredients."""
        return [x for x in self.adjusted_ingredients if x.bottle is None and x.amount > 0]

    @property
    def machineadds(self) -> list[Ingredient]:
        """Returns a list of all machine Ingredients."""
        return [x for x in self.adjusted_ingredients if x.bottle is not None and x.amount > 0]

    @property
    def virgin_handadds(self) -> list[Ingredient]:
        """Returns a list of all non-alcoholic handadd Ingredients."""
        return [x for x in self.handadds if x.alcohol == 0]

    @property
    def virgin_machineadds(self) -> list[Ingredient]:
        """Returns a list of all non-alcoholic machine Ingredients."""
        return [x for x in self.machineadds if x.alcohol == 0]

    @property
    def is_virgin(self) -> bool:
        """Returns if the cocktail is virgin."""
        return self.adjusted_alcohol == 0

    def current_price(
        self,
        round_to_next: float,
        amount: int | None = None,
        price_multiplier: float = 1.0,
    ) -> float:
        """Return the price of the cocktail matched to next multiple of round_to_next."""
        if amount is None:
            amount = self.adjusted_amount
        raw_price = self.price_per_100_ml / 100 * amount * price_multiplier
        if round_to_next <= 0:
            return raw_price
        return math.ceil(raw_price / round_to_next) * round_to_next

    def is_possible(self, hand_available: list[int], max_hand_ingredients: int) -> bool:
        """Return if the recipe is possible with given additional hand add ingredients."""
        self.only_virgin = False
        if self._is_normal_cocktail_possible(hand_available, max_hand_ingredients):
            return True
        if self.virgin_available and self._is_virgin_cocktail_possible(hand_available, max_hand_ingredients):
            self.only_virgin = True
            return True
        return False

    def _has_all_ingredients(
        self,
        hand_available: list[int],
        max_hand_ingredients: int,
        machine_adds: list[Ingredient],
        hand_adds: list[Ingredient],
    ) -> bool:
        """Return if the recipe is possible with given additional hand add ingredients."""
        # If machine got not at least 1 add (=all handadd) return false
        # We don't want to let the user do all the work
        if len(machine_adds) < 1:
            return False
        # if the number of hand adds is higher than the allowed hand adds, return false
        if len(hand_adds) > max_hand_ingredients:
            return False
        for ing in machine_adds:
            if ing.bottle is None:
                return False
        hand_id = {x.id for x in hand_adds}
        return not hand_id - set(hand_available)

    def _is_normal_cocktail_possible(self, hand_available: list[int], max_hand_ingredients: int) -> bool:
        """Check if the normal (alcoholic) cocktail is possible."""
        return self._has_all_ingredients(
            hand_available,
            max_hand_ingredients,
            self.machineadds,
            self.handadds,
        )

    def _is_virgin_cocktail_possible(self, hand_available: list[int], max_hand_ingredients: int) -> bool:
        """Check if the virgin cocktail is possible."""
        return self._has_all_ingredients(
            hand_available,
            max_hand_ingredients,
            self.virgin_machineadds,
            self.virgin_handadds,
        )

    def enough_fill_level(self) -> Ingredient | None:
        """Check if the needed volume is there.

        Accepts if there is at least 80% of needed volume
        to be more efficient with the remainder volume in the bottle.
        """
        for ing in self.machineadds:
            if ing.amount * 0.8 > ing.fill_level:
                return ing
        return None

    def scale_cocktail(self, amount: int, alcohol_factor: float) -> None:
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
            ing.amount *= factor  # pyright: ignore[reportAttributeAccessIssue]
            scaled_amount += ing.amount
            concentration += ing.amount * ing.alcohol
        self.adjusted_alcohol = round(concentration / scaled_amount, 1)
        # scale all to desired amount
        scaling = amount / scaled_amount
        for ing in self.adjusted_ingredients:
            ing.amount = round(ing.amount * scaling)
        self.adjusted_amount = amount
        self.adjusted_ingredients.sort()


@pydantic_dataclass
class ConsumeData:
    recipes: dict[str, int]
    ingredients: dict[str, int]
    cost: dict[str, int] | None


@pydantic_dataclass
class AddonData:
    name: str = _NOT_SET
    description: str = _NOT_SET
    url: str = _NOT_SET
    disabled_since: str = ""
    is_installable: bool = False
    disabled: bool = False
    satisfy_min_version: bool = False
    minimal_version: str = ""
    version: str = "1.0.0"
    local_version: str | None = None
    file_name: str = ""
    installed: bool = False
    official: bool = True

    def __post_init__(self) -> None:
        if not self.file_name:
            self.file_name = self.url.rsplit("/", maxsplit=1)[-1]
        current_version = Version(__version__)
        if self.minimal_version != "":
            self.satisfy_min_version = Version(self.minimal_version) <= current_version
        if self.disabled_since != "":
            self.disabled = current_version >= Version(self.disabled_since)
        self.is_installable = self.satisfy_min_version and not self.disabled

    @computed_field
    @property
    def can_update(self) -> bool:
        """Check if addon can be updated based on local and remote versions."""
        if self.local_version is None:
            return False
        return Version(self.local_version) < Version(self.version) and self.is_installable and self.official


@pydantic_dataclass
class ResourceStats:
    min_cpu: float
    max_cpu: float
    mean_cpu: float
    min_ram: float
    max_ram: float
    mean_ram: float
    samples: int
    raw_cpu: list[float]
    raw_ram: list[float]


@pydantic_dataclass
class ResourceInfo:
    session_id: int
    start_time: str
