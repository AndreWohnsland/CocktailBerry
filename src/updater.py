import sys
from dataclasses import dataclass, field
from enum import StrEnum

import requests
from git import GitCommandError, Repo
from requests import Response

from src import FUTURE_PYTHON_VERSION
from src.config.config_manager import shared
from src.database_commander import DatabaseCommander
from src.filepath import ROOT_PATH
from src.logger_handler import LoggerHandler
from src.migration.migrator import Migrator
from src.migration.setup_web import download_web_client
from src.migration.version import Version
from src.models import EventType
from src.utils import restart_v1, restart_v2

_logger = LoggerHandler("updater_module")
_GITHUB_RELEASE_URL = "https://api.github.com/repos/andrewohnsland/cocktailberry/releases"


@dataclass
class VersionInfo:
    """A single released version the user can update to."""

    version: str  # tag name, e.g. "v4.3.0"
    release_notes: str
    is_major: bool  # whether updating to it crosses a major boundary from the current version


@dataclass
class UpdateInfo:
    """Data class to hold update information."""

    status: "Status"
    message: str
    versions: list[VersionInfo] = field(default_factory=list)

    class Status(StrEnum):
        """Enumeration for update status."""

        UP_TO_DATE = "up_to_date"
        UPDATES_AVAILABLE = "updates_available"
        ERROR = "error"
        DISABLED = "disabled"

    def auto_update_version(self) -> str | None:
        """Return the highest available version within the current major, or None.

        This is the target for the low-friction startup paths (v2 silent, v1 yes/no
        prompt): it never crosses a major boundary. Returns None when the only
        available updates are major ones — those must be chosen manually.
        """
        non_major = [v for v in self.versions if not v.is_major]
        if not non_major:
            return None
        return max(non_major, key=lambda v: Version(v.version)).version


class Updater:
    """Class to get update from GitHub."""

    def __init__(self) -> None:
        """Initialize the updater class."""
        self.git_path = ROOT_PATH
        self.repo = Repo(self.git_path)

    def update(self, version: str) -> bool:
        """Update to the given release tag.

        Resets the local master branch hard to the tag (staying on master, so the
        "must be on master" guard in check_for_updates() stays valid). For v2 the
        matching web client build is downloaded first; if that fails the code is left
        untouched so the backend and the served frontend never diverge.
        """
        # v2 serves a pre-built web client; it must match the code we reset to.
        if not shared.is_v1:
            try:
                download_web_client(version)
            except Exception as err:
                # any download/extract failure must abort before we touch the code
                _logger.log_event("ERROR", f"Could not download web client for {version}, aborting update")
                _logger.log_exception(err)
                return False
        try:
            # ensure the target tag is present locally before resetting to it
            self.repo.remotes.origin.fetch(tags=True)
            _logger.log_event("INFO", f"Updating to {version}")
            self.repo.git.reset("--hard", version)
        except GitCommandError as err:
            _logger.log_event(
                "ERROR", "Something went wrong while applying the update, see debug logs for more information"
            )
            _logger.log_exception(err)
            return False
        # Save the software update event
        DatabaseCommander().save_event(EventType.SOFTWARE_UPDATE, version)
        # restart the program, this will not work if executed over IDE
        _logger.info("Restarting the application!")
        _logger.log_event("INFO", "Restarting program to reload updated code")
        if shared.is_v1:
            restart_v1()
        else:
            restart_v2()
        # technically, this will not be reached, but makes type checker happy and is easier for the logic
        return True

    def check_for_updates(self) -> UpdateInfo:
        """Check which newer released versions are available.

        Returns every published release newer than the local version (ascending),
        each flagged with whether it crosses a major boundary. Only runs on the
        master branch — users stay on master pinned to a release tag.
        """
        precondition_error = self._precondition_error()
        if precondition_error is not None:
            _logger.log_event("WARNING", precondition_error)
            return UpdateInfo(UpdateInfo.Status.ERROR, precondition_error)
        # First fetch the origin latest data so the local tags (reset targets) exist
        try:
            self.repo.remotes.origin.fetch(tags=True)
        # if no internet connection, or other error, return False
        except GitCommandError as err:
            update_problem = "Something went wrong while fetching the repo data, see debug logs for more information"
            _logger.log_event("ERROR", update_problem)
            _logger.log_exception(err)
            return UpdateInfo(UpdateInfo.Status.ERROR, update_problem + f"\n{err}")
        # Source the list from the published releases: this excludes drafts/prereleases,
        # carries release notes, and guarantees the web-client asset exists.
        try:
            release_data = requests.get(f"{_GITHUB_RELEASE_URL}?per_page=100", timeout=10)
            release_data.raise_for_status()
        except requests.RequestException as err:
            update_problem = "Could not fetch release information from GitHub"
            _logger.log_event("ERROR", update_problem)
            _logger.log_exception(err)
            return UpdateInfo(UpdateInfo.Status.ERROR, update_problem)
        versions = self._build_version_list(release_data)
        if not versions:
            return UpdateInfo(UpdateInfo.Status.UP_TO_DATE, "")
        _logger.log_event("INFO", f"{len(versions)} update(s) available, newest is {versions[-1].version}")
        return UpdateInfo(UpdateInfo.Status.UPDATES_AVAILABLE, self._format_release_notes(versions), versions)

    def _precondition_error(self) -> str | None:
        """Return why updates cannot be checked (branch / Python), or None if okay."""
        try:
            branch_name = self.repo.active_branch.name
        except TypeError as err:
            _logger.log_exception(err)
            return f"Cannot update: {err}"
        if branch_name != "master":
            return "Not on master branch, not checking for updates"
        # Do not update if the current Python does not satisfy the future requirement
        if sys.version_info < FUTURE_PYTHON_VERSION:
            return f"Python version is too old, not checking for updates. You need at least {FUTURE_PYTHON_VERSION}"
        return None

    def _build_version_list(self, response: Response) -> list[VersionInfo]:
        """Build the ascending list of newer published releases from the API response."""
        migrator = Migrator()
        current_major = migrator.local_version.major
        versions: list[VersionInfo] = []
        for release in response.json():
            if release.get("draft") or release.get("prerelease"):
                continue
            tag_name = release.get("tag_name", "")
            # only releases newer than the local version (forward-only, no downgrade)
            if not tag_name or not migrator.older_than_version(tag_name.replace("v", "")):
                continue
            versions.append(
                VersionInfo(
                    version=tag_name,
                    release_notes=release.get("body", "") or "",
                    is_major=Version(tag_name).major > current_major,
                )
            )
        versions.sort(key=lambda v: Version(v.version))
        return versions

    def _format_release_notes(self, versions: list[VersionInfo]) -> str:
        """Human-readable concatenation of the available release notes, newest first."""
        sep = 70 * "_"
        return "\n".join(f"Release: {v.version}\n{v.release_notes}\n{sep}\n" for v in reversed(versions))
