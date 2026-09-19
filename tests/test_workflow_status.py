"""Tests for pipeline status classification and artifact validation."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from canslim_analysis.cli import build_parser, main
from canslim_analysis.pipeline.status import classify_workflow_state


def intermediate_data() -> dict[str, object]:
    """Create a minimal valid quantitative artifact."""

    return {
        "Metadata": {"Schema_Version": "2.1"},
        "Stocks": [],
    }


def write_json(path: Path, data: object) -> Path:
    """Write a local JSON fixture."""

    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_parser_accepts_status_and_validate_options() -> None:
    """Status and validate commands expose their documented options."""

    status = build_parser().parse_args(["status", "--json"])
    validate = build_parser().parse_args(
        ["validate", "--stage", "quantitative", "--input", "input.json"]
    )

    assert status.json_output is True
    assert validate.stage == "quantitative"
    assert validate.input == "input.json"


def test_empty_pipeline_is_not_started(tmp_path: Path) -> None:
    """An empty output directory has one unambiguous initial state."""

    assert classify_workflow_state(tmp_path) == "not-started"


def test_valid_quantitative_artifact_is_quantitative_complete(tmp_path: Path) -> None:
    """A valid intermediate artifact advances past the initial state."""

    write_json(tmp_path / "intermediate_canslim.json", intermediate_data())

    assert classify_workflow_state(tmp_path) == "quantitative-complete"


def test_template_makes_stage_enrichment_ready(tmp_path: Path) -> None:
    """A template can be generated only after valid quantitative output."""

    write_json(tmp_path / "intermediate_canslim.json", intermediate_data())
    write_json(tmp_path / "enrichment_template.json", {"Findings": []})

    assert classify_workflow_state(tmp_path) == "enrichment-ready"


def test_valid_enriched_artifact_is_enrichment_complete(tmp_path: Path) -> None:
    """Valid enriched output is ready for final scoring."""

    enriched = {
        "Metadata": {"Market_Direction_M": "Confirmed Uptrend"},
        "Stocks": [],
    }
    write_json(tmp_path / "intermediate_canslim.json", intermediate_data())
    write_json(tmp_path / "enriched_canslim.json", enriched)

    assert classify_workflow_state(tmp_path) == "enrichment-complete"


def test_final_and_pdf_artifacts_complete_workflow(tmp_path: Path) -> None:
    """Final JSON plus PDF represents the last normal state."""

    final = {
        "Schema_Version": "2.1",
        "Market_Environment": "Confirmed Uptrend",
        "Top_Candidates": [],
    }
    write_json(tmp_path / "intermediate_canslim.json", intermediate_data())
    write_json(
        tmp_path / "enriched_canslim.json",
        {"Metadata": {}, "Stocks": []},
    )
    write_json(tmp_path / "final_canslim_report.json", final)
    (tmp_path / "canslim_report_2026-09-13.pdf").write_bytes(b"%PDF-1.7\n")

    assert classify_workflow_state(tmp_path) == "report-complete"


def test_invalid_artifact_is_invalid(tmp_path: Path) -> None:
    """A parseable but schema-invalid artifact is not treated as progress."""

    write_json(tmp_path / "intermediate_canslim.json", {"Stocks": "wrong"})

    assert classify_workflow_state(tmp_path) == "invalid"


def test_cli_status_json_reports_not_started(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Machine-readable status is suitable for agent use."""

    exit_code = main(["status", "--json", "--output-dir", str(tmp_path)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["state"] == "not-started"


def test_cli_status_defaults_to_project_output_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Status without an override uses the project-local ``out`` directory."""

    monkeypatch.chdir(tmp_path)
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    exit_code = main(["status", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["state"] == "not-started"


def test_cli_validate_missing_artifact_returns_stable_code(tmp_path: Path) -> None:
    """Validating an absent stage artifact returns exit code 4."""

    exit_code = main(
        [
            "validate",
            "--stage",
            "quantitative",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 4


def test_fresh_quantitative_run_makes_old_downstream_artifacts_stale(
    tmp_path: Path,
) -> None:
    """Refreshing a predecessor regresses status until downstream is rebuilt."""

    intermediate = write_json(
        tmp_path / "intermediate_canslim.json",
        intermediate_data(),
    )
    enriched_path = tmp_path / "enriched_canslim.json"
    enriched_path.write_text(
        json.dumps({"Metadata": {}, "Stocks": []}),
        encoding="utf-8",
    )
    final_path = tmp_path / "final_canslim_report.json"
    final_path.write_text(
        json.dumps(
            {
                "Schema_Version": "2.1",
                "Market_Environment": "Confirmed Uptrend",
                "Top_Candidates": [],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "canslim_report_2026-09-13.pdf").write_bytes(b"%PDF-1.7\n")

    stale_time = time.time() - 3600
    now = time.time()
    os.utime(enriched_path, (stale_time, stale_time))
    os.utime(final_path, (stale_time, stale_time))
    os.utime(intermediate, (now, now))

    assert classify_workflow_state(tmp_path) == "quantitative-complete"


def test_fresh_enrichment_makes_old_final_report_stale(tmp_path: Path) -> None:
    """Final reports are compared with their immediate enriched predecessor."""

    intermediate_path = write_json(
        tmp_path / "intermediate_canslim.json",
        intermediate_data(),
    )
    enriched_path = tmp_path / "enriched_canslim.json"
    enriched_path.write_text(
        json.dumps({"Metadata": {}, "Stocks": []}),
        encoding="utf-8",
    )
    final_path = tmp_path / "final_canslim_report.json"
    final_path.write_text(
        json.dumps(
            {
                "Schema_Version": "2.1",
                "Market_Environment": "Confirmed Uptrend",
                "Top_Candidates": [],
            }
        ),
        encoding="utf-8",
    )

    now = time.time()
    os.utime(intermediate_path, (now - 7200, now - 7200))
    os.utime(enriched_path, (now - 3600, now - 3600))
    os.utime(final_path, (now - 5400, now - 5400))

    assert classify_workflow_state(tmp_path) == "enrichment-complete"
