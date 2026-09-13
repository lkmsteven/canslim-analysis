# Data and Integrations

## Persistence model

The project has no database. It exchanges versioned JSON files and writes one PDF. Files live under the selected output directory, default `out/`, and are normally overwritten by the stage that owns them.

| Data | Input | Output | Owner |
|---|---|---|---|
| Quantitative candidates | External providers | `out/intermediate_canslim.json` | Quantitative stage |
| Enrichment template | Intermediate JSON | `out/enrichment_template.json` | Enrichment preparation |
| Findings | Human/agent research file | User-supplied or generated path | Enrichment merge |
| Enriched candidates | Intermediate + findings | `out/enriched_canslim.json` | Enrichment merge |
| Final report | Enriched JSON | `out/final_canslim_report.json` | Finalization |
| PDF | Final JSON | `out/canslim_report_<date>.pdf` | PDF renderer |

## Quantitative contract highlights

Schema version is `2.1`. The top-level quantitative object contains `Metadata` and `Stocks`. Metadata includes run date, market direction, universe/evaluation counts, failure counts, skipped-fundamental count, and candidate count. Each stock has ticker, company, `Quantitative_Metrics`, and pending qualitative checks.

Verified tests cover normalization, rank selection, C/A/L filtering, missing fundamentals, and schema fields. `Current_Price`, float, ownership, and EPS values remain nullable when unavailable.

## Findings contract

`Findings` must contain exactly one entry for every quantitative candidate. Each entry has exactly:

- `Ticker`
- `N_New_Catalyst` and `N_Catalyst_Details`
- `S_Float_Tightness` and `S_Float_Details`
- `I_Institutional_Quality` and `I_Institutional_Details`

The three qualitative values must be true JSON booleans. A true value requires non-empty text in its matching details field. Unknown tickers, unknown fields, missing findings, duplicates, and type changes are rejected. Merge output preserves quantitative fields and adds verified checks without changing the input mapping.

## Final report contract

The final report is schema `2.1` and includes report date/time, market environment, `M_Criterion_Met`, candidate count, score distribution, `Top_Candidates`, and carried design notes. Candidates are ordered by `Final_Score` descending, then RS rating descending.

The seven-criterion mapping is:

| Criterion | Source |
|---|---|
| C | `Quantitative_Metrics.C_Met` |
| A | `Quantitative_Metrics.A_Met` |
| N | `AI_Qualitative_Checks.N_New_Catalyst` |
| S | `Quantitative_Metrics.S_Quant_Met` **and** `AI_Qualitative_Checks.S_Float_Tightness` |
| L | `Quantitative_Metrics.L_Met` |
| I | `AI_Qualitative_Checks.I_Institutional_Quality` |
| M | `Metadata.Market_Direction_M == "Confirmed Uptrend"` |

## External integrations

| Integration | Use | Protocol/library | Authentication | Failure behavior |
|---|---|---|---|---|
| Wikipedia S&P 500 page | Equity universe list | HTTPS via `requests`; HTML parser | None | Bounded attempts, delay between attempts, `ExternalDataError` when all fail |
| Yahoo Finance | Market history, stock fundamentals/history | `yfinance` | None in implemented workflow | Individual stock failures are counted; total failure is an external-data error |
| ReportLab | PDF generation | In-process library | Not applicable | Renderer exception is wrapped as `ReportGenerationError` |

The CLI allows universe limit, worker count, timeout, retries, delay, and output location overrides. There is no explicit provider-specific rate-limit API key or quota configuration.

## Privacy and classification

- Public ticker symbols and market values are operational analysis data.
- A user-supplied findings file may contain proprietary research; the CLI does not publish, upload, or archive it.
- Do not place credentials in findings, JSON, reports, logs, or tests. The implemented workflow requires none.
