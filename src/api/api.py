from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import bottles, cocktails, ingredients, options
from src.config.config_manager import CONFIG as cfg
from src.config.errors import ConfigError
from src.database_commander import DatabaseTransactionError
from src.filepath import CUSTOM_CONFIG_FILE
from src.machine.controller import MACHINE
from src.programs.addons import ADDONS
from src.utils import start_resource_tracker, time_print

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
        "name": "testing",
        "description": "For testing purposes.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_resource_tracker()
    ADDONS.setup_addons()
    try:
        cfg.read_local_config(update_config=True)
    except ConfigError as e:
        logger.error(f"Config Error: {e}")
        logger.exception(e)
        time_print(f"Config Error: {e}, please check the config file. You can edit the file at: {CUSTOM_CONFIG_FILE}.")
        time_print("Opening the config window to correct the error.")
        raise
    MACHINE.init_machine()
    MACHINE.default_led()
    yield
    MACHINE.cleanup()


app = FastAPI(
    title="CocktailBerry API", version="1.0", description=_DESC, openapi_tags=_TAGS_METADATA, lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DatabaseTransactionError)
async def database_transaction_error_handler(request: Request, exc: DatabaseTransactionError):
    return JSONResponse(
        status_code=406,
        content={"detail": str(exc)},
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
