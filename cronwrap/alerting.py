"""Alerting module for cronwrap — sends notifications on job failure or success."""

from __future__ import annotations

import smtplib
import logging
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Optional

from cronwrap.runner import JobResult

logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_addr: str = "cronwrap@localhost"
    to_addrs: list[str] = field(default_factory=list)
    alert_on_failure: bool = True
    alert_on_success: bool = False


def _build_message(job_name: str, result: JobResult, from_addr: str, to_addrs: list[str]) -> EmailMessage:
    msg = EmailMessage()
    status = "SUCCESS" if result.success else "FAILURE"
    msg["Subject"] = f"[cronwrap] Job '{job_name}' {status}"
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)

    body_lines = [
        f"Job: {job_name}",
        f"Status: {status}",
        f"Return code: {result.returncode}",
        f"Duration: {result.duration:.2f}s",
    ]
    if result.stdout:
        body_lines += ["", "--- stdout ---", result.stdout]
    if result.stderr:
        body_lines += ["", "--- stderr ---", result.stderr]

    msg.set_content("\n".join(body_lines))
    return msg


def send_alert(job_name: str, result: JobResult, alert_cfg: AlertConfig) -> bool:
    """Send an email alert for the given job result. Returns True if sent."""
    should_alert = (not result.success and alert_cfg.alert_on_failure) or (
        result.success and alert_cfg.alert_on_success
    )
    if not should_alert or not alert_cfg.to_addrs:
        return False

    msg = _build_message(job_name, result, alert_cfg.from_addr, alert_cfg.to_addrs)

    try:
        with smtplib.SMTP(alert_cfg.smtp_host, alert_cfg.smtp_port) as smtp:
            if alert_cfg.smtp_user and alert_cfg.smtp_password:
                smtp.login(alert_cfg.smtp_user, alert_cfg.smtp_password)
            smtp.send_message(msg)
        logger.info("Alert sent for job '%s' to %s", job_name, alert_cfg.to_addrs)
        return True
    except smtplib.SMTPException as exc:
        logger.error("Failed to send alert for job '%s': %s", job_name, exc)
        return False
