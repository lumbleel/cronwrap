"""Tests for cronwrap.hooks."""

import pytest

from cronwrap.hooks import HookResult, _run_hook, run_hooks, all_passed


# ---------------------------------------------------------------------------
# HookResult
# ---------------------------------------------------------------------------

def test_hook_result_success_true_on_zero():
    r = HookResult(command="echo hi", returncode=0, stdout="hi", stderr="")
    assert r.success is True


def test_hook_result_success_false_on_nonzero():
    r = HookResult(command="false", returncode=1, stdout="", stderr="")
    assert r.success is False


# ---------------------------------------------------------------------------
# _run_hook
# ---------------------------------------------------------------------------

def test_run_hook_captures_stdout():
    result = _run_hook("echo hello")
    assert result.stdout == "hello"
    assert result.returncode == 0


def test_run_hook_captures_stderr():
    result = _run_hook("echo err >&2")
    assert result.stderr == "err"


def test_run_hook_nonzero_returncode():
    result = _run_hook("exit 42")
    assert result.returncode == 42
    assert result.success is False


def test_run_hook_stores_command():
    cmd = "echo stored"
    result = _run_hook(cmd)
    assert result.command == cmd


# ---------------------------------------------------------------------------
# run_hooks
# ---------------------------------------------------------------------------

def test_run_hooks_runs_all_on_success():
    results = run_hooks(["echo a", "echo b", "echo c"])
    assert len(results) == 3
    assert all(r.success for r in results)


def test_run_hooks_stops_on_failure_by_default():
    results = run_hooks(["exit 1", "echo should_not_run"])
    assert len(results) == 1
    assert not results[0].success


def test_run_hooks_continues_on_failure_when_disabled():
    results = run_hooks(["exit 1", "echo second"], stop_on_failure=False)
    assert len(results) == 2


def test_run_hooks_empty_list():
    assert run_hooks([]) == []


# ---------------------------------------------------------------------------
# all_passed
# ---------------------------------------------------------------------------

def test_all_passed_true():
    results = [HookResult("cmd", 0, "", ""), HookResult("cmd2", 0, "", "")]
    assert all_passed(results) is True


def test_all_passed_false():
    results = [HookResult("cmd", 0, "", ""), HookResult("cmd2", 1, "", "")]
    assert all_passed(results) is False


def test_all_passed_empty():
    assert all_passed([]) is True
