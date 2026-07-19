# Final Process

**File:** [Scripts/final_process.py](../../../Scripts/final_process.py)  
**Stage:** 3 of 3  
**Input:** `Scripts/enriched_canslim.json` (preferred) or `Scripts/intermediate_canslim.json` (fallback)  
**Output:** `Scripts/final_canslim_report.json` + PDF report

## Purpose

The Final Process module combines quantitative metrics and AI qualitative checks into a unified CANSLIM score, ranks all candidates, assigns letter grades, and produces the final JSON report. It also triggers PDF generation as a subprocess.

## Entry Point

```bash
python Scripts/final_process.py
```

## High-Level Flow

```
1. Load enriched_canslim.json (fallback: intermediate_canslim.json)
2. Validate dataset schema
3. Normalize all stock records (fill defaults, map legacy aliases)
4. For each stock:
   a. Calculate CANSLIM score (0-7)
   b. Determine letter grade
   c. Compile metrics and details
5. Sort by (Final_Score, RS_Rating) descending
6. Build final report JSON
7. Write final_canslim_report.json
8. Invoke pdf_report_generator.py as subprocess
```

## Key Functions

### `main()`

Orchestrates the final processing stage.

### `load_json_data(script_dir: str) -> Dict[str, Any]`

Loads the best available JSON data file.

| Priority | File | Condition |
|----------|------|-----------|
| 1 | `enriched_canslim.json` | Preferred — has AI checks filled |
| 2 | `intermediate_canslim.json` | Fallback — AI checks default to `false` |

Raises `FileNotFoundError` if neither exists.

### `validate_dataset(data: Dict[str, Any]) -> None`

Validates the input JSON structure.

**Checks:**
- Top-level keys `Metadata` and `Stocks` exist
- `Stocks` is a list
- Each stock has `Ticker`, `Company_Name`, and `Quantitative_Metrics`

Raises `ValueError` with a descriptive message on failure.

### `normalize_stock(stock: Dict) -> Dict[str, Any]`

Normalizes a stock record to ensure all expected fields exist.

- Fills `Quantitative_Metrics` defaults via `normalize_quantitative_metrics()`
- Maps legacy aliases (`S_Met` → `S_Quant_Met`, `I_Met` → `I_Quant_Flag`, `N_Met` → `N_Technical_Met`)
- Merges `AI_Qualitative_Checks_Pending` and `AI_Qualitative_Checks` via `merge_ai_checks()`

### `calculate_score(stock: Dict, m_is_uptrend: bool) -> Tuple[int, List[str], List[str], Dict[str, Any]]`

Applies the CANSLIM scoring contract.

**Returns:**
- `score` — integer 0-7
- `met` — list of met criterion letters (e.g., `["C", "A", "L"]`)
- `missed` — list of missed criterion letters
- `details` — dictionary of all supporting data

**Scoring rules:**

| Criterion | Rule |
|-----------|------|
| C | `Quantitative_Metrics.C_Met` |
| A | `Quantitative_Metrics.A_Met` |
| L | `Quantitative_Metrics.L_Met` |
| M | `m_is_uptrend` (global market direction) |
| N | `AI_Qualitative_Checks.N_New_Catalyst` |
| S | `Quantitative_Metrics.S_Quant_Met AND AI_Qualitative_Checks.S_Float_Tightness` |
| I | `AI_Qualitative_Checks.I_Institutional_Quality` |

### `determine_grade(score: int) -> str`

Maps numeric score to letter grade.

| Score | Grade |
|-------|-------|
| 7 | A+ |
| 6 | A |
| 5 | A- |
| 4 | B+ |
| 3 | B |
| 2 | C |
| ≤1 | D |

### `merge_ai_checks(stock: Dict) -> Dict[str, Any]`

Merges AI check fields with priority: defaults → pending → final.

```python
merged = default_ai_checks()      # All false/empty
merged.update(pending)             # From AI_Qualitative_Checks_Pending
merged.update(final_ai)            # From AI_Qualitative_Checks (wins)
```

This ensures backward compatibility with older files that only have `AI_Qualitative_Checks_Pending`.

### `normalize_quantitative_metrics(quant: Dict) -> Dict[str, Any]`

Fills all missing quantitative fields with safe defaults:

| Field | Default |
|-------|---------|
| `C_Met`, `A_Met`, `L_Met` | `False` |
| `C_Details`, `A_Details` | `""` |
| `Quarterly_EPS_Growth`, `Annual_EPS_Growth` | `None` |
| `EPS_Accelerating` | `False` |
| `RS_Rating`, `Current_Price` | `0.0` |
| `S_Score` | `0` |
| `Today_Volume_Strong`, `Volume_Skew_Positive` | `False` |
| `Near_52_Week_High`, `Recent_Breakout` | `False` |
| `Pct_From_High`, `Float_Shares`, `Institutional_Ownership`, `High_52_Week` | `None` |
| `Schema_Version` | `"2.1"` |

## Output Schema

See [API Reference](../API-Reference.md) for the full `final_canslim_report.json` schema.

## PDF Generation

After writing the JSON report, `main()` attempts to generate a PDF:

```python
subprocess.run(
    [sys.executable, pdf_generator_path],
    cwd=script_dir,
    capture_output=True,
    text=True,
    timeout=60,
)
```

- **Non-fatal**: If PDF generation fails, a warning is logged but the JSON report remains valid.
- **Timeout**: 60 seconds
- **Working directory**: `Scripts/` (so relative paths in the PDF generator resolve correctly)

## Dependencies

- `json` — JSON I/O
- `logging` — Log to `canslim_analysis.log` and console
- `subprocess` — PDF generator invocation
- `tqdm` — Progress bar for score compilation
- `datetime` — Report timestamp

## Logging

Key log events:
- Which JSON file was loaded (enriched vs. intermediate)
- Market environment and M criterion status
- Total stocks evaluated
- Score distribution
- Output file path
- PDF generation success/failure
