# CANSLIM Analysis — Task Backlog

Status values: `todo`, `in-progress`, `review`, `done`.

A task may move to `done` only when its acceptance tests pass, the full test suite passes, required documentation is synchronized, and an atomic project-local Git commit references the task ID.

## Task Queue

### T-001 Establish package skeleton and offline test harness

- **Status:** `done`
- **Depends on:** None
- **Requirements:** RQ-002, RQ-009, RQ-010, RQ-012, RQ-014
- **Design sections:** §3 Target Architecture, §11 Testing Strategy, §13 Local Setup Design
- **Scope:** Create the installable `src/canslim_analysis` package, CLI entry point, development test extra, and pytest layout. Implement only enough CLI dispatch for `--help` to work.
- **Acceptance test:** A failing test is written first for package import and `python -m canslim_analysis --help`; after implementation, the help command exits `0`, documents available command groups, and `pytest` passes.

### T-002 Add configuration, paths, logging, and error foundation

- **Status:** `done`
- **Depends on:** T-001
- **Requirements:** RQ-004, RQ-011, RQ-012, RQ-013
- **Design sections:** §3.2 Module Responsibilities, §6 Artifact and Path Strategy, §9 Error-Handling Strategy
- **Scope:** Add the project exception hierarchy, immutable configuration type, deterministic output path resolution, and unified logging setup.
- **Acceptance test:** Tests prove valid and invalid configuration values, path overrides, exception classification, and log setup. No path resolution writes files or accesses the network. Full suite passes.

### T-003 Isolate universe retrieval and parsing

- **Status:** `done`
- **Depends on:** T-002
- **Requirements:** RQ-010, RQ-011, RQ-012
- **Design sections:** §3.2 Module Responsibilities, §8.2 Provider Isolation
- **Scope:** Extract S&P 500 universe retrieval behind an injectable provider and separate HTTP retrieval from HTML/list parsing.
- **Acceptance test:** Local fixtures cover a valid ticker list, malformed HTML, an empty result, and an HTTP/network failure. Business logic is verified without network access, and full suite passes.

### T-004 Implement market-direction assessment

- **Status:** `done`
- **Depends on:** T-002
- **Requirements:** RQ-005, RQ-010, RQ-012
- **Design sections:** §7.1 Preserved Schema, §7.2 Scoring Algorithm, §8.2 Provider Isolation
- **Scope:** Extract market-direction logic into a pure function supplied with market history and configuration.
- **Acceptance test:** Tests cover `Confirmed Uptrend`, `Under Pressure`, `Downtrend`, missing data, and insufficient history without network access. Existing result semantics remain unchanged, and full suite passes.

### T-005 Implement quantitative transformation and candidate selection

- **Status:** `done`
- **Depends on:** T-004
- **Requirements:** RQ-005, RQ-010, RQ-011, RQ-012
- **Design sections:** §7.1 Preserved Schema, §7.2 Scoring Algorithm, §8.1 Configuration Object
- **Scope:** Extract EPS calculations, RS ranking inputs, supply/demand analysis, technical N analysis, institutional reference analysis, candidate filtering, and schema `2.1` stock-record construction into explicit pure functions.
- **Acceptance test:** Local fixtures verify all quantitative booleans, threshold boundaries, missing fundamentals, malformed and null market values, technical evidence separation, and candidate ordering. Full suite passes.

### T-006 Implement the quantitative CLI stage

- **Status:** `done`
- **Depends on:** T-003, T-004, T-005
- **Requirements:** RQ-002, RQ-003, RQ-004, RQ-011
- **Design sections:** §5.1 Commands, §6 Artifact and Path Strategy, §8.1 Configuration Object, §8.2 Provider Isolation
- **Scope:** Add the `quantitative` command, inject external providers, expose supported configuration options, write the intermediate JSON artifact, and preserve aggregate metadata.
- **Acceptance test:** CLI tests using fake providers cover successful output, a valid universe limit, individual ticker failure tolerance, zero evaluated stocks, output-directory override, external-data failure, and correct exit codes. Generated data is written only to the selected output location. Full suite passes.

### T-007 Implement enrichment template generation

- **Status:** `done`
- **Depends on:** T-006
- **Requirements:** RQ-002, RQ-003, RQ-006
- **Design sections:** §5.1 Commands, §7.3 Enrichment Findings Template
- **Scope:** Add `prepare-enrichment` and generate one conservative, all-false qualitative template entry for every quantitative candidate.
- **Acceptance test:** Tests cover a valid template, missing quantitative input, malformed input, zero candidates, deterministic ticker matching, and output-directory override. Full suite passes.

### T-008 Implement enrichment validation and merge

- **Status:** `done`
- **Depends on:** T-007
- **Requirements:** RQ-002, RQ-003, RQ-005, RQ-006
- **Design sections:** §5.1 Commands, §7.3 Enrichment Findings Template
- **Scope:** Add the `enrich` command and strict findings validation. Merge only the six documented qualitative fields while preserving quantitative fields.
- **Acceptance test:** Tests cover successful merge, missing candidate, duplicate ticker, unknown ticker, unknown field, non-boolean value, missing rationale for a true finding, malformed schema, and preservation of quantitative data. Invalid findings never create enriched output. Full suite passes.

### T-009 Implement dataset validation and CANSLIM scoring

- **Status:** `done`
- **Depends on:** T-008
- **Requirements:** RQ-005, RQ-010, RQ-012
- **Design sections:** §7.1 Preserved Schema, §7.2 Scoring Algorithm
- **Scope:** Extract schema validation, metric normalization, seven-criterion scoring, grade selection, met/missed ordering, and candidate ranking into testable functions.
- **Acceptance test:** Table-driven tests cover every criterion true and false, combined seven-letter scores, the S conjunction, M market rule, grade boundaries, rank ordering, missing AI checks, and invalid schemas. Full suite passes.

### T-010 Implement final report generation CLI

- **Status:** `done`
- **Depends on:** T-009
- **Requirements:** RQ-002, RQ-003, RQ-004, RQ-005
- **Design sections:** §5.1 Commands, §6 Artifact and Path Strategy, §7 Data Contracts
- **Scope:** Add the `finalize` command to normalize enriched input, calculate final scores, assemble report metadata and score distribution, and write `final_canslim_report.json`.
- **Acceptance test:** CLI tests cover successful report generation, stable ordering, score distribution, nullable metrics, empty candidate handling, missing enriched input, malformed input, and output override. Full suite passes.

### T-011 Implement workflow status and standalone validation

- **Status:** `done`
- **Depends on:** T-010
- **Requirements:** RQ-003, RQ-005
- **Design sections:** §5.3 Workflow State
- **Scope:** Add `status` and `validate`. Classify pipeline state from validated artifacts and report the next valid action.
- **Acceptance test:** Tests cover `not-started`, every complete state, invalid artifact, missing predecessor, human-readable output, and `--json` output. Full suite passes.

### T-012 Implement PDF report generation CLI

- **Status:** `done`
- **Depends on:** T-010
- **Requirements:** RQ-002, RQ-004, RQ-005, RQ-007
- **Design sections:** §3.2 Module Responsibilities, §5.1 Commands, §6 Artifact and Path Strategy
- **Scope:** Move and adapt PDF generation behind the `report` command. Use the final JSON contract and project error handling.
- **Acceptance test:** A fixture-based test renders a deterministic minimal report, verifies the configured output path and PDF signature or readable output, and covers missing input, malformed input, and renderer failure. Full suite passes.

### T-013 Implement complete workflow orchestration

- **Status:** `done`
- **Depends on:** T-006, T-008, T-010, T-012
- **Requirements:** RQ-002, RQ-003, RQ-006
- **Design sections:** §5.2 Orchestration Flow
- **Scope:** Add `run` to execute quantitative, enrichment, final, and PDF stages in order. Require findings unless the user explicitly selects unverified fallback.
- **Acceptance test:** Fake-provider CLI tests cover complete success, stop-after-quantitative behavior when findings are absent, explicit unverified fallback, stage failure short-circuiting, and absence of partial final artifacts when an earlier stage fails. Full suite passes.

### T-014 Reframe the project skill for Codex

- **Status:** `done`
- **Depends on:** T-013
- **Requirements:** RQ-001, RQ-006, RQ-007
- **Design sections:** §4 Codex Skill Contract
- **Scope:** Replace OpenClaw-specific instructions with Codex-readable front matter and a complete agent-neutral workflow, response contract, safety rules, and failure-reporting contract.
- **Acceptance test:** Documentation tests verify valid `name` and `description` front matter, no required OpenClaw execution step, all documented commands exist in CLI help, mandatory qualitative-safety language, and mandated success/failure response elements. Full suite passes.

### T-015 Migrate and synchronize project documentation

- **Status:** `done`
- **Depends on:** T-013
- **Requirements:** RQ-001, RQ-008, RQ-014
- **Design sections:** §12 Documentation and Migration Design, §13 Local Setup Design
- **Scope:** Move useful wiki content from `.doc/wiki` to `doc/wiki`, update architecture/configuration/API/troubleshooting/getting-started content, and rewrite README setup and usage.
- **Acceptance test:** Documentation checks confirm required wiki pages, no stale operational script instructions, no contradictory artifact paths, correct local-environment setup, and consistent CLI examples. Full suite passes.

### T-016 Remove superseded scripts and generated source-directory artifacts

- **Status:** `done`
- **Depends on:** T-014, T-015
- **Requirements:** RQ-004, RQ-008, RQ-012
- **Design sections:** §3.1 Proposed Source Layout, §12.2 Backward Compatibility
- **Scope:** After package behavior and documentation are complete, remove superseded `Scripts/*.py` entry points and operational generated JSON. Preserve only explicitly selected, documented fixtures under `tests/fixtures/`.
- **Acceptance test:** Tests confirm the old script entry points are gone, package CLI remains available, no live pipeline writes to `Scripts/`, selected fixtures are documented, and full suite passes.

### T-017 Perform delivery verification and release checklist

- **Status:** `done`
- **Depends on:** T-016
- **Requirements:** RQ-001 through RQ-014
- **Design sections:** All approved design sections
- **Scope:** Run final offline verification, review requirements-to-task coverage, inspect generated artifacts and documentation, update task statuses, and record delivery results.
- **Acceptance test:** From a clean tracked workspace, documented dependency setup succeeds, `pytest` passes, `python -m canslim_analysis --help` succeeds, `status` handles an empty output directory, no OpenClaw-required workflow remains, and specifications/wiki reflect delivered behavior.

### T-018 Repair zero-candidate qualitative execution

- **Status:** `done`
- **Depends on:** T-017
- **Requirements:** RQ-003, RQ-006, RQ-011, RQ-014, RQ-015
- **Design sections:** §5.2 Orchestration Flow, §5.3 Workflow State, §7.3 Enrichment Findings Template, §8.1 Configuration Object
- **Scope:** Reject stale findings after a zero-candidate quantitative run, allow only explicit fallback to produce a conservative empty report, compare every downstream artifact to its immediate predecessor, activate output-directory logging, suppress provider deprecation noise, and ensure the local editable install resolves to this project.
- **Acceptance test:** Offline workflow tests cover zero candidates with findings and fallback, the enrichment validator reports a zero-candidate mismatch, status detects a stale final report after enriched regeneration, CLI logging and traceback capture are installed, Pandas4 suppression has filter precedence, and the editable-hook source is this project. Full suite passes.

### T-019 Add partial rate-limit recovery

- **Status:** `done`
- **Depends on:** T-018
- **Requirements:** RQ-003, RQ-010, RQ-011
- **Design sections:** §5.2 Orchestration Flow, §8.2 Provider Isolation
- **Scope:** After a live run encounters partial stock-fetch failures, wait once for the provider rate-limit window and retry only failed tickers. Preserve immediate failure for complete provider outages. Keep tests isolated from the default `out/` directory and all generated `out/` artifacts out of Git except the directory placeholder.
- **Acceptance test:** Offline orchestration tests prove a failed ticker is retried after the cooldown and recovered, a total outage performs no cooldown retry, the universe-limit CLI test writes only to its temporary directory, and Git ignores generated workflow artifacts while retaining `out/.gitkeep`. Full suite passes.

### T-020 Guard malformed provider price panels

- **Status:** `done`
- **Depends on:** T-019
- **Requirements:** RQ-010, RQ-011
- **Design sections:** §8.2 Provider Isolation, §9 Error Handling and Reliability
- **Scope:** Discard provider price rows with non-finite required values and reject a stock whose cleaned panel has fewer than the configured usable-history minimum before calculating any metric.
- **Acceptance test:** A provider panel containing at least the minimum raw rows but fewer than the minimum usable bars returns no stock record without retries; the malformed-row transformation regression remains green, and the full suite plus a live Yahoo Finance quantitative run pass.

### T-021 Preserve EPS panel alignment

- **Status:** `done`
- **Depends on:** T-020
- **Requirements:** RQ-010, RQ-011
- **Design sections:** §8.2 Provider Isolation, §9 Error Handling and Reliability
- **Scope:** Preserve missing-value positions when extracting provider EPS rows, select positional valid endpoints for annual CAGR, and require both positional endpoints for quarterly year-over-year comparisons so missing observations cannot shift periods or cause subtraction failures.
- **Acceptance test:** A missing latest quarterly EPS returns no growth instead of raising, a missing middle annual EPS uses true endpoint spacing, an incomplete extraction preserves positional nulls, and the full suite plus a live Yahoo Finance quantitative run pass.

## Dependency Overview

```text
T-001
└── T-002
    ├── T-003
    │   └── T-006 ─┐
    ├── T-004 ─────┤
    │   └── T-005 ─┘
    │              ├── T-007
    │              │   └── T-008
    │              │       └── T-009
    │              │           └── T-010
    │              │               ├── T-011
    │              │               ├── T-012
    │              │               └── T-013
    │              │                   ├── T-014
    │              │                   └── T-015
    │              │                       └── T-016
    │              │                           └── T-017
    │              │                               └── T-018
    │              │                                   └── T-019
    │              │                                       └── T-020
    │              │                                           └── T-021
```

## Coverage Check

| Requirement | Tasks |
|---|---|
| RQ-001 | T-014, T-015, T-017 |
| RQ-002 | T-001, T-006, T-007, T-008, T-010, T-012, T-013 |
| RQ-003 | T-006, T-007, T-008, T-011, T-013 |
| RQ-004 | T-002, T-006, T-010, T-012, T-016 |
| RQ-005 | T-004, T-005, T-008, T-009, T-010, T-011, T-012, T-017 |
| RQ-006 | T-007, T-008, T-013, T-014 |
| RQ-007 | T-012, T-014 |
| RQ-008 | T-015, T-016, T-017 |
| RQ-009 | T-001, T-017 |
| RQ-010 | T-001, T-003, T-004, T-005, T-009, T-020, T-021 |
| RQ-011 | T-002, T-003, T-005, T-006, T-018, T-019, T-020, T-021 |
| RQ-012 | T-001, T-002, T-003, T-004, T-005, T-016, T-017 |
| RQ-013 | T-002, T-017 |
| RQ-014 | T-001, T-015, T-017 |
| RQ-015 | T-018 |
