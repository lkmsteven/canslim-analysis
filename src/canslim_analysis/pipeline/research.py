"""Artifact-driven, conservatively validated qualitative research."""

from __future__ import annotations

import json
import logging
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from canslim_analysis.errors import ArtifactNotFoundError, SchemaValidationError
from canslim_analysis.pipeline.enrichment import (
    FINDING_BOOLEAN_FIELDS,
    FINDING_EVIDENCE_FIELDS,
    validate_quantitative_input,
)


logger = logging.getLogger(__name__)

RESEARCH_SCHEMA_VERSION = "1.0"
FINDINGS_SCHEMA_VERSION = "2.1"
QUALITATIVE_FIELDS = FINDING_BOOLEAN_FIELDS
EVIDENCE_FIELDS = {
    "N_New_Catalyst": "N_Catalyst_Details",
    "S_Float_Tightness": "S_Float_Details",
    "I_Institutional_Quality": "I_Institutional_Details",
}
POSITIVE_EVIDENCE_FIELDS = (
    "Issuer",
    "Share_Class",
    "Source",
    "Evidence_Date",
    "Citation",
    "Summary",
    "Criterion_Context",
)
BASE_EVIDENCE_FIELDS = ("Ticker", "Field", "Supported", "Summary")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
NEGATIVE_EVIDENCE_PHRASES = (
    "ambiguous",
    "contradictory",
    "low-quality",
    "tangential",
    "search snippet",
    "secondary offering",
    "lockup expiration",
    "dilution",
    "unexecuted",
)


def parse_iso_date(value: Any, field: str) -> date:
    """Parse and return a strict ISO calendar date."""

    if not isinstance(value, str) or not ISO_DATE.fullmatch(value):
        raise SchemaValidationError(f"{field} must be a YYYY-MM-DD date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SchemaValidationError(f"{field} must be a valid calendar date") from exc


def candidate_identity(stock: dict[str, Any]) -> str:
    """Return the occurrence key for one candidate without collapsing rows."""

    candidate_id = stock.get("Candidate_ID")
    if candidate_id is not None:
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise SchemaValidationError("Candidate_ID must be non-empty text")
        return candidate_id
    ticker = stock.get("Ticker")
    if not isinstance(ticker, str) or not ticker.strip():
        raise SchemaValidationError("Candidate requires a ticker")
    return ticker


def validate_candidate_occurrences(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate candidates and metadata as a complete passing-candidate set.

    Args:
        data: Parsed quantitative intermediate JSON.

    Returns:
        Candidate occurrences in artifact order.

    Raises:
        SchemaValidationError: If the passing set, date, or occurrence identity
            cannot be determined safely.
    """

    stocks = validate_quantitative_input(data)
    metadata = data["Metadata"]
    declared_count = metadata.get("Stocks_Passed_To_AI")
    if not isinstance(declared_count, int) or isinstance(declared_count, bool):
        raise SchemaValidationError("Metadata.Stocks_Passed_To_AI must be an integer")
    if declared_count != len(stocks):
        raise SchemaValidationError(
            "Metadata.Stocks_Passed_To_AI must equal the complete Stocks array"
        )
    if not stocks:
        raise SchemaValidationError("Intermediate artifact contains no passing candidates")
    parsed_date = parse_iso_date(metadata.get("Date_Run"), "Metadata.Date_Run")
    if parsed_date > date.today():
        raise SchemaValidationError("Metadata.Date_Run cannot be later than the current date")

    identities = [candidate_identity(stock) for stock in stocks]
    if len(identities) != len(set(identities)):
        raise SchemaValidationError("Candidate occurrence identity is not unique")
    ticker_counts: dict[str, int] = {}
    for stock in stocks:
        ticker = str(stock["Ticker"])
        ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1
    for stock in stocks:
        ticker = str(stock["Ticker"])
        has_id = "Candidate_ID" in stock
        if ticker_counts[ticker] > 1 and not has_id:
            raise SchemaValidationError(
                f"Duplicate ticker {ticker} requires a unique Candidate_ID"
            )
        # Candidate_ID is intentionally any stable non-empty string accepted by
        # the source system; no source-system-specific format is invented here.
    return stocks


def _validate_positive_evidence(
    record: dict[str, Any],
    field: str,
    analysis_date: date,
) -> None:
    """Validate one record that claims direct positive support."""

    expected = {*BASE_EVIDENCE_FIELDS, *POSITIVE_EVIDENCE_FIELDS}
    if "Candidate_ID" in record:
        expected.add("Candidate_ID")
    if set(record) != expected:
        raise SchemaValidationError(
            f"Positive {field} evidence fields must exactly match {sorted(expected)}"
        )
    if "Candidate_ID" in record and (
        not isinstance(record["Candidate_ID"], str) or not record["Candidate_ID"].strip()
    ):
        raise SchemaValidationError(
            f"Positive {field} evidence requires Candidate_ID to be non-empty text"
        )
    for field_name in POSITIVE_EVIDENCE_FIELDS:
        value = record.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise SchemaValidationError(
                f"Positive {field} evidence requires {field_name.casefold()}"
            )
    evidence_date = parse_iso_date(record["Evidence_Date"], "Evidence_Date")
    if evidence_date > analysis_date:
        raise SchemaValidationError(
            f"Positive {field} evidence is dated after analysis date"
        )
    citation = record["Citation"]
    parsed = urlsplit(citation)
    is_url = parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    is_sec_accession = bool(re.fullmatch(r"SEC accession [-\w.]+", citation, re.IGNORECASE))
    if not is_url and not is_sec_accession:
        raise SchemaValidationError(
            f"Positive {field} evidence requires a retrievable citation"
        )
    evidence_text = " ".join(
        (record["Summary"], record["Criterion_Context"])
    ).casefold()
    if any(phrase in evidence_text for phrase in NEGATIVE_EVIDENCE_PHRASES):
        raise SchemaValidationError(
            f"Positive {field} evidence is not direct positive evidence"
        )


def _evidence_identity_matches(
    record: dict[str, Any],
    stock: dict[str, Any],
) -> bool:
    """Return whether an evidence record targets this exact occurrence."""

    if record.get("Ticker") != stock["Ticker"]:
        return False
    expected_id = stock.get("Candidate_ID")
    actual_id = record.get("Candidate_ID")
    return actual_id == expected_id


def _validate_evidence_pack(
    pack: Any,
    stocks: list[dict[str, Any]],
    analysis_date: date,
) -> list[dict[str, Any]]:
    """Validate complete one-to-one evidence for candidate occurrences."""

    if not isinstance(pack, dict):
        raise SchemaValidationError("Research evidence must be a JSON object")
    if pack.get("Schema_Version") != RESEARCH_SCHEMA_VERSION:
        raise SchemaValidationError("Research evidence schema version must be 1.0")
    if parse_iso_date(pack.get("Analysis_Date"), "Research Analysis_Date") != analysis_date:
        raise SchemaValidationError("Research evidence Analysis_Date must match the intermediate artifact")
    records = pack.get("Evidence")
    if not isinstance(records, list):
        raise SchemaValidationError("Research evidence requires an Evidence array")

    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(records, start=1):
        if not isinstance(raw, dict):
            raise SchemaValidationError(f"Evidence record #{index} must be an object")
        record = dict(raw)
        supported = record.get("Supported")
        if not isinstance(supported, bool):
            raise SchemaValidationError(f"Evidence record #{index} requires boolean Supported")
        field = record.get("Field")
        if field not in QUALITATIVE_FIELDS:
            raise SchemaValidationError(f"Evidence record #{index} has an unknown qualitative field")
        if not isinstance(record.get("Ticker"), str) or not record["Ticker"].strip():
            raise SchemaValidationError(f"Evidence record #{index} requires a ticker")
        if not isinstance(record.get("Summary"), str) or not record["Summary"].strip():
            raise SchemaValidationError(f"Evidence record #{index} requires a summary or reason")
        if supported:
            _validate_positive_evidence(record, field, analysis_date)
        else:
            expected = set(BASE_EVIDENCE_FIELDS)
            if "Candidate_ID" in record:
                expected.add("Candidate_ID")
            if set(record) != expected:
                raise SchemaValidationError(
                    f"Negative {field} evidence fields must exactly match {sorted(expected)}"
                )
        normalized.append(record)

    expected_occurrences = [
        (candidate_identity(stock), str(stock["Ticker"]), field)
        for stock in stocks
        for field in QUALITATIVE_FIELDS
    ]
    actual_occurrences: list[tuple[str, str, str]] = []
    stocks_by_identity = {candidate_identity(stock): stock for stock in stocks}
    for record in normalized:
        identity = record.get("Candidate_ID") or record.get("Ticker")
        stock = stocks_by_identity.get(identity)
        if stock is None or not _evidence_identity_matches(record, stock):
            raise SchemaValidationError(
                f"Evidence for {record.get('Ticker')} does not identify a candidate occurrence"
            )
        actual_occurrences.append((identity, str(record["Ticker"]), str(record["Field"])))
    missing = set(expected_occurrences).difference(actual_occurrences)
    if missing:
        raise SchemaValidationError(
            f"Research evidence is incomplete; missing {len(missing)} candidate-field records"
        )
    if len(actual_occurrences) != len(set(actual_occurrences)):
        raise SchemaValidationError("Research evidence contains duplicate candidate-field records")
    if len(actual_occurrences) != len(expected_occurrences):
        raise SchemaValidationError("Research evidence contains records outside the candidate set")
    return normalized


def _details(record: dict[str, Any], field: str) -> str:
    """Serialize one evidence decision into the existing free-text field."""

    if not record["Supported"]:
        return f"Not verified: {record['Summary']}"
    return (
        f"Verified: {record['Summary']} Source: {record['Source']}; "
        f"published/filed {record['Evidence_Date']}; citation {record['Citation']}. "
        f"Issuer/share class: {record['Issuer']} / {record['Share_Class']}. "
        f"Criterion context: {record['Criterion_Context']}"
    )


def verified_research_findings(
    quantitative_data: dict[str, Any],
    evidence_data: Any,
) -> dict[str, Any]:
    """Convert validated evidence into existing enrichment findings.

    Args:
        quantitative_data: Parsed intermediate quantitative artifact.
        evidence_data: Parsed research evidence artifact.

    Returns:
        Findings in the existing schema 2.1 shape, with additive Candidate_ID
        only when required to preserve duplicate occurrences.

    Raises:
        SchemaValidationError: If input, identity, date, evidence, or output
            validation fails.
    """

    stocks = validate_candidate_occurrences(quantitative_data)
    analysis_date = parse_iso_date(
        quantitative_data["Metadata"]["Date_Run"],
        "Metadata.Date_Run",
    )
    records = _validate_evidence_pack(evidence_data, stocks, analysis_date)
    indexed = {
        (
            record.get("Candidate_ID") or record.get("Ticker"),
            record.get("Field"),
        ): record
        for record in records
    }
    findings: list[dict[str, Any]] = []
    for stock in stocks:
        finding: dict[str, Any] = {"Ticker": stock["Ticker"]}
        if "Candidate_ID" in stock:
            finding["Candidate_ID"] = stock["Candidate_ID"]
        for field in QUALITATIVE_FIELDS:
            record = indexed[(candidate_identity(stock), field)]
            finding[field] = bool(record["Supported"])
            finding[EVIDENCE_FIELDS[field]] = _details(record, field)
        if set(finding) not in (
            {"Ticker", *FINDING_BOOLEAN_FIELDS, *FINDING_EVIDENCE_FIELDS},
            {
                "Ticker",
                "Candidate_ID",
                *FINDING_BOOLEAN_FIELDS,
                *FINDING_EVIDENCE_FIELDS,
            },
        ):
            raise SchemaValidationError("Generated finding does not match the documented schema")
        findings.append(finding)
    result = {"Schema_Version": FINDINGS_SCHEMA_VERSION, "Findings": findings}
    _validate_generated_findings(result, stocks)
    return result


def _validate_generated_findings(
    findings: dict[str, Any],
    stocks: list[dict[str, Any]],
) -> None:
    """Guard the output before it is allowed to touch the filesystem."""

    expected_keys = [candidate_identity(stock) for stock in stocks]
    actual_keys = [
        candidate.get("Candidate_ID") or candidate.get("Ticker")
        for candidate in findings["Findings"]
    ]
    if actual_keys != expected_keys:
        raise SchemaValidationError("Generated findings do not preserve candidate occurrences")
    for finding in findings["Findings"]:
        for field in FINDING_BOOLEAN_FIELDS:
            if not isinstance(finding[field], bool):
                raise SchemaValidationError(f"Generated {field} is not boolean")
        for field in FINDING_EVIDENCE_FIELDS:
            if not isinstance(finding[field], str) or not finding[field].strip():
                raise SchemaValidationError(f"Generated {field} is not meaningful text")


def load_research_input(path: Path, label: str) -> dict[str, Any]:
    """Load one UTF-8 JSON research input with actionable failure behavior."""

    if not path.is_file():
        raise ArtifactNotFoundError(f"{label} input not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaValidationError(f"{label} input is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SchemaValidationError(f"{label} input must be a JSON object")
    return data


def write_research_findings(
    findings: dict[str, Any],
    output_path: Path,
) -> Path:
    """Atomically persist validated research findings.

    The output is created only after in-memory validation has succeeded. A
    failed write removes its temporary file and never leaves partial JSON.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(f".{output_path.name}.tmp")
    try:
        temporary_path.write_text(
            json.dumps(findings, indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(output_path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    return output_path
