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

    def log_connection_error(self, func: str):
        self.logger.log_event("ERROR", f"Could not connect to the microservice endpoint: '{func}'")

    def return_service_disabled(self):
        return {
            "status": 503,
            "message": "microservice disabled",
        }

    def post_cocktail_to_hook(self, cocktailname: str, cocktail_volume: int) -> Dict:
        if not self.USE_MICROSERVICE:
            return self.return_service_disabled()
        # calculare volume in litre
        payload = json.dumps({"cocktailname": cocktailname, "volume": cocktail_volume / 1000})
        endpoint = "/hookhandler/cocktail"
        full_url = f"{self.base_url}{endpoint}"
        ret_data = {}
        try:
            req = requests.post(full_url, data=payload, headers=self.headers)
            message = str(req.text).replace("\n", "")
            ret_data = {
                "status": req.status_code,
                "message": message,
            }
            self.logger.log_event("INFO", f"Posted cocktail to {full_url} | {req.status_code}: {message}")
        except requests.exceptions.ConnectionError:
            self.log_connection_error(full_url)
        return ret_data

    def send_mail(self, file_name, binary_file):
        if not self.USE_MICROSERVICE:
            return self.return_service_disabled()
        endpoint = "/email"
        full_url = f"{self.base_url}{endpoint}"
        ret_data = {}
        files = {"upload_file": (file_name, binary_file,)}
        try:
            req = requests.post(full_url, files=files)
            message = str(req.text).replace("\n", "")
            ret_data = {
                "status": req.status_code,
                "message": message,
            }
            self.logger.log_event("INFO", f"Posted file to {full_url} | {req.status_code}: {message}")
        except requests.exceptions.ConnectionError:
            self.log_connection_error(full_url)
        return ret_data
