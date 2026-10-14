import os
from http import HTTPStatus

import requests
from fastapi.logger import logger

# Sentinel values must match the placeholders shipped in .env.example / user .env files.
DEFAULT_HOOK_EP = "enpointforhook"
DEFAULT_API_KEY = "readdocshowtoget"
API_ENDPOINT = "https://api.cocktailberry.org/api/v1/cocktail"
API_CHECK_ENDPOINT = "https://api.cocktailberry.org/api/v1/"


def check_api_key() -> None:
    """Check the configured api key against the protected check route and log the result."""
    api_key = os.getenv("API_KEY")
    if api_key is None or api_key == DEFAULT_API_KEY:
        logger.info("API key is not set or is using the default placeholder.")
        return
    try:
        response = requests.get(API_CHECK_ENDPOINT, headers={"x-api-key": api_key}, timeout=10)
    except requests.exceptions.RequestException:
        logger.warning("Could not reach the CocktailBerry api to verify the API key, check skipped.")
        return
    if response.ok:
        logger.info("API key check ok: %s", response.json().get("message", ""))
    elif HTTPStatus.BAD_REQUEST <= response.status_code < HTTPStatus.INTERNAL_SERVER_ERROR:
        logger.error(
            "API key check failed (%s), the api rejects your key. Check the API_KEY in your .env, "
            "cocktail data will not be accepted until it is fixed.",
            response.status_code,
        )
    else:
        logger.warning("API key check inconclusive, the api responded with %s.", response.status_code)


def parse_hook_headers(config: str) -> dict[str, str]:
    """Parse the HOOK_HEADERS env format `name:value,name2:value2`."""
    headers: dict[str, str] = {}
    for entry in config.split(","):
        # values may contain colons themselves, so split only at the first one
        name, value = entry.split(":", 1)
        headers[name] = value
    return headers


def generate_urls_and_headers() -> list[tuple[str, dict[str, str]]]:
    """Generate the urls as well as the header from the .env data."""
    hook_url = os.getenv("HOOK_ENDPOINT")
    api_key = os.getenv("API_KEY")
    hook_headers_config = os.getenv("HOOK_HEADERS")
    if hook_headers_config is None:
        hook_headers = {"content-type": "application/json"}
    else:
        hook_headers = parse_hook_headers(hook_headers_config)
    endpoint_data: list[tuple[str, dict[str, str]]] = []
    if (hook_url != DEFAULT_HOOK_EP) and (hook_url is not None):
        endpoint_data.append(
            (
                hook_url,
                hook_headers,
            )
        )
    if (api_key != DEFAULT_API_KEY) and (api_key is not None):
        api_headers = {
            "content-type": "application/json",
            "x-api-key": api_key,
        }
        endpoint_data.append(
            (
                API_ENDPOINT,
                api_headers,
            )
        )

    return endpoint_data
