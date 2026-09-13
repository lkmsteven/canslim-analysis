# Quantitative Analyzer

## Scope

The quantitative stage fetches an equity universe and market history, evaluates stock data, ranks returns, and applies the C/A/L gate.

## Implementation

- Orchestration: `src/canslim_analysis/pipeline/quantitative.py`
- External providers: `src/canslim_analysis/pipeline/market_data.py`
- Command: `python -m canslim_analysis quantitative`
- Output: `out/intermediate_canslim.json`

## Contract

The output is schema `2.1` and contains metadata plus only candidates passing quarterly EPS growth, annual EPS growth, and minimum RS rating. Missing fundamentals are skipped. Individual stock failures are counted, while a total failure raises an external-data error.

Technical N and quantitative S evidence are preserved as supporting context; they do not finalize qualitative N or S.
