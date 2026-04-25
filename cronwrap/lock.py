"""Simple file-based locking to prevent concurrent job execution."""

import os
import time
import logging
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_LOCK_DIR = "/tmp/cronwrap"


@dataclass
class LockResult:
    acquired: bool
    lock_path: str
    existing_pid: int | None = None


def _lock_path(job_name: str, lock_dir: str = DEFAULT_LOCK_DIR) -> str:
    safe_name = job_name.replace("/", "_").replace(" ", "_")
    return os.path.join(lock_dir, f"{safe_name}.lock")


def acquire_lock(job_name: str, lock_dir: str = DEFAULT_LOCK_DIR) -> LockResult:
    """Try to acquire a lock for the given job. Returns LockResult."""
    Path(lock_dir).mkdir(parents=True, exist_ok=True)
    path = _lock_path(job_name, lock_dir)

    if os.path.exists(path):
        try:
            with open(path) as f:
                pid = int(f.read().strip())
            # Check if the process is still running
            os.kill(pid, 0)
            logger.warning("Lock held by PID %d for job '%s'", pid, job_name)
            return LockResult(acquired=False, lock_path=path, existing_pid=pid)
        except (ProcessLookupError, ValueError):
            logger.info("Stale lock found for '%s', removing", job_name)
            os.remove(path)

    with open(path, "w") as f:
        f.write(str(os.getpid()))

    logger.debug("Lock acquired for '%s' at %s", job_name, path)
    return LockResult(acquired=True, lock_path=path)


def release_lock(job_name: str, lock_dir: str = DEFAULT_LOCK_DIR) -> None:
    """Release the lock for the given job."""
    path = _lock_path(job_name, lock_dir)
    try:
        os.remove(path)
        logger.debug("Lock released for '%s'", job_name)
    except FileNotFoundError:
        logger.warning("Lock file not found when releasing '%s'", job_name)
