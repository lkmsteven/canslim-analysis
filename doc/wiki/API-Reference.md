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

## Key Artifacts

| Stage | Path |
|---|---|
| Quantitative | `out/intermediate_canslim.json` |
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
