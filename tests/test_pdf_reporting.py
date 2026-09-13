"""Tests for final-report PDF generation."""

from __future__ import annotations

import json
from pathlib import Path

from canslim_analysis.cli import build_parser, main


def final_report() -> dict[str, object]:
    """Create a minimal valid final report."""

    return {
        "Schema_Version": "2.1",
        "Report_Date": "2026-01-02",
        "Market_Environment": "Confirmed Uptrend",
        "M_Criterion_Met": True,
        "Total_Candidates_Evaluated": 0,
        "Score_Distribution": {},
        "Top_Candidates": [],
    }


def test_parser_accepts_pdf_paths() -> None:
    """PDF input and output directory can be overridden."""

    arguments = build_parser().parse_args(
        ["report", "--input", "final.json", "--output-dir", "pdf-out"]
    )

    assert arguments.input == "final.json"
    assert arguments.output_dir == "pdf-out"


def test_cli_renders_final_report_to_deterministic_pdf(tmp_path: Path) -> None:
    """The report command writes a real PDF using the report date."""

    input_path = tmp_path / "final.json"
    output_dir = tmp_path / "pdf"
    input_path.write_text(json.dumps(final_report()), encoding="utf-8")

    exit_code = main(
        [
            "report",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
        ]
    )

    output_path = output_dir / "canslim_report_2026-01-02.pdf"
    assert exit_code == 0
    assert output_path.read_bytes().startswith(b"%PDF-")


def test_cli_missing_final_report_returns_stable_code(tmp_path: Path) -> None:
    """A missing final artifact produces exit code 4."""

    exit_code = main(
        [
            "report",
            "--input",
            str(tmp_path / "missing.json"),
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 4


def test_cli_malformed_final_report_returns_stable_code(tmp_path: Path) -> None:
    """Malformed JSON is classified as schema validation, not a crash."""

    input_path = tmp_path / "final.json"
    input_path.write_text("{bad}", encoding="utf-8")

    exit_code = main(
        [
            "report",
            "--input",
            str(input_path),
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 3
