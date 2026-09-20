# Artifact Inventory

## Method

- Generated: 2026-09-13.
- Source revision: `db36b1cd22ae0b9a63fd6dc329bee535b454713b`.
- Inputs: Git-tracked files, relevant untracked files, specifications, existing wiki.
- Candidate command: `git ls-files`.
- Baseline tree was clean. Pages added by this wiki task are outputs, not pre-write inventory inputs.

## Project artifacts

| Path | Category | Purpose and evidence use | Status |
|---|---|---|---|
| `.gitignore` | Configuration | Excludes virtualenvs, caches, generated reports, secrets, and local state. | Included |
| `README.md` | Existing documentation | Current setup, CLI, artifact paths, scoring contract, exit codes. | Included |
| `SKILL.md` | Existing documentation / agent contract | Codex discovery, operating workflow, safety and response contracts. | Included |
| `pyproject.toml` | Build and dependencies | Python 3.12+, package metadata, pinned runtime dependencies, pytest configuration. | Included |
| `out/.gitkeep` | Repository placeholder | Keeps the output directory represented without generated content. | Included |
| `doc/spec/requirements.md` | Specification | Normative requirements RQ-001 through RQ-015. | Included |
| `doc/spec/design.md` | Specification | Architecture, contracts, alternatives, migration design. | Included |
| `doc/spec/tasks.md` | Specification / progress | T-001 through T-017, dependencies, acceptance tests, completion state. | Included |
| `doc/wiki/API-Reference.md` | Existing wiki | CLI, artifact, and scoring contract summary. | Included; reconciled |
| `doc/wiki/Architecture.md` | Existing wiki | Component responsibilities and data flow. | Included; reconciled |
| `doc/wiki/Configuration.md` | Existing wiki | Defaults and override behavior. | Included; reconciled |
| `doc/wiki/Delivery-Verification.md` | Existing wiki | Release evidence recorded on 2026-09-13. | Included |
| `doc/wiki/FAQ-Troubleshooting.md` | Existing wiki | Short recovery and safety answers. | Included |
| `doc/wiki/Getting-Started.md` | Existing wiki | Setup and state-driven workflow. | Included; reconciled |
| `doc/wiki/Home.md` | Existing wiki | Overview and entry links. | Included; updated by this task |
| `doc/wiki/Modules/AI-Enrichment.md` | Existing wiki | Enrichment commands and safety contract. | Included; reconciled |
| `doc/wiki/Modules/Final-Process.md` | Existing wiki | Final scoring and output contract. | Included; reconciled |
| `doc/wiki/Modules/PDF-Report-Generator.md` | Existing wiki | PDF command and failure behavior. | Included; reconciled |
| `doc/wiki/Modules/Quantitative-Analyzer.md` | Existing wiki | Quantitative stage command and contract. | Included; reconciled |
| `src/canslim_analysis/__init__.py` | Source | Package version `2.1.0`. | Included |
| `src/canslim_analysis/__main__.py` | Source | `python -m canslim_analysis` entry point. | Included |
| `src/canslim_analysis/cli.py` | Source | Eight-command parser, dispatch, defaults, exit codes. | Included |
| `src/canslim_analysis/errors.py` | Source | Project error hierarchy. | Included |
| `src/canslim_analysis/logging_setup.py` | Source | Console/file logging helper. | Included; CLI integration gap documented |
| `src/canslim_analysis/paths.py` | Source | Artifact names and output path resolution. | Included |
| `src/canslim_analysis/pipeline/__init__.py` | Source | Pipeline package marker. | Included |
| `src/canslim_analysis/pipeline/config.py` | Source | Frozen configuration and boundary validation. | Included |
| `src/canslim_analysis/pipeline/enrichment.py` | Source | Quantitative input checks, findings validation, merge, persistence. | Included |
| `src/canslim_analysis/pipeline/market_data.py` | Source | S&P 500 parsing, Yahoo providers, and Pandas4 suppression. | Included |
| `src/canslim_analysis/pipeline/quantitative.py` | Source | Market direction, transformations, ranking, quantitative run, partial-fetch recovery. | Included |
| `src/canslim_analysis/pipeline/reporting.py` | Source | Final-report assembly and persistence. | Included |
| `src/canslim_analysis/pipeline/scoring.py` | Source | Dataset validation, normalization, scoring, grades. | Included |
| `src/canslim_analysis/pipeline/status.py` | Source | Artifact validation and workflow state. | Included |
| `src/canslim_analysis/pipeline/workflow.py` | Source | Ordered quantitative-to-PDF orchestration. | Included |
| `src/canslim_analysis/reporting/__init__.py` | Source | Reporting package marker. | Included |
| `src/canslim_analysis/reporting/pdf.py` | Source | Final-report PDF renderer. | Included |
| `tests/test_cleanup.py` | Tests | Legacy interface removal and no source writes to `Scripts/`. | Included |
| `tests/test_cli.py` | Tests | Top-level help, no-command help, unknown command, runtime logging, and tracebacks. | Included |
| `tests/test_documentation.py` | Tests | Mandatory specs/wiki paths and current README/wiki contracts. | Included |
| `tests/test_enrichment.py` | Tests | Template coverage, determinism, invalid input, CLI missing input. | Included |
| `tests/test_enrichment_merge.py` | Tests | Exact findings shape, evidence, one-to-one merge, CLI success. | Included |
| `tests/test_final_reporting.py` | Tests | Final ranking, distribution, nullable metrics, CLI errors. | Included |
| `tests/test_infrastructure.py` | Tests | Config defaults/bounds, errors, paths, logging helper, and editable-install source. | Included |
| `tests/test_market_data.py` | Tests | HTML parsing, retry, bounded failure, custom universe URL. | Included |
| `tests/test_market_direction.py` | Tests | Uptrend, under pressure, downtrend, malformed/short history. | Included |
| `tests/test_pdf_reporting.py` | Tests | PDF command, naming, signature, missing/malformed input. | Included |
| `tests/test_quantitative_cli.py` | Tests | Overrides, output metadata, provider failures, universe limit. | Included |
| `tests/test_quantitative_transform.py` | Tests | Normalization, EPS, S/N evidence, ranking, schema records. | Included |
| `tests/test_scoring.py` | Tests | Dataset validation, aliases, criteria order, grades. | Included |
| `tests/test_skill_document.py` | Tests | Skill front matter, command alignment, safety/response contract. | Included |
| `tests/test_workflow_run.py` | Tests | Full run, findings stop, fallback, short-circuit failures. | Included |
| `tests/test_workflow_status.py` | Tests | State machine, JSON status, validation missing artifact. | Included |

Complete result: all 51 Git-tracked candidates at the baseline are accounted for.

## Excluded

| Path or pattern | Reason |
|---|---|
| `.git/` | Repository metadata, not project source. |
| `.venv/` | Editable dependency environment. |
| `.pytest_cache/`, `.pytest-tmp/`, `__pycache__/` | Local test/runtime caches. |
| `out/**` except tracked `.gitkeep` | Generated reports, JSON, PDFs, and logs. |
| `*.log` | Generated local diagnostics; inspect locally, do not publish. |
| `.env` and similar private files, if present | Never read or document secret values. |

No relevant untracked files were present at the baseline.

## External dependencies

| Dependency | Constraint | Purpose | Evidence |
|---|---|---|---|
| Python | `>=3.12` | Required language/runtime. | [`../../pyproject.toml`](../../pyproject.toml) |
| requests | `==2.34.2` | HTTP retrieval for the universe provider. | [`../../pyproject.toml`](../../pyproject.toml); verified install |
| yfinance | `==0.2.66` | Market fundamentals and price history. | [`../../pyproject.toml`](../../pyproject.toml); verified install |
| reportlab | `==4.5.1` | PDF rendering. | [`../../pyproject.toml`](../../pyproject.toml); verified install |
| pytest | `==9.1.1` (development) | Test framework. | [`../../pyproject.toml`](../../pyproject.toml) |
| pandas / numpy / Pillow | Installed transitively | yfinance numerical/data support; PDF image support. | Observed editable-install output; not directly pinned |

## Limitations

- No lockfile pins transitive dependency versions.
- Live Yahoo Finance and Wikipedia retrieval was not exercised for this wiki; behavior is supported by source and offline tests.
- There is no CI configuration in the inventory.
