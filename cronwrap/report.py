"""Generate a simple text report of recent job history."""

from pathlib import Path
from typing import Optional

from cronwrap.history import get_recent_runs, DEFAULT_DB_PATH, HistoryEntry


_STATUS_OK = "\u2713"
_STATUS_FAIL = "\u2717"


def _format_entry(entry: HistoryEntry) -> str:
    status = _STATUS_OK if entry.success else _STATUS_FAIL
    return (
        f"  [{status}] started={entry.started_at}  exit={entry.exit_code}"
        f"  retries={entry.retries}"
    )


def generate_report(
    job_name: str,
    limit: int = 10,
    db_path: Path = DEFAULT_DB_PATH,
    include_output: bool = False,
) -> str:
    """Return a human-readable report string for a job's recent runs."""
    entries = get_recent_runs(job_name, limit=limit, db_path=db_path)

    if not entries:
        return f"No history found for job '{job_name}'."

    total = len(entries)
    successes = sum(1 for e in entries if e.success)
    failures = total - successes

    lines = [
        f"Job: {job_name}",
        f"Last {total} run(s): {successes} succeeded, {failures} failed",
        "-" * 50,
    ]

    for entry in entries:
        lines.append(_format_entry(entry))
        if include_output and entry.stdout:
            for out_line in entry.stdout.strip().splitlines():
                lines.append(f"      stdout: {out_line}")
        if include_output and entry.stderr:
            for err_line in entry.stderr.strip().splitlines():
                lines.append(f"      stderr: {err_line}")

    return "\n".join(lines)


def print_report(
    job_name: str,
    limit: int = 10,
    db_path: Path = DEFAULT_DB_PATH,
    include_output: bool = False,
) -> None:
    """Print the report for a job to stdout."""
    print(generate_report(job_name, limit=limit, db_path=db_path, include_output=include_output))
