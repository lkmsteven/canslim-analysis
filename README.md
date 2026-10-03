# CANSLIM Analysis

A hybrid quantitative and qualitative CANSLIM analysis workflow for U.S. stocks. The project combines market-data screening, verified Codex qualitative research, strict validation, final scoring, JSON artifacts, and PDF reporting.

This project is educational software. Its output is not investment advice, does not guarantee accuracy, and must not be used as a substitute for independent research and risk management.

## Requirements

- Python 3.12 or newer
- Git
- Network access for live quantitative runs (Wikipedia and Yahoo Finance)
- No global package installation

## Setup

From this project root:

```text
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e '.[dev]'
pytest
```

On macOS or Linux, activate with `source .venv/bin/activate`.

## CLI

All workflow operations use:

```text
python -m canslim_analysis --help
```

### Inspect state

```text
python -m canslim_analysis status --json
```

### Quantitative screening

```text
python -m canslim_analysis quantitative
```

Useful options include `--limit`, `--workers`, `--min-rs-rating`, `--output-dir`, and `--help`.

### Qualitative enrichment

Create a findings worksheet:

```text
python -m canslim_analysis prepare-enrichment
```

After Codex or a reviewer fills verified findings:

```text
python -m canslim_analysis enrich --findings <findings.json>
```

A true catalyst, float-tightness, or institutional-quality claim requires non-empty evidence in its matching details field. Missing evidence must remain `false`.

### Verified research conversion

To convert a separate auditable evidence file into findings, supply all research paths explicitly:

```text
python -m canslim_analysis verified-research --input <intermediate.json> --evidence <evidence.json> --output <verified_findings.json>
```

The command discovers passing candidates in `Stocks` artifact order and emits one findings entry per occurrence. `Candidate_ID` is optional on legacy ticker-unique rows; duplicate tickers and distinct share-class occurrences require unique non-empty IDs, which the findings preserve. Positive evidence may include an optional matching non-empty `Candidate_ID`.

Evidence is approved only through `Metadata.Date_Run`—`2026-09-26` for the current execution run—without a backward age threshold. Later dates fail. Prefer primary issuer or regulatory sources; unsupported, ambiguous, contradictory, low-quality, tangential, offering, lockup, dilution, or unexecuted-buyback evidence remains conservatively `false`. A failed validation is actionable, non-zero, and writes no completed output. `--unverified-fallback` is prohibited on this command.

### Final report and PDF

```text
python -m canslim_analysis finalize
python -m canslim_analysis report
```

### Complete workflow

```text
python -m canslim_analysis run --findings <findings.json>
```

Without findings, `run` stops after quantitative screening. `--unverified-fallback` is opt-in, sets all qualitative checks to false, and must be disclosed as unverified.

If the current quantitative run selects zero candidates, `run --findings` stops safely instead of merging findings from an older run. `--unverified-fallback` may still produce an explicitly conservative, empty report.

## Artifacts

| Artifact | Default path |
|---|---|
| Quantitative candidates | `out/intermediate_canslim.json` |
| Verified research evidence input | Operator-selected explicit path |
| Verified research findings output | Operator-selected explicit path |
| Enrichment worksheet | `out/enrichment_template.json` |
| Enriched candidates | `out/enriched_canslim.json` |
| Final JSON report | `out/final_canslim_report.json` |
| PDF report | `out/canslim_report_<date>.pdf` |
| Runtime log | `out/canslim_analysis.log` |

Generated files are not source code. Do not edit them to change pipeline state.

## Scoring Contract

Final scoring counts these criteria:

- **C:** `Quantitative_Metrics.C_Met`
- **A:** `Quantitative_Metrics.A_Met`
- **N:** `AI_Qualitative_Checks.N_New_Catalyst`
- **S:** `Quantitative_Metrics.S_Quant_Met` and `AI_Qualitative_Checks.S_Float_Tightness`
- **L:** `Quantitative_Metrics.L_Met`
- **I:** `AI_Qualitative_Checks.I_Institutional_Quality`
- **M:** `Metadata.Market_Direction_M == "Confirmed Uptrend"`

Technical N evidence and quantitative S or institutional ownership values are supporting context, not final qualitative confirmation.

## Validation and Exit Codes

Validate an artifact without writing:

```text
python -m canslim_analysis validate --stage quantitative
python -m canslim_analysis validate --stage enriched
python -m canslim_analysis validate --stage final
```

| Exit code | Meaning |
|---|---|
| 0 | Success, or an intentional findings stop |
| 1 | Unexpected internal error |
| 2 | Usage or configuration error |
| 3 | Schema or validation failure |
| 4 | Missing artifact |
| 5 | External market-data failure |
| 6 | PDF generation failure |

## Compatibility

The JSON schema remains `2.1`. The former standalone files under `Scripts/` were superseded by the package CLI during this refactor. See `doc/spec/design.md` for the migration decision and `doc/wiki/` for architecture and troubleshooting.
