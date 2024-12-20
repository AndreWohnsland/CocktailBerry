import atexit
import datetime
import os
import shutil
import tempfile
import zipfile
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from src.api.models import DataResponse, WifiData
from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.data_utils import AddonData, ConsumeData, generate_consume_data, get_addon_data
from src.logger_handler import LoggerHandler
from src.machine.controller import MACHINE
from src.migration.backup import BACKUP_FILES, FILE_SELECTION_MAPPER, NEEDED_BACKUP_FILES
from src.models import PrepareResult
from src.updater import Updater
from src.utils import (
    get_log_files,
    get_platform_data,
    has_connection,
    list_available_ssids,
    read_log_file,
    setup_wifi,
    update_os,
)

_logger = LoggerHandler("options_router")
_platform_data = get_platform_data()

router = APIRouter(tags=["options"], prefix="/options")


@router.get("")
async def get_options():
    return cfg.get_config()


@router.get("/ui")
async def get_options_with_ui_properties():
    return cfg.get_config_with_ui_information()


@router.post("")
async def update_options(options: dict):
    cfg.set_config(options, True)
    cfg.sync_config_to_file()
    return {"message": "Options updated successfully!"}


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
async def data_insights() -> DataResponse[dict[str, ConsumeData]]:
    return DataResponse(data=generate_consume_data())


@router.get("/backup")
async def create_backup():
    backup_folder_name = f"CocktailBerry_backup_{datetime.datetime.now().strftime('%Y-%m-%d')}"
    zip_file_name = f"{backup_folder_name}.zip"
    zip_file_path = Path(tempfile.gettempdir()) / zip_file_name  # Store in the system's temp folder

    with tempfile.TemporaryDirectory() as tmp_dirname:
        backup_folder = Path(tmp_dirname) / backup_folder_name
        backup_folder.mkdir()

        for _file in BACKUP_FILES:
            if _file.is_file():
                shutil.copy(_file, backup_folder)
            if _file.is_dir():
                shutil.copytree(_file, backup_folder / _file.name)

        # Create the ZIP file in the temp directory
        with zipfile.ZipFile(zip_file_path, "w") as zipf:
            for root, dirs, files in os.walk(backup_folder):
                for file in files:
                    file_path = Path(root) / file
                    zipf.write(file_path, file_path.relative_to(backup_folder.parent))

    # Return the file from the temp directory
    headers = {"Access-Control-Expose-Headers": "Content-Disposition"}
    return FileResponse(zip_file_path, filename=zip_file_path.name, headers=headers)


def parse_restored_file(
    restored_file: str = Query("style,config,images,database"),
) -> Sequence[Literal["style", "config", "images", "database"]]:
    allowed = ["style", "config", "images", "database"]
    try:
        data = restored_file.split(",")
    except Exception as e:
        raise HTTPException(422, detail=f"Invalid input for restored_file: {e}")
    if not all(x in allowed for x in data):
        raise HTTPException(422, f"Only {allowed} are allowed")
    return data  # type: ignore


@router.post("/backup")
async def upload_backup(
    file: UploadFile = File(...),
    restored_file: list[Literal["style", "config", "images", "database"]] = Depends(parse_restored_file),
):
    file_name = file.filename
    if not file_name:
        raise HTTPException(400, detail="Could not get filename from file")
    if not file_name.endswith(".zip"):
        raise HTTPException(400, detail="Uploaded file is not a ZIP backup file")

    with tempfile.TemporaryDirectory() as tmp_dirname:
        tmpdir = Path(tmp_dirname)
        zip_file_path = tmpdir / file_name

        # Save the uploaded file
        with open(zip_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract the ZIP file
        with zipfile.ZipFile(zip_file_path, "r") as zipf:
            zipf.extractall(tmpdir)

        extracted_root = tmpdir / zip_file_path.stem

        # Check for required files inside the extracted folder
        backup_files = NEEDED_BACKUP_FILES
        for name in restored_file:
            backup_files.extend(FILE_SELECTION_MAPPER[name])
        for needed_file in backup_files:
            if not (extracted_root / needed_file.name).exists():
                raise HTTPException(
                    status_code=400, detail=f"Backup file {needed_file.name} not found in the ZIP backup"
                )

        for _file in backup_files:
            source_path = extracted_root / _file.name
            target_path = _file
            # Differentiate between files and folders
            if source_path.is_file():
                shutil.copy(source_path, target_path)
            elif source_path.is_dir():
                shutil.copytree(source_path, target_path, dirs_exist_ok=True)

    return {"message": "Backup restored successfully"}


@router.get("/logs")
async def get_logs(warning_and_higher: bool = False) -> DataResponse[dict[str, list[str]]]:
    log_data: dict[str, list[str]] = {}
    for _file in get_log_files():
        log_data[_file] = read_log_file(_file, warning_and_higher)
    return DataResponse(data=log_data)


@router.post("/rfid/scan")
async def rfid_writer():
    # Return RFID writer data
    return {"message": "NOT IMPLEMENTED"}


@router.get("/wifi")
async def get_available_ssids() -> list[str]:
    if _platform_data.system == "Windows":
        raise HTTPException(status_code=400, detail="Cannot scan WiFi on Windows")
    return list_available_ssids()


@router.post("/wifi")
async def update_wifi_data(wifi_data: WifiData):
    if _platform_data.system == "Windows":
        raise HTTPException(status_code=400, detail="Cannot set WiFi on Windows")
    success = setup_wifi(wifi_data.ssid, wifi_data.password)
    if not success:
        raise HTTPException(400, detail="Could not setup WiFi, check logs for more information")
    return {"message": f"Wifi {wifi_data.ssid} setup successfully"}


@router.get("/addon")
async def addon_data() -> list[AddonData]:
    return get_addon_data()


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
    success = updater.update()
    if not success:
        raise HTTPException(400, detail="Could not update, see in logs for more information.")
    return {"message": "Software update "}
