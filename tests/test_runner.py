"""Tests for cronwrap.runner module."""

import pytest
from unittest.mock import patch
from cronwrap.config import JobConfig
from cronwrap.runner import run_job, JobResult


@pytest.fixture
def basic_job():
    return JobConfig(
        name="basic",
        command="echo hello",
        schedule="* * * * *",
        retries=0,
        retry_delay=0,
        timeout=30,
        prevent_overlap=False,
    )


@pytest.fixture
def retrying_job():
    return JobConfig(
        name="retrying",
        command="exit 1",
        schedule="* * * * *",
        retries=2,
        retry_delay=0,
        timeout=30,
        prevent_overlap=False,
    )


def test_run_job_success(basic_job):
    result = run_job(basic_job)
    assert result.success is True
    assert result.exit_code == 0


def test_run_job_stdout_captured(basic_job):
    result = run_job(basic_job)
    assert "hello" in result.stdout


def test_run_job_failure_no_retry(basic_job):
    basic_job.command = "exit 1"
    result = run_job(basic_job)
    assert result.success is False
    assert result.attempts == 1


def test_run_job_retries_on_failure(retrying_job):
    result = run_job(retrying_job)
    assert result.attempts == 3  # 1 initial + 2 retries
    assert result.success is False


def test_run_job_duration_positive(basic_job):
    result = run_job(basic_job)
    assert result.duration >= 0.0


def test_run_job_skipped_when_lock_held(basic_job, tmp_path):
    basic_job.prevent_overlap = True
    lock_dir = str(tmp_path / "locks")

    # Acquire the lock manually so the job sees it as held
    import os
    from cronwrap.lock import acquire_lock, _lock_path
    from pathlib import Path
    Path(lock_dir).mkdir(parents=True, exist_ok=True)
    lock_path = _lock_path(basic_job.name, lock_dir)
    with open(lock_path, "w") as f:
        f.write(str(os.getpid()))  # current PID = alive

    result = run_job(basic_job, lock_dir=lock_dir)
    assert result.skipped is True
    assert result.attempts == 0


def test_run_job_no_skip_when_no_lock_dir(basic_job):
    basic_job.prevent_overlap = True
    result = run_job(basic_job, lock_dir=None)
    assert result.skipped is False
    assert result.success is True


def test_run_job_timeout_returns_failure(basic_job):
    basic_job.command = "sleep 10"
    basic_job.timeout = 1
    result = run_job(basic_job)
    assert result.success is False
    assert "timeout" in result.stderr
