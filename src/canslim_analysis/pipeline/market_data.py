"""Injectable external market-universe retrieval and parsing."""

from __future__ import annotations

import logging
from collections.abc import Callable
from html.parser import HTMLParser

from canslim_analysis.errors import ExternalDataError, SchemaValidationError
from canslim_analysis.pipeline.config import PipelineConfig


SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
DEFAULT_USER_AGENT = "Mozilla/5.0"

logger = logging.getLogger(__name__)

UniverseFetcher = Callable[[str, dict[str, str], float], str]
SleepFunction = Callable[[float], None]


class _SymbolTableParser(HTMLParser):
    """Collect row cells from the first HTML table in a document."""

    def __init__(self) -> None:
        """Initialize an empty table representation."""

        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._in_row = False
        self._in_cell = False
        self._row: list[str] = []
        self._cell: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Track rows and cells while parsing.

        Args:
            tag: HTML tag name.
            attrs: Unused HTML attributes.
        """

        del attrs
        if tag == "tr":
            self._in_row = True
            self._row = []
        elif tag in {"td", "th"} and self._in_row:
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
            self._row.append("".join(self._cell).strip())
            self._in_cell = False
        elif tag == "tr" and self._in_row:
            if self._row:
                self.rows.append(self._row)
            self._in_row = False
            self._in_cell = False


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

    symbol_index: int | None = None
    symbol_row_index: int | None = None
    for row_index, row in enumerate(parser.rows):
        for index, cell in enumerate(row):
            if cell.strip().casefold() == "symbol":
                symbol_index = index
                symbol_row_index = row_index
                break
        if symbol_index is not None:
            break

    if symbol_index is None:
        raise SchemaValidationError("HTML table does not contain a Symbol column")

    tickers = [
        row[symbol_index].strip().replace(".", "-")
        for row_index, row in enumerate(parser.rows)
        if row_index != symbol_row_index
        if len(row) > symbol_index and row[symbol_index].strip()
    ]
    if not tickers:
        raise SchemaValidationError("No ticker symbols were found in the HTML table")
    return tickers


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
