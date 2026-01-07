from enum import StrEnum

DESCRIPTION = """
An endpoint for [CocktailBerry](https://github.com/AndreWohnsland/CocktailBerry) to control the machine over an API.

## Cocktails

Everything related to cocktails.
- Get all (or possible) cocktails.
- CRUD (Create, Read, Update, Delete) operations for cocktails.
- Prepare a cocktail.
- Stop a cocktail preparation.

## Preparation

Operations for the preparation of cocktails.

## Bottles

Options to change or refill bottles.
- Get all bottles.
- Refill a bottle.
- Update/Change a bottle.

## Ingredients

Manage the ingredients of the cocktails.
- Get all ingredients.
- CRUD (Create, Read, Update, Delete) operations for ingredients.

## Options

Different options, like settings and OS control. User mainly by the operator.

## Testing

For testing purposes, usually not used in production.
"""


class Tags(StrEnum):
    BOTTLES = "bottles"
    COCKTAILS = "cocktails"
    PREPARATION = "preparation"
    INGREDIENTS = "ingredients"
    OPTIONS = "options"
    PAYMENT = "payment"
    MAKER_PROTECTED = "maker protected"
    MASTER_PROTECTED = "master protected"
    TESTING = "testing"


TAGS_METADATA = [
    {
        "name": Tags.BOTTLES,
        "description": "Manage or change bottles.",
    },
    {
        "name": Tags.COCKTAILS,
        "description": "Operations with cocktails/recipes.",
    },
    {
        "name": Tags.PREPARATION,
        "description": "Operation for cocktail preparation.",
    },
    {
        "name": Tags.INGREDIENTS,
        "description": "Operations with ingredients.",
    },
    {
        "name": Tags.OPTIONS,
        "description": "Options for the machine.",
    },
    {
        "name": Tags.PAYMENT,
        "description": "Operation related to the payment service.",
    },
    {
        "name": Tags.MAKER_PROTECTED,
        "description": "Need x-maker-key header with the maker password, if this section is set to protected and password is set.",  # noqa: E501
    },
    {
        "name": Tags.MASTER_PROTECTED,
        "description": "Need x-master-key header with the master password if password is set.",
    },
    {
        "name": Tags.TESTING,
        "description": "For testing purposes.",
    },
]
