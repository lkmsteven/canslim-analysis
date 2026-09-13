"""Pure quantitative CANSLIM transformations."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence

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
