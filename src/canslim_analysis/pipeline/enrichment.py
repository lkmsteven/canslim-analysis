"""Qualitative enrichment template creation and validation."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from canslim_analysis.errors import ArtifactNotFoundError, SchemaValidationError
from canslim_analysis.paths import ENRICHMENT_TEMPLATE_ARTIFACT, resolve_artifact_path


logger = logging.getLogger(__name__)


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
