import subprocess
import time
from dataclasses import dataclass
from typing import Optional

from cronwrap.config import JobConfig
from cronwrap.logger import setup_logger, log_job_start, log_job_success, log_job_failure


@dataclass
class JobResult:
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    attempts: int

    @property
    def success(self) -> bool:
        return self.exit_code == 0


def run_job(job: JobConfig, logger=None) -> JobResult:
    """Run a cron job with retry logic and logging."""
    if logger is None:
        logger = setup_logger(job.name)

    log_job_start(logger, job.name, job.command)

    attempt = 0
    last_result: Optional[JobResult] = None

    while attempt <= job.retries:
        attempt += 1
        start_time = time.monotonic()

        try:
            proc = subprocess.run(
                job.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=job.timeout,
            )
            duration = time.monotonic() - start_time
            last_result = JobResult(
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration=duration,
                attempts=attempt,
            )
        except subprocess.TimeoutExpired:
            duration = time.monotonic() - start_time
            last_result = JobResult(
                exit_code=-1,
                stdout="",
                stderr=f"Job timed out after {job.timeout}s",
                duration=duration,
                attempts=attempt,
            )

        if last_result.success:
            log_job_success(logger, job.name, last_result.duration, attempt)
            return last_result

        if attempt <= job.retries:
            logger.warning(
                f"Job '{job.name}' failed on attempt {attempt}/{job.retries + 1}, "
                f"retrying in {job.retry_delay}s..."
            )
            time.sleep(job.retry_delay)

    log_job_failure(
        logger,
        job.name,
        last_result.exit_code,
        last_result.stderr,
        last_result.attempts,
    )
    return last_result
