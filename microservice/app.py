#!flask/bin/python
import os
import datetime
import logging
import json
from threading import Thread
from typing import Dict
import requests
from dotenv import load_dotenv
from flask import Flask, request, abort, jsonify

from querry_sender import try_send_querry_data
from email_sender import send_mail
from database import DatabaseHandler
from helper import generate_headers_and_urls

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


@app.route("/")
def welcome():
    return jsonify({"status": "api working"})


@app.route("/hookhandler/cocktail", methods=["POST"])
def post_cocktail_hook():
    def post_to_hook(url: str, payload: str, headers: Dict, send_querry: bool):
        try:
            req = requests.post(url, data=payload, headers=headers)
            app.logger.info(f"{req.status_code}: Posted to {url} with payload: {payload}")
            # Check if there is still querries data which was not send previously
            # Needs to be specified to send, since multiple threads would cause double sending
            if send_querry:
                try_send_querry_data(app)
        except requests.exceptions.ConnectionError:
            app.logger.error(f"Could not connect to {url} for the cocktail data!")
            db_handler = DatabaseHandler()
            db_handler.save_failed_post(payload, url)
        # pylint: disable=broad-except
        except Exception as err:
            app.logger.error(f"Some other error occured: {err}")

    if not request.json or "cocktailname" not in request.json:
        abort(400)
    cocktail = {
        "cocktailname": request.json["cocktailname"],
        "volume": request.json["volume"],
        "machinename": request.json["machinename"],
        "countrycode": request.json["countrycode"],
        "makedate": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M"),
    }
    headers, urls = generate_headers_and_urls()
    payload = json.dumps(cocktail)

    for pos, url in enumerate(urls):
        send_querry = pos == 0
        thread = Thread(target=post_to_hook, args=(url, payload, headers, send_querry,))
        thread.start()
    return jsonify({"text": "Post to cocktail webhook started"}), 201


@app.route("/email", methods=["POST"])
def post_file_with_mail():
    data_file = request.files["upload_file"]
    text = send_mail(data_file.filename, data_file)
    app.logger.info(text)
    return jsonify({"text": text}), 200


@app.route("/debug", methods=["POST"])
def debug_ep():
    app.logger.info(request.json)
    return jsonify({"text": "debug"}), 200


if __name__ == "__main__":
    try_send_querry_data(app)
    app.run(host="0.0.0.0", port=os.getenv("PORT"))
