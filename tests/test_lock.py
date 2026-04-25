"""Tests for cronwrap.lock module."""

import os
import pytest
from unittest.mock import patch
from cronwrap.lock import acquire_lock, release_lock, LockResult, _lock_path


@pytest.fixture
def lock_dir(tmp_path):
    return str(tmp_path / "locks")


def test_lock_path_contains_job_name(lock_dir):
    path = _lock_path("my-job", lock_dir)
    assert "my-job" in path


def test_lock_path_sanitizes_slashes(lock_dir):
    path = _lock_path("jobs/my-job", lock_dir)
    assert "/" not in os.path.basename(path)


def test_acquire_lock_returns_lock_result(lock_dir):
    result = acquire_lock("test-job", lock_dir)
    assert isinstance(result, LockResult)
    release_lock("test-job", lock_dir)


def test_acquire_lock_creates_file(lock_dir):
    result = acquire_lock("test-job", lock_dir)
    assert result.acquired is True
    assert os.path.exists(result.lock_path)
    release_lock("test-job", lock_dir)


def test_acquire_lock_writes_pid(lock_dir):
    result = acquire_lock("test-job", lock_dir)
    with open(result.lock_path) as f:
        pid = int(f.read().strip())
    assert pid == os.getpid()
    release_lock("test-job", lock_dir)


def test_acquire_lock_fails_if_already_held(lock_dir):
    first = acquire_lock("test-job", lock_dir)
    assert first.acquired is True

    # Simulate another process holding the lock by writing a valid PID
    with open(first.lock_path, "w") as f:
        f.write(str(os.getpid()))  # current PID is definitely alive

    second = acquire_lock("test-job", lock_dir)
    assert second.acquired is False
    assert second.existing_pid == os.getpid()
    release_lock("test-job", lock_dir)


def test_acquire_lock_removes_stale_lock(lock_dir, tmp_path):
    path = _lock_path("stale-job", lock_dir)
    os.makedirs(lock_dir, exist_ok=True)
    with open(path, "w") as f:
        f.write("99999999")  # very unlikely to be a real PID

    result = acquire_lock("stale-job", lock_dir)
    assert result.acquired is True
    release_lock("stale-job", lock_dir)


def test_release_lock_removes_file(lock_dir):
    result = acquire_lock("test-job", lock_dir)
    assert os.path.exists(result.lock_path)
    release_lock("test-job", lock_dir)
    assert not os.path.exists(result.lock_path)


def test_release_lock_missing_file_no_error(lock_dir):
    # Should not raise even if lock doesn't exist
    release_lock("nonexistent-job", lock_dir)
