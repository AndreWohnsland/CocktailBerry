import json
import os
from enum import Enum
from typing import Optional

import requests

from src.config.config_manager import CONFIG as cfg
from src.database_commander import DatabaseCommander
from src.logger_handler import LogFiles, LoggerHandler
from src.models import Cocktail


class PostType(Enum):
    TEAMDATA = "teamdata"
    COCKTAIL = "cocktail"
    FILE = "file"


logger = LoggerHandler("microservice", LogFiles.SERVICE)


class ServiceHandler:
    """Class to handle all calls to the microservice within the docker."""

    def __init__(self):
        super().__init__()
        self.base_url = cfg.MICROSERVICE_BASE_URL
        self.headers = {"content-type": "application/json"}

    def post_cocktail_to_hook(self, cocktail_name: str, cocktail_volume: int, cocktail_object: Cocktail) -> dict:
        """Post the given cocktail data to the microservice handling internet traffic to send to defined webhook."""
        if not cfg.MICROSERVICE_ACTIVE:
            return _service_disabled()
        # Extracts the volume and name from the ingredient objects
        ingredient_data = [{"name": i.name, "volume": i.amount} for i in cocktail_object.adjusted_ingredients]
        data = {
            "cocktailname": cocktail_name,
            "volume": cocktail_volume,
            "machinename": cfg.MAKER_NAME,
            "countrycode": cfg.UI_LANGUAGE,
            "ingredients": ingredient_data,
        }
        payload = json.dumps(data)
        endpoint = self._decide_debug_endpoint(f"{self.base_url}/hookhandler/cocktail")
        return self._try_to_send(endpoint, PostType.COCKTAIL, payload=payload)

    def send_export_data(self, file_name: str, binary_file, is_disabled=True) -> dict:
        """Post the given file to the microservice handling internet traffic to send data to external source."""
        if not cfg.MICROSERVICE_ACTIVE:
            return _service_disabled()
        endpoint = self._decide_debug_endpoint(f"{self.base_url}/data-export")
        files = {
            "upload_file": (
                file_name,
                binary_file,
            )
        }
        # Currently not configured
        if is_disabled:
            return _service_disabled()
        return self._try_to_send(endpoint, PostType.FILE, files=files)

    def post_team_data(self, team_name: str, cocktail_volume: int, person: Optional[str] = None) -> dict:
        """Post the given team name to the team api if activated."""
        if not cfg.TEAMS_ACTIVE:
            return _team_disabled()
        data = {"team": team_name, "volume": cocktail_volume}
        if person is not None:
            data["person"] = person
        payload = json.dumps(data)
        endpoint = self._decide_debug_endpoint(f"{cfg.TEAM_API_URL}/cocktail")
        return self._try_to_send(endpoint, PostType.TEAMDATA, payload=payload)

    def get_team_data(self) -> dict[str, int]:
        """Get the current team data from the team api if activated."""
        if not cfg.TEAMS_ACTIVE:
            return {}
        endpoint = self._decide_debug_endpoint(f"{cfg.TEAM_API_URL}/leaderboard")
        headers = {"content-type": "application/json"}
        payload = {"limit": 100, "hour_range": 24}
        try:
            req = requests.get(endpoint, params=payload, headers=headers, timeout=2)
            try:
                return json.loads(req.text)
            except json.JSONDecodeError:
                logger.log_event("ERROR", f"Could not decode JSON from: '{endpoint}' for value {req.text}")
                return {}
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            self._log_connection_error(endpoint, PostType.TEAMDATA)
            return {}

    def _decide_debug_endpoint(self, endpoint: str):
        """Check if to use the given or the debug ep."""
        debug = os.getenv("DEBUG_MS", "False") == "True"
        if debug:
            return f"{self.base_url}/debug"
        return endpoint

    def _try_to_send(
        self, endpoint: str, post_type: PostType, payload: Optional[str] = None, files: Optional[dict] = None
    ) -> dict:
        """Try to send the data to the given endpoint.

        Logs the action, catches and logs if there is no connection.
        Raises an exception if there is no data to send.

        Args:
        ----
            endpoint (str): url to send
            post_type (PostType): Additional info for logger what was posted.
            payload (str, optional): JSON data for payload. Defaults to None.
            files (dict, optional): dict with key 'upload_file' + filename and binary data as tuple. Defaults to None.

        Raises:
        ------
            Exception: There is no data to send. This shouldn't be happening if used correctly.

        Returns:
        -------
            Dict: Status code and message, or empty if cannot reach service

        """
        DBC = DatabaseCommander()
        try:
            if payload is not None:
                req = requests.post(endpoint, data=payload, headers=self.headers, timeout=2)
                # if successfully send to teams, see if there are other to send.
                if post_type is PostType.TEAMDATA:
                    self._check_failed_data()
            elif files is not None:
                req = requests.post(endpoint, files=files, timeout=2)
            else:
                raise ValueError("Neither payload nor files given!")
            message = str(req.text).replace("\n", "")
            logger.log_event("INFO", f"Posted {post_type.value} to {endpoint} | {req.status_code}: {message}")
            return {
                "status": req.status_code,
                "message": message,
            }
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            self._log_connection_error(endpoint, post_type)
            # only save failed team data for now
            if post_type is PostType.TEAMDATA:
                DBC.save_failed_teamdata(payload)
            return {}

    def _log_connection_error(self, endpoint: str, post_type: PostType):
        logger.log_event("ERROR", f"Could not connect to: '{endpoint}' for {post_type.value}")

    def _check_failed_data(self):
        """Get one failed teamdata and sends it."""
        endpoint = f"{cfg.TEAM_API_URL}/cocktail"
        DBC = DatabaseCommander()
        failed_data = DBC.get_failed_teamdata()
        if failed_data:
            msg_id, payload = failed_data
            # Delete the old thing before recursion hell comes live
            DBC.delete_failed_teamdata(msg_id)
            self._try_to_send(endpoint, PostType.TEAMDATA, payload)


def _service_disabled():
    """Return that microservice is disabled."""
    return {
        "status": 503,
        "message": "Microservice disabled",
    }


def _team_disabled():
    """Return that teams is disabled."""
    return {
        "status": 503,
        "message": "Teams disabled",
    }


SERVICE_HANDLER = ServiceHandler()
