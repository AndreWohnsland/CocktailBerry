import json
from typing import Dict
import requests
from config.config_manager import ConfigManager
from src.logger_handler import LoggerHandler


class ServiceHandler(ConfigManager):
    """Class to handle all calls to the mircoservice within the docker"""

    def __init__(self):
        self.base_url = self.MICROSERVICE_BASE_URL
        self.logger = LoggerHandler("microservice", "service_logs")
        self.headers = {"content-type": "application/json"}

    def log_connection_error(self, endpoint: str):
        self.logger.log_event("ERROR", f"Could not connect to the microservice endpoint: '{endpoint}'")

    def post_cocktail_to_hook(self, cocktailname: str, cocktail_volume: int) -> Dict:
        """Post the given cocktail data to the microservice handling internet traffic to send to defined webhook"""
        if not self.USE_MICROSERVICE:
            return service_disabled()
        # calculate volume in litre
        payload = json.dumps({"cocktailname": cocktailname, "volume": cocktail_volume / 1000})
        endpoint = f"{self.base_url}/hookhandler/cocktail"
        return self.try_to_send(endpoint, payload=payload, post_type="cocktail")

    def send_mail(self, file_name: str, binary_file) -> Dict:
        """Post the given file to the microservice handling internet traffic to send as mail"""
        if not self.USE_MICROSERVICE:
            return service_disabled()
        endpoint = f"{self.base_url}/email"
        files = {"upload_file": (file_name, binary_file,)}
        return self.try_to_send(endpoint, post_type="file", files=files)

    def post_team_data(self, team_name: str, cocktail_volume: int) -> Dict:
        """Post the given team name to the team api if activated"""
        if not self.USE_TEAMS:
            return team_disabled()
        payload = json.dumps({"team": team_name, "volume": cocktail_volume})
        endpoint = f"{self.TEAM_API_URL}/cocktail"
        return self.try_to_send(endpoint, payload=payload, post_type="teamdata")

    def try_to_send(self, endpoint: str, payload: str = None, post_type: str = "", files: dict = None) -> Dict:
        """Try to send the data to the given endpoint.
        Logs the action, catches and logs if there is no connection.
        Raises an exception if there is no data to send.

        Args:
            endpoint (str): url to send
            payload (str, optional): JSON data for payload. Defaults to None.
            post_type (str, optional): Addional info for logger what was posted. Defaults to "".
            files (dict, optional): dict with key 'upload_file' + filename and binary data as tuple. Defaults to None.

        Raises:
            Exception: There is no data to send. This shouldn't be happening if used correctly.

        Returns:
            Dict: Statuscode and message, or empty if cannot reach service
        """
        try:
            if payload is not None:
                req = requests.post(endpoint, data=payload, headers=self.headers)
            elif files is not None:
                req = requests.post(endpoint, files=files)
            else:
                raise Exception('Neither payload nor files given!')
            message = str(req.text).replace("\n", "")
            self.logger.log_event("INFO", f"Posted {post_type} to {endpoint} | {req.status_code}: {message}")
            return {
                "status": req.status_code,
                "message": message,
            }
        except requests.exceptions.ConnectionError:
            self.log_connection_error(endpoint)
            return {}


def service_disabled():
    return {
        "status": 503,
        "message": "Microservice disabled",
    }


def team_disabled():
    return {
        "status": 503,
        "message": "Teams disabled",
    }
