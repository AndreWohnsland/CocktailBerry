import os

DEFAULT_HOOK_EP = "enpointforhook"
DEFAULT_API_KEY = "readdocshowtoget"
OLD_API_ENDPOINT = "https://cocktailberryapi-1-u0613408.deta.app/cocktail"
API_ENDPOINT = "https://api.cocktailberry.org/api/v1/cocktail"


def generate_urls_and_headers() -> list[tuple[str, dict[str, str]]]:
    """Generate the urls as well as the header from the .env data."""
    hook_url = os.getenv("HOOK_ENDPOINT")
    api_key = os.getenv("API_KEY")
    hook_headers_config = os.getenv("HOOK_HEADERS", None)
    if hook_headers_config is None:
        # If no headers are set, use common content type
        hook_headers = {"content-type": "application/json"}
    else:
        # Split the header config into a list
        # the config is header:value,header2:value2
        headers = hook_headers_config.split(",")
        hook_headers = dict([x.split(":") for x in headers])
    api_headers = {
        "content-type": "application/json",
        "x-api-key": api_key,
    }
    use_hook = (hook_url != DEFAULT_HOOK_EP) and (hook_url is not None)
    use_api = (api_key != DEFAULT_API_KEY) and (api_key is not None)
    endpoint_data = []
    if use_hook:
        endpoint_data.append(
            (
                hook_url,
                hook_headers,
            )
        )
    if use_api:
        endpoint_data.append(
            (
                API_ENDPOINT,
                api_headers,
            )
        )

    return endpoint_data
