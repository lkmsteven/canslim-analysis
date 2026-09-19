"""Tests for injectable external equity-universe access."""

from __future__ import annotations

import warnings

import pytest

from canslim_analysis.errors import ExternalDataError, SchemaValidationError
from canslim_analysis.pipeline.config import PipelineConfig
from canslim_analysis.pipeline.market_data import (
    SP500_URL,
    _suppress_pandas4_warnings,
    fetch_sp500_tickers,
    parse_sp500_symbols,
)


VALID_HTML = """
<html><body>
  <table>
    <thead><tr><th>Symbol</th><th>Security</th></tr></thead>
    <tbody>
      <tr><td>BRK.B</td><td>Berkshire Hathaway</td></tr>
      <tr><td> MMM </td><td>3M</td></tr>
    </tbody>
  </table>
</body></html>
"""


def test_parse_sp500_symbols_normalizes_b_share_symbols() -> None:
    """Ticker formatting matches Yahoo Finance's hyphenated B-share style."""

    assert parse_sp500_symbols(VALID_HTML) == ["BRK-B", "MMM"]


def test_parse_sp500_symbols_excludes_follow_on_tables() -> None:
    """Only rows from the table containing the Symbol header are accepted."""

    html = """
    <html><body>
      <table>
        <tr><th>Symbol</th><th>Security</th></tr>
        <tr><td>MMM</td><td>3M</td></tr>
      </table>
      <table>
        <tr><th>S&amp;P 500 companies</th></tr>
        <tr><td>Energy</td></tr>
        <tr><td>Financials</td></tr>
      </table>
    </body></html>
    """

    assert parse_sp500_symbols(html) == ["MMM"]


def test_parse_sp500_symbols_rejects_missing_symbol_column() -> None:
    """Malformed HTML fails with a schema error, not an empty silent result."""

    with pytest.raises(SchemaValidationError, match="Symbol column"):
        parse_sp500_symbols("<table><tr><td>MMM</td></tr></table>")


def test_parse_sp500_symbols_rejects_empty_symbol_column() -> None:
    """A structurally valid but empty universe is rejected."""

    html = "<table><tr><th>Symbol</th></tr><tr><td> </td></tr></table>"

    with pytest.raises(SchemaValidationError, match="No ticker symbols"):
        parse_sp500_symbols(html)


def test_fetch_sp500_tickers_retries_transient_failure_then_parses() -> None:
    """A transient first failure is retried without exposing network details."""

    calls: list[str] = []
    sleeps: list[float] = []

    def flaky_fetch(url: str, headers: dict[str, str], timeout: float) -> str:
        calls.append(url)
        if len(calls) == 1:
            raise OSError("temporarily unavailable")
        assert headers["User-Agent"]
        assert timeout == 10.0
        return VALID_HTML

    tickers = fetch_sp500_tickers(
        PipelineConfig(),
        fetch=flaky_fetch,
        sleeper=sleeps.append,
    )

    assert tickers == ["BRK-B", "MMM"]
    assert calls == [SP500_URL, SP500_URL]
    assert sleeps == [3.0]


def test_pandas4_suppression_takes_precedence_over_yfinance_default() -> None:
    """yfinance re-enables deprecations, so suppression must be restored later."""

    from pandas.errors import Pandas4Warning

    with warnings.catch_warnings():
        warnings.simplefilter("default", Pandas4Warning)
        _suppress_pandas4_warnings()
        assert warnings.filters[0][:3] == ("ignore", None, Pandas4Warning)


def test_fetch_sp500_tickers_fails_after_bounded_attempts() -> None:
    """All failures are wrapped in the project's external-data error type."""

    attempts: list[int] = []

    def failing_fetch(url: str, headers: dict[str, str], timeout: float) -> str:
        attempts.append(1)
        raise OSError("source unavailable")

    with pytest.raises(ExternalDataError, match="Failed to fetch S&P 500 tickers"):
        fetch_sp500_tickers(
            PipelineConfig(max_retries=3, retry_delay=0.5),
            fetch=failing_fetch,
            sleeper=lambda seconds: None,
        )

    assert len(attempts) == 3


def test_fetch_sp500_tickers_accepts_custom_universe_url() -> None:
    """A caller-supplied URL supports offline tests and future data sources."""

    seen_urls: list[str] = []

    def fake_fetch(url: str, headers: dict[str, str], timeout: float) -> str:
        seen_urls.append(url)
        return VALID_HTML

    tickers = fetch_sp500_tickers(
        PipelineConfig(),
        fetch=fake_fetch,
        sleeper=lambda seconds: None,
        url="file://offline-universe",
    )

    assert tickers == ["BRK-B", "MMM"]
    assert seen_urls == ["file://offline-universe"]
