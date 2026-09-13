"""Tests for pure quantitative CANSLIM transformations."""

from __future__ import annotations

import pytest

from canslim_analysis.pipeline.config import PipelineConfig
from canslim_analysis.pipeline.quantitative import (
    PriceBar,
    analyze_institutional_ownership,
    analyze_new_highs,
    analyze_supply_demand,
    build_stock_record,
    calculate_cagr,
    calculate_quarterly_acceleration,
    normalize_ratio,
    pct_text,
    rank_percentiles,
    safe_float,
    select_quantitative_candidates,
)


CONFIG = PipelineConfig()


def bar(open_price: float, close_price: float, volume: float) -> PriceBar:
    """Construct one deterministic price bar."""

    return PriceBar(open=open_price, close=close_price, volume=volume)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, None), ("bad", None), (float("nan"), None), ("12.5", 12.5), (3, 3.0)],
)
def test_safe_float_normalizes_untrusted_values(
    raw: object, expected: float | None
) -> None:
    """Financial values may be missing, malformed, numeric, or string-like."""

    assert safe_float(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(-1, 0.0), (0.4, 0.4), (1.2, 1.0), (55, 0.55), (150, 1.0), (None, None)],
)
def test_normalize_ratio_preserves_original_source_ranges(
    raw: float | None, expected: float | None
) -> None:
    """Ownership values from different provider scales normalize defensively."""

    assert normalize_ratio(raw) == expected


def test_percentage_text_handles_missing_values() -> None:
    """Display strings distinguish missing values from zero."""

    assert pct_text(0.25) == "25.0%"
    assert pct_text(None) == "N/A"


@pytest.mark.parametrize(
    ("newest", "oldest", "periods", "expected"),
    [(2.0, 1.0, 4, 2.0 ** 0.25 - 1), (0.0, 1.0, 4, None), (2.0, 1.0, 0, None)],
)
def test_calculate_cagr_rejects_invalid_compounding_inputs(
    newest: float, oldest: float, periods: int, expected: float | None
) -> None:
    """CAGR is undefined for nonpositive inputs or periods."""

    assert calculate_cagr(newest, oldest, periods) == pytest.approx(expected)


def test_quarterly_acceleration_requires_two_positive_increases() -> None:
    """Acceleration follows the original year-over-year ordering convention."""

    result = calculate_quarterly_acceleration([5.0, 4.0, 3.0, 2.0, 1.0, 0.8])

    assert result["latest_yoy_growth"] == pytest.approx(4.0)
    assert result["previous_yoy_growth"] == pytest.approx(4.0)
    assert result["is_accelerating"] is False


def test_supply_demand_requires_both_volume_conditions() -> None:
    """Quantitative S is true only when volume strength and skew both pass."""

    bars = [bar(100, 101, 1_000) for _ in range(30)] + [
        bar(101, 100, 400) for _ in range(29)
    ] + [bar(100, 101, 1_600)]

    result = analyze_supply_demand(bars, CONFIG)

    assert result["Today_Volume_Strong"] is True
    assert result["Volume_Skew_Positive"] is True
    assert result["S_Score"] == 2
    assert result["S_Quant_Met"] is True


def test_supply_demand_insufficient_history_is_not_true() -> None:
    """Short volume history remains supporting evidence, never a confirmed pass."""

    result = analyze_supply_demand([bar(1, 1, 1) for _ in range(59)], CONFIG)

    assert result["S_Quant_Met"] is False
    assert result["S_Quant_Details"] == "Insufficient volume history"


def test_new_highs_identifies_near_high_and_breakout() -> None:
    """Technical N remains separate from AI catalyst confirmation."""

    bars = [bar(100, 100 + index, 1_000) for index in range(50)]
    bars[-1] = bar(199, 199.5, 1_000)

    result = analyze_new_highs(bars, CONFIG)

    assert result["Near_52_Week_High"] is True
    assert result["Recent_Breakout"] is True
    assert result["N_Technical_Met"] is True
    assert result["Pct_From_High"] == 0.0


def test_institutional_analysis_records_reference_evidence_only() -> None:
    """Institutional ownership is context and does not score final I."""

    result = analyze_institutional_ownership(
        {"heldPercentInstitutions": 0.96893},
        CONFIG,
    )

    assert result["Institutional_Ownership"] == pytest.approx(0.96893)
    assert result["I_Quant_Flag"] is True
    assert result["I_Quant_Details"] == "96.9% institutional ownership"


def test_rank_percentiles_uses_average_tie_ranks() -> None:
    """Relative-strength ranks match percentile ranking with tied averages."""

    assert rank_percentiles([1.0, 2.0, 2.0, 3.0]) == [24.8, 61.9, 61.9, 99.0]


def _stock_row(ticker: str, return_1y: float) -> dict[str, object]:
    """Create a minimally valid fetched stock row."""

    return {
        "Ticker": ticker,
        "Company_Name": f"{ticker} Company",
        "Current_Price": 100.0,
        "Return_1Y": return_1y,
        "Quarterly_EPS_Growth": 0.30,
        "EPS_Accelerating": True,
        "Annual_EPS_Growth": 0.40,
        "Float_Shares": 50_000_000.0,
        "Institutional_Ownership": 0.7,
        "RS_Rating": 90.0,
        "S_Quant_Met": True,
        "S_Quant_Details": "Today volume >= 1.5x 50-day average",
        "S_Score": 2,
        "Today_Volume_Strong": True,
        "Volume_Skew_Positive": True,
        "N_Technical_Met": True,
        "N_Technical_Details": "Within 2.0% of 52-week high",
        "Near_52_Week_High": True,
        "Recent_Breakout": False,
        "Pct_From_High": 0.02,
        "High_52_Week": 102.0,
    }


def test_build_stock_record_preserves_schema_and_scoring_booleans() -> None:
    """Schema 2.1 records preserve quantitative fields and pending AI checks."""

    record = build_stock_record(_stock_row("EXAMPLE", 0.35), CONFIG)
    metrics = record["Quantitative_Metrics"]

    assert metrics["C_Met"] is True
    assert metrics["A_Met"] is True
    assert metrics["L_Met"] is True
    assert metrics["C_Details"] == "Q EPS Growth: 30.0% (accelerating)"
    assert metrics["Schema_Version"] == "2.1"
    assert record["AI_Qualitative_Checks_Pending"]["N_New_Catalyst"] is None


def test_select_candidates_rejects_missing_and_threshold_failures() -> None:
    """Candidates must pass fundamental presence plus C, A, and L thresholds."""

    weak = _stock_row("WEAK", 0.10)
    missing = _stock_row("MISSING", 0.90)
    missing["Annual_EPS_Growth"] = None
    strong = _stock_row("STRONG", 0.90)
    strong["Quarterly_EPS_Growth"] = 0.20

    result = select_quantitative_candidates(
        [_stock_row("MID", 0.95), weak, missing, strong],
        CONFIG,
    )

    assert result.evaluated_count == 4
    assert result.skipped_for_missing_fundamentals == 1
    assert [stock["Ticker"] for stock in result.passed_stocks] == ["MID"]
    assert result.passed_stocks[0]["Quantitative_Metrics"]["RS_Rating"] == 99.0
