"""Environment variable injection and masking for cron job execution."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_SECRET_PATTERN = re.compile(r"(password|secret|token|key|auth)", re.IGNORECASE)
_MASK = "***"


@dataclass
class EnvContext:
    """Holds the resolved environment for a job run."""

    base: Dict[str, str] = field(default_factory=dict)
    overrides: Dict[str, str] = field(default_factory=dict)

    def resolved(self) -> Dict[str, str]:
        """Return merged environment: base + overrides."""
        env = dict(self.base)
        env.update(self.overrides)
        return env

    def masked(self) -> Dict[str, str]:
        """Return resolved env with secret values replaced by ***."""
        return {
            k: (_MASK if _SECRET_PATTERN.search(k) else v)
            for k, v in self.resolved().items()
        }


def build_env_context(
    job_env: Optional[Dict[str, str]] = None,
    inherit: bool = True,
) -> EnvContext:
    """Build an EnvContext for a job.

    Args:
        job_env: Extra variables defined in the job config.
        inherit: Whether to inherit the current process environment.

    Returns:
        An EnvContext ready for use.
    """
    base = dict(os.environ) if inherit else {}
    overrides = dict(job_env) if job_env else {}
    return EnvContext(base=base, overrides=overrides)


def list_secret_keys(env: Dict[str, str]) -> List[str]:
    """Return keys that look like secrets."""
    return [k for k in env if _SECRET_PATTERN.search(k)]
