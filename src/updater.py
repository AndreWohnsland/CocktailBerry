import sys
from git import Repo, GitCommandError  # type: ignore
import requests
from requests import Response

from src.filepath import ROOT_PATH
from src.migration.migrator import Migrator, _Version
from src.logger_handler import LoggerHandler
from src import FUTURE_PYTHON_VERSION
from src.utils import restart_program


_logger = LoggerHandler("updater_module")
_GITHUB_RELEASE_URL = "https://api.github.com/repos/andrewohnsland/cocktailberry/releases"


class Updater:
    """Class to get update from GitHub"""

    def __init__(self):
        self.git_path = ROOT_PATH
        self.repo = Repo(self.git_path)

    def update(self) -> bool:
        """Updates from the Git remote"""
        latest_tag = self._get_latest_tag()
        _logger.log_event("INFO", f"Updating to {latest_tag.name}")
        # Is there a better way to pull the state of a specific tag, without checking out to that tag?
        try:
            self.repo.remotes.origin.pull()
        except GitCommandError as err:
            _logger.log_event("ERROR", "Something went wrong while pulling the update, see debug logs for more information")  # noqa
            _logger.log_exception(err)
            return False
        # restart the program, this will not work if executed over IDE
        print("Restarting the application!")
        _logger.log_event("INFO", "Restarting program to reload updated code")
        restart_program()
        # technically, this will not be reached, but makes mypy happy and is easier for the logic
        return True

    def check_for_updates(self) -> tuple[bool, str]:
        """Check if there is a new version available"""
        # if not on master (e.g. dev) return false
        update_problem = ""
        if self.repo.active_branch.name != "master":
            update_problem = "Not on master branch, not checking for updates"
            _logger.log_event("WARNING", update_problem)
            return False, update_problem
        # Also do not make updates if current version does
        # not satisfy the future version requirement
        if sys.version_info < FUTURE_PYTHON_VERSION:
            update_problem = f"Python version is too old, not checking for updates. You need at least {FUTURE_PYTHON_VERSION}"  # noqa
            _logger.log_event("WARNING", update_problem)
            return False, update_problem
        # First fetch the origin latest data
        try:
            self.repo.remotes.origin.fetch()
        # if no internet connection, or other error, return False
        except GitCommandError as err:
            update_problem = "Something went wrong while fetching the repo data, see debug logs for more information"
            _logger.log_event("ERROR", update_problem)
            _logger.log_exception(err)
            return False, update_problem + f"\n{err}"
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
        """Extracts the latest version number from the tags"""
        latest_tag = sorted(self.repo.tags, key=lambda t: _Version(t.name.replace("v", "")))[-1]
        return latest_tag

    def _parse_release_data(self, response: Response):
        """Converts the response into a string to display """
        migrator = Migrator()
        text = ""
        for release in response.json():
            name = release.get('name', '')
            body = release.get("body", '')
            tag_name = release.get("tag_name", '')
            # only add release information newer than local version
            if not migrator.older_than_version(tag_name.replace("v", "")):
                break
            sep = 70 * "_"
            text += f"Release: {name}\n{body}\n{sep}\n\n"
        return text
