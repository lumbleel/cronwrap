"""Lightweight in-process metrics collection for cronwrap jobs."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class JobMetric:
    job_name: str
    started_at: float
    finished_at: Optional[float] = None
    exit_code: Optional[int] = None
    retries: int = 0

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.finished_at is None:
            return None
        return round(self.finished_at - self.started_at, 4)

    @property
    def succeeded(self) -> Optional[bool]:
        if self.exit_code is None:
            return None
        return self.exit_code == 0


@dataclass
class MetricsStore:
    _records: List[JobMetric] = field(default_factory=list)

    def start(self, job_name: str) -> JobMetric:
        metric = JobMetric(job_name=job_name, started_at=time.monotonic())
        self._records.append(metric)
        return metric

    def finish(self, metric: JobMetric, exit_code: int, retries: int = 0) -> None:
        metric.finished_at = time.monotonic()
        metric.exit_code = exit_code
        metric.retries = retries

    def all(self) -> List[JobMetric]:
        return list(self._records)

    def for_job(self, job_name: str) -> List[JobMetric]:
        return [r for r in self._records if r.job_name == job_name]

    def summary(self) -> Dict[str, object]:
        total = len(self._records)
        finished = [r for r in self._records if r.finished_at is not None]
        successes = sum(1 for r in finished if r.succeeded)
        failures = sum(1 for r in finished if not r.succeeded)
        durations = [r.duration_seconds for r in finished if r.duration_seconds is not None]
        avg_duration = round(sum(durations) / len(durations), 4) if durations else None
        return {
            "total": total,
            "finished": len(finished),
            "successes": successes,
            "failures": failures,
            "avg_duration_seconds": avg_duration,
        }


_default_store = MetricsStore()


def get_store() -> MetricsStore:
    return _default_store


def reset_store() -> None:
    global _default_store
    _default_store = MetricsStore()
