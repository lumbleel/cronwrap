"""Tests for cronwrap.alerting module."""

from unittest.mock import MagicMock, patch

import pytest

from cronwrap.alerting import AlertConfig, _build_message, send_alert
from cronwrap.runner import JobResult


@pytest.fixture
def success_result():
    return JobResult(success=True, returncode=0, stdout="all good", stderr="", duration=1.23)


@pytest.fixture
def failure_result():
    return JobResult(success=False, returncode=1, stdout="", stderr="something broke", duration=0.5)


@pytest.fixture
def alert_cfg():
    return AlertConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="user",
        smtp_password="pass",
        from_addr="cron@example.com",
        to_addrs=["ops@example.com"],
        alert_on_failure=True,
        alert_on_success=False,
    )


def test_build_message_failure_subject(failure_result, alert_cfg):
    msg = _build_message("backup", failure_result, alert_cfg.from_addr, alert_cfg.to_addrs)
    assert "FAILURE" in msg["Subject"]
    assert "backup" in msg["Subject"]


def test_build_message_success_subject(success_result, alert_cfg):
    msg = _build_message("backup", success_result, alert_cfg.from_addr, alert_cfg.to_addrs)
    assert "SUCCESS" in msg["Subject"]


def test_build_message_contains_stderr(failure_result, alert_cfg):
    msg = _build_message("backup", failure_result, alert_cfg.from_addr, alert_cfg.to_addrs)
    assert "something broke" in msg.get_content()


def test_build_message_contains_stdout(success_result, alert_cfg):
    msg = _build_message("backup", success_result, alert_cfg.from_addr, alert_cfg.to_addrs)
    assert "all good" in msg.get_content()


def test_send_alert_no_recipients_returns_false(failure_result):
    cfg = AlertConfig(to_addrs=[])
    assert send_alert("job", failure_result, cfg) is False


def test_send_alert_success_when_not_configured(success_result, alert_cfg):
    """alert_on_success is False by default — should not send."""
    assert send_alert("job", success_result, alert_cfg) is False


def test_send_alert_failure_sends_email(failure_result, alert_cfg):
    with patch("cronwrap.alerting.smtplib.SMTP") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp
        result = send_alert("backup", failure_result, alert_cfg)
    assert result is True
    mock_smtp.send_message.assert_called_once()


def test_send_alert_smtp_error_returns_false(failure_result, alert_cfg):
    import smtplib
    with patch("cronwrap.alerting.smtplib.SMTP", side_effect=smtplib.SMTPException("conn refused")):
        result = send_alert("backup", failure_result, alert_cfg)
    assert result is False


def test_send_alert_success_when_enabled(success_result, alert_cfg):
    alert_cfg.alert_on_success = True
    with patch("cronwrap.alerting.smtplib.SMTP") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp
        result = send_alert("backup", success_result, alert_cfg)
    assert result is True
