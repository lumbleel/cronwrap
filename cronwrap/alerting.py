"""Alert configuration and message building for cronwrap."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cronwrap.runner import JobResult


@dataclass
class AlertConfig:
    on_failure: bool = True
    on_success: bool = False
    to_email: str = ""
    from_email: str = "cronwrap@localhost"
    smtp_host: str = ""
    smtp_port: int = 25
    webhook_url: str = ""
    extra: dict = field(default_factory=dict)


def _build_message(alert: AlertConfig, result: "JobResult") -> tuple[str, str]:
    """Return (subject, body) for the given job result."""
    status = "SUCCESS" if result.success else "FAILURE"
    subject = f"[cronwrap] {status}: {result.job_name}"

    lines = [
        f"Job      : {result.job_name}",
        f"Status   : {status}",
        f"Exit code: {result.returncode}",
        f"Duration : {result.duration:.2f}s",
        f"Attempts : {result.attempts}",
    ]
    if result.stdout:
        lines += ["", "--- stdout ---", result.stdout.strip()]
    if result.stderr:
        lines += ["", "--- stderr ---", result.stderr.strip()]

    return subject, "\n".join(lines)


def send_alert(alert: AlertConfig, result: "JobResult") -> bool:
    """Return True if a notification should be dispatched, False otherwise.

    Also handles legacy direct email sending for backwards compatibility;
    actual channel dispatch is handled by cronwrap.notify.dispatch.
    """
    if result.success and not alert.on_success:
        return False
    if not result.success and not alert.on_failure:
        return False
    return True
