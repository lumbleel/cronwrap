"""Tests for cronwrap config loader."""

import os
import tempfile
import pytest
from cronwrap.config import load_config, JobConfig


TOML_CONTENT = """
[jobs.backup]
command = "/usr/bin/backup.sh"
schedule = "0 2 * * *"
retries = 3
retry_delay = 10
timeout = 120
alert_on_failure = true
log_output = true

[jobs.cleanup]
command = "rm -rf /tmp/old_*"
schedule = "0 4 * * 0"
retries = 0
alert_on_success = true
"""

YAML_CONTENT = """
jobs:
  sync:
    command: "rsync -av /src /dst"
    schedule: "*/15 * * * *"
    retries: 2
    timeout: 60
    env:
      RSYNC_PASSWORD: secret
"""


@pytest.fixture
def toml_config_file():
    with tempfile.NamedTemporaryFile(suffix=".toml", mode="w", delete=False) as f:
        f.write(TOML_CONTENT)
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def yaml_config_file():
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        f.write(YAML_CONTENT)
        path = f.name
    yield path
    os.unlink(path)


def test_load_toml_config(toml_config_file):
    jobs = load_config(toml_config_file)
    assert len(jobs) == 2
    backup = next(j for j in jobs if j.name == "backup")
    assert backup.command == "/usr/bin/backup.sh"
    assert backup.retries == 3
    assert backup.timeout == 120
    assert backup.alert_on_failure is True


def test_load_yaml_config(yaml_config_file):
    jobs = load_config(yaml_config_file)
    assert len(jobs) == 1
    sync = jobs[0]
    assert sync.name == "sync"
    assert sync.retries == 2
    assert sync.env == {"RSYNC_PASSWORD": "secret"}


def test_defaults_applied(toml_config_file):
    jobs = load_config(toml_config_file)
    cleanup = next(j for j in jobs if j.name == "cleanup")
    assert cleanup.retry_delay == 5
    assert cleanup.timeout is None
    assert cleanup.log_output is True
    assert cleanup.alert_on_success is True


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/config.toml")


def test_unsupported_format():
    with tempfile.NamedTemporaryFile(suffix=".ini", delete=False) as f:
        path = f.name
    try:
        with pytest.raises(ValueError, match="Unsupported config format"):
            load_config(path)
    finally:
        os.unlink(path)


def test_invalid_retries():
    with pytest.raises(ValueError, match="retries must be >= 0"):
        JobConfig(name="bad", command="echo hi", schedule="* * * * *", retries=-1)


def test_invalid_timeout():
    with pytest.raises(ValueError, match="timeout must be a positive integer"):
        JobConfig(name="bad", command="echo hi", schedule="* * * * *", timeout=0)
