# Architecture

This page describes the system architecture of the CANSLIM Analysis pipeline: its components, how data flows between them, and the contracts that bind them together.

## High-Level View

```
┌─────────────────────────────────────────────────────────────────┐
│                    CANSLIM Analysis Pipeline                     │
└─────────────────────────────────────────────────────────────────┘

   Stage 1                Stage 2                  Stage 3
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Quantitative │────▶│   AI Enrichment  │────▶│ Final Processing │
│   Analyzer   │     │   (OpenClaw AI)  │     │  + PDF Generator │
└──────────────┘     └──────────────────┘     └──────────────────┘
       │                      │                        │
       ▼                      ▼                        ▼
intermediate_           enriched_               final_canslim_
canslim.json            canslim.json            report.json
                                                   │
                                                   ▼
                                          out/canslim_report_
                                             {date}.pdf
```

## Component Responsibilities

### 1. Quantitative Analyzer — [Scripts/quantitative_analyzer.py](../../Scripts/quantitative_analyzer.py)

The entry point of the pipeline. Performs mechanical screening of the S&P 500 universe.

**Responsibilities:**
- Fetch the current S&P 500 constituent list from Wikipedia.
- Assess overall market direction (M criterion) using S&P 500 and Nasdaq indices against 50/200-day moving averages.
- Download 1 year of price/volume history and fundamental data per ticker via `yfinance` (concurrent, 5 workers, with retries).
- Compute per-stock metrics:
  - Quarterly EPS growth (C)
  - Annual EPS CAGR (A)
  - Relative Strength rating (L) — percentile-ranked 1-year return
  - Supply/demand signals (S-quant): today's volume vs. 50-day average, up-day vs. down-day volume skew
  - Institutional ownership flag (I-quant)
  - Technical N context: proximity to 52-week high, recent breakouts
- Apply the gate: a stock must pass **C AND A AND L** to advance.
- Emit `intermediate_canslim.json` with `Quantitative_Metrics` filled and `AI_Qualitative_Checks_Pending` placeholders.

### 2. AI Enrichment — external (OpenClaw)

**Not a script in this repository.** This stage is performed by the OpenClaw AI agent, which:

- Reads `intermediate_canslim.json`.
- For each stock, researches recent news, catalysts, float dynamics, and institutional sponsorship quality.
- **Preserves** every field in `Quantitative_Metrics` unchanged.
- Fills `AI_Qualitative_Checks` with six fields: `N_New_Catalyst`, `N_Catalyst_Details`, `S_Float_Tightness`, `S_Float_Details`, `I_Institutional_Quality`, `I_Institutional_Details`.
- Writes `enriched_canslim.json`.

This separation keeps mechanical screening deterministic and auditable, while isolating subjective judgment in a clearly-scoped AI step. See [SKILL.md](../../SKILL.md) for the agent's execution checklist and constraints.

### 3. Final Process — [Scripts/final_process.py](../../Scripts/final_process.py)

Combines quantitative and AI results into the final ranked report.

**Responsibilities:**
- Load `enriched_canslim.json` (falls back to `intermediate_canslim.json` if enrichment was skipped, with all AI checks defaulting to `false`).
- Validate the dataset schema (top-level `Metadata` + `Stocks`, per-stock required fields).
- Normalize stock records — fills defaults for any missing metric fields and maps legacy aliases (`S_Met` → `S_Quant_Met`, etc.).
- Apply the **scoring contract** (7 criteria) to each stock.
- Rank candidates by `(Final_Score, RS_Rating)` descending.
- Assign letter grades (A+ for 7/7 down to D for ≤1/7).
- Write `final_canslim_report.json`.
- Invoke the PDF generator as a subprocess (60-second timeout, non-fatal on failure).

### 4. PDF Report Generator — [Scripts/pdf_report_generator.py](../../Scripts/pdf_report_generator.py)

Renders the final JSON into a professional PDF using ReportLab.

**Responsibilities:**
- Read `final_canslim_report.json`.
- Build a formatted document: report header with metadata, score distribution table, and one page per candidate with grade badge, criteria status grid, key metrics table, and per-criterion analysis sections.
- Output to `out/canslim_report_{Report_Date}.pdf` (at project root level).

## Data Flow

```
Wikipedia (S&P 500 list)
        │
        ▼
Yahoo Finance (prices, volumes, fundamentals)
        │
        ▼
┌─────────────────────────────┐
│ intermediate_canslim.json   │   Schema 2.1
│  Metadata                   │
│  Stocks[]                   │
│   ├─ Quantitative_Metrics   │   ← owned by Stage 1
│   └─ AI_Qualitative_Checks_Pending (nulls)
└─────────────────────────────┘
        │
        ▼  (OpenClaw AI fills AI checks, preserves quant)
┌─────────────────────────────┐
│ enriched_canslim.json       │
│  Stocks[]                   │
│   ├─ Quantitative_Metrics   │   ← unchanged
│   └─ AI_Qualitative_Checks  │   ← filled by Stage 2
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ final_canslim_report.json   │
│  Market_Environment         │
│  Score_Distribution         │
│  Top_Candidates[] (ranked)  │
│   ├─ Final_Score, Grade     │
│   ├─ Met/Missed_Criteria    │
│   ├─ Metrics                │
│   └─ Details                │
└─────────────────────────────┘
        │
        ▼
out/canslim_report_{date}.pdf
```

## The Scoring Contract

The binding logic applied in [final_process.py](../../Scripts/final_process.py) `calculate_score()`:

| Criterion | Rule |
|-----------|------|
| C | `Quantitative_Metrics.C_Met` |
| A | `Quantitative_Metrics.A_Met` |
| L | `Quantitative_Metrics.L_Met` |
| M | `Metadata.Market_Direction_M == "Confirmed Uptrend"` |
| N | `AI_Qualitative_Checks.N_New_Catalyst == true` |
| S | `Quantitative_Metrics.S_Quant_Met AND AI_Qualitative_Checks.S_Float_Tightness` |
| I | `AI_Qualitative_Checks.I_Institutional_Quality == true` |

Notable design decisions:
- **N and I have quantitative "context" signals** (`N_Technical_Met`, `I_Quant_Flag`) that are *not* scored directly — they inform the AI but the final letter requires AI verification.
- **S requires both halves**: quantitative volume accumulation AND AI-verified float tightness.
- **M is global**: a market downtrend costs every candidate one point.

## Concurrency & Reliability

- **ThreadPoolExecutor** with `MAX_WORKERS = 5` for parallel yfinance downloads (reduced from 10 to avoid rate limiting).
- **Retry policy**: 3 attempts with 2-second delay for ticker list fetch and per-stock data fetch.
- **Request timeouts**: 10 seconds on HTTP requests.
- **Graceful degradation**: stocks with missing fundamental data are skipped (counted in metadata), not penalized.
- **Logging**: all stages append to `canslim_analysis.log` (file + console).

## External Dependencies

| Dependency | Role |
|------------|------|
| Wikipedia | Source of S&P 500 constituent symbols |
| Yahoo Finance (via `yfinance`) | Price/volume history, income statements, institutional ownership |
| OpenClaw AI | Qualitative enrichment (Stage 2) |
| ReportLab | PDF rendering |

## Failure Boundaries

- Stage 1 failure → no `intermediate_canslim.json`; later stages cannot run.
- Stage 2 skipped → Stage 3 falls back to intermediate file; all AI checks score as `false`.
- Stage 3 PDF subprocess failure → logged as warning; JSON report is still valid.

See [FAQ & Troubleshooting](./FAQ-Troubleshooting.md) for operational issues.
