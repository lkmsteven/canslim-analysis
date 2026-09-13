"""Pure quantitative CANSLIM transformations."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from typing import Any

from canslim_analysis.errors import SchemaValidationError
from canslim_analysis.pipeline.config import PipelineConfig


logger = logging.getLogger(__name__)

CONFIRMED_UPTREND = "Confirmed Uptrend"
UNDER_PRESSURE = "Under Pressure"
DOWNTREND = "Downtrend"

MARKET_INDEXES = {
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
}


@dataclass(frozen=True)
class PriceBar:
    """One normalized historical OHLCV observation."""

    open: float
    close: float
    volume: float


@dataclass(frozen=True)
class QuantitativeSelectionResult:
    """The result of applying C, A, and L selection gates."""

    passed_stocks: list[dict[str, Any]]
    evaluated_count: int
    skipped_for_missing_fundamentals: int


def safe_float(value: Any) -> float | None:
    """Convert untrusted provider data to a finite float when possible.

    Args:
        value: Raw provider value.

    Returns:
        A finite float, or ``None`` when the value is absent or invalid.
    """

    try:
        if value is None or value != value:  # Covers NaN without pandas.
            return None
        converted = float(value)
    except (TypeError, ValueError):
        return None
    return converted if isfinite(converted) else None


def normalize_ratio(value: Any) -> float | None:
    """Normalize provider ownership ratios across known source representations.

    Args:
        value: Raw provider ratio, fraction, or percentage.

    Returns:
        A ratio between zero and one, or ``None`` when unavailable.
    """

    raw = safe_float(value)
    if raw is None:
        return None
    if raw < 0:
        return 0.0
    if raw <= 1.0:
        return raw
    if raw <= 2.0:
        return 1.0
    if raw <= 100.0:
        return min(raw / 100.0, 1.0)
    return 1.0


def pct_text(value: float | None) -> str:
    """Format a decimal fraction as user-facing percentage text."""

    return "N/A" if value is None else f"{value * 100:.1f}%"


def _index_is_in_uptrend(
    name: str,
    close_prices: Sequence[float] | None,
    config: PipelineConfig,
) -> bool:
    """Assess whether one market index satisfies the original trend shape.

    Args:
        name: Human-readable index name used in diagnostics.
        close_prices: Ordered historical Close values, oldest first.
        config: Runtime configuration containing the required lookback length.

    Returns:
        True only when price exceeds both moving averages and the short-term
        average exceeds the long-term average.
    """

    if close_prices is None or len(close_prices) < config.market_lookback_days:
        logger.warning("Insufficient market history for %s", name)
        return False

    try:
        configured_values = close_prices[-config.market_lookback_days :]
        lookback = [float(value) for value in configured_values]
    except (TypeError, ValueError) as exc:
        raise SchemaValidationError(
            f"Market history for {name} contains non-numeric Close values"
        ) from exc

    current_price = lookback[-1]
    short_average = sum(lookback[-50:]) / len(lookback[-50:])
    long_average = sum(lookback) / len(lookback)
    confirmed = (
        current_price > short_average
        and current_price > long_average
        and short_average > long_average
    )
    logger.info(
        "%s market assessment: price=%.2f, 50MA=%.2f, 200MA=%.2f, confirmed=%s",
        name,
        current_price,
        short_average,
        long_average,
        confirmed,
    )
    return confirmed


def assess_market_direction(
    market_history: Mapping[str, Sequence[float] | None],
    config: PipelineConfig,
) -> str:
    """Assess market direction from injected index histories.

    Args:
        market_history: Mapping of index names to ordered Close values.
        config: Runtime configuration containing the required lookback length.

    Returns:
        ``Confirmed Uptrend`` when both indexes confirm, ``Under Pressure`` when
        one confirms, and ``Downtrend`` otherwise.

    Raises:
        SchemaValidationError: If a supplied history contains non-numeric values.
    """

    logger.info("Assessing market direction...")
    confirming_indexes = sum(
        _index_is_in_uptrend(name, market_history.get(name), config)
        for name in MARKET_INDEXES
    )

    if confirming_indexes == len(MARKET_INDEXES):
        return CONFIRMED_UPTREND
    if confirming_indexes == 1:
        return UNDER_PRESSURE
    return DOWNTREND


def calculate_cagr(newest: float, oldest: float, periods: int) -> float | None:
    """Calculate compound annual growth rate.

    Args:
        newest: Most recent positive EPS value.
        oldest: Oldest positive EPS value.
        periods: Number of compounding periods between the values.

    Returns:
        The growth rate as a decimal fraction, or ``None`` when undefined.
    """

    if periods <= 0 or newest <= 0 or oldest <= 0:
        return None
    return (newest / oldest) ** (1 / periods) - 1


def calculate_quarterly_acceleration(
    eps_values: Sequence[Any],
) -> dict[str, Any]:
    """Calculate latest and prior year-over-year quarterly EPS acceleration.

    Args:
        eps_values: Provider-ordered EPS values, newest first.

    Returns:
        A dictionary containing supporting values and the acceleration verdict.
    """

    normalized = [safe_float(value) for value in eps_values]
    result: dict[str, Any] = {
        "is_accelerating": False,
        "latest_yoy_growth": None,
        "previous_yoy_growth": None,
        "eps_values": [value for value in normalized if value is not None],
    }

    if len(normalized) >= 5 and normalized[4] not in (None, 0):
        result["latest_yoy_growth"] = (
            normalized[0] - normalized[4]
        ) / abs(normalized[4])
    if len(normalized) >= 6 and normalized[5] not in (None, 0):
        result["previous_yoy_growth"] = (
            normalized[1] - normalized[5]
        ) / abs(normalized[5])

    latest = result["latest_yoy_growth"]
    previous = result["previous_yoy_growth"]
    result["is_accelerating"] = (
        latest is not None
        and previous is not None
        and latest > 0
        and previous > 0
        and latest > previous
    )
    return result


def analyze_supply_demand(
    bars: Sequence[PriceBar],
    config: PipelineConfig,
) -> dict[str, Any]:
    """Evaluate quantitative supply-and-demand evidence from price bars.

    Args:
        bars: Ordered historical bars, oldest first.
        config: Runtime configuration containing both S thresholds.

    Returns:
        A schema-compatible quantitative S evidence dictionary.
    """

    result: dict[str, Any] = {
        "S_Quant_Met": False,
        "S_Quant_Details": "",
        "S_Score": 0,
        "Today_Volume_Strong": False,
        "Volume_Skew_Positive": False,
        "Vol_Today": None,
        "Vol_50D_Avg": None,
    }
    if len(bars) < 60:
        result["S_Quant_Details"] = "Insufficient volume history"
        return result

    volume_today = safe_float(bars[-1].volume)
    volume_average = safe_float(sum(bar.volume for bar in bars[-50:]) / 50)
    result["Vol_Today"] = volume_today
    result["Vol_50D_Avg"] = volume_average

    if volume_today is not None and volume_average not in (None, 0):
        result["Today_Volume_Strong"] = volume_today >= (
            volume_average * config.min_volume_ratio
        )

    last_60 = bars[-60:]
    up_volumes = [bar.volume for bar in last_60 if bar.close > bar.open]
    down_volumes = [bar.volume for bar in last_60 if bar.close < bar.open]
    if up_volumes and down_volumes:
        average_up = safe_float(sum(up_volumes) / len(up_volumes))
        average_down = safe_float(sum(down_volumes) / len(down_volumes))
        if average_up is not None and average_down not in (None, 0):
            result["Volume_Skew_Positive"] = average_up >= (
                average_down * config.min_volume_skew
            )

    result["S_Score"] = int(result["Today_Volume_Strong"]) + int(
        result["Volume_Skew_Positive"]
    )
    result["S_Quant_Met"] = result["S_Score"] >= 2

    details: list[str] = []
    if result["Today_Volume_Strong"]:
        details.append(
            f"Today volume >= {config.min_volume_ratio:.1f}x 50-day average"
        )
    if result["Volume_Skew_Positive"]:
        details.append("Up-day volume skew positive")
    if not details:
        details.append("No strong quantitative S signal")
    result["S_Quant_Details"] = ", ".join(details)
    return result


def analyze_institutional_ownership(
    info: Mapping[str, Any],
    config: PipelineConfig,
) -> dict[str, Any]:
    """Normalize institutional ownership as reference evidence.

    Args:
        info: Raw provider fundamentals.
        config: Runtime configuration containing the ownership threshold.

    Returns:
        A schema-compatible institutional reference dictionary.
    """

    ownership = normalize_ratio(info.get("heldPercentInstitutions"))
    return {
        "I_Quant_Flag": ownership is not None
        and ownership >= config.min_institutional_ownership,
        "I_Quant_Details": "Institutional ownership unavailable"
        if ownership is None
        else f"{ownership * 100:.1f}% institutional ownership",
        "Institutional_Ownership": ownership,
    }


def analyze_new_highs(
    bars: Sequence[PriceBar],
    config: PipelineConfig,
) -> dict[str, Any]:
    """Evaluate technical N evidence from near-high and breakout behavior.

    Args:
        bars: Ordered historical bars, oldest first.
        config: Runtime configuration containing the near-high threshold.

    Returns:
        A schema-compatible technical N evidence dictionary.
    """

    result: dict[str, Any] = {
        "N_Technical_Met": False,
        "N_Technical_Details": "",
        "Near_52_Week_High": False,
        "Recent_Breakout": False,
        "Pct_From_High": None,
        "High_52_Week": None,
    }
    if len(bars) < 50:
        result["N_Technical_Details"] = "Insufficient price history"
        return result

    current_price = safe_float(bars[-1].close)
    high_52_week = safe_float(max(bar.close for bar in bars))
    if current_price is None or high_52_week in (None, 0):
        result["N_Technical_Details"] = "Unable to compute 52-week high"
        return result

    result["High_52_Week"] = high_52_week
    pct_from_high = (high_52_week - current_price) / high_52_week
    result["Pct_From_High"] = pct_from_high
    result["Near_52_Week_High"] = pct_from_high <= config.near_high_threshold
    if len(bars) >= 21:
        prior_high = safe_float(max(bar.close for bar in bars[-21:-1]))
        result["Recent_Breakout"] = (
            prior_high is not None and current_price > prior_high
        )

    result["N_Technical_Met"] = (
        result["Near_52_Week_High"] or result["Recent_Breakout"]
    )
    details = [
        f"Within {pct_from_high * 100:.1f}% of 52-week high"
        if result["Near_52_Week_High"]
        else f"{pct_from_high * 100:.1f}% below 52-week high"
    ]
    if result["Recent_Breakout"]:
        details.append("Recent breakout above prior 20-day high")
    result["N_Technical_Details"] = ", ".join(details)
    return result


def rank_percentiles(
    values: Sequence[float | None],
) -> list[float | None]:
    """Calculate average-tie percentile ranks using the original pandas formula.

    Args:
        values: One value per evaluated stock; missing values remain unranked.

    Returns:
        Percentile ranks scaled from 1 through 99, with one output per input.
    """

    valid_indices = [index for index, value in enumerate(values) if value is not None]
    ranked: list[float | None] = [None] * len(values)
    if not valid_indices:
        return ranked

    ordered = sorted(valid_indices, key=lambda index: values[index])
    position = 0
    while position < len(ordered):
        tied = [ordered[position]]
        while position + len(tied) < len(ordered) and values[
            ordered[position + len(tied)]
        ] == values[tied[0]]:
            tied.append(ordered[position + len(tied)])

        average_rank = (position + 1 + position + len(tied)) / 2
        percentile = max(1.0, min(99.0, average_rank / len(ordered) * 99.0))
        for index in tied:
            ranked[index] = round(percentile, 1)
        position += len(tied)
    return ranked


def default_ai_pending() -> dict[str, Any]:
    """Create the schema's pending qualitative checks."""

    return {
        "N_New_Catalyst": None,
        "N_Catalyst_Details": "",
        "S_Float_Tightness": None,
        "S_Float_Details": "",
        "I_Institutional_Quality": None,
        "I_Institutional_Details": "",
    }


def _c_details(quarterly_growth: float, accelerating: bool) -> str:
    """Build human-readable C evidence."""

    details = f"Q EPS Growth: {quarterly_growth * 100:.1f}%"
    return f"{details} (accelerating)" if accelerating else details


def build_stock_record(
    row: Mapping[str, Any],
    config: PipelineConfig,
) -> dict[str, Any]:
    """Build one schema 2.1 quantitative stock record.

    Args:
        row: Normalized fetched stock data, including an RS rating.
        config: Runtime configuration containing the C, A, and L thresholds.

    Returns:
        A canonical schema 2.1 stock dictionary with pending AI checks.
    """

    quarterly_growth = safe_float(row.get("Quarterly_EPS_Growth"))
    annual_growth = safe_float(row.get("Annual_EPS_Growth"))
    rs_rating = safe_float(row.get("RS_Rating")) or 0.0
    c_met = quarterly_growth is not None and quarterly_growth >= config.min_eps_growth
    a_met = (
        annual_growth is not None
        and annual_growth >= config.min_annual_eps_growth
    )
    l_met = rs_rating >= config.min_rs_rating

    quantitative: dict[str, Any] = {
        "C_Met": bool(c_met),
        "C_Details": _c_details(quarterly_growth, bool(row.get("EPS_Accelerating")))
        if quarterly_growth is not None
        else "Quarterly EPS growth unavailable",
        "Quarterly_EPS_Growth": quarterly_growth,
        "EPS_Accelerating": bool(row.get("EPS_Accelerating", False)),
        "A_Met": bool(a_met),
        "A_Details": f"Annual EPS CAGR: {annual_growth * 100:.1f}%"
        if annual_growth is not None
        else "Annual EPS growth unavailable",
        "Annual_EPS_Growth": annual_growth,
        "L_Met": bool(l_met),
        "RS_Rating": round(rs_rating, 1),
        "S_Quant_Met": bool(row.get("S_Quant_Met", False)),
        "S_Quant_Details": row.get("S_Quant_Details", ""),
        "S_Score": int(row.get("S_Score", 0)),
        "Today_Volume_Strong": bool(row.get("Today_Volume_Strong", False)),
        "Volume_Skew_Positive": bool(row.get("Volume_Skew_Positive", False)),
        "I_Quant_Flag": bool(row.get("I_Quant_Flag", False)),
        "I_Quant_Details": row.get("I_Quant_Details", ""),
        "N_Technical_Met": bool(row.get("N_Technical_Met", False)),
        "N_Technical_Details": row.get("N_Technical_Details", ""),
        "Near_52_Week_High": bool(row.get("Near_52_Week_High", False)),
        "Recent_Breakout": bool(row.get("Recent_Breakout", False)),
        "Pct_From_High": safe_float(row.get("Pct_From_High")),
        "Current_Price": safe_float(row.get("Current_Price")),
        "Float_Shares": safe_float(row.get("Float_Shares")),
        "Institutional_Ownership": normalize_ratio(
            row.get("Institutional_Ownership")
        ),
        "High_52_Week": safe_float(row.get("High_52_Week")),
        "Vol_Today": safe_float(row.get("Vol_Today")),
        "Vol_50D_Avg": safe_float(row.get("Vol_50D_Avg")),
        "Schema_Version": "2.1",
        "S_Met": bool(row.get("S_Quant_Met", False)),
        "S_Details": row.get("S_Quant_Details", ""),
        "I_Met": bool(row.get("I_Quant_Flag", False)),
        "I_Details": row.get("I_Quant_Details", ""),
        "N_Met": bool(row.get("N_Technical_Met", False)),
        "N_Details": row.get("N_Technical_Details", ""),
    }
    return {
        "Ticker": row["Ticker"],
        "Company_Name": row["Company_Name"],
        "Quantitative_Metrics": quantitative,
        "AI_Qualitative_Checks_Pending": default_ai_pending(),
    }


def select_quantitative_candidates(
    stock_rows: Sequence[Mapping[str, Any]],
    config: PipelineConfig,
) -> QuantitativeSelectionResult:
    """Rank fetched rows and select stocks passing all C, A, and L gates.

    Args:
        stock_rows: Normalized fetched stock rows.
        config: Runtime configuration containing all quantitative thresholds.

    Returns:
        Passed schema records, evaluation count, and missing-fundamental count.
    """

    return_values: list[float | None] = [
        safe_float(row.get("Return_1Y")) for row in stock_rows
    ]
    rs_ratings = rank_percentiles(return_values)
    evaluated: list[dict[str, Any]] = []
    for row, rs_rating in zip(stock_rows, rs_ratings, strict=True):
        enriched = dict(row)
        enriched["RS_Rating"] = rs_rating or 0.0
        evaluated.append(enriched)

    passed: list[dict[str, Any]] = []
    skipped = 0
    for row in evaluated:
        quarterly_growth = safe_float(row.get("Quarterly_EPS_Growth"))
        annual_growth = safe_float(row.get("Annual_EPS_Growth"))
        rs_rating = safe_float(row.get("RS_Rating")) or 0.0
        if quarterly_growth is None or annual_growth is None:
            skipped += 1
            continue
        if (
            quarterly_growth >= config.min_eps_growth
            and annual_growth >= config.min_annual_eps_growth
            and rs_rating >= config.min_rs_rating
        ):
            passed.append(build_stock_record(row, config))

    passed.sort(
        key=lambda stock: stock["Quantitative_Metrics"]["RS_Rating"],
        reverse=True,
    )
    return QuantitativeSelectionResult(
        passed_stocks=passed,
        evaluated_count=len(stock_rows),
        skipped_for_missing_fundamentals=skipped,
    )
