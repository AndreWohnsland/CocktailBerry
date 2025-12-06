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

TAGS_METADATA = [
    {
        "name": "bottles",
        "description": "Manage or change bottles.",
    },
    {
        "name": "cocktails",
        "description": "Operations with cocktails/recipes.",
    },
    {
        "name": "preparation",
        "description": "Operation for cocktail preparation.",
    },
    {
        "name": "ingredients",
        "description": "Operations with ingredients.",
    },
    {
        "name": "options",
        "description": "Options for the machine.",
    },
    {
        "name": "payment",
        "description": "Operation related to the payment service.",
    },
    {
        "name": "maker protected",
        "description": "Need x-maker-key header with the maker password, if this section is set to protected and password is set.",  # noqa: E501
    },
    {
        "name": "master protected",
        "description": "Need x-master-key header with the master password if password is set.",
    },
    {
        "name": "testing",
        "description": "For testing purposes.",
    },
]
