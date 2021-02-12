#!flask/bin/python
import os
import datetime
import logging
import json
from threading import Thread
import requests
from dotenv import load_dotenv
from flask import Flask, request, abort, jsonify
from email_sender import send_mail

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


@app.route("/")
def welcome():
    return jsonify({"status": "api working"})


@app.route("/hookhandler/cocktail", methods=["POST"])
def post_cocktail_hook():
    def post_to_hook(url, payload, headers):
        try:
            req = requests.post(url, data=payload, headers=headers)
            app.logger.info(f"{req.status_code}: Posted to webhook with payload: {payload}")
        except requests.exceptions.ConnectionError:
            app.logger.error("Could not connect to the webhook for the cocktail!")

    if not request.json or not "cocktailname" in request.json:
        abort(400)
    cocktail = {
        "cocktailname": request.json["cocktailname"],
        "volume": request.json["volume"],
        "makedate": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M"),
    }
    url = os.getenv("HOOK_ENDPOINT")
    headers = {"content-type": "application/json"}
    payload = json.dumps(cocktail)

    thread = Thread(target=post_to_hook, args=(url, payload, headers,))
    thread.start()
    return jsonify({"text": "Post to cocktail webhook started"}), 201


@app.route("/email", methods=["POST"])
def post_file_with_mail():
    data_file = request.files["upload_file"]
    text = send_mail(data_file.filename, data_file)
    app.logger.info(text)
    return jsonify({"text": text}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("PORT"))
