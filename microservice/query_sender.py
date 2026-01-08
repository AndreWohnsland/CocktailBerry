import json

import requests
from database import DatabaseHandler
from fastapi.logger import logger
from helper import API_ENDPOINT, OLD_API_ENDPOINT


def try_send_query_data() -> None:
    db_handler = DatabaseHandler()
    failed_data = db_handler.get_failed_data()
    # Return if nothing to do
    if not failed_data:
        return
    # Else try to send all remaining data
    logger.info("Found some not sended data, trying to send ...")
    for send_id, data, url, headers in failed_data:
        # overwrite old endpoint
        target_url = url
        if url == OLD_API_ENDPOINT:
            target_url = API_ENDPOINT
        try:
            res = requests.post(target_url, data=data, headers=json.loads(headers), timeout=10)
            logger.info(f"Code: {res.status_code}, to: {target_url}, Payload: {data}")
        except requests.exceptions.ConnectionError:
            logger.error("There is still no connection")
            return
        # pylint: disable=broad-except
        except Exception as err:
            logger.error(f"Some other error occurred: {err}")
            return
        # if send successfully, delete this entry
        else:
            db_handler.delete_failed_by_id(send_id)
