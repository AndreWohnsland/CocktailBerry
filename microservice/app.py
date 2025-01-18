import datetime
import json
import os
from threading import Thread

import requests
import uvicorn
from database import DatabaseHandler
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.logger import logger
from fastapi.responses import JSONResponse
from helper import generate_urls_and_headers
from query_sender import try_send_query_data

from models import Cocktail

load_dotenv()

app = FastAPI()


@app.get("/")
async def welcome():
    return JSONResponse(content={"status": "api working"})


@app.post("/hookhandler/cocktail")
async def post_cocktail_hook(cocktail: Cocktail):
    def post_to_hook(url: str, payload: str, headers: dict, send_query: bool):
        try:
            req = requests.post(url, data=payload, headers=headers, timeout=10)
            logger.info("%s: Posted to %s with payload: %s", req.status_code, url, payload)
            if send_query:
                try_send_query_data()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            logger.error("Could not connect to %s for the cocktail data!", url)
            db_handler = DatabaseHandler()
            db_handler.save_failed_post(payload, url, headers)
        except Exception as err:
            logger.error("Some other error occurred: %s", err)

    make_date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")
    if cocktail.makedate is not None:
        make_date = cocktail.makedate

    cocktail_data = {
        "cocktailname": cocktail.cocktailname,
        "volume": cocktail.volume,
        "machinename": cocktail.machinename,
        "countrycode": cocktail.countrycode,
        "ingredients": cocktail.ingredients,
        "makedate": make_date,
    }
    endpoint_data = generate_urls_and_headers()
    payload = json.dumps(cocktail_data)
    if not endpoint_data:
        return JSONResponse(content={"text": "No endpoints activated", "data": cocktail_data}, status_code=201)

    for pos, (url, headers) in enumerate(endpoint_data):
        send_query = pos == 0
        thread = Thread(
            target=post_to_hook,
            args=(url, payload, headers, send_query),
        )
        thread.start()
    return JSONResponse(content={"text": "Post to cocktail webhook started"}, status_code=201)


@app.post("/data-export")
async def post_file_with_mail(upload_file: UploadFile = File(...)):
    text = f"Not implemented sending data. Datatype is {type(upload_file)}"
    logger.info(text)
    return JSONResponse(content={"text": text}, status_code=200)


@app.post("/debug")
@app.get("/debug")
@app.put("/debug")
async def debug_ep(cocktail: dict | None = None):
    logger.info(cocktail)
    return JSONResponse(content={"text": "debug"}, status_code=200)


if __name__ == "__main__":
    try_send_query_data()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
