# API Reference

This page documents the script entry points, JSON schema contracts, and data structures used across the CANSLIM Analysis pipeline.

## Script Entry Points

### 1. Quantitative Analyzer

```bash
python Scripts/quantitative_analyzer.py
```

**Input:** None (fetches live data from Wikipedia + Yahoo Finance)  
**Output:** `Scripts/intermediate_canslim.json`  
**Exit code:** 0 on success, non-zero on unhandled exception

### 2. AI Enrichment

**Not a script.** Performed by the OpenClaw AI agent.  
**Input:** `Scripts/intermediate_canslim.json`  
**Output:** `Scripts/enriched_canslim.json`

### 3. Final Process

```bash
python Scripts/final_process.py
```

**Input:** `Scripts/enriched_canslim.json` (preferred) or `Scripts/intermediate_canslim.json` (fallback)  
**Output:** `Scripts/final_canslim_report.json` + triggers PDF generation  
**Exit code:** 0 on success (even if PDF generation fails)

### 4. PDF Report Generator

```bash
python Scripts/pdf_report_generator.py
```

**Input:** `Scripts/final_canslim_report.json`  
**Output:** `out/canslim_report_{Report_Date}.pdf`  
**Exit code:** 0 on success

## JSON Schema Contracts

### Schema Version

All JSON files are stamped with `"Schema_Version": "2.1"`.

### Intermediate Schema (`intermediate_canslim.json`)

Produced by [Quantitative Analyzer](./Modules/Quantitative-Analyzer.md).

```json
{
  "Metadata": {
    "Schema_Version": "2.1",
    "Date_Run": "2026-04-04",
    "Market_Direction_M": "Downtrend",
    "Total_Universe_Scanned": 503,
    "Successfully_Evaluated": 487,
    "Failed_Fetches": 16,
    "Skipped_For_Missing_Fundamentals": 39,
    "Stocks_Passed_To_AI": 15,
    "Fixes_Applied": [
      "Canonical schema preserved across pipeline",
      "A criterion uses EPS CAGR instead of ROE proxy",
      "Technical N separated from AI catalyst N",
      "S scoring separated into quantitative accumulation and AI float confirmation",
      "I final scoring reserved for AI institutional-quality validation"
    ]
  },
  "Stocks": [
    {
      "Ticker": "FIX",
      "Company_Name": "Comfort Systems USA, Inc.",
      "Quantitative_Metrics": {
        "C_Met": true,
        "C_Details": "Q EPS Growth: 38.2%",
        "Quarterly_EPS_Growth": 0.382,
        "EPS_Accelerating": false,
        "A_Met": true,
        "A_Details": "Annual EPS CAGR: 61.8%",
        "Annual_EPS_Growth": 0.6178,
        "L_Met": true,
        "RS_Rating": 97.4,
        "S_Quant_Met": false,
        "S_Quant_Details": "No strong quantitative S signal",
        "S_Score": 0,
        "Today_Volume_Strong": false,
        "Volume_Skew_Positive": false,
        "I_Quant_Flag": true,
        "I_Quant_Details": "96.9% institutional ownership",
        "N_Technical_Met": true,
        "N_Technical_Details": "Within 3.6% of 52-week high",
        "Near_52_Week_High": true,
        "Recent_Breakout": false,
        "Pct_From_High": 0.036,
        "Current_Price": 1417.19,
        "Float_Shares": 35945276.0,
        "Institutional_Ownership": 0.96893,
        "High_52_Week": 1470.5,
        "Vol_Today": 1250000.0,
        "Vol_50D_Avg": 1100000.0,
        "Schema_Version": "2.1",
        "S_Met": false,
        "S_Details": "No strong quantitative S signal",
        "I_Met": true,
        "I_Details": "96.9% institutional ownership",
        "N_Met": true,
        "N_Details": "Within 3.6% of 52-week high"
      },
      "AI_Qualitative_Checks_Pending": {
        "N_New_Catalyst": null,
        "N_Catalyst_Details": "",
        "S_Float_Tightness": null,
        "S_Float_Details": "",
        "I_Institutional_Quality": null,
        "I_Institutional_Details": ""
      }
    }
  ]
}
```

### Enriched Schema (`enriched_canslim.json`)

Produced by [AI Enrichment](./Modules/AI-Enrichment.md). Same as intermediate, plus `AI_Qualitative_Checks` per stock:

```json
{
  "Stocks": [
    {
      "Ticker": "FIX",
      "Company_Name": "Comfort Systems USA, Inc.",
      "Quantitative_Metrics": { "...": "unchanged" },
      "AI_Qualitative_Checks_Pending": { "...": "may be kept or removed" },
      "AI_Qualitative_Checks": {
        "N_New_Catalyst": true,
        "N_Catalyst_Details": "Data center infrastructure buildout boom",
        "S_Float_Tightness": true,
        "S_Float_Details": "35.9M float is relatively tight",
        "I_Institutional_Quality": true,
        "I_Institutional_Details": "96.9% institutional ownership indicates strong professional sponsorship"
      }
    }
  ]
}
```

### Final Report Schema (`final_canslim_report.json`)

Produced by [Final Process](./Modules/Final-Process.md).

```json
{
  "Schema_Version": "2.1",
  "Report_Date": "2026-04-04",
  "Report_Time": "08:58:12",
  "Market_Environment": "Downtrend",
  "M_Criterion_Met": false,
  "Total_Candidates_Evaluated": 15,
  "Score_Distribution": {
    "5": 15
  },
  "Top_Candidates": [
    {
      "Ticker": "FIX",
      "Company_Name": "Comfort Systems USA, Inc.",
      "Final_Score": 5,
      "Grade": "A-",
      "Met_Criteria": ["C", "A", "N", "L", "I"],
      "Missed_Criteria": ["S", "M"],
      "AI_Catalyst_Note": "Data center infrastructure buildout boom",
      "Metrics": {
        "RS_Rating": 97.4,
        "Current_Price": 1417.19,
        "Quarterly_EPS_Growth": 0.382,
        "Annual_EPS_Growth": 0.6178,
        "EPS_Accelerating": false,
        "S_Score": 0,
        "S_Quant_Met": false,
        "S_Float_Tightness": true,
        "N_Technical_Met": true,
        "Float_Shares": 35945276.0,
        "Institutional_Ownership": 0.96893
      },
      "Details": {
        "C_Details": "Q EPS Growth: 38.2%",
        "A_Details": "Annual EPS CAGR: 61.8%",
        "N_Catalyst_Details": "Data center infrastructure buildout boom",
        "N_Technical_Met": true,
        "N_Technical_Details": "Within 3.6% of 52-week high",
        "S_Quant_Met": false,
        "S_Quant_Details": "No strong quantitative S signal",
        "S_Float_Tightness": true,
        "S_Float_Details": "35.9M float is relatively tight",
        "I_Quant_Flag": true,
        "I_Quant_Details": "96.9% institutional ownership",
        "I_Institutional_Quality": true,
        "I_Institutional_Details": "96.9% institutional ownership indicates strong professional sponsorship",
        "Quarterly_EPS_Growth": 0.382,
        "Annual_EPS_Growth": 0.6178,
        "EPS_Accelerating": false,
        "RS_Rating": 97.4,
        "Current_Price": 1417.19,
        "S_Score": 0,
        "Float_Shares": 35945276.0,
        "Institutional_Ownership": 0.96893,
        "Market_In_Confirmed_Uptrend": false
      }
    }
  ],
  "Fixes_Applied": [
    "Canonical schema preserved across pipeline",
    "A criterion uses EPS CAGR instead of ROE proxy",
    "Technical N separated from AI catalyst N",
    "S scoring separated into quantitative accumulation and AI float confirmation",
    "I final scoring reserved for AI institutional-quality validation"
  ]
}
```

## Field Reference

### Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| `Schema_Version` | string | JSON schema version (currently `"2.1"`) |
| `Date_Run` | string | Date of analysis (YYYY-MM-DD) |
| `Market_Direction_M` | string | `"Confirmed Uptrend"`, `"Under Pressure"`, or `"Downtrend"` |
| `Total_Universe_Scanned` | int | Number of S&P 500 tickers fetched |
| `Successfully_Evaluated` | int | Stocks with sufficient data downloaded |
| `Failed_Fetches` | int | Stocks that failed to download |
| `Skipped_For_Missing_Fundamentals` | int | Stocks skipped due to missing EPS data |
| `Stocks_Passed_To_AI` | int | Stocks passing C+A+L gate |
| `Fixes_Applied` | string[] | List of schema/design fixes applied |

### Quantitative Metrics Fields

| Field | Type | Description |
|-------|------|-------------|
| `C_Met` | bool | Quarterly EPS growth ≥ 25% |
| `C_Details` | string | Human-readable C criterion summary |
| `Quarterly_EPS_Growth` | float\|null | Quarterly EPS growth as decimal (0.38 = 38%) |
| `EPS_Accelerating` | bool | Whether quarterly EPS growth is accelerating |
| `A_Met` | bool | Annual EPS CAGR ≥ 25% |
| `A_Details` | string | Human-readable A criterion summary |
| `Annual_EPS_Growth` | float\|null | Annual EPS CAGR as decimal |
| `L_Met` | bool | RS Rating ≥ 80 |
| `RS_Rating` | float | Relative Strength percentile (1-99) |
| `S_Quant_Met` | bool | Both quantitative S conditions met |
| `S_Quant_Details` | string | Human-readable S summary |
| `S_Score` | int | 0-2 score from volume checks |
| `Today_Volume_Strong` | bool | Today's volume ≥ 1.5× 50-day average |
| `Volume_Skew_Positive` | bool | Up-day volume ≥ 1.2× down-day volume |
| `I_Quant_Flag` | bool | Institutional ownership ≥ 30% |
| `I_Quant_Details` | string | Human-readable I summary |
| `N_Technical_Met` | bool | Near 52-week high OR recent breakout |
| `N_Technical_Details` | string | Human-readable technical N summary |
| `Near_52_Week_High` | bool | Within 10% of 52-week high |
| `Recent_Breakout` | bool | Above prior 20-day high |
| `Pct_From_High` | float\|null | Distance from 52-week high as decimal |
| `Current_Price` | float\|null | Latest closing price |
| `Float_Shares` | float\|null | Number of floating shares |
| `Institutional_Ownership` | float\|null | Institutional ownership fraction (0-1) |
| `High_52_Week` | float\|null | 52-week high price |
| `Vol_Today` | float\|null | Latest trading volume |
| `Vol_50D_Avg` | float\|null | 50-day average volume |
| `Schema_Version` | string | Schema version for this record |

### AI Qualitative Checks Fields

| Field | Type | Description |
|-------|------|-------------|
| `N_New_Catalyst` | bool | AI-verified new catalyst exists |
| `N_Catalyst_Details` | string | AI explanation of the catalyst |
| `S_Float_Tightness` | bool | AI-verified float tightness |
| `S_Float_Details` | string | AI explanation of float analysis |
| `I_Institutional_Quality` | bool | AI-verified institutional quality |
| `I_Institutional_Details` | string | AI explanation of institutional assessment |

### Final Report Fields

| Field | Type | Description |
|-------|------|-------------|
| `Report_Date` | string | Report generation date (YYYY-MM-DD) |
| `Report_Time` | string | Report generation time (HH:MM:SS) |
| `Market_Environment` | string | Market direction from metadata |
| `M_Criterion_Met` | bool | Whether market is in confirmed uptrend |
| `Total_Candidates_Evaluated` | int | Number of stocks scored |
| `Score_Distribution` | object | Count of stocks per score (e.g., `{"5": 15}`) |
| `Top_Candidates` | array | Ranked list of scored stocks |
| `Fixes_Applied` | string[] | Copied from metadata |

### Top Candidate Fields

| Field | Type | Description |
|-------|------|-------------|
| `Ticker` | string | Stock symbol |
| `Company_Name` | string | Company name |
| `Final_Score` | int | CANSLIM score (0-7) |
| `Grade` | string | Letter grade (A+ to D) |
| `Met_Criteria` | string[] | List of met criterion letters |
| `Missed_Criteria` | string[] | List of missed criterion letters |
| `AI_Catalyst_Note` | string | Best available catalyst summary |
| `Metrics` | object | Key quantitative metrics |
| `Details` | object | Full detail strings for all criteria |

## Backward Compatibility

The schema includes legacy aliases for older consumers:

| Legacy Field | Canonical Field |
|--------------|-----------------|
| `S_Met` | `S_Quant_Met` |
| `S_Details` | `S_Quant_Details` |
| `I_Met` | `I_Quant_Flag` |
| `I_Details` | `I_Quant_Details` |
| `N_Met` | `N_Technical_Met` |
| `N_Details` | `N_Technical_Details` |

The [Final Process](./Modules/Final-Process.md) `normalize_quantitative_metrics()` function maps these automatically.

## Related Pages

- [Architecture](./Architecture.md) — Pipeline overview
- [Quantitative Analyzer](./Modules/Quantitative-Analyzer.md) — Stage 1 details
- [AI Enrichment](./Modules/AI-Enrichment.md) — Stage 2 details
- [Final Process](./Modules/Final-Process.md) — Stage 3 details
