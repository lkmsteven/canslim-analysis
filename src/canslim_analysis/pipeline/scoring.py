"""Enriched-dataset validation and CANSLIM score calculation."""

from __future__ import annotations

from typing import Any

from canslim_analysis.errors import SchemaValidationError


SCHEMA_VERSION = "2.1"
CRITERION_ORDER = ("C", "A", "N", "S", "L", "I", "M")


def validate_enriched_dataset(data: Any) -> list[dict[str, Any]]:
    """Validate the enriched dataset and return its candidate list.

    Args:
        data: Parsed enriched JSON.

    Returns:
        Candidate dictionaries in input order.

    Raises:
        SchemaValidationError: If required structure or uniqueness is invalid.
    """

    if not isinstance(data, dict):
        raise SchemaValidationError("Enriched input must be a JSON object")
    if not isinstance(data.get("Metadata"), dict):
        raise SchemaValidationError("Enriched input is missing Metadata")
    stocks = data.get("Stocks")
    if not isinstance(stocks, list):
        raise SchemaValidationError("Enriched input is missing a Stocks array")

    seen: set[str] = set()
    for index, stock in enumerate(stocks, start=1):
        if not isinstance(stock, dict):
            raise SchemaValidationError(f"Stock #{index} must be an object")
        ticker = stock.get("Ticker")
        company = stock.get("Company_Name")
        if not isinstance(ticker, str) or not ticker.strip():
            raise SchemaValidationError(f"Stock #{index} requires a ticker")
        if not isinstance(company, str) or not company.strip():
            raise SchemaValidationError(f"Stock {ticker} requires a company name")
        if not isinstance(stock.get("Quantitative_Metrics"), dict):
            raise SchemaValidationError(
                f"Stock {ticker} requires Quantitative_Metrics"
            )
        if ticker in seen:
            raise SchemaValidationError(f"Duplicate enriched ticker: {ticker}")
        seen.add(ticker)
    return stocks


def _normalize_quantitative_metrics(raw: Any) -> dict[str, Any]:
    """Normalize quantitative fields and legacy aliases."""

    quant = dict(raw or {})
    for field in ("C_Met", "A_Met", "L_Met", "EPS_Accelerating"):
        quant.setdefault(field, False)
    for field in ("C_Details", "A_Details"):
        quant.setdefault(field, "")
    quant.setdefault("Quarterly_EPS_Growth", None)
    quant.setdefault("Annual_EPS_Growth", None)
    quant.setdefault("RS_Rating", 0.0)
    quant.setdefault("Current_Price", 0.0)

    aliases = {
        "S_Quant_Met": "S_Met",
        "S_Quant_Details": "S_Details",
        "I_Quant_Flag": "I_Met",
        "I_Quant_Details": "I_Details",
        "N_Technical_Met": "N_Met",
        "N_Technical_Details": "N_Details",
    }
    for canonical, alias in aliases.items():
        if canonical not in quant:
            quant[canonical] = quant.get(alias, False if canonical.endswith("Met") or canonical.endswith("Flag") else "")

    quant.setdefault("S_Score", 0)
    quant.setdefault("Today_Volume_Strong", False)
    quant.setdefault("Volume_Skew_Positive", False)
    quant.setdefault("Near_52_Week_High", False)
    quant.setdefault("Recent_Breakout", False)
    quant.setdefault("Pct_From_High", None)
    quant.setdefault("Float_Shares", None)
    quant.setdefault("Institutional_Ownership", None)
    quant.setdefault("High_52_Week", None)
    quant.setdefault("Vol_Today", None)
    quant.setdefault("Vol_50D_Avg", None)
    quant.setdefault("Schema_Version", SCHEMA_VERSION)
    return quant


def _merge_ai_checks(stock: dict[str, Any]) -> dict[str, Any]:
    """Merge pending defaults and verified findings, with findings winning."""

    pending = stock.get("AI_Qualitative_Checks_Pending") or {}
    verified = stock.get("AI_Qualitative_Checks") or {}
    merged = {
        "N_New_Catalyst": False,
        "N_Catalyst_Details": "",
        "S_Float_Tightness": False,
        "S_Float_Details": "",
        "I_Institutional_Quality": False,
        "I_Institutional_Details": "",
    }
    merged.update(pending)
    merged.update(verified)
    return merged


def normalize_stock(stock: dict[str, Any]) -> dict[str, Any]:
    """Normalize one enriched stock into the final-processing shape."""

    return {
        "Ticker": stock.get("Ticker", ""),
        "Company_Name": stock.get("Company_Name", ""),
        "Quantitative_Metrics": _normalize_quantitative_metrics(
            stock.get("Quantitative_Metrics")
        ),
        "AI_Qualitative_Checks_Pending": stock.get(
            "AI_Qualitative_Checks_Pending"
        )
        or {},
        "AI_Qualitative_Checks": _merge_ai_checks(stock),
    }


def calculate_score(
    stock: dict[str, Any],
    market_is_uptrend: bool,
) -> tuple[int, list[str], list[str], dict[str, Any]]:
    """Calculate the seven-criterion CANSLIM score and supporting details."""

    quant = stock["Quantitative_Metrics"]
    ai = stock["AI_Qualitative_Checks"]
    evaluations = {
        "C": bool(quant.get("C_Met", False)),
        "A": bool(quant.get("A_Met", False)),
        "N": bool(ai.get("N_New_Catalyst", False)),
        "S": bool(quant.get("S_Quant_Met", False))
        and bool(ai.get("S_Float_Tightness", False)),
        "L": bool(quant.get("L_Met", False)),
        "I": bool(ai.get("I_Institutional_Quality", False)),
        "M": bool(market_is_uptrend),
    }
    met = [name for name in CRITERION_ORDER if evaluations[name]]
    missed = [name for name in CRITERION_ORDER if not evaluations[name]]
    details = {
        "C_Details": quant.get("C_Details", ""),
        "A_Details": quant.get("A_Details", ""),
        "N_Catalyst_Details": ai.get("N_Catalyst_Details", ""),
        "N_Technical_Met": bool(quant.get("N_Technical_Met", False)),
        "N_Technical_Details": quant.get("N_Technical_Details", ""),
        "S_Quant_Met": bool(quant.get("S_Quant_Met", False)),
        "S_Quant_Details": quant.get("S_Quant_Details", ""),
        "S_Float_Tightness": bool(ai.get("S_Float_Tightness", False)),
        "S_Float_Details": ai.get("S_Float_Details", ""),
        "I_Quant_Flag": bool(quant.get("I_Quant_Flag", False)),
        "I_Quant_Details": quant.get("I_Quant_Details", ""),
        "I_Institutional_Quality": bool(ai.get("I_Institutional_Quality", False)),
        "I_Institutional_Details": ai.get("I_Institutional_Details", ""),
        "Quarterly_EPS_Growth": quant.get("Quarterly_EPS_Growth"),
        "Annual_EPS_Growth": quant.get("Annual_EPS_Growth"),
        "EPS_Accelerating": bool(quant.get("EPS_Accelerating", False)),
        "RS_Rating": quant.get("RS_Rating", 0.0),
        "Current_Price": quant.get("Current_Price", 0.0),
        "S_Score": quant.get("S_Score", 0),
        "Float_Shares": quant.get("Float_Shares"),
        "Institutional_Ownership": quant.get("Institutional_Ownership"),
        "Market_In_Confirmed_Uptrend": bool(market_is_uptrend),
    }
    return len(met), met, missed, details


def determine_grade(score: int) -> str:
    """Map a CANSLIM score to its documented final-report grade."""

    grades = {
        7: "A+",
        6: "A",
        5: "A-",
        4: "B+",
        3: "B",
        2: "C",
    }
    return grades.get(score, "D")
