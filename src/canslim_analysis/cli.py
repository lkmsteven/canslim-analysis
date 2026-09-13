"""Command-line interface for the CANSLIM analysis pipeline."""

from __future__ import annotations

import argparse


COMMANDS = (
    "quantitative",
    "prepare-enrichment",
    "enrich",
    "finalize",
    "report",
    "run",
    "status",
    "validate",
)


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser.

    Returns:
        Parser configured with every supported pipeline command.
    """

    parser = argparse.ArgumentParser(
        prog="python -m canslim_analysis",
        description="Run and validate the CANSLIM analysis pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command")

    for command in COMMANDS:
        subparsers.add_parser(command)

    return parser


def main() -> int:
    """Run the command-line interface.

    Returns:
        Process exit code.
    """

    parser = build_parser()
    arguments = parser.parse_args()

    if arguments.command is None:
        parser.print_help()
        return 0

    return 0
