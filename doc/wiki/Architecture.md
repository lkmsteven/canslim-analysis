# Architecture

## Overview

The package separates orchestration, external access, transformation, scoring, validation, and presentation. The stable entry point is `python -m canslim_analysis`.

## Components

| Area | Location | Responsibility |
|---|---|---|
| CLI | `src/canslim_analysis/cli.py` | Argument parsing, dispatch, exit codes |
| Configuration | `src/canslim_analysis/pipeline/config.py` | Immutable validated settings |
| Market data | `src/canslim_analysis/pipeline/market_data.py` | Universe and Yahoo providers |
| Quantitative | `src/canslim_analysis/pipeline/quantitative.py` | Screening and orchestration |
| Enrichment | `src/canslim_analysis/pipeline/enrichment.py` | Templates, findings, merge |
| Scoring | `src/canslim_analysis/pipeline/scoring.py` | Dataset checks and seven criteria |
| Final report | `src/canslim_analysis/pipeline/reporting.py` | Ranking and final JSON |
| PDF | `src/canslim_analysis/reporting/pdf.py` | Final-report rendering |
| Workflow | `src/canslim_analysis/pipeline/workflow.py` | Ordered end-to-end execution |
| Status | `src/canslim_analysis/pipeline/status.py` | State and artifact validation |

## Data Flow

```text
Universe + market history + stock rows
  -> quantitative schema 2.1
  -> enrichment template
  -> verified findings merge
  -> final scored report
  -> PDF
```

External providers are injected for offline tests. Pure transformations do not call Yahoo Finance or the network.

## Failure Boundaries

Individual stock failures may produce partial quantitative results, but no universe, no market history, or no stock rows fails the quantitative stage. Schema failures fail closed. Each later stage requires its validated predecessor.
