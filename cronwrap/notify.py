"""Notification dispatch layer for cronwrap.

Routes alert messages to one or more channels (email, webhook, stdout)
based on the job's alert configuration.
"""

from __future__ import annotations

import json
import logging
import smtplib
import urllib.request
from email.message import EmailMessage
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cronwrap.alerting import AlertConfig
    from cronwrap.runner import JobResult

logger = logging.getLogger(__name__)


def _send_email(alert: "AlertConfig", subject: str, body: str) -> None:
    """Send notification via SMTP."""
    if not alert.smtp_host or not alert.to_email:
        logger.debug("Email notification skipped: smtp_host or to_email not set")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = alert.from_email or "cronwrap@localhost"
    msg["To"] = alert.to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(alert.smtp_host, alert.smtp_port or 25) as smtp:
            smtp.send_message(msg)
        logger.info("Email notification sent to %s", alert.to_email)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to send email notification: %s", exc)


def _send_webhook(alert: "AlertConfig", subject: str, body: str) -> None:
    """POST a JSON payload to the configured webhook URL."""
    if not alert.webhook_url:
        logger.debug("Webhook notification skipped: webhook_url not set")
        return

    payload = json.dumps({"subject": subject, "body": body}).encode()
    req = urllib.request.Request(
        alert.webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info("Webhook notification sent, status=%s", resp.status)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to send webhook notification: %s", exc)


def dispatch(alert: "AlertConfig", result: "JobResult") -> None:
    """Build and dispatch notifications for *result* according to *alert* config."""
    from cronwrap.alerting import _build_message, send_alert

    should_notify = send_alert(alert, result)
    if not should_notify:
        logger.debug("No notification dispatched for job '%s'", result.job_name)
        return

    subject, body = _build_message(alert, result)
    _send_email(alert, subject, body)
    _send_webhook(alert, subject, body)
