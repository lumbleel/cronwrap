"""Tests for cronwrap.notify dispatch layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock, patch

import pytest

from cronwrap.notify import _send_email, _send_webhook, dispatch


@dataclass
class _FakeAlert:
    to_email: str = ""
    from_email: str = "cronwrap@localhost"
    smtp_host: str = ""
    smtp_port: int = 25
    webhook_url: str = ""
    on_failure: bool = True
    on_success: bool = False


@dataclass
class _FakeResult:
    job_name: str = "test-job"
    success: bool = False
    stdout: str = "some output"
    stderr: str = ""
    returncode: int = 1
    duration: float = 1.5
    attempts: int = 1


@pytest.fixture()
def alert():
    return _FakeAlert(to_email="ops@example.com", smtp_host="localhost")


@pytest.fixture()
def result():
    return _FakeResult()


# --- _send_email ---

def test_send_email_skipped_when_no_smtp_host(alert, result):
    alert.smtp_host = ""
    with patch("smtplib.SMTP") as mock_smtp:
        _send_email(alert, "Subject", "Body")
    mock_smtp.assert_not_called()


def test_send_email_skipped_when_no_to_email(alert, result):
    alert.to_email = ""
    with patch("smtplib.SMTP") as mock_smtp:
        _send_email(alert, "Subject", "Body")
    mock_smtp.assert_not_called()


def test_send_email_calls_smtp(alert):
    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = MagicMock(return_value=False)
    with patch("smtplib.SMTP", return_value=mock_smtp_instance):
        _send_email(alert, "Test subject", "Test body")
    mock_smtp_instance.send_message.assert_called_once()


# --- _send_webhook ---

def test_send_webhook_skipped_when_no_url(alert):
    alert.webhook_url = ""
    with patch("urllib.request.urlopen") as mock_open:
        _send_webhook(alert, "Subject", "Body")
    mock_open.assert_not_called()


def test_send_webhook_posts_json(alert):
    alert.webhook_url = "http://hooks.example.com/notify"
    mock_resp = MagicMock()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200
    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        _send_webhook(alert, "Subject", "Body")
    mock_open.assert_called_once()
    req_arg = mock_open.call_args[0][0]
    assert req_arg.get_header("Content-type") == "application/json"


# --- dispatch ---

def test_dispatch_skips_when_send_alert_false(alert, result):
    result.success = True  # on_success=False => no notification
    with patch("cronwrap.notify._send_email") as mock_email, \
         patch("cronwrap.notify._send_webhook") as mock_hook:
        dispatch(alert, result)
    mock_email.assert_not_called()
    mock_hook.assert_not_called()


def test_dispatch_calls_channels_on_failure(alert, result):
    with patch("cronwrap.notify._send_email") as mock_email, \
         patch("cronwrap.notify._send_webhook") as mock_hook:
        dispatch(alert, result)
    mock_email.assert_called_once()
    mock_hook.assert_called_once()
