"""Qualitative enrichment template creation and validation."""

from __future__ import annotations

import json
import logging
import copy
from pathlib import Path
from typing import Any

from canslim_analysis.errors import ArtifactNotFoundError, SchemaValidationError
from canslim_analysis.paths import (
    ENRICHED_ARTIFACT,
    ENRICHMENT_TEMPLATE_ARTIFACT,
    resolve_artifact_path,
)


logger = logging.getLogger(__name__)

FINDING_BOOLEAN_FIELDS = (
    "N_New_Catalyst",
    "S_Float_Tightness",
    "I_Institutional_Quality",
)
FINDING_EVIDENCE_FIELDS = (
    "N_Catalyst_Details",
    "S_Float_Details",
    "I_Institutional_Details",
)
FINDING_FIELDS = ("Ticker", *FINDING_BOOLEAN_FIELDS, *FINDING_EVIDENCE_FIELDS)


def validate_quantitative_input(data: Any) -> list[dict[str, Any]]:
    """Validate the minimal quantitative structure needed for enrichment.

    Args:
        data: Parsed intermediate JSON.

    Returns:
        The candidate stock list.

    Raises:
        SchemaValidationError: If metadata, candidates, or tickers are invalid.
    """

    if not isinstance(data, dict):
        raise SchemaValidationError("Quantitative input must be a JSON object")
    if not isinstance(data.get("Metadata"), dict):
        raise SchemaValidationError("Quantitative input is missing Metadata")
    stocks = data.get("Stocks")
    if not isinstance(stocks, list):
        raise SchemaValidationError("Quantitative input is missing a Stocks array")

    seen: set[str] = set()
    for stock in stocks:
        if not isinstance(stock, dict):
            raise SchemaValidationError("Each quantitative candidate must be an object")
        ticker = stock.get("Ticker")
        if not isinstance(ticker, str) or not ticker.strip():
            raise SchemaValidationError("Each quantitative candidate requires a ticker")
        if ticker in seen:
            raise SchemaValidationError(f"Duplicate candidate ticker: {ticker}")
        seen.add(ticker)
        if not isinstance(stock.get("Quantitative_Metrics"), dict):
            raise SchemaValidationError(
                f"Candidate {ticker} is missing Quantitative_Metrics"
            )
    return stocks


def build_enrichment_template(data: dict[str, Any]) -> dict[str, Any]:
    """Build conservative qualitative findings for every quantitative candidate.

    Args:
        data: Intermediate JSON data.

    Returns:
        A schema-compatible template with every qualitative check false.
    """

    stocks = validate_quantitative_input(data)
    return {
        "Schema_Version": data["Metadata"].get("Schema_Version", "2.1"),
        "Findings": [
            {
                "Ticker": stock["Ticker"],
                "N_New_Catalyst": False,
                "N_Catalyst_Details": "",
                "S_Float_Tightness": False,
                "S_Float_Details": "",
                "I_Institutional_Quality": False,
                "I_Institutional_Details": "",
            }
            for stock in stocks
        ],
    }


def validate_findings(
    data: Any,
    candidate_tickers: set[str],
) -> dict[str, dict[str, Any]]:
    """Validate findings and index them one-to-one by candidate ticker."""

    if not isinstance(data, dict):
        raise SchemaValidationError("Findings input must be a JSON object")
    schema_version = data.get("Schema_Version")
    if schema_version is not None and schema_version != "2.1":
        raise SchemaValidationError("Findings schema version must be 2.1")
    findings = data.get("Findings")
    if not isinstance(findings, list):
        raise SchemaValidationError("Findings input is missing a Findings array")

    indexed: dict[str, dict[str, Any]] = {}
    for finding in findings:
        if not isinstance(finding, dict):
            raise SchemaValidationError("Each finding must be an object")
        if set(finding) != set(FINDING_FIELDS):
            raise SchemaValidationError(
                "Finding fields must exactly match the documented template"
            )
        ticker = finding["Ticker"]
        if not isinstance(ticker, str) or not ticker.strip():
            raise SchemaValidationError("Each finding requires a valid ticker")
        if ticker not in candidate_tickers:
            raise SchemaValidationError(f"Unknown finding ticker: {ticker}")
        for field in FINDING_BOOLEAN_FIELDS:
            if not isinstance(finding[field], bool):
                raise SchemaValidationError(f"Finding field {field} must be boolean")
        for field in FINDING_EVIDENCE_FIELDS:
            if not isinstance(finding[field], str):
                raise SchemaValidationError(f"Finding field {field} must be text")
        for boolean_field, evidence_field in zip(
            FINDING_BOOLEAN_FIELDS,
            FINDING_EVIDENCE_FIELDS,
            strict=True,
        ):
            if finding[boolean_field] and not finding[evidence_field].strip():
                raise SchemaValidationError(
                    f"True {boolean_field} requires non-empty evidence or rationale"
                )
        if ticker in indexed:
            raise SchemaValidationError(
                f"Exactly one finding is required for each ticker; {ticker} repeats"
            )
        indexed[ticker] = finding

    missing = candidate_tickers.difference(indexed)
    if missing:
        raise SchemaValidationError(
            "Exactly one finding is required for each candidate; missing: "
            + ", ".join(sorted(missing))
        )
    return indexed


def merge_enrichment(
    quantitative_data: dict[str, Any],
    findings_data: dict[str, Any],
) -> dict[str, Any]:
    """Merge validated findings into a schema-compatible enriched artifact."""

    stocks = validate_quantitative_input(quantitative_data)
    candidate_tickers = {stock["Ticker"] for stock in stocks}
    findings = validate_findings(findings_data, candidate_tickers)
    enriched = copy.deepcopy(quantitative_data)
    for stock in enriched["Stocks"]:
        finding = findings[stock["Ticker"]]
        checks = {
            field: finding[field]
            for field in (*FINDING_BOOLEAN_FIELDS, *FINDING_EVIDENCE_FIELDS)
        }
        stock["AI_Qualitative_Checks_Pending"] = checks
        stock["AI_Qualitative_Checks"] = checks
    return enriched


def load_quantitative_input(path: Path) -> dict[str, Any]:
    """Load and validate an intermediate quantitative artifact."""

    if not path.is_file():
        raise ArtifactNotFoundError(f"Quantitative input not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaValidationError(
            f"Quantitative input is not valid JSON: {exc}"
        ) from exc
    validate_quantitative_input(data)
    return data


def prepare_enrichment_template(
    input_path: Path,
    *,
    output_dir: Path | str | None = None,
    project_root: Path | str | None = None,
) -> Path:
    """Generate and persist the qualitative findings template."""

    data = load_quantitative_input(input_path)
    template = build_enrichment_template(data)
    output_path = resolve_artifact_path(
        ENRICHMENT_TEMPLATE_ARTIFACT,
        output_dir=output_dir,
        project_root=project_root,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        temporary_path.write_text(
            json.dumps(template, indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(output_path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    logger.info(
        "Prepared enrichment template with %s candidates",
        len(template["Findings"]),
    )
    return output_path


def merge_enrichment_artifacts(
    quantitative_path: Path,
    findings_path: Path,
    *,
    output_dir: Path | str | None = None,
    project_root: Path | str | None = None,
) -> Path:
    """Load, merge, and persist enriched pipeline artifacts."""

    quantitative_data = load_quantitative_input(quantitative_path)
    if not findings_path.is_file():
        raise ArtifactNotFoundError(f"Findings input not found: {findings_path}")
    try:
        findings_data = json.loads(findings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaValidationError(
            f"Findings input is not valid JSON: {exc}"
        ) from exc

    enriched = merge_enrichment(quantitative_data, findings_data)
    output_path = resolve_artifact_path(
        ENRICHED_ARTIFACT,
        output_dir=output_dir,
        project_root=project_root,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        temporary_path.write_text(
            json.dumps(enriched, indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(output_path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    logger.info(
        "Merged qualitative findings for %s candidates",
        len(enriched["Stocks"]),
    )
    return output_path
