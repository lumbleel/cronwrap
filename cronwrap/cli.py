#!/usr/bin/env python3
"""CLI entry point for cronwrap."""
import argparse
import sys

from cronwrap.config import load_config
from cronwrap.logger import setup_logger
from cronwrap.runner import run_job


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap",
        description="Lightweight cron job wrapper with logging and retry logic.",
    )
    parser.add_argument("config", help="Path to the TOML or YAML config file")
    parser.add_argument("job", help="Name of the job to run")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logger = setup_logger("cronwrap", level=args.log_level)

    try:
        jobs = load_config(args.config)
    except FileNotFoundError:
        logger.error(f"Config file not found: {args.config}")
        return 2
    except Exception as exc:
        logger.error(f"Failed to load config: {exc}")
        return 2

    job = jobs.get(args.job)
    if job is None:
        logger.error(
            f"Job '{args.job}' not found in config. "
            f"Available jobs: {', '.join(jobs.keys()) or 'none'}"
        )
        return 2

    result = run_job(job, logger=logger)
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
