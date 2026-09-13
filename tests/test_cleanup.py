"""Tests for removal of superseded script-based implementation."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPERSEDED_PATHS = (
    "Scripts",
    "Scripts/quantitative_analyzer.py",
    "Scripts/final_process.py",
    "Scripts/pdf_report_generator.py",
    "Scripts/intermediate_canslim.json",
    "Scripts/enriched_canslim.json",
    "Scripts/final_canslim_report.json",
)


def test_superseded_scripts_and_generated_artifacts_are_removed() -> None:
    """The package CLI is the only operational interface."""

    for relative_path in SUPERSEDED_PATHS:
        assert not (PROJECT_ROOT / relative_path).exists()


def test_live_source_does_not_target_legacy_scripts_directory() -> None:
    """Runtime code must not write through the removed source/artifact path."""

    source_files = list((PROJECT_ROOT / "src").rglob("*.py"))
    assert source_files
    for path in source_files:
        assert "Scripts" not in path.read_text(encoding="utf-8"), path


def test_unselected_operational_fixtures_do_not_exist() -> None:
    """Any retained generated JSON must live in a documented fixture path."""

    fixture_dir = PROJECT_ROOT / "tests" / "fixtures"
    if not fixture_dir.exists():
        return
    for path in fixture_dir.rglob("*.json"):
        assert (fixture_dir / "README.md").is_file()
        assert path.name in (fixture_dir / "README.md").read_text(encoding="utf-8")
