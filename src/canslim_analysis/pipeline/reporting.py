"""Final CANSLIM report assembly and persistence."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from canslim_analysis.errors import ArtifactNotFoundError, SchemaValidationError
from canslim_analysis.pipeline.scoring import (
    calculate_score,
    determine_grade,
    normalize_stock,
    validate_enriched_dataset,
)
from canslim_analysis.paths import FINAL_REPORT_ARTIFACT, resolve_artifact_path


logger = logging.getLogger(__name__)


def build_final_report(data: dict[str, Any]) -> dict[str, Any]:
    """Build the canonical final report from enriched pipeline data.

    Args:
        data: Parsed enriched JSON data.

    Returns:
        A schema 2.1 final report dictionary.
    """

    stocks = validate_enriched_dataset(data)
    market_direction = data["Metadata"].get("Market_Direction_M", "Unknown")
    market_is_uptrend = market_direction == "Confirmed Uptrend"
    processed: list[dict[str, Any]] = []

    for raw_stock in stocks:
        stock = normalize_stock(raw_stock)
        score, met, missed, details = calculate_score(stock, market_is_uptrend)
        quant = stock["Quantitative_Metrics"]
        ai = stock["AI_Qualitative_Checks"]
        processed.append(
            {
                "Ticker": stock["Ticker"],
                "Company_Name": stock["Company_Name"],
                "Final_Score": score,
                "Grade": determine_grade(score),
                "Met_Criteria": met,
                "Missed_Criteria": missed,
                "AI_Catalyst_Note": ai.get("N_Catalyst_Details")
                or quant.get("N_Technical_Details")
                or "No catalyst analysis available.",
                "Metrics": {
                    "RS_Rating": quant.get("RS_Rating", 0.0),
                    "Current_Price": quant.get("Current_Price", 0.0),
                    "Quarterly_EPS_Growth": quant.get("Quarterly_EPS_Growth"),
                    "Annual_EPS_Growth": quant.get("Annual_EPS_Growth"),
                    "EPS_Accelerating": bool(quant.get("EPS_Accelerating", False)),
                    "S_Score": quant.get("S_Score", 0),
                    "S_Quant_Met": bool(quant.get("S_Quant_Met", False)),
                    "S_Float_Tightness": bool(ai.get("S_Float_Tightness", False)),
                    "N_Technical_Met": bool(quant.get("N_Technical_Met", False)),
                    "Float_Shares": quant.get("Float_Shares"),
                    "Institutional_Ownership": quant.get("Institutional_Ownership"),
                },
                "Details": details,
            }
        )

    processed.sort(
        key=lambda stock: (stock["Final_Score"], stock["Metrics"]["RS_Rating"]),
        reverse=True,
    )
    score_distribution: dict[str, int] = {}
    for stock in processed:
        key = str(stock["Final_Score"])
        score_distribution[key] = score_distribution.get(key, 0) + 1

    timestamp = datetime.now()
    return {
        "Schema_Version": "2.1",
        "Report_Date": timestamp.strftime("%Y-%m-%d"),
        "Report_Time": timestamp.strftime("%H:%M:%S"),
        "Market_Environment": market_direction,
        "M_Criterion_Met": market_is_uptrend,
        "Total_Candidates_Evaluated": len(processed),
        "Score_Distribution": score_distribution,
        "Top_Candidates": processed,
        "Fixes_Applied": data["Metadata"].get("Fixes_Applied", []),
    }


def load_enriched_input(path: Path) -> dict[str, Any]:
    """Load and validate enriched input from a project artifact."""

    if not path.is_file():
        raise ArtifactNotFoundError(f"Enriched input not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaValidationError(f"Enriched input is not valid JSON: {exc}") from exc
    validate_enriched_dataset(data)
    return data


def finalize_report(
    input_path: Path,
    *,
    output_dir: Path | str | None = None,
    project_root: Path | str | None = None,
) -> Path:
    """Build and atomically persist the final report artifact."""

    report = build_final_report(load_enriched_input(input_path))
    output_path = resolve_artifact_path(
        FINAL_REPORT_ARTIFACT,
        output_dir=output_dir,
        project_root=project_root,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        temporary_path.write_text(
            json.dumps(report, indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(output_path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    logger.info(
        "Generated final report with %s candidates",
        report["Total_Candidates_Evaluated"],
    )
    return output_path
