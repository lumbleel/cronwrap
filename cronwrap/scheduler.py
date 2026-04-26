"""Scheduler integration helpers for cronwrap.

Provides utilities to validate cron expressions and determine whether a job
is due to run based on its schedule string.  This module intentionally avoids
spawning background threads — cronwrap is designed to be *invoked* by an
external scheduler (e.g. system cron) and this module simply helps with
schedule-related bookkeeping and validation.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Cron field validation
# ---------------------------------------------------------------------------

# Allowed ranges for each of the five standard cron fields.
_FIELD_RANGES: list[tuple[int, int]] = [
    (0, 59),   # minute
    (0, 23),   # hour
    (1, 31),   # day-of-month
    (1, 12),   # month
    (0, 7),    # day-of-week  (0 and 7 both represent Sunday)
]

_STEP_RE = re.compile(r"^(\*|\d+)(?:-(\d+))?(?:/(\d+))?$")


class InvalidCronExpression(ValueError):
    """Raised when a cron expression cannot be parsed or is out of range."""


def _parse_field(token: str, min_val: int, max_val: int) -> list[int]:
    """Expand a single cron field token into a sorted list of integers.

    Supports:
    - ``*``          — every value
    - ``*/N``        — every N-th value
    - ``A-B``        — range
    - ``A-B/N``      — stepped range
    - ``N``          — single value
    """
    match = _STEP_RE.match(token)
    if not match:
        raise InvalidCronExpression(f"Cannot parse cron field token: {token!r}")

    start_tok, end_tok, step_tok = match.groups()

    step = int(step_tok) if step_tok else 1
    if step < 1:
        raise InvalidCronExpression(f"Step must be >= 1, got {step}")

    if start_tok == "*":
        start, end = min_val, max_val
    else:
        start = int(start_tok)
        end = int(end_tok) if end_tok else start

    if not (min_val <= start <= max_val and min_val <= end <= max_val):
        raise InvalidCronExpression(
            f"Value(s) {start}-{end} out of range [{min_val}, {max_val}]"
        )

    return list(range(start, end + 1, step))


def parse_cron(expression: str) -> list[list[int]]:
    """Parse a five-field cron expression and return expanded field lists.

    Returns a list of five lists, one per field (minute, hour, dom, month, dow).

    Raises :class:`InvalidCronExpression` if the expression is malformed.
    """
    parts = expression.strip().split()
    if len(parts) != 5:
        raise InvalidCronExpression(
            f"Expected 5 fields, got {len(parts)}: {expression!r}"
        )

    result: list[list[int]] = []
    for token, (min_val, max_val) in zip(parts, _FIELD_RANGES):
        values: set[int] = set()
        for sub in token.split(","):
            values.update(_parse_field(sub, min_val, max_val))
        result.append(sorted(values))

    return result


def is_valid_cron(expression: str) -> bool:
    """Return *True* if *expression* is a valid five-field cron string."""
    try:
        parse_cron(expression)
        return True
    except InvalidCronExpression:
        return False


# ---------------------------------------------------------------------------
# Due-time check
# ---------------------------------------------------------------------------


def is_due(expression: str, at: Optional[datetime] = None) -> bool:
    """Return *True* if the cron *expression* matches the given datetime.

    When *at* is ``None`` the current local time (minute precision) is used.

    Day-of-week values 0 and 7 are both treated as Sunday, matching standard
    cron behaviour.
    """
    if at is None:
        at = datetime.now()

    fields = parse_cron(expression)
    minute_vals, hour_vals, dom_vals, month_vals, dow_vals = fields

    # Normalise Sunday: cron allows both 0 and 7.
    dow = at.isoweekday() % 7  # Monday=1 … Saturday=6, Sunday=0

    return (
        at.minute in minute_vals
        and at.hour in hour_vals
        and at.day in dom_vals
        and at.month in month_vals
        and dow in dow_vals
    )
