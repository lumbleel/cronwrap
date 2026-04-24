"""Config loading for cronwrap."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from cronwrap.alerting import AlertConfig


@dataclass
class JobConfig:
    name: str
    command: str
    retries: int = 0
    retry_delay: float = 5.0
    timeout: Optional[float] = None
    log_file: Optional[str] = None
    log_level: str = "INFO"
    alert: AlertConfig = field(default_factory=AlertConfig)

    def __post_init__(self) -> None:
        if self.retries < 0:
            raise ValueError("retries must be >= 0")
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be >= 0")


def _parse_alert(raw: dict[str, Any]) -> AlertConfig:
    alert_raw = raw.get("alert", {})
    return AlertConfig(
        smtp_host=alert_raw.get("smtp_host", "localhost"),
        smtp_port=int(alert_raw.get("smtp_port", 25)),
        smtp_user=alert_raw.get("smtp_user"),
        smtp_password=alert_raw.get("smtp_password"),
        from_addr=alert_raw.get("from_addr", "cronwrap@localhost"),
        to_addrs=alert_raw.get("to_addrs", []),
        alert_on_failure=alert_raw.get("alert_on_failure", True),
        alert_on_success=alert_raw.get("alert_on_success", False),
    )


def _parse_job(name: str, raw: dict[str, Any]) -> JobConfig:
    return JobConfig(
        name=name,
        command=raw["command"],
        retries=int(raw.get("retries", 0)),
        retry_delay=float(raw.get("retry_delay", 5.0)),
        timeout=raw.get("timeout"),
        log_file=raw.get("log_file"),
        log_level=raw.get("log_level", "INFO").upper(),
        alert=_parse_alert(raw),
    )


def load_config(path: str | Path) -> dict[str, JobConfig]:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".toml":
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
    elif suffix in (".yaml", ".yml"):
        import yaml
        with open(path) as fh:
            data = yaml.safe_load(fh)
    else:
        raise ValueError(f"Unsupported config format: {suffix}")

    jobs_raw: dict[str, Any] = data.get("jobs", {})
    return {name: _parse_job(name, raw) for name, raw in jobs_raw.items()}
