#!/usr/bin/env python3
"""Unified test runner for automation pipelines."""

import argparse
import os
import subprocess
import sys
from pathlib import Path


SCOPES = {"all", "unit", "e2e"}


def build_command(scope: str, extra_args: list[str]) -> list[str]:
    cmd = [sys.executable, "-m", "pytest"]
    if scope == "unit":
        cmd += ["-m", "not e2e"]
    elif scope == "e2e":
        cmd += ["-m", "e2e"]
    if extra_args:
        cmd += extra_args
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pytest suites with standard scopes.")
    parser.add_argument(
        "--scope",
        choices=sorted(SCOPES),
        default="all",
        help="Select which portion of the suite to execute (default: all)",
    )
    parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="Additional arguments passed through to pytest.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    cmd = build_command(args.scope, args.extra or [])

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=repo_root, env=os.environ.copy())
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
