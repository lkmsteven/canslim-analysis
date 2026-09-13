"""Consistent logging configuration for CLI and pipeline execution."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(log_file: Path, *, debug: bool = False) -> None:
    """Replace root handlers with one console and one file handler.

    Args:
        log_file: Project-local file that receives detailed execution messages.
        debug: Whether to emit debug-level records.
    """

    resolved_log_file = log_file.expanduser().resolve()
    resolved_log_file.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    file_handler = logging.FileHandler(resolved_log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    root.setLevel(logging.DEBUG if debug else logging.INFO)
