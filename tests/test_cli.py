"""Tests for the Codex-facing command-line entry point."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COMMANDS = (
    "quantitative",
    "prepare-enrichment",
    "enrich",
    "finalize",
    "report",
    "run",
    "status",
    "validate",
)


def _run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Run the package CLI with the repository's source tree importable."""

    environment = os.environ.copy()
    source_path = PROJECT_ROOT / "src"
    environment["PYTHONPATH"] = str(source_path)
    return subprocess.run(
        [sys.executable, "-m", "canslim_analysis", *arguments],
        cwd=PROJECT_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )


def test_package_cli_help_lists_all_pipeline_commands() -> None:
    """The top-level help must expose every supported pipeline command."""

    result = _run_cli("--help")

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    for command in EXPECTED_COMMANDS:
        assert command in result.stdout


def test_package_cli_without_command_prints_help() -> None:
    """The no-command invocation is a safe help operation."""

    result = _run_cli()

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()


def test_package_cli_rejects_unknown_command() -> None:
    """Unexpected command names fail using argparse's usage exit code."""

    result = _run_cli("not-a-command")

    assert result.returncode == 2
    assert "invalid choice" in result.stderr
