import uvicorn
from fastapi import FastAPI

from src.api.routers import bottles, cocktails, ingredients, options

_DESC = """
An endpoint for [CocktailBerry](https://github.com/AndreWohnsland/CocktailBerry) to control the machine over an API.

## Cocktails

Everything related to cocktails.
- Get all (or possible) cocktails.
- CRUD (Create, Read, Update, Delete) operations for cocktails.
- Prepare a cocktail.
- Stop a cocktail preparation.

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

_TAGS_METADATA = [
    {
        "name": "bottles",
        "description": "Manage or change bottles.",
    },
    {
        "name": "cocktails",
        "description": "Operations with cocktails/recipes.",
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
        "name": "testing",
        "description": "For testing purposes.",
    },
]

app = FastAPI(
    title="CocktailBerry API",
    version="1.0",
    description=_DESC,
    openapi_tags=_TAGS_METADATA,
)


app.include_router(cocktails.router)
app.include_router(bottles.router)
app.include_router(options.router)
app.include_router(ingredients.router)


@app.get("/", tags=["testing"])
async def root():
    return {"message": "Welcome to CocktailBerry, this API works!"}


def run_api(port: int = 8888):
    uvicorn.run("src.api.api:app", host="0.0.0.0", port=port)
