import pytest
from unittest.mock import patch, MagicMock

from cronwrap.config import JobConfig
from cronwrap.runner import run_job, JobResult


@pytest.fixture
def basic_job():
    return JobConfig(
        name="test-job",
        command="echo hello",
        schedule="* * * * *",
        retries=0,
        retry_delay=0,
        timeout=30,
    )


@pytest.fixture
def retrying_job():
    return JobConfig(
        name="retry-job",
        command="exit 1",
        schedule="* * * * *",
        retries=2,
        retry_delay=0,
        timeout=30,
    )


def test_run_job_success(basic_job):
    result = run_job(basic_job)
    assert result.success is True
    assert result.exit_code == 0
    assert result.attempts == 1


def test_run_job_stdout_captured(basic_job):
    result = run_job(basic_job)
    assert "hello" in result.stdout


def test_run_job_failure_no_retry():
    job = JobConfig(
        name="fail-job",
        command="exit 42",
        schedule="* * * * *",
        retries=0,
        retry_delay=0,
        timeout=30,
    )
    result = run_job(job)
    assert result.success is False
    assert result.exit_code == 42
    assert result.attempts == 1


def test_run_job_retries_exhausted(retrying_job):
    result = run_job(retrying_job)
    assert result.success is False
    assert result.attempts == 3  # 1 initial + 2 retries


def test_run_job_succeeds_on_retry():
    call_count = 0
    original_run = __import__("subprocess").run

    def mock_run(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        result.returncode = 0 if call_count >= 2 else 1
        result.stdout = ""
        result.stderr = ""
        return result

    job = JobConfig(
        name="flaky-job",
        command="flaky",
        schedule="* * * * *",
        retries=2,
        retry_delay=0,
        timeout=30,
    )

    with patch("subprocess.run", side_effect=mock_run):
        result = run_job(job)

    assert result.success is True
    assert result.attempts == 2


def test_run_job_timeout():
    job = JobConfig(
        name="slow-job",
        command="sleep 10",
        schedule="* * * * *",
        retries=0,
        retry_delay=0,
        timeout=0.01,
    )
    result = run_job(job)
    assert result.success is False
    assert result.exit_code == -1
    assert "timed out" in result.stderr


def test_job_result_duration(basic_job):
    result = run_job(basic_job)
    assert result.duration >= 0
