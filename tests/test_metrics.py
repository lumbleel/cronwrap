"""Tests for cronwrap.metrics."""
import time

import pytest

from cronwrap.metrics import JobMetric, MetricsStore, get_store, reset_store


@pytest.fixture(autouse=True)
def clean_store():
    reset_store()
    yield
    reset_store()


def test_job_metric_duration_none_when_not_finished():
    m = JobMetric(job_name="demo", started_at=time.monotonic())
    assert m.duration_seconds is None


def test_job_metric_duration_calculated():
    m = JobMetric(job_name="demo", started_at=100.0, finished_at=102.5)
    assert m.duration_seconds == 2.5


def test_job_metric_succeeded_true_on_zero():
    m = JobMetric(job_name="demo", started_at=0.0, finished_at=1.0, exit_code=0)
    assert m.succeeded is True


def test_job_metric_succeeded_false_on_nonzero():
    m = JobMetric(job_name="demo", started_at=0.0, finished_at=1.0, exit_code=1)
    assert m.succeeded is False


def test_job_metric_succeeded_none_when_no_exit_code():
    m = JobMetric(job_name="demo", started_at=0.0)
    assert m.succeeded is None


def test_store_start_returns_metric():
    store = MetricsStore()
    m = store.start("myjob")
    assert isinstance(m, JobMetric)
    assert m.job_name == "myjob"


def test_store_finish_sets_fields():
    store = MetricsStore()
    m = store.start("myjob")
    store.finish(m, exit_code=0, retries=2)
    assert m.exit_code == 0
    assert m.retries == 2
    assert m.finished_at is not None


def test_store_all_returns_all_records():
    store = MetricsStore()
    store.start("a")
    store.start("b")
    assert len(store.all()) == 2


def test_store_for_job_filters_by_name():
    store = MetricsStore()
    store.start("alpha")
    store.start("beta")
    store.start("alpha")
    assert len(store.for_job("alpha")) == 2
    assert len(store.for_job("beta")) == 1


def test_summary_counts_successes_and_failures():
    store = MetricsStore()
    m1 = store.start("job")
    store.finish(m1, exit_code=0)
    m2 = store.start("job")
    store.finish(m2, exit_code=1)
    s = store.summary()
    assert s["successes"] == 1
    assert s["failures"] == 1
    assert s["total"] == 2


def test_summary_avg_duration():
    store = MetricsStore()
    m = store.start("job")
    m.started_at = 0.0
    store.finish(m, exit_code=0)
    m.finished_at = 4.0
    s = store.summary()
    assert s["avg_duration_seconds"] == 4.0


def test_get_store_returns_same_instance():
    s1 = get_store()
    s2 = get_store()
    assert s1 is s2


def test_reset_store_creates_fresh_store():
    s1 = get_store()
    s1.start("job")
    reset_store()
    s2 = get_store()
    assert len(s2.all()) == 0
