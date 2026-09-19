"""Injectable external market-universe retrieval and parsing."""

from __future__ import annotations

import logging
from collections.abc import Callable
from html.parser import HTMLParser
from time import sleep
from typing import Any
import warnings

from canslim_analysis.pipeline.quantitative import (
    PriceBar,
    analyze_institutional_ownership,
    analyze_new_highs,
    analyze_supply_demand,
    calculate_quarterly_acceleration,
    safe_float,
)

from canslim_analysis.errors import ExternalDataError, SchemaValidationError
from canslim_analysis.pipeline.config import PipelineConfig


SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
DEFAULT_USER_AGENT = "Mozilla/5.0"

logger = logging.getLogger(__name__)

UniverseFetcher = Callable[[str, dict[str, str], float], str]
SleepFunction = Callable[[float], None]


def _suppress_pandas4_warnings() -> None:
    """Restore Pandas4 suppression after yfinance changes default filters."""

    try:
        from pandas.errors import Pandas4Warning
    except ImportError:
        return
    warnings.filterwarnings("ignore", category=Pandas4Warning)


class _SymbolTableParser(HTMLParser):
    """Collect rows from each top-level HTML table in a document."""

    def __init__(self) -> None:
        """Initialize an empty table representation."""

        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._table_stack: list[list[list[str]]] = []
        self._in_cell = False
        self._cell: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Track rows and cells while parsing.

        Args:
            tag: HTML tag name.
            attrs: Unused HTML attributes.
        """

        del attrs
        if tag == "table":
            self._table_stack.append([])
        elif tag == "tr" and self._table_stack:
            self._table_stack[-1].append([])
        elif tag in {"td", "th"} and self._table_stack and self._table_stack[-1]:
            self._in_cell = True
            self._cell = []

    def handle_data(self, data: str) -> None:
        """Accumulate text belonging to the active cell.

        Args:
            data: Decoded HTML text.
        """

        if self._in_cell:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        """Complete cells and rows as closing tags are encountered.

        Args:
            tag: HTML tag name.
        """

        if tag in {"td", "th"} and self._in_cell:
            self._table_stack[-1][-1].append("".join(self._cell).strip())
            self._in_cell = False
        elif tag == "table" and self._table_stack:
            self.tables.append(self._table_stack.pop())


def _fetch_over_http(url: str, headers: dict[str, str], timeout: float) -> str:
    """Fetch one HTTP text response.

    Args:
        url: External document URL.
        headers: Request headers.
        timeout: Timeout in seconds.

    Returns:
        The response body.

    Raises:
        Exception: Propagates provider-specific network failures for retry.
    """

    import requests

    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def parse_sp500_symbols(html: str) -> list[str]:
    """Parse and normalize ticker symbols from an S&P 500 HTML table.

    Args:
        html: Untrusted HTML containing a table with a ``Symbol`` column.

    Returns:
        Tickers in document order with Yahoo-style hyphenated share classes.

    Raises:
        SchemaValidationError: If the table has no symbols to evaluate.
    """

    parser = _SymbolTableParser()
    parser.feed(html)

    for table_rows in parser.tables:
        symbol_index: int | None = None
        symbol_row_index: int | None = None
        for row_index, row in enumerate(table_rows):
            for index, cell in enumerate(row):
                if cell.strip().casefold() == "symbol":
                    symbol_index = index
                    symbol_row_index = row_index
                    break
            if symbol_index is not None:
                break

        if symbol_index is None:
            continue

        tickers = [
            row[symbol_index].strip().replace(".", "-")
            for row_index, row in enumerate(table_rows)
            if row_index != symbol_row_index
            if len(row) > symbol_index and row[symbol_index].strip()
        ]
        if not tickers:
            raise SchemaValidationError("No ticker symbols were found in the HTML table")
        return tickers

    raise SchemaValidationError("HTML table does not contain a Symbol column")


def fetch_sp500_tickers(
    config: PipelineConfig,
    *,
    fetch: UniverseFetcher = _fetch_over_http,
    sleeper: SleepFunction,
    url: str = SP500_URL,
) -> list[str]:
    """Fetch and parse an equity universe with bounded retries.

    Args:
        config: Runtime configuration controlling timeout and retry behavior.
        fetch: Callable that retrieves one text document.
        sleeper: Callable used to delay between attempts; injected for tests.
        url: Document URL; defaults to the canonical S&P 500 source.

    Returns:
        A non-empty list of normalized ticker symbols.

    Raises:
        ExternalDataError: If every bounded attempt fails.
        SchemaValidationError: If the final response has no usable symbols.
    """

    headers = {"User-Agent": DEFAULT_USER_AGENT}
    last_error: Exception | None = None

    for attempt in range(config.max_retries):
        try:
            html = fetch(url, headers, config.request_timeout)
            tickers = parse_sp500_symbols(html)
            logger.info("Fetched %s ticker symbols", len(tickers))
            return tickers
        except Exception as exc:  # Deliberately wrapped and surfaced below.
            last_error = exc
            logger.warning(
                "Attempt %s/%s failed fetching tickers",
                attempt + 1,
                config.max_retries,
            )
            if attempt < config.max_retries - 1:
                sleeper(config.retry_delay)

    raise ExternalDataError(
        f"Failed to fetch S&P 500 tickers from {url}: {last_error}"
    )


def _eps_values_from_frame(frame: Any, row_names: tuple[str, ...]) -> list[float]:
    """Extract numeric EPS values from a provider accounting frame."""

    if frame is None or getattr(frame, "empty", True):
        return []
    for row_name in row_names:
        if row_name not in getattr(frame, "index", []):
            continue
        values = [safe_float(value) for value in frame.loc[row_name].tolist()]
        numeric = [value for value in values if value is not None]
        if numeric:
            return numeric
    return []


def _annual_eps_growth(stock: Any) -> float | None:
    """Calculate annual diluted/basic EPS CAGR from provider statements."""

    values = _eps_values_from_frame(stock.income_stmt, ("Diluted EPS", "Basic EPS"))
    if len(values) < 3:
        return None
    newest, oldest = values[0], values[-1]
    periods = len(values) - 1
    if newest <= 0 or oldest <= 0:
        return None
    return (newest / oldest) ** (1 / periods) - 1


def fetch_market_history_yfinance(index_name: str) -> list[float] | None:
    """Fetch one market index's one-year Close series.

    Args:
        index_name: Canonical market-index name used by the analysis stage.

    Returns:
        Ordered Close values, or ``None`` when no usable history is returned.
    """

    import yfinance as yf

    _suppress_pandas4_warnings()
    from canslim_analysis.pipeline.quantitative import MARKET_INDEXES

    ticker = MARKET_INDEXES.get(index_name, index_name)
    frame = yf.Ticker(ticker).history(period="1y", auto_adjust=False)
    if frame.empty or "Close" not in frame:
        return None
    values = [safe_float(value) for value in frame["Close"].tolist()]
    return [value for value in values if value is not None]


def fetch_stock_yfinance(
    ticker: str,
    config: Any,
    *,
    sleeper: Callable[[float], None] = sleep,
) -> dict[str, Any] | None:
    """Fetch fundamentals and normalized price bars from Yahoo Finance.

    Args:
        ticker: Equity ticker to fetch.
        config: Runtime configuration controlling history and retry behavior.
        sleeper: Delay callable injected for deterministic tests.

    Returns:
        A normalized quantitative input row, or ``None`` after bounded failures.
    """

    last_error: Exception | None = None
    for attempt in range(config.max_retries):
        try:
            import yfinance as yf

            _suppress_pandas4_warnings()
            stock = yf.Ticker(ticker)
            info = stock.info or {}
            frame = stock.history(period="1y", auto_adjust=False)
            if frame.empty or len(frame) < config.min_history_days:
                return None

            bars = [
                PriceBar(
                    open=float(row["Open"]),
                    close=float(row["Close"]),
                    volume=float(row["Volume"]),
                )
                for _, row in frame.iterrows()
            ]
            current_price = bars[-1].close
            price_1y_ago = bars[0].close
            if price_1y_ago == 0:
                return None

            quarterly = calculate_quarterly_acceleration(
                _eps_values_from_frame(
                    stock.quarterly_income_stmt,
                    ("Diluted EPS", "Basic EPS"),
                )
            )
            quarterly_growth = safe_float(info.get("earningsQuarterlyGrowth"))
            if quarterly_growth is None:
                quarterly_growth = quarterly["latest_yoy_growth"]
            institutional = analyze_institutional_ownership(info, config)
            supply = analyze_supply_demand(bars, config)
            technical = analyze_new_highs(bars, config)

            return {
                "Ticker": ticker,
                "Company_Name": info.get("shortName", ticker),
                "Current_Price": round(current_price, 2),
                "Return_1Y": (current_price - price_1y_ago) / abs(price_1y_ago),
                "Quarterly_EPS_Growth": quarterly_growth,
                "EPS_Accelerating": quarterly["is_accelerating"],
                "Annual_EPS_Growth": _annual_eps_growth(stock),
                "Float_Shares": safe_float(info.get("floatShares")),
                "Institutional_Ownership": institutional["Institutional_Ownership"],
                **supply,
                "I_Quant_Flag": institutional["I_Quant_Flag"],
                "I_Quant_Details": institutional["I_Quant_Details"],
                **technical,
            }
        except Exception as exc:
            last_error = exc
            if attempt < config.max_retries - 1:
                sleeper(config.retry_delay)

    logger.warning("%s failed after retries: %s", ticker, last_error)
    return None
