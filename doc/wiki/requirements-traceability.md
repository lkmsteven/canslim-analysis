# Requirements Traceability

Normative IDs come from [`../spec/requirements.md`](../spec/requirements.md). Design references come from [`../spec/design.md`](../spec/design.md); task IDs come from [`../spec/tasks.md`](../spec/tasks.md).

| Requirement | Priority | Design | Tasks | Implementation evidence | Test evidence | Status |
|---|---|---|---|---|---|---|
| RQ-001 Codex-ready skill | MUST | §4 | T-014, T-015, T-017 | `SKILL.md` has `name` and `description`; workflow is agent-neutral. | `tests/test_skill_document.py` | Verified |
| RQ-002 Stable CLI | MUST | §5, §16.3 | T-001, T-006–T-010, T-012, T-013, T-024 | `cli.py` implements and dispatches all nine commands, including `verified-research`. | `test_cli.py`, `test_verified_research.py`; stage-specific tests | Verified |
| RQ-003 State and next action | MUST | §5.3 | T-006–T-008, T-011, T-013, T-018 | `pipeline/status.py` classifies states, checks immediate-predecessor freshness, and supplies next command. | `test_workflow_status.py` | Verified |
| RQ-004 Deterministic artifacts | MUST | §6 | T-002, T-006, T-010, T-012, T-016 | `paths.py` defines stable names; commands accept `--output-dir`; `Scripts/` operational files removed. | Infrastructure and stage CLI tests; `test_cleanup.py` | Verified |
| RQ-005 JSON and scoring compatibility | MUST | §7 | T-004, T-005, T-008–T-010, T-012 | Scoring/report/enrichment modules preserve schema `2.1` and seven-criterion mapping. | `test_quantitative_transform.py`, `test_scoring.py`, `test_final_reporting.py` | Verified |
| RQ-006 Safe enrichment | MUST | §7.3 | T-007, T-008, T-013, T-014, T-018 | Findings require exact shape, one-to-one coverage, booleans, evidence for true claims, and a zero-candidate mismatch guard. | `test_enrichment.py`, `test_enrichment_merge.py`, `test_workflow_run.py` | Verified |
| RQ-007 Result contract | MUST | §4.2 | T-012, T-014 | `SKILL.md` defines success/failure response; PDF includes disclaimer. | `test_skill_document.py`, `test_pdf_reporting.py` | Verified |
| RQ-008 Documentation migration | MUST | §12 | T-015–T-017 | Specs live in `doc/spec`; wiki in `doc/wiki`; `.doc` and stale scripts removed. | `test_documentation.py`, `test_cleanup.py` | Verified |
| RQ-009 Offline verification | MUST | §11, §16.3 | T-001, T-017, T-018, T-019, T-022–T-024 | Pytest configuration uses local `src` and project-local temporary files; providers and research fixtures are offline. | 177 tests collected; full suite passed | Verified |
| RQ-010 Testability and offline safety | MUST | §8.2, §11 | T-001, T-003–T-005, T-009 | External access is isolated in providers; transformations accept supplied values/bars. | market-data, market-direction, quantitative-transform, scoring tests | Verified |
| RQ-011 Deliberate failure handling | MUST | §9 | T-002, T-003, T-005, T-006, T-018, T-019 | Expected errors have a hierarchy, bounded retries, partial-fetch cooldown recovery, mapped CLI exit codes, and dispatched commands install file logging. | Infrastructure, market-data, quantitative CLI/transform, workflow-run, CLI tests | Verified |
| RQ-012 Maintainability | MUST | §3 | T-001–T-005, T-016 | Orchestration, I/O, transformation, scoring, validation, and presentation are separated. | Broad module-focused suite | Verified |
| RQ-013 Security and secrets | MUST | §10 | T-002, T-017 | No credential setup; public endpoints; direct dependencies pinned. | No secret fixture; `pip check` and inventory review | Verified |
| RQ-014 Reproducible setup | SHOULD | §13 | T-001, T-015, T-017, T-018 | `pyproject.toml` and README document local virtualenv and editable install; the hook is checked against this project source. | Documentation tests; `test_infrastructure.py` | Verified |
| RQ-015 Zero-candidate qualitative guard | MUST | §5.2, §5.3, §7.3 | T-018 | Zero-candidate runs reject supplied stale findings; explicit fallback creates a conservative empty report; downstream freshness and editable install are checked. | `test_workflow_run.py`, `test_enrichment_merge.py`, `test_workflow_status.py`, `test_infrastructure.py` | Verified |
| RQ-016 Artifact-driven verified research | MUST | §16 | T-022, T-023, T-024 | `pipeline/research.py` and the `verified-research` CLI discover ordered occurrences, preserve optional `Candidate_ID` identity, validate an explicit evidence pack, classify conservatively, and write atomically. | `tests/test_verified_research.py` | Verified |

## Unmapped implementation behavior

- PDF rendering performs its own minimal final-report structure checks in addition to the standalone validator. This is consistent with defense in depth but is not separately required by an RQ.

## Conflicts and gaps

- **Gap:** No lockfile pins transitive dependencies; only direct runtime and development dependencies are pinned.
- **Gap:** No CI workflow enforces the full verification gate.
- **Partial evidence:** RQ-011 requires errors to identify the failed stage. Some modules label quantitative/log warnings, while CLI maps errors to numeric classes and delegates the user-facing phase name to `SKILL.md`. The complete agent response is not automatically embedded in every CLI message.
