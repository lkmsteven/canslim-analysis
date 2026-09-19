"""Workflow state classification and standalone artifact validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from canslim_analysis.errors import ArtifactNotFoundError, SchemaValidationError
from canslim_analysis.pipeline.enrichment import validate_quantitative_input
from canslim_analysis.pipeline.scoring import validate_enriched_dataset
from canslim_analysis.paths import (
    ENRICHED_ARTIFACT,
    ENRICHMENT_TEMPLATE_ARTIFACT,
    FINAL_REPORT_ARTIFACT,
    INTERMEDIATE_ARTIFACT,
)


WORKFLOW_STATES = (
    "not-started",
    "quantitative-complete",
    "enrichment-ready",
    "enrichment-complete",
    "final-complete",
    "report-complete",
    "invalid",
)


def _read_json(path: Path) -> Any:
    """Read one UTF-8 JSON artifact."""

    if not path.is_file():
        raise ArtifactNotFoundError(f"Artifact not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaValidationError(f"Artifact is not valid JSON: {path}") from exc


def validate_artifact(path: Path, stage: str) -> Any:
    """Validate one artifact against its selected stage contract.

    Args:
        path: Artifact path to validate.
        stage: ``quantitative``, ``enriched``, or ``final``.

    Returns:
        Parsed artifact data after validation.
    """

    data = _read_json(path)
    if stage == "quantitative":
        validate_quantitative_input(data)
    elif stage == "enriched":
        validate_enriched_dataset(data)
    elif stage == "final":
        _validate_final_report(data)
    else:
        raise SchemaValidationError(f"Unknown validation stage: {stage}")
    return data


def _validate_final_report(data: Any) -> None:
    """Validate the minimal final-report contract."""

    if not isinstance(data, dict):
        raise SchemaValidationError("Final report must be a JSON object")
    if data.get("Schema_Version") != "2.1":
        raise SchemaValidationError("Final report schema version must be 2.1")
    if not isinstance(data.get("Market_Environment"), str):
        raise SchemaValidationError("Final report requires Market_Environment")
    if not isinstance(data.get("Top_Candidates"), list):
        raise SchemaValidationError("Final report requires a Top_Candidates array")


def _is_valid(path: Path, stage: str) -> bool:
    """Return whether one artifact exists and passes stage validation."""

    try:
        validate_artifact(path, stage)
    except (ArtifactNotFoundError, SchemaValidationError, OSError):
        return False
    return True


def _is_current(path: Path, stage: str, *, source: Path | None = None) -> bool:
    """Return whether an artifact is valid and not older than its source."""

    if not path.is_file() or not _is_valid(path, stage):
        return False
    if source is not None and path.stat().st_mtime < source.stat().st_mtime:
        return False
    return True


def classify_workflow_state(
    output_dir: Path | str,
    *,
    project_root: Path | str | None = None,
) -> str:
    """Classify pipeline progress from current, validated artifacts.

    Args:
        output_dir: Output directory containing generated artifacts.
        project_root: Unused root kept for path-resolution symmetry.

    Returns:
        One of the documented workflow states. Artifacts older than their
        required predecessor are stale and do not advance the state; for
        example, a fresh quantitative rerun correctly returns the workflow to
        ``quantitative-complete`` until downstream stages are regenerated.
    """

    del project_root
    directory = Path(output_dir)
    intermediate = directory / INTERMEDIATE_ARTIFACT
    template = directory / ENRICHMENT_TEMPLATE_ARTIFACT
    enriched = directory / ENRICHED_ARTIFACT
    final = directory / FINAL_REPORT_ARTIFACT

    if not intermediate.exists():
        return "not-started"
    if not _is_valid(intermediate, "quantitative"):
        return "invalid"
    enriched_is_current = _is_current(enriched, "enriched", source=intermediate)
    final_is_current = _is_current(final, "final", source=enriched)

    if enriched_is_current:
        if final_is_current:
            report_newer = any(
                report.stat().st_mtime >= final.stat().st_mtime
                for report in directory.glob("canslim_report_*.pdf")
            )
            if report_newer:
                return "report-complete"
            return "final-complete"
        return "enrichment-complete"
    if template.is_file() and template.stat().st_mtime >= intermediate.stat().st_mtime:
        return "enrichment-ready"
    return "quantitative-complete"


def next_command(state: str) -> str | None:
    """Return the next safe command for a normal workflow state."""

    commands = {
        "not-started": "python -m canslim_analysis quantitative",
        "quantitative-complete": "python -m canslim_analysis prepare-enrichment",
        "enrichment-ready": "python -m canslim_analysis enrich",
        "enrichment-complete": "python -m canslim_analysis finalize",
        "final-complete": "python -m canslim_analysis report",
        "report-complete": None,
        "invalid": "python -m canslim_analysis validate",
    }
    return commands.get(state)
