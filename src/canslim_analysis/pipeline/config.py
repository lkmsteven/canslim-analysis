"""Validated runtime configuration for analysis stages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from canslim_analysis.errors import ConfigurationError


@dataclass(frozen=True)
class PipelineConfig:
    """Immutable settings for one pipeline execution.

    Attributes:
        min_eps_growth: Minimum quarterly EPS growth as a decimal fraction.
        min_annual_eps_growth: Minimum annual EPS growth as a decimal fraction.
        min_rs_rating: Minimum Relative Strength rating from 1 through 99.
        min_volume_ratio: Required ratio of current volume to its 50-day average.
        min_volume_skew: Required ratio of up-day to down-day volume.
        min_institutional_ownership: Institutional-ownership reference threshold.
        market_lookback_days: Market-history length used for trend assessment.
        min_history_days: Minimum stock history required for evaluation.
        max_workers: Maximum concurrent external-data requests.
        universe_limit: Optional maximum number of tickers to evaluate.
        request_timeout: Per-request timeout in seconds.
        max_retries: Maximum retry attempts after an initial failure.
        retry_delay: Base delay between retries in seconds.
        output_dir: Optional project-local output directory override.
    """

    min_eps_growth: float = 0.25
    min_annual_eps_growth: float = 0.25
    min_rs_rating: float = 80.0
    min_volume_ratio: float = 1.5
    min_volume_skew: float = 1.2
    min_institutional_ownership: float = 0.30
    near_high_threshold: float = 0.10
    market_lookback_days: int = 200
    min_history_days: int = 250
    max_workers: int = 5
    universe_limit: int | None = None
    request_timeout: float = 10.0
    max_retries: int = 3
    retry_delay: float = 2.0
    output_dir: Path | None = None

    def __post_init__(self) -> None:
        """Validate all operationally significant values.

        Raises:
            ConfigurationError: If a value falls outside its permitted range.
        """

        self._validate_range("min_eps_growth", self.min_eps_growth, 0.0, 1.0)
        self._validate_range(
            "min_annual_eps_growth", self.min_annual_eps_growth, 0.0, 1.0
        )
        self._validate_range("min_rs_rating", self.min_rs_rating, 0.0, 99.0, True)
        self._validate_range("min_volume_ratio", self.min_volume_ratio, 0.0, None, True)
        self._validate_range("min_volume_skew", self.min_volume_skew, 0.0, None, True)
        self._validate_range(
            "min_institutional_ownership",
            self.min_institutional_ownership,
            0.0,
            1.0,
        )
        self._validate_range("near_high_threshold", self.near_high_threshold, 0.0, 1.0)
        self._validate_positive_integer("market_lookback_days", self.market_lookback_days)
        self._validate_positive_integer("min_history_days", self.min_history_days)
        self._validate_positive_integer("max_workers", self.max_workers)

        if self.universe_limit is not None and self.universe_limit <= 0:
            raise ConfigurationError("universe_limit must be greater than zero")
        self._validate_range("request_timeout", self.request_timeout, 0.0, None, True)
        self._validate_range("max_retries", self.max_retries, 0, None, False)
        self._validate_range("retry_delay", self.retry_delay, 0.0, None, False)

    @staticmethod
    def _validate_range(
        field: str,
        value: float | int,
        minimum: float | int,
        maximum: float | int | None,
        exclusive_minimum: bool = False,
    ) -> None:
        """Validate one numeric range and include the field name in errors."""

        below_minimum = value <= minimum if exclusive_minimum else value < minimum
        if below_minimum or (maximum is not None and value > maximum):
            raise ConfigurationError(f"{field} is outside its valid range")

    @staticmethod
    def _validate_positive_integer(field: str, value: int) -> None:
        """Validate a strictly positive integer field."""

        if value <= 0:
            raise ConfigurationError(f"{field} must be greater than zero")
