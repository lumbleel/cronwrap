import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logger(
    job_name: str,
    log_dir: Optional[str] = None,
    log_level: str = "INFO",
    log_to_stdout: bool = True,
) -> logging.Logger:
    """
    Set up a logger for a cron job.

    Args:
        job_name: Name of the cron job (used as logger name and in log filename).
        log_dir: Directory to write log files. If None, file logging is disabled.
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR).
        log_to_stdout: Whether to also log to stdout.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(job_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if log_to_stdout:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)

    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = log_path / f"{job_name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_job_start(logger: logging.Logger, job_name: str, command: str) -> None:
    """Log the start of a cron job execution."""
    logger.info(f"Starting job '{job_name}' | command: {command}")


def log_job_success(logger: logging.Logger, job_name: str, duration: float) -> None:
    """Log successful completion of a cron job."""
    logger.info(f"Job '{job_name}' completed successfully in {duration:.2f}s")


def log_job_failure(
    logger: logging.Logger,
    job_name: str,
    return_code: int,
    duration: float,
    attempt: int,
    max_attempts: int,
) -> None:
    """Log a failed cron job attempt."""
    logger.error(
        f"Job '{job_name}' failed (exit code {return_code}) "
        f"after {duration:.2f}s [attempt {attempt}/{max_attempts}]"
    )
