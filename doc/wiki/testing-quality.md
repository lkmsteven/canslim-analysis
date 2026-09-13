# Testing and Quality

## Framework and layout

- Framework: pytest 9.1.1, declared as the `dev` extra in [`../../pyproject.toml`](../../pyproject.toml).
- Test root: `tests/`.
- pytest settings: `testpaths = ["tests"]`, `pythonpath = ["src"]`, strict markers, and project-local temporary base directory.
- Baseline collection: 137 tests.
- Tests do not require live market data, Wikipedia, Yahoo Finance, an AI provider, or network access.

## Commands

| Scope | Command | Source |
|---|---|---|
| Full suite | `pytest` | `pyproject.toml`, README |
| One module | `pytest tests/test_scoring.py -q` | Standard pytest invocation supported by configured test root |
| Dependency consistency | `python -m pip check` | Observed delivery-verification procedure |
| CLI smoke | `python -m canslim_analysis --help` | `cli.py` |
| Empty-state smoke | `python -m canslim_analysis status --json --output-dir <empty-directory>` | `pipeline/status.py` |

## Coverage map

| Test module | Principal behavior covered |
|---|---|
| `test_cleanup.py` | Legacy scripts/artifacts removed; source no longer targets `Scripts`. |
| `test_cli.py` | Help, no-command behavior, and unknown-command rejection. |
| `test_documentation.py` | Mandatory specs/wiki paths and current README/package references. |
| `test_enrichment.py` | Template shape, candidate coverage, determinism, zero candidates, duplicates, CLI missing input. |
| `test_enrichment_merge.py` | Exact finding fields, evidence rules, unknown/duplicate/missing coverage, type checks, merge isolation, CLI success. |
| `test_final_reporting.py` | Ranking, grades, score distribution, nullable metrics, empty market, CLI output/errors. |
| `test_infrastructure.py` | Config defaults and bounds, immutability, error hierarchy, path resolution, logging helper. |
| `test_market_data.py` | Symbol parsing/normalization, malformed/empty HTML, transient and bounded failures, custom URL. |
| `test_market_direction.py` | Confirmed uptrend, under pressure, downtrend, short/malformed history, moving-average shape. |
| `test_pdf_reporting.py` | PDF command, deterministic filename, `%PDF-` signature, missing/malformed input. |
| `test_quantitative_cli.py` | Quantitative options, schema metadata, provider failures, universe limit, invalid config. |
| `test_quantitative_transform.py` | Numeric/ratio normalization, CAGR, acceleration, S/N evidence, ownership context, ranking, candidate selection. |
| `test_scoring.py` | Enriched validation, legacy aliases, verified-over-pending precedence, criterion order, S conjunction, M mapping, grades. |
| `test_skill_document.py` | Skill front matter, command alignment, no OpenClaw dependency, safety and response contracts. |
| `test_workflow_run.py` | Full pipeline, findings gate, explicit fallback, total and findings failures. |
| `test_workflow_status.py` | State transitions, invalid state, JSON status, missing validation target. |

## Requirement gate

Every requirement RQ-001 through RQ-014 is mapped in [requirements traceability](requirements-traceability.md). RQ-009 explicitly requires the offline suite; T-017 requires the full-suite gate before completion.

## Full verification

The project-supported verification sequence is:

```powershell
python -m pip check
pytest
python -m canslim_analysis --help
python -m canslim_analysis status --json --output-dir <empty-directory>
```

The delivery revision recorded all four checks as passing.

## Known limits

- Live retrieval from Yahoo Finance and Wikipedia is not exercised by automated tests.
- PDF tests verify generation and file signature, not visual layout or PDF content parsing.
- Status validation is intentionally lightweight for final reports; it does not perform every scoring-field check performed by finalization.
- `configure_logging` is tested as a helper but not wired into CLI dispatch.
- No coverage measurement, mutation testing, linting, type-checking, security scanning, or CI gate is configured.

When adding tests, use injected providers or local temporary fixtures for external systems. Keep the full suite network-free.
