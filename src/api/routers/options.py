import atexit
import datetime
import os
import shutil
import tempfile
import time
import zipfile
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from src.api.internal.utils import not_on_demo, only_change_theme_on_demo
from src.api.middleware import master_protected_dependency
from src.api.models import DataResponse, DateTimeInput, IssueData, PasswordInput, WifiData
from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.data_utils import generate_consume_data, get_addon_data, install_addon, remove_addon
from src.database_commander import DatabaseCommander
from src.dialog_handler import DIALOG_HANDLER as DH
from src.logger_handler import LoggerHandler
from src.machine.controller import MACHINE
from src.migration.backup import BACKUP_FILES, FILE_SELECTION_MAPPER, NEEDED_BACKUP_FILES
from src.models import AddonData, ConsumeData, PrepareResult, ResourceInfo, ResourceStats
from src.save_handler import SAVE_HANDLER
from src.updater import Updater
from src.utils import (
    get_log_files,
    get_platform_data,
    has_connection,
    list_available_ssids,
    read_log_file,
    restart_program,
    set_system_datetime,
    setup_wifi,
    update_os,
)

_logger = LoggerHandler("options_router")
_platform_data = get_platform_data()

router = APIRouter(tags=["options"], prefix="/options")
protected_router = APIRouter(
    tags=["options", "master protected"],
    prefix="/options",
    dependencies=[
        Depends(master_protected_dependency),
    ],
)


@router.get("", summary="Get the current options, passwords are sanitized as boolean (yes/no)")
async def get_options():
    # need to sanitized the passwords before returning, frontend only need to know if they are set
    # e.g. 0: False otherwise: True
    config = cfg.get_config()
    config["UI_MASTERPASSWORD"] = config["UI_MASTERPASSWORD"] != 0
    config["UI_MAKER_PASSWORD"] = config["UI_MAKER_PASSWORD"] != 0
    return config


@protected_router.get("/full", summary="Get the current options with UI properties/descriptions and passwords")
async def get_options_with_ui_properties():
    return cfg.get_config_with_ui_information()


def _restart_task():
    time.sleep(1)
    restart_program()


@protected_router.post("", summary="Update the options", dependencies=[Depends(only_change_theme_on_demo)])
async def update_options(options: dict, background_tasks: BackgroundTasks):
    cfg.set_config(options, True)
    cfg.sync_config_to_file()
    # resolve the issue, when we get here, there was no error in the config and we can resolve potential issues
    shared.startup_config_issue.has_issue = False
    # also create a background task to restart the backend after 1 second
    # only do this if more than the theme was changed (theme is handled by the frontend)
    if any(key != "MAKER_THEME" for key in options):
        background_tasks.add_task(_restart_task)
        return {"message": DH.get_translation("options_updated_and_restart")}
    return {"message": DH.get_translation("options_updated")}


@protected_router.post("/clean", tags=["preparation"], summary="Start the machine cleaning")
async def clean_machine(background_tasks: BackgroundTasks):
    if shared.cocktail_status.status == PrepareResult.IN_PROGRESS:
        return JSONResponse(
            status_code=400, content={"status": PrepareResult.IN_PROGRESS.value, "detail": DH.cocktail_in_progress()}
        )
    _logger.log_header("INFO", "Cleaning the Pumps")
    revert_pumps = cfg.MAKER_PUMP_REVERSION
    background_tasks.add_task(MACHINE.clean_pumps, None, revert_pumps)
    return {"message": DH.get_translation("cleaning_started")}


@protected_router.post("/reboot", summary="Reboot the system", dependencies=[not_on_demo])
async def reboot_system():
    if _platform_data.system == "Windows":
        raise HTTPException(status_code=400, detail="Cannot reboot on Windows")
    atexit._run_exitfuncs()  # pylint: disable=protected-access
    os.system("sudo reboot")
    return {"message": "System rebooting"}


@protected_router.post("/shutdown", summary="Shutdown the system", dependencies=[not_on_demo])
async def shutdown_system():
    if _platform_data.system == "Windows":
        raise HTTPException(status_code=400, detail="Cannot shutdown on Windows")
    atexit._run_exitfuncs()  # pylint: disable=protected-access
    os.system("sudo shutdown now")
    return {"message": "System shutting down"}


@protected_router.get("/data", summary="Get the data insights")
async def data_insights() -> DataResponse[dict[str, ConsumeData]]:
    return DataResponse(data=generate_consume_data())


@protected_router.post("/data/reset", summary="Reset the data insights", dependencies=[not_on_demo])
async def reset_data_insights():
    SAVE_HANDLER.export_data()
    return {"message": DH.get_translation("all_data_exported")}


@protected_router.get("/backup", summary="Create a backup of CocktailBerry data", dependencies=[not_on_demo])
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


@protected_router.post("/backup", summary="Restore a backup of CocktailBerry data", dependencies=[not_on_demo])
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

        # Detect the extracted root folder
        extracted_items = [item for item in tmpdir.iterdir() if item.is_dir()]
        if len(extracted_items) != 1:
            raise HTTPException(400, detail="Invalid ZIP structure: expected a single root folder")
        extracted_root = extracted_items[0]

        # Check for required files inside the extracted folder
        backup_files = NEEDED_BACKUP_FILES
        for name in restored_file:
            backup_files.extend(FILE_SELECTION_MAPPER[name])
        for needed_file in backup_files:
            if not (extracted_root / needed_file.name).exists():
                raise HTTPException(status_code=400, detail=DH.get_translation("backup_failed", file=needed_file.name))

        for _file in backup_files:
            source_path = extracted_root / _file.name
            target_path = _file
            # Differentiate between files and folders
            if source_path.is_file():
                shutil.copy(source_path, target_path)
            elif source_path.is_dir():
                shutil.copytree(source_path, target_path, dirs_exist_ok=True)

    return {"message": "Backup restored successfully"}


@protected_router.get("/logs", summary="Get the logs")
async def get_logs(warning_and_higher: bool = False) -> DataResponse[dict[str, list[str]]]:
    log_data: dict[str, list[str]] = {}
    for _file in get_log_files():
        log_data[_file] = read_log_file(_file, warning_and_higher)
    return DataResponse(data=log_data)


@protected_router.post("/rfid/scan", summary="Scan RFID card")
async def rfid_writer():
    # Return RFID writer data
    if _platform_data.system == "Windows":
        raise HTTPException(status_code=400, detail="NO RFID on Windows")
    return {"message": "NOT IMPLEMENTED"}


@protected_router.get("/wifi", summary="Get available WiFi SSIDs")
async def get_available_ssids() -> list[str]:
    if _platform_data.system == "Windows":
        raise HTTPException(status_code=400, detail="Cannot scan WiFi on Windows")
    return list_available_ssids()


@protected_router.post("/wifi", summary="Set WiFi SSID and password", dependencies=[not_on_demo])
async def update_wifi_data(wifi_data: WifiData):
    if _platform_data.system == "Windows":
        raise HTTPException(status_code=400, detail="Cannot set WiFi on Windows")
    success = setup_wifi(wifi_data.ssid, wifi_data.password)
    if not success:
        raise HTTPException(400, detail=DH.get_translation("wifi_setup_failed"))
    return {"message": DH.get_translation("wifi_success")}


@protected_router.get("/addon", summary="Get installed and available addons")
async def addon_data() -> list[AddonData]:
    return get_addon_data()


@protected_router.post("/addon", summary="Install addon")
async def add_addon(addon: AddonData):
    install_addon(addon)
    return {"message": f"Addon {addon.name} installed"}


@protected_router.delete("/addon/remove", summary="Remove addon")
async def delete_addon(addon: AddonData):
    remove_addon(addon)
    return {"message": f"Addon {addon.name} removed"}


@protected_router.get("/connection", summary="Check internet connection")
async def check_internet_connection():
    is_connected = has_connection()
    return {
        "is_connected": is_connected,
        "message": DH.get_translation("internet_connection_ok")
        if is_connected
        else DH.get_translation("internet_connection_not_ok"),
    }


@protected_router.post("/update/system", summary="Update the system", dependencies=[not_on_demo])
async def update_system(background_tasks: BackgroundTasks):
    if _platform_data.system == "Windows":
        raise HTTPException(status_code=400, detail="Cannot update system on Windows")
    background_tasks.add_task(update_os)
    return {"message": "System update started"}


@protected_router.post("/update/software", summary="Update CocktailBerry software", dependencies=[not_on_demo])
async def update_software():
    updater = Updater()
    update_available, info = updater.check_for_updates()
    if not update_available and not info:
        return {"message": DH.get_translation("cocktailberry_up_to_date")}
    if not update_available and info:
        return {"message": info}
    success = updater.update()
    if not success:
        raise HTTPException(400, detail=DH.get_translation("update_failed"))
    return {"message": "Software update started"}


@router.post("/password/master/validate", summary="Validate Master Password")
async def validate_master_password(password: PasswordInput):
    if password.password != cfg.UI_MASTERPASSWORD:
        raise HTTPException(status_code=403, detail="Invalid Master Password")
    return {"message": "Master password is valid"}


@router.post("/password/maker/validate", summary="Validate Maker Password")
async def validate_maker_password(password: PasswordInput):
    if password.password != cfg.UI_MAKER_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid Maker Password")
    return {"message": "Maker password is valid"}


@router.get("/issues", summary="Check if CocktailBerry has issues")
async def check_issues() -> IssueData:
    return IssueData(
        deprecated=shared.startup_python_deprecated,
        internet=shared.startup_need_time_adjustment,
        config=shared.startup_config_issue,
    )


@router.post("/issues/ignore", summary="Ignore issues", dependencies=[not_on_demo])
async def ignore_issues():
    shared.startup_python_deprecated.set_ignored()
    shared.startup_need_time_adjustment.set_ignored()
    shared.startup_config_issue.set_ignored()
    return {"message": "Issues ignored"}


@router.post("/datetime", summary="Update the system date and time", dependencies=[not_on_demo])
async def update_datetime(data: DateTimeInput):
    # need YYYY-MM-DD HH:MM:SS format, time from web is "just" HH:MM
    # users might also add ms, so remove them as well
    time_string = data.time.split(".")[0]
    # Add ":00" if seconds are missing
    if len(time_string.split(":")) == 2:
        time_string += ":00"
    datetime_string = f"{data.date} {time_string}"
    set_system_datetime(datetime_string)
    # resolve the internet connection issue, since time is set properly now (only thing we care)
    shared.startup_need_time_adjustment.has_issue = False
    return {"message": "Success"}


@router.get(
    "/resource_tracker/{session_number:int}",
    summary="Get system resource usage statistics",
    response_model=ResourceStats,
)
async def get_resource_stats_endpoint(session_number: int) -> ResourceStats:
    """Get system resource usage statistics and timeline for the current session."""
    return DatabaseCommander().get_resource_stats(session_number)


@router.get(
    "/resource_tracker/sessions",
    summary="Get start date and session number of all sessions",
    response_model=list[ResourceInfo],
)
async def get_resource_stats_all_sessions_endpoint() -> list[ResourceInfo]:
    """Get system resource usage statistics and timeline for all sessions."""
    return DatabaseCommander().get_resource_session_numbers()
