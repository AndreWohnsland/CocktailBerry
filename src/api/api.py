from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src import __version__
from src.api.api_config import DESCRIPTION, TAGS_METADATA
from src.api.internal.log_config import log_config
from src.api.internal.validation import ValidationError
from src.api.models import ApiMessage
from src.api.routers import bottles, cocktails, ingredients, options
from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.config.errors import ConfigError
from src.data_utils import CouldNotInstallAddonError
from src.database_commander import DatabaseTransactionError
from src.filepath import CUSTOM_CONFIG_FILE, DEFAULT_IMAGE_FOLDER, USER_IMAGE_FOLDER
from src.machine.controller import MachineController
from src.migration.setup_web import download_latest_web_client
from src.programs.addons import ADDONS
from src.resource_stats import start_resource_tracker
from src.startup_checks import can_update, connection_okay, is_python_deprecated
from src.updater import Updater
from src.utils import time_print


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    start_resource_tracker()
    ADDONS.setup_addons()
    try:
        cfg.read_local_config(update_config=True)
    except ConfigError as e:
        logger.error(f"Config Error: {e}")
        time_print(f"Config Error: {e}, please check the config file. You can edit the file at: {CUSTOM_CONFIG_FILE}.")
        shared.startup_config_issue.set_issue(message=str(e))
        # only read in valid config and use default for faulty ones
        cfg.read_local_config(validate=False)
    if not connection_okay():
        shared.startup_need_time_adjustment.set_issue()
    if is_python_deprecated():
        shared.startup_python_deprecated.set_issue()
    mc = MachineController()
    mc.init_machine()
    mc.default_led()
    if cfg.MAKER_SEARCH_UPDATES:
        update_available, _ = can_update()
        if update_available:
            time_print("Update available, performing update...")
            # need to get also latest web build
            download_latest_web_client()
            updater = Updater()
            updater.update()
    ADDONS.start_trigger_loop()
    yield
    mc.cleanup()


app = FastAPI(
    title="CocktailBerry API",
    version=__version__,
    description=DESCRIPTION,
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
    root_path="/api",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/default", StaticFiles(directory=DEFAULT_IMAGE_FOLDER), name="default_images")
app.mount("/static/user", StaticFiles(directory=USER_IMAGE_FOLDER), name="user_images")


@app.exception_handler(DatabaseTransactionError)
async def database_transaction_error_handler(request: Request, exc: DatabaseTransactionError) -> JSONResponse:
    return JSONResponse(
        status_code=406,
        content={"detail": str(exc)},
    )


@app.exception_handler(ConfigError)
async def config_error_handler(request: Request, exc: ConfigError) -> JSONResponse:
    return JSONResponse(
        status_code=406,
        content={"detail": str(exc)},
    )


@app.exception_handler(CouldNotInstallAddonError)
async def addon_error_handler(request: Request, exc: CouldNotInstallAddonError) -> JSONResponse:
    return JSONResponse(
        status_code=406,
        content={"detail": str(exc)},
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    content = {
        "status": exc.status,
        "detail": exc.detail_msg,
        "bottle": exc.bottle,
    }
    return JSONResponse(status_code=exc.status_code, content=content)


app.include_router(cocktails.router)
app.include_router(cocktails.protected_router)
app.include_router(bottles.router)
app.include_router(bottles.protected_router)
app.include_router(options.router)
app.include_router(options.protected_router)
app.include_router(ingredients.router)
app.include_router(ingredients.protected_router)


@app.get("/", tags=["testing"], summary="Test endpoint, check if api works")
async def root() -> ApiMessage:
    return ApiMessage(message="Welcome to CocktailBerry, this API works!")


def run_api(port: int = 8000) -> None:
    uvicorn.run(app, host="0.0.0.0", port=port, log_config=log_config)
