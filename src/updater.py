import contextlib
import json
import sys
from dataclasses import dataclass, field
from enum import StrEnum

import requests
from git import GitCommandError, Repo

from src import FUTURE_PYTHON_VERSION
from src.config.config_manager import shared
from src.database_commander import DatabaseCommander
from src.filepath import RELEASE_CACHE_FILE, ROOT_PATH
from src.logger_handler import LoggerHandler
from src.migration.migrator import Migrator
from src.migration.setup_web import download_web_client
from src.migration.version import Version
from src.models import EventType

_logger = LoggerHandler("updater_module")
_GITHUB_RELEASE_URL = "https://api.github.com/repos/andrewohnsland/cocktailberry/releases"


@dataclass
class VersionInfo:
    """A single released version the user can update to."""

    version: str  # tag name, e.g. "v4.3.0"
    release_notes: str | None  # None when the notes could not be fetched
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
        """Apply the given release tag to the local checkout.

        The caller restarts the program afterwards, which is what actually loads the
        new code. Keeping that out of here lets v2 send its response before the
        process is replaced.

        Order matters so a failure never leaves backend and served frontend diverged:
        fetch first (network preflight, tag present locally), then for v2 download
        and stage the matching web client, then reset the local master branch hard
        to the tag (staying on master, so the "must be on master" guard in
        check_for_updates() stays valid).
        """
        try:
            self.repo.remotes.origin.fetch(tags=True, prune=True, prune_tags=True)
        except GitCommandError as err:
            _logger.log_event("ERROR", "Could not fetch the repo data, aborting update")
            _logger.log_exception(err)
            return False
        if version not in {tag.name for tag in self.repo.tags}:
            _logger.log_event("ERROR", f"Release {version} does not exist, aborting update")
            return False
        # v2 serves a pre-built web client; it must match the code we reset to.
        if not shared.is_v1:
            try:
                download_web_client(version)
            except Exception as err:
                _logger.log_event("ERROR", f"Could not download web client for {version}, aborting update")
                _logger.log_exception(err)
                return False
        try:
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
        return True

    def check_for_updates(self) -> UpdateInfo:
        """Check which newer released versions are available.

        Returns every release newer than the local version (ascending), each flagged
        with whether it crosses a major boundary. Releases are read from the git tags,
        which never hit the GitHub API rate limit; the API only supplies the notes.
        Only runs on the master branch — users stay on master pinned to a release tag.
        """
        precondition_error = self._precondition_error()
        if precondition_error is not None:
            _logger.log_event("WARNING", precondition_error)
            return UpdateInfo(UpdateInfo.Status.ERROR, precondition_error)
        # Tags are the release list (a tag exists only for a published release, see ADR 0001/0004).
        # Prune so a tag deleted on the remote by the release guard does not linger as a phantom release.
        try:
            self.repo.remotes.origin.fetch(tags=True, prune=True, prune_tags=True)
        except GitCommandError as err:
            update_problem = "Something went wrong while fetching the repo data, see debug logs for more information"
            _logger.log_event("ERROR", update_problem)
            _logger.log_exception(err)
            return UpdateInfo(UpdateInfo.Status.ERROR, update_problem + f"\n{err}")
        versions = self._newer_releases()
        if not versions:
            return UpdateInfo(UpdateInfo.Status.UP_TO_DATE, "")
        self._attach_release_notes(versions)
        _logger.log_event("INFO", f"{len(versions)} update(s) available, newest is {versions[-1].version}")
        return UpdateInfo(UpdateInfo.Status.UPDATES_AVAILABLE, "", versions)

    def _newer_releases(self) -> list[VersionInfo]:
        """Build the ascending list of tags newer than the installed version."""
        local_version = Migrator().local_version
        versions: list[VersionInfo] = []
        for tag in self.repo.tags:
            try:
                candidate = Version(tag.name)
            except ValueError:
                continue
            if candidate > local_version:
                versions.append(
                    VersionInfo(version=tag.name, release_notes=None, is_major=candidate.major > local_version.major)
                )
        versions.sort(key=lambda v: Version(v.version))
        return versions

    def _attach_release_notes(self, versions: list[VersionInfo]) -> None:
        """Fill in the GitHub release notes, best effort: a version keeps None if they are unavailable."""
        releases = self._fetch_releases()
        if releases is None:
            return
        notes = {release.get("tag_name"): release.get("body") or "" for release in releases}
        for version in versions:
            version.release_notes = notes.get(version.version)

    def _fetch_releases(self) -> list[dict] | None:
        """Fetch the published releases for their notes, or None if unavailable.

        Unauthenticated GitHub API access is limited to 60 requests/hour per IP,
        so the last successful response is cached: on fetch errors (e.g. rate
        limit exceeded) the cached data is used, and the ETag skips the body
        transfer when nothing changed. Only the newest releases are needed, since
        notes are attached to versions newer than the installed one.
        """
        cache: dict = {}
        with contextlib.suppress(OSError, ValueError):
            cache = json.loads(RELEASE_CACHE_FILE.read_text())
        headers = {"If-None-Match": cache["etag"]} if "etag" in cache else {}
        try:
            response = requests.get(f"{_GITHUB_RELEASE_URL}?per_page=20", headers=headers, timeout=10)
            if response.status_code == requests.codes.not_modified:
                return cache["releases"]
            response.raise_for_status()
        except requests.RequestException as err:
            if "releases" in cache:
                _logger.log_event("WARNING", f"Could not fetch releases from GitHub, using cached data ({err})")
                return cache["releases"]
            _logger.log_event("WARNING", f"Could not fetch release notes from GitHub ({err})")
            return None
        releases = response.json()
        etag = response.headers.get("ETag")
        if etag:
            # cache is an optimization only; write may fail e.g. when the file is owned by root after a sudo run
            with contextlib.suppress(OSError):
                RELEASE_CACHE_FILE.write_text(json.dumps({"etag": etag, "releases": releases}))
        return releases

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
