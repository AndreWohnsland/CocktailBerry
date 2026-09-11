import json
from pathlib import Path

import pytest
import requests
from git import Repo

from src.migration.version import Version
from src.updater import UpdateInfo, Updater


class _Resp:
    def __init__(self, status_code: int, json_data: list | None = None, etag: str | None = None) -> None:
        self.status_code = status_code
        self._json = json_data or []
        self.headers = {"ETag": etag} if etag else {}

    def json(self) -> list:
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


def test_fetch_releases_caches_etag_and_serves_from_304(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cache_file = tmp_path / "cache.json"
    monkeypatch.setattr("src.updater.RELEASE_CACHE_FILE", cache_file)
    releases = [{"tag_name": "v9.9.9"}]
    monkeypatch.setattr(requests, "get", lambda *_, **__: _Resp(200, releases, 'W/"abc"'))
    updater = Updater()
    assert updater._fetch_releases() == releases
    assert json.loads(cache_file.read_text())["etag"] == 'W/"abc"'

    def not_modified(_url: str, headers: dict | None = None, timeout: int | None = None) -> _Resp:
        assert headers == {"If-None-Match": 'W/"abc"'}
        return _Resp(304)

    monkeypatch.setattr(requests, "get", not_modified)
    assert updater._fetch_releases() == releases


def test_fetch_releases_falls_back_to_cache_on_rate_limit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cache_file = tmp_path / "cache.json"
    monkeypatch.setattr("src.updater.RELEASE_CACHE_FILE", cache_file)
    cache_file.write_text(json.dumps({"etag": 'W/"abc"', "releases": [{"tag_name": "v1.2.3"}]}))
    monkeypatch.setattr(requests, "get", lambda *_, **__: _Resp(403))
    assert Updater()._fetch_releases() == [{"tag_name": "v1.2.3"}]


def test_fetch_releases_errors_without_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("src.updater.RELEASE_CACHE_FILE", tmp_path / "cache.json")
    monkeypatch.setattr(requests, "get", lambda *_, **__: _Resp(403))
    assert Updater()._fetch_releases() is None


def test_check_for_updates_lists_newer_tags_without_notes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Detection comes from the remote tags alone; unreachable release notes only leave the notes empty."""
    origin = Repo.init(tmp_path / "origin")
    (tmp_path / "origin" / "f").write_text("x")
    origin.index.add(["f"])
    origin.index.commit("init")
    for tag in ("v3.9.0", "v4.1.0", "v5.0.0", "v1.0"):
        origin.create_tag(tag)
    local = origin.clone(str(tmp_path / "local"))
    local.create_tag("v4.2.0")  # exists only locally, e.g. deleted on the remote by the release guard

    class _FakeMigrator:
        local_version = Version("4.0.0")

    monkeypatch.setattr("src.updater.Migrator", _FakeMigrator)
    monkeypatch.setattr("src.updater.RELEASE_CACHE_FILE", tmp_path / "cache.json")
    monkeypatch.setattr(requests, "get", lambda *_, **__: _Resp(403))
    updater = Updater()
    updater.repo = local
    monkeypatch.setattr(updater, "_precondition_error", lambda: None)

    info = updater.check_for_updates()

    assert info.status == UpdateInfo.Status.UPDATES_AVAILABLE
    assert [(v.version, v.is_major, v.release_notes) for v in info.versions] == [
        ("v4.1.0", False, None),
        ("v5.0.0", True, None),
    ]


def test_update_aborts_before_touching_web_client_when_fetch_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    from git import GitCommandError

    downloaded: list[str] = []
    monkeypatch.setattr("src.updater.download_web_client", downloaded.append)
    monkeypatch.setattr("src.updater.shared.is_v1", False)
    updater = Updater()

    def failing_fetch(*_: object, **__: object) -> None:
        raise GitCommandError("fetch", 128)

    monkeypatch.setattr("git.Remote.fetch", failing_fetch)

    assert updater.update("v9.9.9") is False
    assert downloaded == []
