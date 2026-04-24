"""Job execution history tracking using a simple SQLite backend."""

import sqlite3
import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List


DEFAULT_DB_PATH = Path.home() / ".cronwrap" / "history.db"


@dataclass
class HistoryEntry:
    job_name: str
    started_at: str
    finished_at: str
    exit_code: int
    retries: int
    stdout: str
    stderr: str
    success: bool


def _get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Create the history table if it doesn't exist."""
    with _get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS job_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                exit_code INTEGER NOT NULL,
                retries INTEGER NOT NULL DEFAULT 0,
                stdout TEXT,
                stderr TEXT,
                success INTEGER NOT NULL
            )
            """
        )


def record_run(
    job_name: str,
    started_at: datetime.datetime,
    finished_at: datetime.datetime,
    exit_code: int,
    retries: int,
    stdout: str,
    stderr: str,
    db_path: Path = DEFAULT_DB_PATH,
) -> None:
    """Insert a job run record into the history database."""
    init_db(db_path)
    success = 1 if exit_code == 0 else 0
    with _get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO job_history
                (job_name, started_at, finished_at, exit_code, retries, stdout, stderr, success)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_name,
                started_at.isoformat(),
                finished_at.isoformat(),
                exit_code,
                retries,
                stdout,
                stderr,
                success,
            ),
        )


def get_recent_runs(
    job_name: str, limit: int = 10, db_path: Path = DEFAULT_DB_PATH
) -> List[HistoryEntry]:
    """Fetch the most recent runs for a given job."""
    init_db(db_path)
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT job_name, started_at, finished_at, exit_code, retries, stdout, stderr, success
            FROM job_history
            WHERE job_name = ?
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (job_name, limit),
        ).fetchall()
    return [
        HistoryEntry(
            job_name=r["job_name"],
            started_at=r["started_at"],
            finished_at=r["finished_at"],
            exit_code=r["exit_code"],
            retries=r["retries"],
            stdout=r["stdout"] or "",
            stderr=r["stderr"] or "",
            success=bool(r["success"]),
        )
        for r in rows
    ]
