"""Tests for cronwrap.timeout."""

import time
import pytest

from cronwrap.timeout import (
    JobTimeoutError,
    TimeoutResult,
    enforce_timeout,
    check_timeout_supported,
)


# ---------------------------------------------------------------------------
# JobTimeoutError
# ---------------------------------------------------------------------------

def test_job_timeout_error_message():
    err = JobTimeoutError("backup", 60)
    assert "backup" in str(err)
    assert "60" in str(err)


def test_job_timeout_error_attributes():
    err = JobTimeoutError("sync", 10)
    assert err.job_name == "sync"
    assert err.timeout_seconds == 10


# ---------------------------------------------------------------------------
# TimeoutResult
# ---------------------------------------------------------------------------

def test_timeout_result_defaults():
    result = TimeoutResult(timed_out=False)
    assert result.timed_out is False
    assert result.elapsed_seconds is None
    assert result.message == ""


def test_timeout_result_fields():
    result = TimeoutResult(timed_out=True, elapsed_seconds=5.2, message="too slow")
    assert result.timed_out is True
    assert result.elapsed_seconds == pytest.approx(5.2)
    assert result.message == "too slow"


# ---------------------------------------------------------------------------
# enforce_timeout — no limit
# ---------------------------------------------------------------------------

def test_enforce_timeout_none_does_not_raise():
    with enforce_timeout("job", None):
        pass  # should complete without error


def test_enforce_timeout_zero_does_not_raise():
    with enforce_timeout("job", 0):
        pass


# ---------------------------------------------------------------------------
# enforce_timeout — with limit (Unix only)
# ---------------------------------------------------------------------------

pytestmark_unix = pytest.mark.skipif(
    not check_timeout_supported(),
    reason="SIGALRM not available on this platform",
)


@pytestmark_unix
def test_enforce_timeout_completes_within_limit():
    with enforce_timeout("fast-job", 5):
        time.sleep(0.01)


@pytestmark_unix
def test_enforce_timeout_raises_on_exceeded():
    with pytest.raises(JobTimeoutError) as exc_info:
        with enforce_timeout("slow-job", 1):
            time.sleep(3)
    assert exc_info.value.job_name == "slow-job"
    assert exc_info.value.timeout_seconds == 1


# ---------------------------------------------------------------------------
# check_timeout_supported
# ---------------------------------------------------------------------------

def test_check_timeout_supported_returns_bool():
    assert isinstance(check_timeout_supported(), bool)
