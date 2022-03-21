import os
from typing import Dict, List, Tuple

DEFAULT_HOOK_EP = "enpointforhook"
DEFAULT_API_KEY = "readdocshowtoget"
API_ENDPOINT = "https://cberry.deta.dev/cocktail"


def generate_headers_and_urls() -> Tuple[Dict, List[str]]:
    """Generates the header as well as the urls from the .env data"""
    hookurl = os.getenv("HOOK_ENDPOINT")
    api_key = os.getenv("API_KEY")
    headers = {
        "content-type": "application/json",
        "X-API-Key": api_key,
    }
    use_hook = (hookurl != DEFAULT_HOOK_EP) and (hookurl is not None)
    use_api = (api_key != DEFAULT_API_KEY) and (api_key is not None)
    urls = ([hookurl] if use_hook else []) + ([API_ENDPOINT] if use_api else [])

    return headers, urls
