#!flask/bin/python
from flask import Flask, request, abort, jsonify
import os
import requests
import json
import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


@app.route("/")
def welcome():
    return jsonify({"status": "api working"})


@app.route("/hookhandler/cocktail", methods=["POST"])
def post_cocktail_hook():
    if not request.json or not "cocktailname" in request.json:
        abort(400)
    cocktail = {
        "cocktailname": request.json["cocktailname"],
        "makedate": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M"),
    }
    url = os.getenv("HOOK_ENDPOINT")
    headers = {"content-type": "application/json"}
    req = requests.post(url, data=json.dumps(cocktail), headers=headers)
    print(cocktail)
    return jsonify({"cocktail": cocktail, "text": req.text}), req.status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("PORT"))
