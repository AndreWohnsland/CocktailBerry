import json
import requests
from flask import Flask
from database import DatabaseHandler

from helper import API_ENDPOINT, OLD_API_ENDPOINT


def try_send_query_data(app: Flask):
    db_handler = DatabaseHandler()
    failed_data = db_handler.get_failed_data()
    # Return if nothing to do
    if not failed_data:
        return
    # Else try to send all remaining data
    app.logger.info("Found some not sended data, trying to send ...")
    for send_id, data, url, headers in failed_data:
        # overwrite old endpoint
        if url == OLD_API_ENDPOINT:
            url = API_ENDPOINT
        try:
            res = requests.post(url, data=data, headers=json.loads(headers), timeout=10)
            app.logger.info(f"Code: {res.status_code}, to: {url}, Payload: {data}")
        except requests.exceptions.ConnectionError:
            app.logger.error("There is still no connection")
            return
        # pylint: disable=broad-except
        except Exception as err:
            app.logger.error(f"Some other error occurred: {err}")
            return
        # if send successfully, delete this entry
        else:
            db_handler.delete_failed_by_id(send_id)
