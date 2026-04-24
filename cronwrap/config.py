"""Config loader for cronwrap — parses YAML/TOML job definitions."""

import os
from dataclasses import dataclass, field
from typing import Optional

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class JobConfig:
    name: str
    command: str
    schedule: str
    retries: int = 0
    retry_delay: int = 5  # seconds
    timeout: Optional[int] = None  # seconds
    alert_on_failure: bool = True
    alert_on_success: bool = False
    log_output: bool = True
    env: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.retries < 0:
            raise ValueError(f"Job '{self.name}': retries must be >= 0")
        if self.timeout is not None and self.timeout <= 0:
            raise ValueError(f"Job '{self.name}': timeout must be a positive integer")


def _parse_job(name: str, data: dict) -> JobConfig:
    return JobConfig(
        name=name,
        command=data["command"],
        schedule=data.get("schedule", ""),
        retries=data.get("retries", 0),
        retry_delay=data.get("retry_delay", 5),
        timeout=data.get("timeout", None),
        alert_on_failure=data.get("alert_on_failure", True),
        alert_on_success=data.get("alert_on_success", False),
        log_output=data.get("log_output", True),
        env=data.get("env", {}),
    )


def load_config(path: str) -> list[JobConfig]:
    """Load job configs from a TOML or YAML file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    ext = os.path.splitext(path)[1].lower()

    if ext == ".toml":
        if tomllib is None:
            raise ImportError("tomllib/tomli is required to parse TOML configs")
        with open(path, "rb") as f:
            raw = tomllib.load(f)
    elif ext in (".yaml", ".yml"):
        if yaml is None:
            raise ImportError("pyyaml is required to parse YAML configs")
        with open(path, "r") as f:
            raw = yaml.safe_load(f)
    else:
        raise ValueError(f"Unsupported config format: {ext}")

    jobs_data = raw.get("jobs", {})
    if not jobs_data:
        raise ValueError("Config file contains no jobs")

    return [_parse_job(name, data) for name, data in jobs_data.items()]
