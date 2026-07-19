# Configuration

This page documents all tunable constants and environment settings in the CANSLIM Analysis pipeline.

## Quantitative Analyzer Constants

Located in [Scripts/quantitative_analyzer.py](../../Scripts/quantitative_analyzer.py) lines 28-44.

### Screening Thresholds

| Constant | Default | Description |
|----------|---------|-------------|
| `MIN_EPS_GROWTH` | `0.25` | Minimum quarterly EPS growth rate (25%) for **C** criterion |
| `MIN_ANNUAL_EPS_GROWTH` | `0.25` | Minimum annual EPS CAGR (25%) for **A** criterion |
| `MIN_RS_RATING` | `80.0` | Minimum Relative Strength percentile (1-99) for **L** criterion |
| `MIN_VOLUME_RATIO` | `1.5` | Today's volume must be ≥ this multiple of the 50-day average |
| `MIN_VOLUME_SKEW` | `1.2` | Up-day average volume must be ≥ this multiple of down-day average |
| `MIN_INSTITUTIONAL_OWNERSHIP` | `0.30` | Minimum institutional ownership fraction (30%) for quantitative **I** flag |
| `NEAR_HIGH_THRESHOLD` | `0.10` | Stock must be within 10% of 52-week high for technical **N** context |

### Data & Performance

| Constant | Default | Description |
|----------|---------|-------------|
| `MARKET_LOOKBACK_DAYS` | `200` | Days of history needed to compute 50/200-day moving averages for market direction |
| `MIN_HISTORY_DAYS` | `250` | Minimum trading days required per stock (stocks with less are skipped) |
| `MAX_WORKERS` | `5` | Thread pool size for concurrent Yahoo Finance downloads |
| `DEFAULT_UNIVERSE_LIMIT` | `None` | Max number of S&P 500 stocks to analyze (`None` = no limit) |
| `REQUEST_TIMEOUT` | `10` | HTTP request timeout in seconds |
| `MAX_RETRIES` | `3` | Retry attempts for failed network requests |
| `RETRY_DELAY` | `2` | Seconds to wait between retries |
| `SCHEMA_VERSION` | `"2.1"` | JSON schema version stamped into output metadata |

## Final Process Constants

Located in [Scripts/final_process.py](../../Scripts/final_process.py).

| Constant | Default | Description |
|----------|---------|-------------|
| `SCHEMA_VERSION` | `"2.1"` | Must match the quantitative analyzer schema version |

## Grade Mapping

Determined by [Scripts/final_process.py](../../Scripts/final_process.py) `determine_grade()`:

| Final Score | Grade |
|-------------|-------|
| 7 | A+ |
| 6 | A |
| 5 | A- |
| 4 | B+ |
| 3 | B |
| 2 | C |
| ≤1 | D |

## Market Direction Logic

Determined by [Scripts/quantitative_analyzer.py](../../Scripts/quantitative_analyzer.py) `assess_market_direction()`:

| Condition | Result |
|-----------|--------|
| Both S&P 500 and Nasdaq above 50-day and 200-day SMAs, with 50-day > 200-day | `Confirmed Uptrend` |
| Exactly one index in uptrend | `Under Pressure` |
| Neither index in uptrend | `Downtrend` |

## PDF Generator

No tunable constants exposed. The generator:
- Uses **Letter** page size with 0.75-inch margins
- Outputs to `out/canslim_report_{Report_Date}.pdf`
- Applies a fixed color scheme (navy headers, color-coded grades)

## Dependency Versions

Pinned in [Scripts/requirements.txt](../../Scripts/requirements.txt):

| Package | Version Range | Purpose |
|---------|---------------|---------|
| `yfinance` | `>=0.2.28,<0.3.0` | Yahoo Finance data fetching |
| `pandas` | `>=2.0.0,<3.0.0` | Data manipulation and RS ranking |
| `lxml` | `>=5.0.0,<6.0.0` | HTML parsing for Wikipedia table |
| `tqdm` | `>=4.65.0,<5.0.0` | Progress bars |
| `requests` | `>=2.31.0,<3.0.0` | HTTP requests |
| `reportlab` | `>=4.0.0,<5.0.0` | PDF generation |

## How to Change a Threshold

1. Open [Scripts/quantitative_analyzer.py](../../Scripts/quantitative_analyzer.py).
2. Edit the constant value at the top of the file.
3. Re-run the pipeline (`quantitative_analyzer.py` → AI enrichment → `final_process.py`).

> **Tip:** To screen a smaller universe for testing, set `DEFAULT_UNIVERSE_LIMIT = 50` before running.
