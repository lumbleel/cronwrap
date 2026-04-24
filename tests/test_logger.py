import logging
import os
from pathlib import Path

import pytest

from cronwrap.logger import (
    log_job_failure,
    log_job_start,
    log_job_success,
    setup_logger,
)


def test_setup_logger_returns_logger():
    logger = setup_logger("test_job", log_to_stdout=False)
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_job"


def test_setup_logger_default_level():
    logger = setup_logger("test_level_job", log_to_stdout=False)
    assert logger.level == logging.INFO


def test_setup_logger_custom_level():
    logger = setup_logger("test_debug_job", log_level="DEBUG", log_to_stdout=False)
    assert logger.level == logging.DEBUG


def test_setup_logger_stdout_handler():
    logger = setup_logger("test_stdout_job", log_to_stdout=True)
    handler_types = [type(h) for h in logger.handlers]
    assert logging.StreamHandler in handler_types


def test_setup_logger_no_stdout_handler():
    logger = setup_logger("test_no_stdout_job", log_to_stdout=False)
    assert len(logger.handlers) == 0


def test_setup_logger_file_handler(tmp_path):
    log_dir = str(tmp_path / "logs")
    logger = setup_logger("test_file_job", log_dir=log_dir, log_to_stdout=False)
    handler_types = [type(h) for h in logger.handlers]
    assert logging.FileHandler in handler_types
    assert (tmp_path / "logs" / "test_file_job.log").exists()


def test_setup_logger_creates_log_dir(tmp_path):
    log_dir = str(tmp_path / "nested" / "logs")
    setup_logger("test_nested_job", log_dir=log_dir, log_to_stdout=False)
    assert Path(log_dir).exists()


def test_setup_logger_clears_existing_handlers():
    logger = setup_logger("test_clear_job", log_to_stdout=True)
    # Call again — should not accumulate handlers
    logger = setup_logger("test_clear_job", log_to_stdout=True)
    stdout_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(stdout_handlers) == 1


def test_log_job_start(caplog):
    logger = setup_logger("start_job", log_to_stdout=False)
    with caplog.at_level(logging.INFO, logger="start_job"):
        log_job_start(logger, "start_job", "echo hello")
    assert "Starting job 'start_job'" in caplog.text
    assert "echo hello" in caplog.text


def test_log_job_success(caplog):
    logger = setup_logger("success_job", log_to_stdout=False)
    with caplog.at_level(logging.INFO, logger="success_job"):
        log_job_success(logger, "success_job", 1.23)
    assert "completed successfully" in caplog.text
    assert "1.23s" in caplog.text


def test_log_job_failure(caplog):
    logger = setup_logger("fail_job", log_to_stdout=False)
    with caplog.at_level(logging.ERROR, logger="fail_job"):
        log_job_failure(logger, "fail_job", return_code=1, duration=0.5, attempt=2, max_attempts=3)
    assert "failed" in caplog.text
    assert "exit code 1" in caplog.text
    assert "attempt 2/3" in caplog.text
