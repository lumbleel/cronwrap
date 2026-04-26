"""Timeout enforcement for cron job execution."""

import signal
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional


class JobTimeoutError(Exception):
    """Raised when a job exceeds its allowed runtime."""

    def __init__(self, job_name: str, timeout_seconds: int) -> None:
        self.job_name = job_name
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Job '{job_name}' timed out after {timeout_seconds}s"
        )


@dataclass
class TimeoutResult:
    timed_out: bool
    elapsed_seconds: Optional[float] = None
    message: str = ""


def _timeout_handler(signum, frame):
    raise TimeoutError()


@contextmanager
def enforce_timeout(job_name: str, timeout_seconds: Optional[int]):
    """Context manager that raises JobTimeoutError if the block exceeds timeout.

    If timeout_seconds is None or 0 no limit is applied.

    Usage::

        with enforce_timeout("my-job", 30):
            subprocess.run(...)
    """
    if not timeout_seconds:
        yield
        return

    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(timeout_seconds)
    try:
        yield
    except TimeoutError:
        raise JobTimeoutError(job_name, timeout_seconds)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def check_timeout_supported() -> bool:
    """Return True if SIGALRM is available (Unix only)."""
    return hasattr(signal, "SIGALRM")
