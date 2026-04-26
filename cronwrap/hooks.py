"""Pre- and post-run shell hooks for cron jobs."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class HookResult:
    """Outcome of a single hook command."""

    command: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


def _run_hook(
    command: str,
    env: Optional[Dict[str, str]] = None,
    timeout: int = 30,
) -> HookResult:
    """Execute a single hook command and return its result."""
    proc = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )
    return HookResult(
        command=command,
        returncode=proc.returncode,
        stdout=proc.stdout.strip(),
        stderr=proc.stderr.strip(),
    )


def run_hooks(
    commands: List[str],
    env: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    stop_on_failure: bool = True,
) -> List[HookResult]:
    """Run a list of hook commands in order.

    Args:
        commands: Shell commands to execute.
        env: Environment for the subprocesses.
        timeout: Per-command timeout in seconds.
        stop_on_failure: Abort remaining hooks if one fails.

    Returns:
        List of HookResult for every command that was attempted.
    """
    results: List[HookResult] = []
    for cmd in commands:
        result = _run_hook(cmd, env=env, timeout=timeout)
        results.append(result)
        if stop_on_failure and not result.success:
            break
    return results


def all_passed(results: List[HookResult]) -> bool:
    """Return True only if every hook succeeded."""
    return all(r.success for r in results)
