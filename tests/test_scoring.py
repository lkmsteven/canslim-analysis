"""Tests for enriched-dataset validation and CANSLIM scoring."""

from __future__ import annotations

import pytest

from canslim_analysis.errors import SchemaValidationError
from canslim_analysis.pipeline.scoring import (
    calculate_score,
    determine_grade,
    normalize_stock,
    validate_enriched_dataset,
)


def enriched_stock(ticker: str = "AAA") -> dict[str, object]:
    """Create an enriched candidate with every qualitative check true."""

    return {
        "Ticker": ticker,
        "Company_Name": f"{ticker} Company",
        "Quantitative_Metrics": {
            "C_Met": True,
            "A_Met": True,
            "L_Met": True,
            "S_Quant_Met": True,
            "I_Quant_Flag": True,
            "N_Technical_Met": True,
            "RS_Rating": 95.0,
        },
        "AI_Qualitative_Checks": {
            "N_New_Catalyst": True,
            "S_Float_Tightness": True,
            "I_Institutional_Quality": True,
            "N_Catalyst_Details": "Fresh catalyst",
            "S_Float_Details": "Tight float",
            "I_Institutional_Details": "Quality holders",
        },
    }


def enriched_data(*stocks: dict[str, object]) -> dict[str, object]:
    """Wrap stocks in an enriched dataset."""

    return {"Metadata": {"Market_Direction_M": "Confirmed Uptrend"}, "Stocks": list(stocks)}


def test_validate_dataset_accepts_valid_candidates() -> None:
    """A valid enriched dataset returns its candidates unchanged."""

    data = enriched_data(enriched_stock())

    assert validate_enriched_dataset(data) == [enriched_stock()]


@pytest.mark.parametrize(
    "mutator",
    [
        lambda data: data.pop("Metadata"),
        lambda data: data.pop("Stocks"),
        lambda data: data["Stocks"][0].pop("Ticker"),
        lambda data: data["Stocks"][0].pop("Quantitative_Metrics"),
    ],
)
def test_validate_dataset_rejects_required_field_gaps(mutator: object) -> None:
    """Dataset-level required-field failures use a project schema error."""

    data = enriched_data(enriched_stock())
    mutator(data)

    with pytest.raises(SchemaValidationError):
        validate_enriched_dataset(data)


def test_normalize_stock_maps_backward_compatible_aliases() -> None:
    """Aliases support legacy artifacts but cannot override canonical fields."""

    stock = enriched_stock()
    stock["Quantitative_Metrics"] = {
        "S_Met": True,
        "I_Met": True,
        "N_Met": True,
        "S_Quant_Met": False,
    }

    normalized = normalize_stock(stock)
    metrics = normalized["Quantitative_Metrics"]

    assert metrics["S_Quant_Met"] is False
    assert metrics["I_Quant_Flag"] is True
    assert metrics["N_Technical_Met"] is True


def test_normalize_stock_lets_verified_ai_override_pending_defaults() -> None:
    """Verified findings are the scoring source and override pending values."""

    stock = enriched_stock()
    stock["AI_Qualitative_Checks_Pending"] = {
        "N_New_Catalyst": False,
        "N_Catalyst_Details": "",
    }

    normalized = normalize_stock(stock)

    assert normalized["AI_Qualitative_Checks"]["N_New_Catalyst"] is True


def test_score_preserves_documented_criterion_order() -> None:
    """Met and missed criteria always follow C,A,N,S,L,I,M order."""

    score, met, missed, _ = calculate_score(enriched_stock(), True)

    assert score == 7
    assert met == ["C", "A", "N", "S", "L", "I", "M"]
    assert missed == []


def test_score_requires_both_s_conditions() -> None:
    """S passes only when quantitative and float-tightness evidence agree."""

    stock = enriched_stock()
    stock["AI_Qualitative_Checks"]["S_Float_Tightness"] = False

    score, met, missed, _ = calculate_score(stock, True)

    assert score == 6
    assert "S" in missed
    assert "S" not in met


@pytest.mark.parametrize("uptrend", [True, False])
def test_score_maps_market_environment_to_m(uptrend: bool) -> None:
    """Only Confirmed Uptrend makes M true."""

    _, met, missed, details = calculate_score(enriched_stock(), uptrend)

    assert ("M" in met) is uptrend
    assert ("M" in missed) is not uptrend
    assert details["Market_In_Confirmed_Uptrend"] is uptrend


@pytest.mark.parametrize(
    ("score", "grade"),
    [
        (7, "A+"),
        (6, "A"),
        (5, "A-"),
        (4, "B+"),
        (3, "B"),
        (2, "C"),
        (1, "D"),
        (0, "D"),
    ],
)
def test_grade_boundaries_remain_compatible(score: int, grade: str) -> None:
    """Grades preserve the original final-report contract."""

    assert determine_grade(score) == grade
