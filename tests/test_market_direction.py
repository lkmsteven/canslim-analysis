"""Tests for pure market-direction assessment."""

from __future__ import annotations

import pytest

from canslim_analysis.errors import SchemaValidationError
from canslim_analysis.pipeline.config import PipelineConfig
from canslim_analysis.pipeline.quantitative import assess_market_direction


def uptrend_prices(length: int = 200) -> list[float]:
    """Create prices above both moving averages in a confirmed uptrend."""

    return [100.0 + index for index in range(length)]


def downtrend_prices(length: int = 200) -> list[float]:
    """Create prices below their moving averages."""

    return [300.0 - index for index in range(length)]


def test_both_indexes_in_uptrend_is_confirmed_uptrend() -> None:
    """Two confirming indexes preserve the M criterion's successful value."""

    result = assess_market_direction(
        {
            "S&P 500": uptrend_prices(),
            "Nasdaq": uptrend_prices(),
        },
        PipelineConfig(),
    )

    assert result == "Confirmed Uptrend"


def test_one_confirming_index_is_under_pressure() -> None:
    """Only one confirming index yields the existing intermediate result."""

    result = assess_market_direction(
        {
            "S&P 500": uptrend_prices(),
            "Nasdaq": downtrend_prices(),
        },
        PipelineConfig(),
    )

    assert result == "Under Pressure"


def test_no_confirming_index_is_downtrend() -> None:
    """No confirming index yields the existing conservative result."""

    result = assess_market_direction(
        {
            "S&P 500": downtrend_prices(),
            "Nasdaq": downtrend_prices(),
        },
        PipelineConfig(),
    )

    assert result == "Downtrend"


@pytest.mark.parametrize("history", [None, [], uptrend_prices(199)])
def test_insufficient_history_does_not_confirm_an_index(
    history: list[float] | None,
) -> None:
    """Missing, empty, or short histories cannot produce a confirming index."""

    result = assess_market_direction(
        {
            "S&P 500": uptrend_prices(),
            "Nasdaq": history,
        },
        PipelineConfig(),
    )

    assert result == "Under Pressure"


def test_market_direction_uses_configured_lookback() -> None:
    """The configured lookback controls both sufficiency and moving averages."""

    custom_history = [0.0] * 10 + [100.0] * 49 + [101.0]
    result = assess_market_direction(
        {
            "S&P 500": custom_history,
            "Nasdaq": custom_history,
        },
        PipelineConfig(market_lookback_days=60),
    )

    assert result == "Confirmed Uptrend"


def test_non_numeric_close_values_fail_validation() -> None:
    """Malformed external values are surfaced through a project error."""

    with pytest.raises(SchemaValidationError, match="numeric Close values"):
        assess_market_direction(
            {
                "S&P 500": uptrend_prices(),
                "Nasdaq": [100.0, "not-a-price", 102.0, 103.0],
            },
            PipelineConfig(market_lookback_days=4),
        )


def test_mixed_uptrend_shape_is_not_confirmed() -> None:
    """Price above both averages is insufficient when the 50-day is below the 200-day."""

    prices = [200.0] * 150 + [0.0] * 49 + [250.0]

    result = assess_market_direction(
        {
            "S&P 500": prices,
            "Nasdaq": downtrend_prices(),
        },
        PipelineConfig(),
    )

    assert result == "Downtrend"
