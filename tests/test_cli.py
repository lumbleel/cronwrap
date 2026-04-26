"""Tests for the CLI entry point."""

import pytest
from unittest.mock import patch, MagicMock
from argparse import ArgumentParser

from cronwrap.cli import build_parser, main
from cronwrap.config import JobConfig
from cronwrap.runner import JobResult


@pytest.fixture
def sample_job_config():
    return JobConfig(
        name="test-job",
        command="echo hello",
        schedule="* * * * *",
        retries=0,
        retry_delay=5,
        timeout=60,
        notify_on_failure=False,
        notify_on_success=False,
        notify_email=None,
        log_file=None,
        log_level="INFO",
    )


def test_build_parser_returns_argument_parser():
    parser = build_parser()
    assert isinstance(parser, ArgumentParser)


def test_build_parser_has_config_argument():
    parser = build_parser()
    args = parser.parse_args(["--config", "cronwrap.toml", "--job", "myjob"])
    assert args.config == "cronwrap.toml"


def test_build_parser_has_job_argument():
    parser = build_parser()
    args = parser.parse_args(["--config", "cronwrap.toml", "--job", "myjob"])
    assert args.job == "myjob"


def test_build_parser_default_config():
    """Config should have a sensible default."""
    parser = build_parser()
    args = parser.parse_args(["--job", "myjob"])
    assert args.config is not None


def test_build_parser_verbose_flag():
    parser = build_parser()
    args = parser.parse_args(["--job", "myjob", "--verbose"])
    assert args.verbose is True


def test_build_parser_verbose_defaults_false():
    parser = build_parser()
    args = parser.parse_args(["--job", "myjob"])
    assert args.verbose is False


def test_main_exits_zero_on_success(sample_job_config):
    """main() should exit with code 0 when the job succeeds."""
    success_result = JobResult(
        success=True,
        returncode=0,
        stdout="done",
        stderr="",
        attempts=1,
        duration=0.1,
    )
    with patch("cronwrap.cli.load_config", return_value={"test-job": sample_job_config}), \
         patch("cronwrap.cli.run_job", return_value=success_result), \
         patch("cronwrap.cli.setup_logger", return_value=MagicMock()), \
         patch("sys.argv", ["cronwrap", "--job", "test-job"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_main_exits_nonzero_on_failure(sample_job_config):
    """main() should exit with a non-zero code when the job fails."""
    failure_result = JobResult(
        success=False,
        returncode=1,
        stdout="",
        stderr="something broke",
        attempts=1,
        duration=0.05,
    )
    with patch("cronwrap.cli.load_config", return_value={"test-job": sample_job_config}), \
         patch("cronwrap.cli.run_job", return_value=failure_result), \
         patch("cronwrap.cli.setup_logger", return_value=MagicMock()), \
         patch("sys.argv", ["cronwrap", "--job", "test-job"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0


def test_main_exits_nonzero_on_unknown_job(sample_job_config):
    """main() should exit with a non-zero code when the requested job is not found in config."""
    with patch("cronwrap.cli.load_config", return_value={"test-job": sample_job_config}), \
         patch("cronwrap.cli.setup_logger", return_value=MagicMock()), \
         patch("sys.argv", ["cronwrap", "--job", "nonexistent-job"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0
