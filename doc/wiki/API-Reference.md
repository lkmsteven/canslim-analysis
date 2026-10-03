# JSON and CLI Reference

Schema version `2.1` is preserved across the refactoring.

## CLI Commands

| Command | Purpose |
|---|---|
| `quantitative` | Fetch data, rank candidates, apply C/A/L gates. |
| `prepare-enrichment` | Create conservative findings for every candidate. |
| `enrich` | Validate findings and write enriched output. |
| `finalize` | Validate enriched data, score, rank, and write final JSON. |
| `report` | Render final JSON as PDF. |
| `run` | Execute ordered stages. |
| `status` | Report and classify workflow state. |
| `validate` | Validate quantitative, enriched, or final JSON. |
| `verified-research` | Convert an explicit evidence artifact into validated findings. |

## Key Artifacts

| Stage | Path |
|---|---|
| Quantitative | `out/intermediate_canslim.json` |
| Verified evidence | Explicit operator-selected path |
| Verified findings | Explicit operator-selected path |
| Template | `out/enrichment_template.json` |
| Enriched | `out/enriched_canslim.json` |
| Final | `out/final_canslim_report.json` |

## Scoring Mapping

- C: `Quantitative_Metrics.C_Met`
- A: `Quantitative_Metrics.A_Met`
- N: `AI_Qualitative_Checks.N_New_Catalyst`
- S: `Quantitative_Metrics.S_Quant_Met` and `AI_Qualitative_Checks.S_Float_Tightness`
- L: `Quantitative_Metrics.L_Met`
- I: `AI_Qualitative_Checks.I_Institutional_Quality`
- M: `Metadata.Market_Direction_M == "Confirmed Uptrend"`

The final score is the number of passing criteria from C, A, N, S, L, I, and M.

## Verified research contract

```text
verified-research --input <intermediate.json> --evidence <evidence.json> --output <findings.json>
```

The intermediate must be schema `2.1`, contain more than zero `Stocks` rows, declare a matching `Metadata.Stocks_Passed_To_AI`, and contain a valid `Metadata.Date_Run`. The evidence file must use schema `1.0`, set `Analysis_Date` to that date, and contain exactly one record for every candidate occurrence and qualitative field. Findings preserve candidate order and `Candidate_ID`; legacy ticker-unique rows may omit it. Duplicate tickers require unique non-empty occurrence IDs.

Negative evidence fields are `Ticker`, `Field`, `Supported`, `Summary`, and optional `Candidate_ID`. Positive evidence adds `Issuer`, `Share_Class`, `Source`, `Evidence_Date`, `Citation`, and `Criterion_Context`; an included `Candidate_ID` must be non-empty text and match the occurrence. `Evidence_Date` may equal, but not follow, `Metadata.Date_Run` (`2026-09-26` for the current execution run); no backward age threshold applies. Positive citations must be HTTP/HTTPS URLs or SEC accession references. Unsupported or nonqualifying evidence remains `false`.

`--unverified-fallback` is not accepted. Schema and missing-input failures use the stable non-zero codes below and leave no completed output.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success, or `run` intentionally stopped for findings |
| 1 | Unexpected internal error |
| 2 | Usage/configuration error |
| 3 | Schema/validation failure |
| 4 | Missing artifact |
| 5 | External-data failure |
| 6 | PDF-generation failure |

Detailed field contracts and lifecycle rules are in [data and integrations](data-and-integrations.md).
