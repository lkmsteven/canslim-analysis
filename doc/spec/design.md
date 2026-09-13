# CANSLIM Analysis — Design

## 1. Design Summary

The project will be refactored into a small Python package with a Codex-facing command-line interface. The analysis logic will remain separate from external-data access and presentation. The existing CANSLIM schema version `2.1` and scoring semantics will be preserved.

Codex will operate the workflow through a local skill document and stable CLI commands. Qualitative research remains a Codex task, but Codex will express its findings in a structured JSON template that the CLI validates and merges into the pipeline. The CLI will not invent qualitative conclusions.

## 2. Requirements-to-Design Traceability

| Requirement | Design element |
|---|---|
| RQ-001 | §4 Codex skill contract; §12 documentation design |
| RQ-002 | §5.1 CLI commands; §5.2 orchestration flow |
| RQ-003 | §5.3 status and state machine; §6 artifact paths |
| RQ-004 | §6 artifact and path strategy |
| RQ-005 | §7.1 JSON contracts; §7.2 scoring algorithm |
| RQ-006 | §7.3 enrichment findings and merge rules |
| RQ-007 | §4.2 success and failure response contract |
| RQ-008 | §12 documentation and migration plan |
| RQ-009 | §11 testing strategy and task verification |
| RQ-010 | §8.2 provider isolation and offline tests |
| RQ-011 | §9 error handling and reliability |
| RQ-012 | §3 module architecture and boundaries |
| RQ-013 | §10 security and configuration design |
| RQ-014 | §13 local setup and reproducibility |

## 3. Target Architecture

### 3.1 Proposed source layout

```text
Projects/canslim-analysis/
├── SKILL.md
├── README.md
├── pyproject.toml
├── doc/
│   ├── spec/
│   │   ├── requirements.md
│   │   ├── design.md
│   │   └── tasks.md
│   └── wiki/
├── src/canslim_analysis/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── errors.py
│   ├── logging_setup.py
│   ├── paths.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── market_data.py
│   │   ├── quantitative.py
│   │   ├── enrichment.py
│   │   ├── scoring.py
│   │   └── reporting.py
│   └── reporting/
│       ├── __init__.py
│       └── pdf.py
├── tests/
│   ├── fixtures/
│   └── ...
└── out/
```

The existing logic in `Scripts/*.py` will be migrated into this package and the old scripts will be removed after their behavior is represented by package modules and tests. Existing committed JSON files will either become named test fixtures under `tests/fixtures/` or be removed from operational use; they will no longer be treated as live pipeline inputs.

### 3.2 Module responsibilities

| Module | Responsibility | Forbidden dependencies |
|---|---|---|
| `cli.py` | Argument parsing, command dispatch, exit-code mapping | Direct Yahoo Finance or Wikipedia access |
| `pipeline/market_data.py` | Fetch and parse an equity universe and market/history data through narrow provider functions | Business scoring or report rendering |
| `pipeline/quantitative.py` | Transform fetched records into schema `2.1` quantitative metrics | Interactive input or PDF rendering |
| `pipeline/enrichment.py` | Load, validate, merge, and normalize Codex qualitative findings | Network access or report rendering |
| `pipeline/scoring.py` | Validate datasets and calculate the seven-letter CANSLIM score | Network access, logging configuration, rendering |
| `pipeline/reporting.py` | Prepare final-report dictionaries and JSON output | Market-data retrieval |
| `reporting/pdf.py` | Render an existing final report to PDF | Market-data retrieval or enrichment |
| `paths.py` | Resolve project-local default paths and CLI overrides | Business logic |
| `errors.py` | Define the public exception hierarchy | Business logic |
| `logging_setup.py` | Configure consistent console and file logging | Business logic |

Pure functions will accept explicit inputs and configuration objects or mappings. Functions will not read module-level constants for thresholds, paths, retries, or worker counts.

## 4. Codex Skill Contract

### 4.1 Discovery and operation

The project-root `SKILL.md` will contain:

```yaml
---
name: canslim-analysis
description: Run and validate the local CANSLIM analysis pipeline through its supported CLI.
---
```

The body will be agent-neutral and will instruct Codex to:

1. Confirm the project root and use the documented local environment.
2. Inspect workflow state with the CLI before overwriting artifacts.
3. Run quantitative analysis when required.
4. Generate the structured enrichment template.
5. Perform qualitative research and fill only verified findings.
6. Validate and merge findings through the CLI.
7. Generate final JSON and PDF outputs.
8. Report results using the mandated response format.
9. Report failures by phase with the smallest useful next action.

Codex must not edit generated JSON to force a stage to pass. Qualitative changes must pass through the enrichment validation command.

### 4.2 User-facing response contract

For success, Codex will summarize:

- Market environment and M result.
- Ranked candidates with ticker, company, score, met/missed criteria, price, RS rating, and catalyst note.
- Important AI catalyst insight.
- Missing-data caveats.
- A statement that the output is not investment advice.

For failure, Codex will identify:

- Failed phase: setup, quantitative, enrichment, final processing, or PDF reporting.
- The concise actionable error.
- The smallest next step.
- Any missing required field when the failure is schema-related.

## 5. Command-Line Interface

### 5.1 Commands

The package will be invoked as:

```text
python -m canslim_analysis
```

The standard library `argparse` module will provide these commands:

| Command | Purpose |
|---|---|
| `quantitative` | Fetch market data, evaluate quantitative criteria, and write `intermediate_canslim.json`. |
| `prepare-enrichment` | Read quantitative output and create a structured findings template. |
| `enrich` | Validate a Codex findings file and merge it into `enriched_canslim.json`. |
| `finalize` | Validate enriched input, score candidates, and write `final_canslim_report.json`. |
| `report` | Render an existing final JSON report as a PDF. |
| `run` | Execute the complete ordered workflow. |
| `status` | Report which pipeline artifacts exist and the next valid action. |
| `validate` | Validate one selected artifact without writing output. |

All commands will support `--help`. Commands that read or write pipeline artifacts will support explicit path or output-directory overrides. The default remains the project-local `out/` directory.

### 5.2 Orchestration flow

`run` will execute:

1. Quantitative screening.
2. Enrichment merge from a supplied findings file.
3. Final scoring.
4. PDF report generation.

By default, `run --findings <file>` is the complete path. If `--findings` is omitted, the command will stop after quantitative analysis and instruct the user or agent to run `prepare-enrichment`, research the candidates, and provide findings. An explicit `--unverified-fallback` option may continue with every qualitative check set to false; its output will identify those checks as unverified. This prevents the CLI from silently presenting conservative fallback results as AI-verified analysis.

### 5.3 Workflow state

`status` will classify the artifact state as:

| State | Condition |
|---|---|
| `not-started` | No intermediate report exists. |
| `quantitative-complete` | Intermediate report is valid. |
| `enrichment-ready` | Quantitative output and enrichment template exist. |
| `enrichment-complete` | Enriched report is valid. |
| `final-complete` | Final JSON report is valid. |
| `report-complete` | Final JSON and PDF report exist. |
| `invalid` | A file exists but fails validation. |

The human-readable status will include the next valid command. A `--json` option will emit machine-readable state for deterministic agent use.

## 6. Artifact and Path Strategy

Default generated files will be:

| Artifact | Default path |
|---|---|
| Application log | `out/canslim_analysis.log` |
| Quantitative output | `out/intermediate_canslim.json` |
| Enrichment template | `out/enrichment_template.json` |
| Codex findings input | Agent-provided path or `out/enrichment_findings.json` |
| Enriched output | `out/enriched_canslim.json` |
| Final JSON | `out/final_canslim_report.json` |
| PDF report | `out/canslim_report_<YYYY-MM-DD>.pdf` |

Generated paths will be excluded from Git. Input overrides will be resolved before reading. Output overrides will be resolved before writing. Commands will not write generated artifacts into `src/` or `Scripts/`.

The current stable filenames intentionally favor deterministic agent operation over retaining every historical run. Retaining run history is out of scope.

## 7. Data Contracts

### 7.1 Preserved schema

The existing quantitative, enriched, and final report schema version `2.1` will be retained.

The implementation will preserve these important existing distinctions:

- Technical near-high/breakout evidence is not itself the scored N criterion.
- Quantitative supply/demand evidence is only one half of the scored S criterion.
- Institutional-ownership percentage is reference evidence, not itself the scored I criterion.
- M is true only for `Confirmed Uptrend`.

The enrichment template is a new operational artifact, not a change to the existing enriched schema.

### 7.2 Scoring algorithm

The final score remains a count of seven booleans:

| Criterion | Scored as true when |
|---|---|
| C | `Quantitative_Metrics.C_Met` is true. |
| A | `Quantitative_Metrics.A_Met` is true. |
| N | `AI_Qualitative_Checks.N_New_Catalyst` is true. |
| S | `Quantitative_Metrics.S_Quant_Met` and `AI_Qualitative_Checks.S_Float_Tightness` are both true. |
| L | `Quantitative_Metrics.L_Met` is true. |
| I | `AI_Qualitative_Checks.I_Institutional_Quality` is true. |
| M | `Metadata.Market_Direction_M` equals `Confirmed Uptrend`. |

Candidates will be ordered by final score descending, then RS rating descending. Missing optional metrics remain nullable in JSON rather than being converted to fabricated zeros.

### 7.3 Enrichment findings template

`prepare-enrichment` will emit one template entry for every stock in the quantitative output. Each entry will use:

```json
{
  "Ticker": "EXAMPLE",
  "N_New_Catalyst": false,
  "N_Catalyst_Details": "",
  "S_Float_Tightness": false,
  "S_Float_Details": "",
  "I_Institutional_Quality": false,
  "I_Institutional_Details": ""
}
```

The findings input will contain a `Findings` array. `enrich` will enforce:

- The quantitative input is valid.
- Every finding ticker matches a candidate.
- Every candidate has exactly one finding.
- Boolean fields are actual booleans, not strings or numbers.
- A true finding has a non-empty corresponding evidence or rationale string.
- A false finding may have an explanatory reason, but the CLI will not fabricate one.
- Unknown tickers and unknown fields are rejected.

Successful merge will preserve all quantitative fields and replace only the six qualitative fields represented by the template.

## 8. External Data and Configuration

### 8.1 Configuration object

A typed, immutable configuration object will replace module constants at call sites. It will carry quantitative thresholds, concurrency, timeout, retry, universe limit, and path settings.

CLI defaults will preserve current behavior:

| Setting | Current default |
|---|---|
| Minimum quarterly EPS growth | `0.25` |
| Minimum annual EPS growth | `0.25` |
| Minimum RS rating | `80.0` |
| Strong-volume ratio | `1.5` |
| Positive volume-skew ratio | `1.2` |
| Reference institutional ownership | `0.30` |
| Near-high threshold | `0.10` |
| Worker count | `5` |
| Request timeout | `10` seconds |
| Retry count | `3` |
| Retry delay | `2` seconds |
| Universe limit | unlimited, with an optional CLI limit |

The CLI will expose operationally useful options rather than requiring source edits. The first implementation will expose universe limit, worker count, timeout, retry count, output directory, and principal quantitative thresholds.

### 8.2 Provider isolation

External access will be isolated behind small, injectable functions or classes:

- Universe provider: returns ticker symbols.
- Market-direction provider: returns market-history data.
- Stock-data provider: returns fundamentals and price history for one ticker.

CLI composition will install Yahoo Finance and Wikipedia-backed implementations. Tests will install in-memory or file-backed fakes. This avoids live network access in unit tests and allows malformed, partial, timeout, and empty external responses to be tested deterministically.

No new category of runtime dependency is required. Direct runtime dependencies are `requests` for HTTP retrieval, `yfinance` for market data (which supplies pandas transitively), and `reportlab` for PDF rendering. They are pinned to versions verified by local setup. The former direct `lxml` and `tqdm` dependencies are removed because the new HTML parser and orchestration do not use them. `pytest` remains a development-only test dependency.

## 9. Error-Handling Strategy

### 9.1 Exception hierarchy

| Exception | Meaning |
|---|---|
| `CanslimError` | Base class for expected project errors. |
| `ConfigurationError` | Invalid CLI values, paths, or environment configuration. |
| `ArtifactNotFoundError` | A required predecessor artifact is absent. |
| `SchemaValidationError` | A dataset has a missing, unknown, malformed, duplicate, or inconsistent field. |
| `ExternalDataError` | Network, HTTP, parsing, timeout, or empty-universe failure. |
| `ReportGenerationError` | Final or PDF report generation failure. |

### 9.2 CLI behavior

Expected errors will produce one clear stderr message and a documented exit code. Unexpected errors will log the stack trace when `--debug` is enabled and otherwise report that an unexpected failure occurred.

| Exit code | Meaning |
|---|---|
| `0` | Success. |
| `1` | Unexpected internal error. |
| `2` | CLI usage error. |
| `3` | Schema or validation failure. |
| `4` | Missing artifact. |
| `5` | External-data failure. |
| `6` | Report-generation failure. |

The quantitative stage may tolerate individual ticker failures because partial market data is normal, but it must fail when it cannot obtain a universe, market-direction data, or any valid stock data. Enrichment and final processing must fail closed on schema inconsistency.

## 10. Security Considerations

- No secret is required by the current pipeline; optional future credentials must come from environment variables and must never be logged.
- HTTP responses are validated before parsing.
- External HTML and financial values are treated as untrusted input and normalized defensively.
- Error messages describe data problems without dumping full external response bodies.
- Output paths supplied on the CLI are explicit user or agent decisions; the tool will not construct paths from untrusted market-data content.
- Logs and reports will contain analysis data, not credentials or local secret values.
- Dependencies remain limited to current runtime needs plus development-only test tooling.

## 11. Testing Strategy

The full-suite command will be:

```text
pytest
```

Automated tests will use local fixtures and fakes. Required coverage includes:

| Area | Verified behavior |
|---|---|
| Quantitative transformation | C, A, L, S, technical N, missing fundamentals, boundary thresholds, and rank order. |
| Market-data normalization | Missing, malformed, null, and valid values. |
| Universe parsing | Valid ticker list, malformed HTML, empty list, and HTTP failure. |
| Market direction | Uptrend, under-pressure, downtrend, and insufficient-history branches. |
| Enrichment | Template generation, merge, duplicate/unknown ticker rejection, malformed booleans, missing rationale for true findings, and false fallback behavior. |
| Scoring | Every criterion, combined scores, met/missed ordering, M behavior, and grade boundaries. |
| Final reporting | Empty input handling, nullable metrics, deterministic ordering, and score distribution. |
| CLI | Help, stage dispatch, status transitions, validation failures, output paths, and exit codes. |
| PDF | Report-data rendering using a small fixture; rendering failures raise the project error type. |

Each task will follow red-green-refactor TDD. A task is done only after its new tests and the entire suite pass.

## 12. Documentation and Migration Design

### 12.1 Migration actions

1. Move useful pages from `.doc/wiki/` to `doc/wiki/`.
2. Remove `.doc/` after verifying no useful content is lost.
3. Replace OpenClaw instructions with the Codex skill workflow.
4. Update README, architecture, getting-started, configuration, API reference, and troubleshooting pages.
5. Record the project-local Git migration decisions in the wiki.
6. Keep `requirements.md`, `design.md`, and `tasks.md` synchronized during implementation.

### 12.2 Backward compatibility

JSON schema `2.1`, scoring rules, and report semantics remain compatible. Script paths are not guaranteed: `Scripts/quantitative_analyzer.py`, `Scripts/final_process.py`, and `Scripts/pdf_report_generator.py` are superseded by `python -m canslim_analysis`. This interface change is intentional and will be documented in README, wiki, and `SKILL.md`.

## 13. Local Setup Design

The documented setup will use a project-local virtual environment, an editable package install, and explicit Python version expectations. Runtime dependencies will remain declared in `pyproject.toml`; test tooling will be declared as a development extra.

The representative setup is:

```text
python -m venv .venv
activate .venv
python -m pip install -e '.[dev]'
pytest
python -m canslim_analysis --help
```

No global dependency installation will be documented or required.

## 14. Alternatives Considered

### 14.1 Keep standalone scripts and update prose only

This was rejected because the middle stage remains undocumented in executable terms, generated files mix with source files, and there is no practical way to test scoring and validation independently.

### 14.2 Add a thin wrapper around existing scripts

This was rejected as a lower-risk but inadequate option. It would improve invocation but retain global constants, hard-coded paths, weak separation, and untested scoring behavior.

### 14.3 Package-based CLI

This option was selected because it provides stable commands, dependency injection points, explicit configuration, testable pure functions, and deterministic artifact handling without changing the investment methodology.

### 14.4 Call an external AI provider during enrichment

This was rejected because it would add credentials, cost, nondeterminism, and an undisclosed dependency. Codex can perform qualitative research and record evidence in a validated local file without embedding a provider in the pipeline.

### 14.5 Use a schema-validation dependency

Using a schema library was considered but rejected for now. The validation rules are small and domain-specific, and adding a runtime dependency is not justified when explicit normalization and validation functions can be tested directly.

## 15. Expected Refactor Outcome

After implementation, Codex can:

1. Discover the project skill and follow its workflow.
2. Determine pipeline state before acting.
3. Run quantitative analysis with explicit configuration.
4. Generate a structured enrichment worksheet.
5. Add only evidence-backed qualitative findings.
6. Validate and merge findings without hand-editing pipeline state.
7. Produce final JSON and PDF artifacts in stable project-local paths.
8. Report success or failure consistently.

The repository will also have the mandatory specification layout, synchronized wiki, reproducible setup, and an offline test suite.
