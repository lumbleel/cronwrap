"""Run a cron job command with retry logic and optional locking."""

import subprocess
import time
import logging
from dataclasses import dataclass, field
from cronwrap.config import JobConfig
from cronwrap.lock import acquire_lock, release_lock

logger = logging.getLogger(__name__)


@dataclass
class JobResult:
    job_name: str
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    attempts: int
    duration: float
    skipped: bool = False

    @property
    def success(self) -> bool:  # type: ignore[override]
        return self.__dict__["success"]

    @success.setter
    def success(self, value: bool) -> None:
        self.__dict__["success"] = value


def _run_once(command: str, timeout: int | None) -> tuple[int, str, str]:
    proc = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_job(config: JobConfig, lock_dir: str | None = None) -> JobResult:
    """Execute the job described by config, with retry and optional locking."""
    if lock_dir is not None and config.prevent_overlap:
        lock_result = acquire_lock(config.name, lock_dir)
        if not lock_result.acquired:
            logger.warning("Skipping '%s': already running (PID %s)", config.name, lock_result.existing_pid)
            return JobResult(
                job_name=config.name,
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                attempts=0,
                duration=0.0,
                skipped=True,
            )

    attempts = 0
    last_code, last_out, last_err = 1, "", ""
    start = time.monotonic()

    try:
        for attempt in range(1, config.retries + 2):
            attempts = attempt
            logger.info("Running '%s' (attempt %d)", config.name, attempt)
            try:
                code, out, err = _run_once(config.command, config.timeout)
            except subprocess.TimeoutExpired:
                logger.error("Job '%s' timed out on attempt %d", config.name, attempt)
                last_code, last_out, last_err = 124, "", "timeout"
                break

            last_code, last_out, last_err = code, out, err
            if code == 0:
                break
            if attempt <= config.retries:
                logger.warning("'%s' failed (code %d), retrying in %ds", config.name, code, config.retry_delay)
                time.sleep(config.retry_delay)
    finally:
        if lock_dir is not None and config.prevent_overlap:
            release_lock(config.name, lock_dir)

    duration = time.monotonic() - start
    return JobResult(
        job_name=config.name,
        success=last_code == 0,
        exit_code=last_code,
        stdout=last_out,
        stderr=last_err,
        attempts=attempts,
        duration=duration,
    )
