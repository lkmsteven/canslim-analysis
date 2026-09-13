# Verified Qualitative Enrichment

## Scope

Codex or a qualified reviewer evaluates fresh catalysts, float tightness, and institutional quality. The CLI, not an external agent runtime, validates and merges the findings.

## Commands

```text
python -m canslim_analysis prepare-enrichment
python -m canslim_analysis enrich --findings <findings.json>
```

## Paths

- Input: `out/intermediate_canslim.json`
- Template: `out/enrichment_template.json`
- Output: `out/enriched_canslim.json`

## Safety Contract

Findings must map one-to-one to candidates. Unknown fields and tickers are rejected. Boolean fields must be real booleans. A true `N_New_Catalyst`, `S_Float_Tightness`, or `I_Institutional_Quality` requires non-empty evidence in the matching details field.

Missing, stale, ambiguous, or contradictory evidence remains false. Never fabricate qualitative confirmation.
