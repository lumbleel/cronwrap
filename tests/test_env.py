"""Tests for cronwrap.env."""

import os
import pytest

from cronwrap.env import (
    EnvContext,
    build_env_context,
    list_secret_keys,
    _MASK,
)


# ---------------------------------------------------------------------------
# EnvContext
# ---------------------------------------------------------------------------

def test_resolved_merges_base_and_overrides():
    ctx = EnvContext(base={"A": "1", "B": "2"}, overrides={"B": "override", "C": "3"})
    resolved = ctx.resolved()
    assert resolved["A"] == "1"
    assert resolved["B"] == "override"
    assert resolved["C"] == "3"


def test_resolved_empty():
    ctx = EnvContext()
    assert ctx.resolved() == {}


def test_masked_hides_secret_keys():
    ctx = EnvContext(
        base={"DB_PASSWORD": "s3cr3t", "DB_HOST": "localhost"},
        overrides={"API_TOKEN": "tok"},
    )
    masked = ctx.masked()
    assert masked["DB_PASSWORD"] == _MASK
    assert masked["API_TOKEN"] == _MASK
    assert masked["DB_HOST"] == "localhost"


def test_masked_leaves_normal_keys_intact():
    ctx = EnvContext(base={"HOME": "/root", "PATH": "/usr/bin"})
    masked = ctx.masked()
    assert masked["HOME"] == "/root"
    assert masked["PATH"] == "/usr/bin"


# ---------------------------------------------------------------------------
# build_env_context
# ---------------------------------------------------------------------------

def test_build_env_context_inherits_os_env():
    os.environ["_CRONWRAP_TEST_VAR"] = "hello"
    try:
        ctx = build_env_context()
        assert ctx.resolved()["_CRONWRAP_TEST_VAR"] == "hello"
    finally:
        del os.environ["_CRONWRAP_TEST_VAR"]


def test_build_env_context_no_inherit():
    ctx = build_env_context(job_env={"X": "1"}, inherit=False)
    assert list(ctx.resolved().keys()) == ["X"]


def test_build_env_context_job_env_overrides():
    ctx = build_env_context(job_env={"HOME": "/custom"}, inherit=True)
    assert ctx.resolved()["HOME"] == "/custom"


def test_build_env_context_none_job_env():
    ctx = build_env_context(job_env=None, inherit=False)
    assert ctx.resolved() == {}


# ---------------------------------------------------------------------------
# list_secret_keys
# ---------------------------------------------------------------------------

def test_list_secret_keys_detects_password():
    env = {"DB_PASSWORD": "x", "HOST": "y"}
    assert "DB_PASSWORD" in list_secret_keys(env)
    assert "HOST" not in list_secret_keys(env)


def test_list_secret_keys_case_insensitive():
    env = {"MySecretKey": "v", "AUTH_TOKEN": "t", "NORMAL": "n"}
    secrets = list_secret_keys(env)
    assert "MySecretKey" in secrets
    assert "AUTH_TOKEN" in secrets
    assert "NORMAL" not in secrets


def test_list_secret_keys_empty():
    assert list_secret_keys({}) == []
