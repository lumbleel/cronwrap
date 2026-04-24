"""Tests for cronwrap.report module."""

import datetime
import pytest

from cronwrap.history import record_run
from cronwrap.report import generate_report


@pytest.fixture
def tmp_db(tmp_path):
    return tmp_path / "report_test.db"


def _add_run(job_name, exit_code, stdout="", stderr="", db_path=None):
    now = datetime.datetime.utcnow()
    record_run(
        job_name=job_name,
        started_at=now,
        finished_at=now,
        exit_code=exit_code,
        retries=0,
        stdout=stdout,
        stderr=stderr,
        db_path=db_path,
    )


def test_report_no_history(tmp_db):
    report = generate_report("ghost_job", db_path=tmp_db)
    assert "No history found" in report
    assert "ghost_job" in report


def test_report_contains_job_name(tmp_db):
    _add_run("my_job", 0, db_path=tmp_db)
    report = generate_report("my_job", db_path=tmp_db)
    assert "my_job" in report


def test_report_success_count(tmp_db):
    _add_run("count_job", 0, db_path=tmp_db)
    _add_run("count_job", 0, db_path=tmp_db)
    _add_run("count_job", 1, db_path=tmp_db)
    report = generate_report("count_job", db_path=tmp_db)
    assert "2 succeeded" in report
    assert "1 failed" in report


def test_report_shows_checkmark_for_success(tmp_db):
    _add_run("ok_job", 0, db_path=tmp_db)
    report = generate_report("ok_job", db_path=tmp_db)
    assert "\u2713" in report


def test_report_shows_cross_for_failure(tmp_db):
    _add_run("fail_job", 2, db_path=tmp_db)
    report = generate_report("fail_job", db_path=tmp_db)
    assert "\u2717" in report


def test_report_limit_respected(tmp_db):
    for _ in range(8):
        _add_run("limited_job", 0, db_path=tmp_db)
    report = generate_report("limited_job", limit=3, db_path=tmp_db)
    assert "Last 3 run(s)" in report


def test_report_include_output(tmp_db):
    _add_run("verbose_job", 0, stdout="hello world", db_path=tmp_db)
    report = generate_report("verbose_job", db_path=tmp_db, include_output=True)
    assert "hello world" in report


def test_report_no_output_by_default(tmp_db):
    _add_run("quiet_job", 0, stdout="secret output", db_path=tmp_db)
    report = generate_report("quiet_job", db_path=tmp_db, include_output=False)
    assert "secret output" not in report
