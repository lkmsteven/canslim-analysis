# Architecture Decision Record

These decisions are reconciled from [`../spec/design.md`](../spec/design.md), task history, and delivered source. Each is implemented unless a consequence says otherwise.

## D-001 Use a package CLI instead of standalone scripts

- **Decision:** Run all stages through `python -m canslim_analysis`.
- **Status:** Implemented.
- **Context:** The original `Scripts/*.py` design mixed generated JSON with source and required manual orchestration.
- **Alternatives documented:** Keep scripts with revised prose; add a thin wrapper.
- **Rationale:** A package exposes stable commands, dependency injection, testable transformations, and deterministic paths.
- **Consequence:** Legacy script paths were removed in T-016; the interface break is documented in README and wiki.
- **Evidence:** `src/canslim_analysis/cli.py`, `pipeline/workflow.py`, `tests/test_cleanup.py`.

## D-002 Preserve schema 2.1 and scoring semantics

- **Decision:** Retain existing field names and seven-criterion scoring.
- **Status:** Implemented.
- **Context:** Existing JSON consumers and the investment methodology depend on compatible semantics.
- **Rationale:** Refactoring should not silently change analysis behavior.
- **Consequence:** Legacy aliases remain supported and nullable values remain nullable.
- **Evidence:** `pipeline/scoring.py`, `pipeline/reporting.py`, `tests/test_scoring.py`, `tests/test_final_reporting.py`.

## D-003 Keep qualitative judgment outside the executable pipeline

- **Decision:** Codex or a qualified reviewer researches findings; the CLI validates and merges them.
- **Status:** Implemented.
- **Alternatives documented:** Embed an external AI provider call.
- **Rationale:** Avoids credentials, provider cost, nondeterminism, and fabricated conclusions inside the pipeline.
- **Consequence:** `run` stops without findings unless the user explicitly chooses conservative fallback.
- **Evidence:** `pipeline/workflow.py`, `pipeline/enrichment.py`, `tests/test_workflow_run.py`.

## D-004 Validate findings fail-closed

- **Decision:** Require exact fields, booleans, one-to-one coverage, and evidence for true claims.
- **Status:** Implemented.
- **Rationale:** Missing evidence must produce `false`, not ambiguity or fabricated confirmation.
- **Evidence:** `validate_findings`, `merge_enrichment`, enrichment tests.

## D-005 Use deterministic output names

- **Decision:** Keep stable `out/` filenames rather than timestamped run directories.
- **Status:** Implemented.
- **Rationale:** Stable names make state inspection and agent operation unambiguous.
- **Consequence:** A rerun overwrites the same stage artifacts; retention is the operator's responsibility.
- **Evidence:** `paths.py`, stage tests, `operations.md`.

## D-006 Isolate external access for offline tests

- **Decision:** Inject universe, market-history, and stock providers.
- **Status:** Implemented.
- **Rationale:** Scoring and workflow behavior can be tested without network, secrets, or live volatility.
- **Evidence:** `QuantitativeProviders`, `tests/test_quantitative_cli.py`, `tests/test_workflow_run.py`.

## D-007 Do not add a schema-validation runtime dependency

- **Decision:** Use explicit domain validation functions.
- **Status:** Implemented.
- **Rationale:** Existing direct dependencies do not justify a new schema library for these focused contracts.
- **Consequence:** New fields require deliberate validator and test updates.
- **Evidence:** `pipeline/enrichment.py`, `pipeline/scoring.py`, `pipeline/status.py`.

## D-008 Remove obsolete direct dependencies

- **Decision:** Pin `requests`, `yfinance`, and `reportlab`; remove direct `lxml` and `tqdm`.
- **Status:** Implemented.
- **Context:** Cleanup and design reconciliation occurred in T-016/T-017.
- **Rationale:** The delivered parser and orchestration no longer use them directly.
- **Consequence:** `pandas` remains available transitively through `yfinance`; no lockfile pins transitive versions.
- **Evidence:** `pyproject.toml`, `artifact-inventory.md`.

## D-009 Keep verified research deterministic and fail-closed

**Decision:** Convert only an explicit, complete evidence artifact; preserve occurrence order and `Candidate_ID`; allow optional occurrence identity on legacy positive records but validate any included ID as non-empty and matching; apply only the analysis-date cutoff; keep nonqualifying evidence false; and prohibit unverified fallback on the command.

- **Status:** Implemented.
- **Context:** Quantitative candidates can contain separate share classes and duplicate tickers, while older ticker-unique artifacts must remain usable.
- **Alternatives documented:** Manual findings editing, provider-side identity resolution, and a fixed backward lookback.
- **Rationale:** Artifact-driven discovery, auditable citations, exact occurrence identity, and conservative classification prevent stale-count merges, collapsed occurrences, and unsupported true flags.
- **Consequence:** A malformed evidence or identity mismatch exits non-zero without completed output. The primary-source preference is an operating rule; direct structural checks cover retrievability and known nonqualifying categories.
- **Evidence:** `pipeline/research.py`, `tests/test_verified_research.py`, `doc/spec/design.md` §16.
