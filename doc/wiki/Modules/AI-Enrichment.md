# Verified Qualitative Enrichment

## Scope

Codex or a qualified reviewer evaluates fresh catalysts, float tightness, and institutional quality. The CLI, not an external agent runtime, validates and merges the findings.

## Commands

### Legacy worksheet path

```text
python -m canslim_analysis prepare-enrichment
python -m canslim_analysis enrich --findings <findings.json>
```

### Verified evidence path

```text
python -m canslim_analysis verified-research --input <intermediate.json> --evidence <evidence.json> --output <verified_findings.json>
python -m canslim_analysis enrich --findings <verified_findings.json>
```

All three verified-research paths are explicit. The input remains user-owned; the output is written only after validation and atomically.

## Paths

- Legacy enrichment input: `out/intermediate_canslim.json`
- Verified research input: explicit intermediate path
- Verified research evidence: explicit evidence path
- Verified research findings: explicit output path
- Template: `out/enrichment_template.json`
- Output: `out/enriched_canslim.json`

## Candidate and occurrence contract

Verified research reads candidates only from `Stocks`, in artifact order, and requires `Metadata.Stocks_Passed_To_AI` to equal that array length. It creates one findings entry per passing occurrence in the same order. `Candidate_ID` is optional for legacy ticker-unique rows; duplicate tickers and distinct share-class occurrences require unique non-empty IDs. The findings mirror the selected identity, so occurrence count and order survive enrichment and finalization.

## Evidence contract

`Metadata.Date_Run` is the approved cutoff; it is `2026-09-26` for the current execution run. Evidence dated after the cutoff fails. There is no backward age threshold: older direct evidence remains eligible unless superseded or contradicted. Prefer primary issuer or regulatory sources, and never rely on search snippets.

Every candidate needs one record for each N, S, and I field. A negative record contains `Ticker`, `Field`, `Supported`, and `Summary`, plus optional matching `Candidate_ID`. A positive record also requires `Issuer`, `Share_Class`, `Source`, `Evidence_Date`, `Citation`, `Summary`, and `Criterion_Context`; its optional `Candidate_ID` must be non-empty text and identify the same occurrence. The retrievable citation must be an HTTP/HTTPS URL or SEC accession reference.

Ambiguous, contradictory, low-quality, tangential, offering, lockup, dilution, and unexecuted-buyback claims are not accepted as positive float or catalyst evidence. Unsupported and nonqualifying evidence remains conservatively `false`, with a "Not verified:" reason in the details field.

Validation failures return an actionable non-zero exit code and leave no completed output. `verified-research` does not support `--unverified-fallback`.

## Legacy findings safety contract

Findings must map one-to-one to candidates. Unknown fields and tickers are rejected. Boolean fields must be real booleans. A true `N_New_Catalyst`, `S_Float_Tightness`, or `I_Institutional_Quality` requires non-empty evidence in the matching details field.

Missing, stale, ambiguous, or contradictory evidence remains false. Never fabricate qualitative confirmation.

If the current quantitative artifact contains no candidates, enrichment accepts only an empty findings array. `run` stops before merge when supplied findings are non-empty; explicit fallback can produce an empty, all-false, unverified report.

This mode is educational research and analysis, not personalized investment advice.
