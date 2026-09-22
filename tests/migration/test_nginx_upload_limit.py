"""Tests for `_raise_nginx_upload_limit` (v4.9.0 migration)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from src.migration import migrator
from src.migration.setup_web import NON_SSL_CONFIG, SSL_CONFIG


@pytest.fixture
def written_config(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Collect what the migration pipes into `sudo tee`, nginx lives outside the test."""
    piped: list[str] = []

    def fake_run(command: list[str], **kwargs: object) -> None:
        if "tee" in command:
            piped.append(str(kwargs["input"]))

    monkeypatch.setattr(subprocess, "run", fake_run)
    return piped


@pytest.fixture
def nginx_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "cocktailberry_web_client"
    monkeypatch.setattr(migrator, "NGINX_SITE_CONFIG", path)
    return path


class TestRaiseNginxUploadLimit:
    def test_missing_config_is_noop(self, nginx_config: Path, written_config: list[str]) -> None:
        migrator._raise_nginx_upload_limit()
        assert written_config == []

    def test_existing_directive_is_adjusted(self, nginx_config: Path, written_config: list[str]) -> None:
        nginx_config.write_text(NON_SSL_CONFIG.replace("client_max_body_size 200M;", "client_max_body_size 20m;"))
        migrator._raise_nginx_upload_limit()
        assert "client_max_body_size 200M;" in written_config[0]
        assert "20m" not in written_config[0]

    def test_missing_directive_is_added_to_the_serving_block(
        self, nginx_config: Path, written_config: list[str]
    ) -> None:
        nginx_config.write_text(SSL_CONFIG.replace("    client_max_body_size 200M;\n", ""))
        migrator._raise_nginx_upload_limit()
        result = written_config[0]
        assert result.count("client_max_body_size 200M;") == 1
        # the redirect-only block above must stay untouched
        assert result.index("client_max_body_size") > result.index("return 301")

    def test_already_migrated_config_is_not_rewritten(self, nginx_config: Path, written_config: list[str]) -> None:
        nginx_config.write_text(NON_SSL_CONFIG)
        migrator._raise_nginx_upload_limit()
        assert written_config == []
