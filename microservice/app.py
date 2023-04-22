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
from flask.logging import create_logger

from query_sender import try_send_query_data
from database import DatabaseHandler
from helper import generate_urls_and_headers

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
_logger = create_logger(app)


@app.route("/")
def welcome():
    return jsonify({"status": "api working"})


@app.route("/hookhandler/cocktail", methods=["POST"])
def post_cocktail_hook():
    def post_to_hook(url: str, payload: str, headers: Dict, send_query: bool):
        try:
            req = requests.post(url, data=payload, headers=headers, timeout=10)
            _logger.info("%s: Posted to %s with payload: %s", req.status_code, url, payload)
            # Check if there is still querries data which was not send previously
            # Needs to be specified to send, since multiple threads would cause double sending
            if send_query:
                try_send_query_data(app)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.error("Could not connect to %s for the cocktail data!", url)
            db_handler = DatabaseHandler()
            db_handler.save_failed_post(payload, url, headers)
        # pylint: disable=broad-except
        except Exception as err:
            _logger.error("Some other error occurred: %s", err)

    if not request.json or "cocktailname" not in request.json:
        abort(400)

    make_date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")
    if "makedate" in request.json:
        make_date = request.json["make_date"]

    cocktail = {
        "cocktailname": request.json["cocktailname"],
        "volume": request.json["volume"],
        "machinename": request.json["machinename"],
        "countrycode": request.json["countrycode"],
        "ingredients": request.json["ingredients"],
        "makedate": make_date,
    }
    endpoint_data = generate_urls_and_headers()
    payload = json.dumps(cocktail)
    if not endpoint_data:
        return jsonify({"text": "No endpoints activated"}), 201

    for pos, (url, headers) in enumerate(endpoint_data):
        send_query = pos == 0
        thread = Thread(target=post_to_hook, args=(url, payload, headers, send_query,))
        thread.start()
    return jsonify({"text": "Post to cocktail webhook started"}), 201


@app.route("/data-export", methods=["POST"])
def post_file_with_mail():
    data_file = request.files["upload_file"]
    # TODO: Implement new sender / Endpoint
    text = f"Not implemented sending data. Datatype is {type(data_file)}"
    _logger.info(text)
    return jsonify({"text": text}), 200


@app.route("/debug", methods=["POST"])
def debug_ep():
    _logger.info(request.json)
    return jsonify({"text": "debug"}), 200


if __name__ == "__main__":
    try_send_query_data(app)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
