import sys
from pathlib import Path
from git import Repo, GitCommandError  # type: ignore
import requests
from requests import Response

from src.migration.migrator import Migrator, _Version
from src.logger_handler import LoggerHandler
from src import FUTURE_PYTHON_VERSION
from src.utils import restart_program


_logger = LoggerHandler("updater_module")
_GITHUB_RELEASE_URL = "https://api.github.com/repos/andrewohnsland/cocktailberry/releases"


class Updater:
    """Class to get update from GitHub"""

    def __init__(self):
        dirpath = Path(__file__).parent.absolute()
        self.git_path = dirpath.parents[0]
        self.repo = Repo(self.git_path)

    def update(self):
        """Updates from the Git remote"""
        latest_tag = self._get_latest_tag()
        _logger.log_event("INFO", f"Updating to {latest_tag.name}")
        # Is there a better way to pull the state of a specific tag, without checking out to that tag?
        try:
            self.repo.remotes.origin.pull()
        except GitCommandError as err:
            _logger.log_event("ERROR", "Something went wrong while pulling the update")
            _logger.log_exception(err)
            return
        # restart the program, this will not work if executed over IDE
        print("Restarting the application!")
        _logger.log_event("INFO", "Restarting program to reload updated code")
        restart_program()

    def check_for_updates(self) -> tuple[bool, str]:
        """Check if there is a new version available"""
        # if not on master (e.g. dev) return false
        if self.repo.active_branch.name != "master":
            return False, ""
        # Also do not make updates if current version does
        # not satisfy the future version requirement
        if sys.version_info < FUTURE_PYTHON_VERSION:
            return False, ""
        # First fetch the origin latest data
        try:
            self.repo.remotes.origin.fetch()
        # if no internet connection, or other error, return False
        except GitCommandError:
            return False, ""
        # Get the latest tag an compare the diff with the current branch
        # Usually this should work since the default is master branch and "normal" users shouldn't be changing files
        # Not using diff but local and remote tags to compare, since some problems exists comparing by diff
        latest_tag = self._get_latest_tag()
        # Either build diff or just simply check local version with latest
        # Currently using local version tag, this will prob work best,
        # if the programmer does not forget to update the version in the migrator
        migrator = Migrator()
        update_available = migrator.older_than_version(latest_tag.name.replace("v", ""))
        info = ""
        if update_available:
            _logger.log_event("INFO", f"Update {latest_tag.name} is available")
            release_data = requests.get(f"{_GITHUB_RELEASE_URL}?per_page=5", timeout=5000)
            info = self._parse_release_data(release_data)
        return update_available, info

    def _get_latest_tag(self):
        latest_tag = sorted(self.repo.tags, key=lambda t: _Version(t.name.replace("v", "")))[-1]
        return latest_tag

    def _parse_release_data(self, response: Response):
        """Converts the response into a string to display """
        text = ""
        for release in response.json():
            name = release.get('name', '')
            body = release.get("body", '')
            sep = 70 * "_"
            text += f"Release: {name}\n{body}\n{sep}\n\n"
        return text
