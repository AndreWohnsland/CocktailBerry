import atexit
import datetime
import os
import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.logger_handler import LoggerHandler
from src.machine.controller import MACHINE
from src.models import PrepareResult
from src.ui.create_backup_restore_window import BACKUP_FILES, NEEDED_BACKUP_FILES
from src.updater import Updater
from src.utils import get_platform_data, has_connection, update_os

_logger = LoggerHandler("options_router")
_platform_data = get_platform_data()

router = APIRouter(tags=["options"], prefix="/options")


@router.get("")
async def get_options():
    return []


@router.post("")
async def update_options(options: dict):
    return {"message": f"Options {options} updated successfully!"}


@router.post("/clean")
async def clean_machine(background_tasks: BackgroundTasks):
    if shared.cocktail_status.status == PrepareResult.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Preparation already in progress")
    _logger.log_header("INFO", "Cleaning the Pumps")
    revert_pumps = cfg.MAKER_PUMP_REVERSION
    background_tasks.add_task(MACHINE.clean_pumps, None, revert_pumps)
    return {"message": "Cleaning process started"}


@router.post("/reboot")
async def reboot_system():
    if _platform_data.system == "Windows":
        raise HTTPException(status_code=400, detail="Cannot reboot on Windows")
    atexit._run_exitfuncs()  # pylint: disable=protected-access
    os.system("sudo reboot")
    return {"message": "System rebooting"}


@router.post("/shutdown")
async def shutdown_system():
    if _platform_data.system == "Windows":
        raise HTTPException(status_code=400, detail="Cannot shutdown on Windows")
    atexit._run_exitfuncs()  # pylint: disable=protected-access
    os.system("sudo shutdown now")
    return {"message": "System shutting down"}


@router.get("/data")
async def data_insights():
    # Return data insights
    return {"message": "Data insights"}


# TODO: Create Backup needs to return the zip file now
@router.get("/backup")
async def create_backup(location: str):
    backup_folder_name = f"CocktailBerry_backup_{datetime.datetime.now().strftime('%Y-%m-%d')}"
    backup_folder = Path(location) / backup_folder_name

    if backup_folder.exists():
        _logger.log_event("INFO", "Backup folder for today already exists, overwriting current data within")
        shutil.rmtree(backup_folder)
    backup_folder.mkdir()

    for _file in BACKUP_FILES:
        if _file.is_file():
            shutil.copy(_file, backup_folder)
        if _file.is_dir():
            shutil.copytree(_file, backup_folder / _file.name)

    return {"message": f"Backup created at {backup_folder}"}


# TODO: Upload Backup needs to use the zip file now
@router.post("/backup")
async def upload_backup(location: str):
    for _file in NEEDED_BACKUP_FILES:
        file_name = _file.name
        if not (Path(location) / file_name).exists():
            raise HTTPException(status_code=400, detail=f"Backup file {file_name} not found")
    # Assuming BackupRestoreWindow does some processing
    return {"message": "Backup restored"}


@router.get("/logs")
async def get_logs():
    # Return logs data
    return {"message": "Logs data"}


@router.get("/rfid")
async def rfid_writer():
    # Return RFID writer data
    return {"message": "RFID writer data"}


@router.post("/wifi")
async def update_wifi_data():
    # Return WiFi window data
    return {"message": "WiFi window data"}


@router.get("/addon")
async def addon_data():
    # Return addon window data
    return {"message": "Addon window data"}


@router.get("/connection")
async def check_internet_connection():
    is_connected = has_connection()
    return {
        "is_connected": is_connected,
        "message": "Internet connection is available" if is_connected else "No internet connection",
    }


@router.post("/update/system")
async def update_system(background_tasks: BackgroundTasks):
    if _platform_data.system == "Windows":
        raise HTTPException(status_code=400, detail="Cannot update system on Windows")
    background_tasks.add_task(update_os)
    return {"message": "System update started"}


@router.post("/update/software")
async def update_software():
    updater = Updater()
    update_available, info = updater.check_for_updates()
    if not update_available and not info:
        return {"message": "CocktailBerry is up to date"}
    if not update_available and info:
        return {"message": info}
    updater.update()
    return {"message": "Software update started"}
