# CANSLIM Analysis — Requirements

## 1. Context

`canslim-analysis` currently implements a hybrid CANSLIM workflow:

1. Quantitative screening with Python and external market-data services.
2. Manual qualitative enrichment previously described as an OpenClaw task.
3. Final scoring, JSON reporting, and PDF report generation.

The project must be refactored so that Codex can discover, operate, validate, and complete the workflow without OpenClaw-specific assumptions. This is an in-place modernization of the existing project, not an extraction into the workspace-level `Skills/` directory.

## 2. Goals

- Make the project directly usable by a Codex agent through clear local instructions.
- Replace OpenClaw-specific workflow language with agent-neutral, Codex-executable instructions.
- Provide one stable command-line interface for the analysis stages.
- Preserve the existing CANSLIM scoring contract and data compatibility.
- Establish the mandatory specification layout and an automated test foundation.

## 3. Functional Requirements

### RQ-001 — Codex-ready project skill definition

**Priority:** MUST

The project root SHALL contain a Codex-readable skill definition that identifies the project, states when Codex should use it, and describes the complete operating workflow.

**Acceptance criteria:**

- `SKILL.md` contains valid front matter with `name` and `description`.
- `SKILL.md` contains no required OpenClaw-specific execution step.
- `SKILL.md` explains prerequisites, safe setup, stage execution, validation, output handling, failure reporting, and cleanup.
- A new contributor can determine how to run the workflow from `SKILL.md` alone.

### RQ-002 — Stable Codex-facing command-line interface

**Priority:** MUST

The project SHALL expose one stable CLI entry point through which Codex can run the workflow stages without editing Python source constants.

**Acceptance criteria:**

- Running the documented help command succeeds and returns usage information.
- The CLI supports the logical stages represented by the existing pipeline: quantitative screening, qualitative enrichment, final scoring/reporting, and PDF generation.
- Each stage can be invoked independently.
- A documented command can orchestrate the stages in the correct order.
- CLI inputs do not require source-code modification.

### RQ-003 — Explicit workflow state and next-action guidance

**Priority:** MUST

The CLI or skill workflow SHALL make the current pipeline state clear from artifact paths or a status command.

**Acceptance criteria:**

- Codex can distinguish absent quantitative output, present-but-unenriched output, enriched output, and final report output.
- The workflow documentation states the valid order of stage execution.
- If a required predecessor artifact is missing, the next stage fails with a clear, actionable error rather than silently inventing data.

### RQ-004 — Deterministic artifact locations

**Priority:** MUST

Generated artifacts SHALL be written to stable, project-local locations that are documented and excluded from source-controlled generated data where appropriate.

**Acceptance criteria:**

- Quantitative, enriched, final JSON, log, and PDF outputs each have one documented target path or documented pattern.
- No stage requires generated output to be written into a source directory merely to function.
- Existing committed sample artifacts are either explicitly treated as fixtures with a documented purpose or removed from operational use.

### RQ-005 — JSON schema and scoring compatibility

**Priority:** MUST

The refactored workflow SHALL preserve the current CANSLIM scoring model and remain compatible with the established JSON field contracts unless a later, explicitly approved requirement changes them.

**Acceptance criteria:**

- Final scoring uses the documented mappings for C, A, N, S, L, I, and M.
- Final output includes composite score, grade, met and missed criteria, and candidate ranking.
- Automated tests cover normalization, scoring, missing AI data, invalid data, and rank ordering.
- A schema mismatch produces a validation failure and identifies the missing or invalid field.

### RQ-006 — Safe qualitative enrichment behavior

**Priority:** MUST

The qualitative enrichment stage SHALL explicitly distinguish verified AI findings from unavailable or unverified findings.

**Acceptance criteria:**

- Missing catalyst evidence sets the scored N check to false.
- Missing float-tightness evidence sets the scored S qualitative check to false.
- Missing institutional-quality evidence sets the scored I qualitative check to false.
- The enrichment format includes a concise evidence or rationale field.
- The workflow forbids fabricated catalysts, float conclusions, or institutional-quality claims.

### RQ-007 — User-facing result contract

**Priority:** MUST

The skill instructions SHALL define the final Codex response format for a successful analysis and a failed run.

**Acceptance criteria:**

- Successful output identifies market environment, ranked candidates, key metrics, AI catalyst insight, caveats, and investment-analysis disclaimer.
- Failure output identifies the failed phase, actionable error information, and the smallest next step.
- Missing-data limitations are disclosed rather than presented as confirmed analysis.

### RQ-008 — Mandatory documentation migration

**Priority:** MUST

The project SHALL use the workspace-mandated documentation layout and keep specifications synchronized with implementation.

**Acceptance criteria:**

- `doc/spec/requirements.md`, `doc/spec/design.md`, and `doc/spec/tasks.md` exist.
- Living project documentation is located under `doc/wiki/`.
- The legacy `.doc/` directory is migrated or superseded without losing materially useful documentation.
- README and skill instructions agree with the implemented CLI and paths.

### RQ-009 — Automated verification foundation

**Priority:** MUST

The project SHALL provide an automated test suite covering pure transformation, scoring, validation, and CLI dispatch behavior without requiring live market-data or AI access.

**Acceptance criteria:**

- A single documented test command runs the full suite.
- The suite passes on a clean checkout after documented dependency setup.
- Tests use local fixtures for schema, scoring, error-path, and CLI cases.
- Full-suite status is checked before each refactor task is marked done.

## 4. Non-Functional Requirements

### RQ-010 — Testability and offline safety

**Priority:** MUST

Core scoring, normalization, validation, report-data preparation, and CLI dispatch SHALL be testable without internet access.

**Acceptance criteria:**

- External-data retrieval is isolated from pure business logic.
- No automated test requires live Yahoo Finance, Wikipedia, or AI-provider access.
- Deterministic fixtures cover normal, boundary, missing, malformed, and empty inputs where applicable.

### RQ-011 — Reliability and deliberate failure handling

**Priority:** MUST

All external input, file input/output, network access, and subprocess or report generation failures SHALL be handled deliberately.

**Acceptance criteria:**

- No exception is silently swallowed without justification.
- User-facing and log errors identify the failed stage.
- Transient external-data failures use bounded retry behavior.
- Timeouts prevent unbounded network waits.

### RQ-012 — Maintainability

**Priority:** MUST

The refactored code SHALL separate orchestration, external-data access, transformation, scoring, and presentation concerns.

**Acceptance criteria:**

- Business rules do not depend directly on ad hoc global script state.
- Public functions and schema elements have documentation.
- Naming follows the project's existing conventions or an explicitly documented convention.
- No dead code or commented-out implementation is introduced.

### RQ-013 — Security and secret handling

**Priority:** MUST

Secrets SHALL NOT be stored in source, configuration, logs, reports, tests, or documentation.

**Acceptance criteria:**

- Any optional credential is supplied by environment variable or another supported local secret mechanism.
- Generated reports and logs are checked for secret leakage requirements.
- External input is validated before use.
- Dependencies remain intentionally selected, justified, and constrained to compatible versions.

### RQ-014 — Reproducible local setup

**Priority:** SHOULD

The project SHALL document a reproducible local environment setup suitable for Codex execution.

**Acceptance criteria:**

- The instructions use a project-local virtual environment rather than global installation.
- Dependency installation is documented.
- Python version expectations are explicit.
- Setup does not require undocumented global changes.

### RQ-015 — Zero-candidate qualitative guard

**Priority:** MUST

The workflow SHALL prevent qualitative findings from one quantitative run from being merged into a different run that selected no candidates.

**Acceptance criteria:**

- A quantitative artifact with an empty `Stocks` array remains valid and can produce an empty enrichment worksheet.
- `run` with supplied non-empty findings and zero candidates stops before enrichment and gives actionable guidance without treating old findings as verified.
- `run --unverified-fallback` may continue with zero candidates only because all qualitative values remain explicitly conservative false values.
- Runtime logging is written to the selected output directory and the local editable installation resolves to this project's source tree.

### RQ-016 — Artifact-driven verified research mode

**Priority:** MUST

The CLI SHALL provide a verified research mode that accepts an explicit intermediate quantitative artifact, validates it before research, derives every research target solely and order-preservingly from its passing-candidate rows, produces schema-compatible findings, and atomically persists the result.

**Acceptance criteria:**

- Passing candidates are the rows in `Stocks`, with `Metadata.Stocks_Passed_To_AI` equal to the row count and greater than zero.
- Candidate occurrence identity preserves separate share classes and, when duplicate tickers are present, requires unique explicit `Candidate_ID` values on both candidate and finding rows.
- A positive evidence record may include `Candidate_ID` as additive occurrence identity; when present, it SHALL be non-empty text matching one candidate occurrence, while omission remains valid for a ticker-unique legacy record.
- Existing intermediate and findings files that use the schema 2.1 ticker-only contract remain accepted.
- `analysis_date` is parsed from `Metadata.Date_Run`; missing or malformed dates fail before research.
- Research evidence records are dated, attributed, retrievable, issuer/share-class specific, and dated no later than `analysis_date`.
- True N, S, and I flags require source, publication or filing date, canonical citation, evidence summary, and criterion context; unsupported, ambiguous, contradictory, stale, or low-quality evidence remains false.
- Secondary offerings, lockup expirations, dilution, and unexecuted buyback authorizations are never classified automatically as positive float tightness.
- Research output is validated and written atomically, with no completed-looking findings file left after a research failure.
- Missing/unreadable input, malformed or schema-invalid input, zero candidates, unsafe identity, unavailable research evidence, and downstream failures return documented non-zero exits.

## 5. Constraints

- Work must remain inside `Projects/canslim-analysis`.
- The project-local Git repository is the only repository used for this task.
- Implementation must follow strict TDD after requirements, design, and task decomposition are approved.
- Existing quantitative behavior and scoring semantics must not change merely as part of refactoring.
- Generated outputs must not be treated as source fixtures unless explicitly committed and documented for that purpose.
- Dependencies must not be added unless the standard library or an existing dependency is insufficient, and the rationale must be recorded.

## 6. Out of Scope

- Changing the CANSLIM investment methodology or thresholds.
- Replacing external market-data providers.
- Building a hosted service, web interface, scheduler, or database.
- Adding paid AI-provider integration.
- Guaranteeing investment outcomes.
- Migrating the project to the workspace-level `Skills/` directory.

## 7. Release Criteria

The refactor is complete when:

1. All MUST and SHOULD requirements have corresponding tasks and verification evidence.
2. The full automated test suite passes.
3. The documented CLI workflow can be operated from the project root without OpenClaw-specific steps.
4. The mandatory specifications and wiki reflect the delivered implementation.
5. Project-local commits are atomic and reference their task IDs.
