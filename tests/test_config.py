"""Tests for cronwrap.config module."""

import textwrap
from pathlib import Path

import pytest

from cronwrap.config import JobConfig, load_config
from cronwrap.alerting import AlertConfig


@pytest.fixture
def toml_config_file(tmp_path: Path) -> Path:
    cfg = tmp_path / "crons.toml"
    cfg.write_text(textwrap.dedent("""
        [jobs.backup]
        command = "/usr/bin/backup.sh"
        retries = 2
        retry_delay = 10.0
        log_level = "DEBUG"
        [jobs.backup.alert]
        to_addrs = ["ops@example.com"]
        alert_on_failure = true

        [jobs.cleanup]
        command = "rm -rf /tmp/cache"
    """))
    return cfg


@pytest.fixture
def yaml_config_file(tmp_path: Path) -> Path:
    cfg = tmp_path / "crons.yaml"
    cfg.write_text(textwrap.dedent("""
        jobs:
          sync:
            command: rsync -av /src /dst
            retries: 1
    """))
    return cfg


def test_load_toml_config(toml_config_file):
    jobs = load_config(toml_config_file)
    assert "backup" in jobs
    assert "cleanup" in jobs


def test_load_yaml_config(yaml_config_file):
    jobs = load_config(yaml_config_file)
    assert "sync" in jobs
    assert jobs["sync"].retries == 1


def test_defaults_applied(toml_config_file):
    jobs = load_config(toml_config_file)
    cleanup = jobs["cleanup"]
    assert cleanup.retries == 0
    assert cleanup.retry_delay == 5.0
    assert cleanup.log_level == "INFO"
    assert cleanup.timeout is None


def test_alert_config_parsed(toml_config_file):
    jobs = load_config(toml_config_file)
    alert = jobs["backup"].alert
    assert isinstance(alert, AlertConfig)
    assert "ops@example.com" in alert.to_addrs
    assert alert.alert_on_failure is True


def test_alert_defaults_when_not_specified(toml_config_file):
    jobs = load_config(toml_config_file)
    alert = jobs["cleanup"].alert
    assert alert.to_addrs == []
    assert alert.smtp_host == "localhost"
    assert alert.alert_on_success is False


def test_invalid_retries_raises():
    with pytest.raises(ValueError, match="retries"):
        JobConfig(name="x", command="echo hi", retries=-1)


def test_unsupported_format_raises(tmp_path):
    bad = tmp_path / "crons.ini"
    bad.write_text("[jobs]")
    with pytest.raises(ValueError, match="Unsupported"):
        load_config(bad)
