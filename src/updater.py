import os
import sys
from pathlib import Path
from git import Repo

from src.migrator import Migrator
from src.logger_handler import LoggerHandler


logger = LoggerHandler("updater_module", "production_logs")


class Updater:
    """Class to get update from GitHub"""

    def __init__(self):
        dirpath = Path(os.path.abspath(__file__)).parents[0]
        self.git_path = dirpath.parents[0]
        self.repo = Repo(self.git_path)

    def update(self):
        """Updates from the Git remote"""
        latest_tag = self.repo.tags[-1]
        logger.log_event("INFO", f"Updating to {latest_tag.name}")
        # Is there a better way to pull the state of a specific tag, without checking out to that tag?
        self.repo.remotes.origin.pull()
        # restart the programm, this will not work if executed over IDE
        print("Restarting the application!")
        os.execl(sys.executable, self.git_path / "runme.py", *sys.argv)

    def check_for_updates(self) -> bool:
        """Check if there is a new version available"""
        # if not on master (e.g. dev) return false
        if self.repo.active_branch.name != "master":
            return False
        # First fetch the origin latest data
        self.repo.remotes.origin.fetch()
        # Get the latest tag an compare the diff with the current branch
        # Usually this should work since the default is master branch and "normal" users shouldn't be chaning files
        # Not using diff but local and remote tags to compare, since some problems exists comparing by diff
        latest_tag = self.repo.tags[-1]
        # Either build diff or just simply check local version with latest
        # Currently using local version tag, this will prob work best,
        # if the programmer does not forget to update the version in the migrator
        migrator = Migrator()
        update_available = migrator.older_than_version(latest_tag.name.replace("v", ""))
        if update_available:
            logger.log_event("INFO", f"Update {latest_tag.name} is available")
        return update_available
