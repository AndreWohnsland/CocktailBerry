import json
import requests
from flask import Flask
from database import DatabaseHandler


def try_send_querry_data(app: Flask):
    db_handler = DatabaseHandler()
    failed_data = db_handler.get_failed_data()
    # Return if nothing to do
    if not failed_data:
        return
    # Else try to send all remaining data
    app.logger.info("Found some not sended data, trying to send ...")
    for send_id, data, url, headers in failed_data:
        try:
            res = requests.post(url, data=data, headers=json.loads(headers))
            app.logger.info(f"Code: {res.status_code}, to: {url}, Payload: {data}")
        except requests.exceptions.ConnectionError:
            app.logger.error("There is still no connection")
            return
        # pylint: disable=broad-except
        except Exception as err:
            app.logger.error(f"Some other error occured: {err}")
            return
        # if send successfully, delete this entry
        else:
            db_handler.delete_failed_by_id(send_id)
