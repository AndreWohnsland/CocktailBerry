import os
import re
import socket
import subprocess
from enum import Enum
from pathlib import Path
from typing import Optional

import typer

from src.filepath import DEFAULT_MICROSERVICE_FILE, LOCAL_MICROSERVICE_FILE, TEAMS_DOCKER_FILE

# defining pattern in file, where env is stored in 2nd grp
_HOOK_EP_REGEX = r"(HOOK_ENDPOINT=)(.+)"
_HOOK_HEADERS_REGEX = r"(HOOK_HEADERS=)(.+)"
_API_KEY_REGEX = r"(API_KEY=)(.+)"

_DEFAULT_HOOK_EP = "enpointforhook"
_DEFAULT_HOOK_HEADERS = "content-type:application/json"
_DEFAULT_API_KEY = "readdocshowtoget"

_SKIP_DIALOG = "Keep empty to skip (just press enter), enter 'd' to set back to default"


def setup_service(
    api_key: Optional[str] = None,
    hook_endpoint: Optional[str] = None,
    hook_header: Optional[str] = None,
    use_v1: bool = False,
) -> None:
    """Set up the microservice if any of args is given skip input.

    Else prompt user for data.
    If user let prompt empty, keep current value.
    """
    # copies the default file if there is no local one
    if not LOCAL_MICROSERVICE_FILE.exists():
        msg = "No local compose file find found, will use default template"
        typer.echo(typer.style(msg, fg=typer.colors.BLUE, bold=True))
        LOCAL_MICROSERVICE_FILE.write_text(DEFAULT_MICROSERVICE_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        msg = "Found local compose file, will use contained values"
        typer.echo(typer.style(msg, fg=typer.colors.BLUE, bold=True))
    # Gets compose file content
    compose_setup = LOCAL_MICROSERVICE_FILE.read_text(encoding="utf-8")

    # Get the current variables, prompt user for variable if not provided
    if not all([api_key, hook_endpoint, hook_header]):
        typer.echo(typer.style(_SKIP_DIALOG, fg=typer.colors.GREEN, bold=True))
    if api_key is None:
        current_api_key = _get_env_var(_API_KEY_REGEX, compose_setup)
        api_key = _user_prompt(current_api_key, _DEFAULT_API_KEY, "API key")
    if hook_endpoint is None:
        current_hook_endpoint = _get_env_var(_HOOK_EP_REGEX, compose_setup)
        hook_endpoint = _user_prompt(current_hook_endpoint, _DEFAULT_HOOK_EP, "hook endpoint")
    if hook_header is None:
        current_hook_header = _get_env_var(_HOOK_HEADERS_REGEX, compose_setup)
        hook_header = _user_prompt(current_hook_header, _DEFAULT_HOOK_HEADERS, "hook header")

    # replace the values in the file, uses default file as base
    # This is to also reflect changes that may occur in the default file
    compose_file_content = DEFAULT_MICROSERVICE_FILE.read_text(encoding="utf-8")
    compose_file_content = _replace_env_var(_API_KEY_REGEX, compose_file_content, api_key)
    compose_file_content = _replace_env_var(_HOOK_EP_REGEX, compose_file_content, hook_endpoint)
    compose_file_content = _replace_env_var(_HOOK_HEADERS_REGEX, compose_file_content, hook_header)

    # Write to the file the changes
    LOCAL_MICROSERVICE_FILE.write_text(compose_file_content, encoding="utf-8")

    # check if user still use v1
    cmd = ["docker", "compose"]
    if use_v1:
        cmd = ["docker-compose"]
    cmd = [*cmd, "-f", str(LOCAL_MICROSERVICE_FILE), "-p", "cocktailberry", "up", "--build", "-d"]
    msg = f"Docker Compose file is located at: {LOCAL_MICROSERVICE_FILE}"
    typer.echo(typer.style(msg, fg=typer.colors.BLUE, bold=True))
    msg = "Setting up the Docker Compose images ..."
    typer.echo(typer.style(msg, fg=typer.colors.GREEN, bold=True))
    subprocess.run(cmd, check=False)


def _get_env_var(regex: str, compose_setup: str) -> str:
    """Get the the according matched value from the file."""
    match = re.search(regex, compose_setup)
    return "" if match is None else match[2]


def _replace_env_var(regex: str, compose_setup: str, value: str) -> str:
    """Replace the value in the file."""
    return re.sub(regex, r"\1" + value, compose_setup)


def _user_prompt(current_value: str, default_value: str, display_name: str) -> str:
    """Prompt the user for the new value, returns new value."""
    current_part = f"the current value is: {current_value}"
    if current_value == default_value:
        current_part = "not set currently, it's the default"
    user_input = typer.prompt(
        f"Enter the {display_name}, {current_part}",
        default="",
        show_default=False,
    )
    if not user_input:
        user_input = current_value
    if user_input == "d":
        user_input = default_value
    return user_input


class LanguageChoice(str, Enum):
    """Enum for the language choice."""

    ENGLISH = "en"
    GERMAN = "de"


def _get_ip() -> str:
    """Get the IP of the machine, because gethostbyname does not work on all systems."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0)
    try:
        sock.connect(("10.254.254.254", 1))
        sock_ip = sock.getsockname()[0]
    except Exception:  # pylint: disable=broad-except
        sock_ip = "127.0.0.1"
    finally:
        sock.close()
    return sock_ip


def setup_teams(language: LanguageChoice) -> None:
    """Set up the Teams frontend + backend from compose file, using the given language."""
    msg = f"Setting up the Teams Docker Compose images, using {language.name} language ..."
    typer.echo(typer.style(msg, fg=typer.colors.BLUE, bold=True))
    # since we need to alter the env var, need a tmp file
    # this is because we cant set env vars in docker compose over the up command as string but file
    tmp_env_file = Path.home().absolute() / ".tmp_docker.env"
    with open(tmp_env_file, "w", encoding="utf_8") as tmp_file:
        tmp_file.write(f"UI_LANGUAGE={language.value}")
    # first need to pull latest image, otherwise it will use the old one, if it exists
    subprocess.run(
        ["docker", "compose", "-f", str(TEAMS_DOCKER_FILE), "--env-file", str(tmp_env_file.resolve()), "pull"],
        check=False,
    )
    cmd = [
        "docker",
        "compose",
        "-f",
        str(TEAMS_DOCKER_FILE),
        "--env-file",
        str(tmp_env_file.resolve()),
        "up",
        "--build",
        "-d",
    ]
    subprocess.run(cmd, check=False)
    typer.echo(typer.style("Done!", fg=typer.colors.GREEN, bold=True))
    os.remove(tmp_env_file)
    host_name = socket.gethostname()
    host_ip = _get_ip()
    msg = f"Teams frontend URL: http://{host_ip}:8050, service url: http://{host_ip}:8080 machine name is {host_name}"
    typer.echo(typer.style(msg, fg=typer.colors.BLUE, bold=True))
    msg = "You can use http://127.0.0.1:8080 in CocktailBerry if you are running it on the same machine"
    typer.echo(typer.style(msg, fg=typer.colors.BLUE, bold=True))
