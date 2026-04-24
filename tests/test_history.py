"""Tests for cronwrap.history module."""

import datetime
import pytest
from pathlib import Path

from cronwrap.history import (
    init_db,
    record_run,
    get_recent_runs,
    HistoryEntry,
)


@pytest.fixture
def tmp_db(tmp_path):
    return tmp_path / "test_history.db"


def _record(job_name="test_job", exit_code=0, retries=0, db_path=None, **kwargs):
    now = datetime.datetime.utcnow()
    record_run(
        job_name=job_name,
        started_at=kwargs.get("started_at", now),
        finished_at=kwargs.get("finished_at", now),
        exit_code=exit_code,
        retries=retries,
        stdout=kwargs.get("stdout", "some output"),
        stderr=kwargs.get("stderr", ""),
        db_path=db_path,
    )


def test_init_db_creates_file(tmp_db):
    init_db(tmp_db)
    assert tmp_db.exists()


def test_record_run_inserts_entry(tmp_db):
    _record(db_path=tmp_db)
    entries = get_recent_runs("test_job", db_path=tmp_db)
    assert len(entries) == 1


def test_history_entry_fields(tmp_db):
    _record(job_name="myjob", exit_code=0, retries=2, stdout="hello", db_path=tmp_db)
    entry = get_recent_runs("myjob", db_path=tmp_db)[0]
    assert isinstance(entry, HistoryEntry)
    assert entry.job_name == "myjob"
    assert entry.exit_code == 0
    assert entry.retries == 2
    assert entry.stdout == "hello"
    assert entry.success is True


def test_failed_run_success_false(tmp_db):
    _record(exit_code=1, db_path=tmp_db)
    entry = get_recent_runs("test_job", db_path=tmp_db)[0]
    assert entry.success is False


def test_get_recent_runs_limit(tmp_db):
    for _ in range(5):
        _record(db_path=tmp_db)
    entries = get_recent_runs("test_job", limit=3, db_path=tmp_db)
    assert len(entries) == 3


def test_get_recent_runs_filters_by_job(tmp_db):
    _record(job_name="job_a", db_path=tmp_db)
    _record(job_name="job_b", db_path=tmp_db)
    entries = get_recent_runs("job_a", db_path=tmp_db)
    assert len(entries) == 1
    assert entries[0].job_name == "job_a"


def test_get_recent_runs_empty(tmp_db):
    entries = get_recent_runs("nonexistent_job", db_path=tmp_db)
    assert entries == []


def test_multiple_runs_ordered_desc(tmp_db):
    base = datetime.datetime(2024, 1, 1, 12, 0, 0)
    for i in range(3):
        record_run(
            job_name="ordered_job",
            started_at=base + datetime.timedelta(minutes=i),
            finished_at=base + datetime.timedelta(minutes=i, seconds=5),
            exit_code=0,
            retries=0,
            stdout=f"run {i}",
            stderr="",
            db_path=tmp_db,
        )
    entries = get_recent_runs("ordered_job", db_path=tmp_db)
    assert entries[0].stdout == "run 2"
    assert entries[-1].stdout == "run 0"
