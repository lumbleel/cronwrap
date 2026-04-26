"""Orchestrates env injection and pre/post hooks around a job run."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwrap.env import EnvContext, build_env_context
from cronwrap.hooks import HookResult, run_hooks, all_passed

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Aggregated outcome of env + hooks pipeline."""

    env_context: EnvContext
    pre_hooks: List[HookResult] = field(default_factory=list)
    post_hooks: List[HookResult] = field(default_factory=list)
    pre_hooks_ok: bool = True
    post_hooks_ok: bool = True

    @property
    def ok(self) -> bool:
        return self.pre_hooks_ok and self.post_hooks_ok


def prepare_pipeline(
    job_env: Optional[Dict[str, str]] = None,
    inherit_env: bool = True,
    pre_hook_commands: Optional[List[str]] = None,
    hook_timeout: int = 30,
    stop_on_failure: bool = True,
) -> PipelineResult:
    """Build env context and run pre-hooks.

    Returns a PipelineResult; callers should check `.pre_hooks_ok` before
    launching the main job command.
    """
    ctx = build_env_context(job_env=job_env, inherit=inherit_env)
    logger.debug("Resolved env (masked): %s", ctx.masked())

    pre_results: List[HookResult] = []
    pre_ok = True
    if pre_hook_commands:
        pre_results = run_hooks(
            pre_hook_commands,
            env=ctx.resolved(),
            timeout=hook_timeout,
            stop_on_failure=stop_on_failure,
        )
        pre_ok = all_passed(pre_results)
        if not pre_ok:
            logger.warning("Pre-hook failed; aborting pipeline.")

    return PipelineResult(
        env_context=ctx,
        pre_hooks=pre_results,
        pre_hooks_ok=pre_ok,
    )


def finalise_pipeline(
    pipeline: PipelineResult,
    post_hook_commands: Optional[List[str]] = None,
    hook_timeout: int = 30,
    stop_on_failure: bool = True,
) -> PipelineResult:
    """Run post-hooks and update the pipeline result in place."""
    if post_hook_commands:
        post_results = run_hooks(
            post_hook_commands,
            env=pipeline.env_context.resolved(),
            timeout=hook_timeout,
            stop_on_failure=stop_on_failure,
        )
        pipeline.post_hooks = post_results
        pipeline.post_hooks_ok = all_passed(post_results)
        if not pipeline.post_hooks_ok:
            logger.warning("Post-hook failed.")
    return pipeline
