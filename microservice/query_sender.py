import json

import requests
from database import DatabaseHandler
from fastapi.logger import logger


def try_send_query_data() -> None:
    db_handler = DatabaseHandler()
    failed_data = db_handler.get_failed_data()
    # Return if nothing to do
    if not failed_data:
        return
    # Else try to send all remaining data
    logger.info("Found unsent data, trying to send ...")
    for send_id, data, url, headers in failed_data:
        try:
            res = requests.post(url, data=data, headers=json.loads(headers), timeout=10)
            logger.info(f"Code: {res.status_code}, to: {url}, Payload: {data}")
        except requests.exceptions.ConnectionError:
            logger.error("There is still no connection")
            return
        except Exception as err:
            logger.exception("Some other error occurred: %s", err)
            return
        # if send successfully, delete this entry
        else:
            db_handler.delete_failed_by_id(send_id)
