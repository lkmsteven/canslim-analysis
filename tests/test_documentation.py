"""Tests for mandatory documentation layout and operational accuracy."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SPEC_FILES = (
    "requirements.md",
    "design.md",
    "tasks.md",
)
REQUIRED_WIKI_FILES = (
    "Home.md",
    "Architecture.md",
    "Getting-Started.md",
    "Configuration.md",
    "API-Reference.md",
    "FAQ-Troubleshooting.md",
    "Modules/Quantitative-Analyzer.md",
    "Modules/AI-Enrichment.md",
    "Modules/Final-Process.md",
    "Modules/PDF-Report-Generator.md",
)
STALE_OPERATIONAL_TEXT = (
    "python Scripts/quantitative_analyzer.py",
    "python Scripts/final_process.py",
    "python Scripts/pdf_report_generator.py",
    "Scripts/intermediate_canslim.json",
    "Scripts/enriched_canslim.json",
    "Scripts/final_canslim_report.json",
)


def test_mandatory_specification_layout_exists() -> None:
    """The project uses the workspace-required specification paths."""

    for filename in REQUIRED_SPEC_FILES:
        assert (PROJECT_ROOT / "doc" / "spec" / filename).is_file()


def test_wiki_is_migrated_from_legacy_directory() -> None:
    """Useful wiki content lives at the mandated path with no legacy root."""

    assert not (PROJECT_ROOT / ".doc").exists()
    assert (PROJECT_ROOT / "doc" / "wiki").is_dir()
    for filename in REQUIRED_WIKI_FILES:
        assert (PROJECT_ROOT / "doc" / "wiki" / filename).is_file()


def test_readme_documents_current_package_cli() -> None:
    """README setup and usage match the delivered package interface."""

    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    for expected in (
        "python -m venv .venv",
        "python -m pip install -e '.[dev]'",
        "pytest",
        "python -m canslim_analysis status",
        "python -m canslim_analysis quantitative",
        "out/intermediate_canslim.json",
    ):
        assert expected in readme
    assert "python Scripts/quantitative_analyzer.py" not in readme


def test_wiki_has_no_stale_operational_paths() -> None:
    """Every wiki page describes the package CLI and out/ artifacts."""

    wiki_files = list((PROJECT_ROOT / "doc" / "wiki").rglob("*.md"))
    assert wiki_files
    for path in wiki_files:
        content = path.read_text(encoding="utf-8")
        for stale in STALE_OPERATIONAL_TEXT:
            assert stale not in content, f"{path} contains {stale}"
