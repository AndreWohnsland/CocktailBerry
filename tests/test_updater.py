import json
from pathlib import Path

import pytest
import requests

from src.updater import Updater


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
