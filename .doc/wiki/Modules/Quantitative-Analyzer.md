# Quantitative Analyzer

**File:** [Scripts/quantitative_analyzer.py](../../../Scripts/quantitative_analyzer.py)  
**Stage:** 1 of 3  
**Output:** `Scripts/intermediate_canslim.json`

## Purpose

The Quantitative Analyzer performs mechanical, data-driven screening of the S&P 500 universe. It applies the **C**, **A**, and **L** criteria as hard gates, computes supporting quantitative metrics for **S** and **I**, and prepares the dataset for AI enrichment.

## Entry Point

```bash
python Scripts/quantitative_analyzer.py
```

## High-Level Flow

```
1. Fetch S&P 500 tickers from Wikipedia
2. Assess market direction (M criterion)
3. Concurrently download 1-year data for all tickers
4. Compute RS Rating (percentile rank of 1-year return)
5. For each stock, evaluate:
   - C: Quarterly EPS growth >= 25%
   - A: Annual EPS CAGR >= 25%
   - L: RS Rating >= 80
   - S (quant): Volume surge + up/down volume skew
   - I (quant): Institutional ownership >= 30%
   - N (technical): Near 52-week high or recent breakout
6. Gate: stock must pass C AND A AND L
7. Write intermediate_canslim.json
```

## Key Functions

### `main()`

Orchestrates the entire stage. Called when the script runs directly.

### `get_sp500_tickers() -> List[str]`

Fetches the current S&P 500 constituent list from Wikipedia.

- URL: `https://en.wikipedia.org/wiki/List_of_S%26P_500_companies`
- Uses `pandas.read_html` with `lxml` parser
- Replaces `.` with `-` in symbols (Yahoo Finance format, e.g., `BRK.B` → `BRK-B`)
- Retries up to `MAX_RETRIES` times with `RETRY_DELAY` seconds between attempts
- Raises `RuntimeError` if all attempts fail

### `assess_market_direction() -> str`

Evaluates the **M** criterion using two indices:

| Index | Yahoo Ticker |
|-------|--------------|
| S&P 500 | `^GSPC` |
| Nasdaq | `^IXIC` |

An index is in a "confirmed uptrend" when:
- Current price > 50-day SMA
- Current price > 200-day SMA
- 50-day SMA > 200-day SMA

Returns: `"Confirmed Uptrend"`, `"Under Pressure"`, or `"Downtrend"`.

### `fetch_stock_data(ticker: str) -> Optional[Dict[str, Any]]`

Downloads and computes metrics for a single ticker. Called concurrently via `ThreadPoolExecutor`.

**Data fetched per ticker:**
- `stock.info` — fundamental data (EPS growth, float, institutional ownership)
- `stock.history(period="1y")` — daily OHLCV
- `stock.income_stmt` — annual income statement (for EPS CAGR)
- `stock.quarterly_income_stmt` — quarterly income statement (for EPS acceleration)

**Returns `None` if:**
- History is empty or has fewer than `MIN_HISTORY_DAYS` (250) rows
- Current price or 1-year-ago price is missing/zero
- All retry attempts fail

### `analyze_supply_demand(hist: pd.DataFrame) -> Dict[str, Any]`

Computes the quantitative **S** score (0-2).

| Check | Condition | Points |
|-------|-----------|--------|
| Today's volume strong | `vol_today >= vol_50d_avg * MIN_VOLUME_RATIO` | 1 |
| Volume skew positive | `avg_up_volume >= avg_down_volume * MIN_VOLUME_SKEW` | 1 |

`S_Quant_Met = (S_Score >= 2)` — both conditions must be true.

### `analyze_institutional_ownership(info: Dict) -> Dict[str, Any]`

Computes the quantitative **I** flag.

- Reads `heldPercentInstitutions` from Yahoo Finance info
- Normalizes to a 0-1 fraction via `normalize_ratio()`
- `I_Quant_Flag = ownership >= MIN_INSTITUTIONAL_OWNERSHIP` (30%)

### `analyze_new_highs(hist: pd.DataFrame) -> Dict[str, Any]`

Computes the technical **N** context (not the scored N letter).

| Check | Condition |
|-------|-----------|
| Near 52-week high | `pct_from_high <= NEAR_HIGH_THRESHOLD` (10%) |
| Recent breakout | `current_price > max(close[-21:-1])` |

`N_Technical_Met = Near_52_Week_High OR Recent_Breakout`

### `get_quarterly_eps_acceleration(stock: yf.Ticker) -> Dict[str, Any]`

Determines if quarterly EPS growth is accelerating.

- Compares year-over-year growth of the latest quarter vs. the previous quarter
- Requires at least 6 quarters of data
- `is_accelerating = latest_yoy > 0 AND previous_yoy > 0 AND latest_yoy > previous_yoy`

### `get_annual_eps_growth(stock: yf.Ticker) -> Optional[float]`

Computes annual EPS CAGR from the income statement.

- Looks for `Diluted EPS` or `Basic EPS` rows
- Requires at least 3 years of data
- Uses `calculate_cagr(newest, oldest, periods)`

### `build_stock_record(row: pd.Series) -> Dict[str, Any]`

Constructs the final stock record for JSON output. Includes:

- `Quantitative_Metrics` — all computed fields with backward-compatible aliases
- `AI_Qualitative_Checks_Pending` — placeholder nulls for the AI stage

### Helper Functions

| Function | Purpose |
|----------|---------|
| `safe_float(value)` | Converts to float, returns `None` on failure |
| `normalize_ratio(value)` | Normalizes ownership/percentage values to 0-1 range |
| `pct_text(value)` | Formats a float as percentage string |
| `default_ai_pending()` | Returns the AI placeholder dictionary |
| `get_eps_series(frame, row_names)` | Extracts EPS values from an income statement |
| `calculate_cagr(newest, oldest, periods)` | Computes compound annual growth rate |

## Output Schema

See [API Reference](../API-Reference.md) for the full `intermediate_canslim.json` schema.

## Dependencies

- `yfinance` — Yahoo Finance data
- `pandas` — Data manipulation and RS ranking
- `requests` — Wikipedia HTTP fetch
- `lxml` — HTML table parsing
- `tqdm` — Progress bars
- `concurrent.futures` — Thread pool

## Logging

All activity is logged to `canslim_analysis.log` and console:
- Ticker fetch attempts and failures
- Market direction assessment
- Download progress
- Criteria evaluation results
- Final statistics (evaluated, skipped, passed)
