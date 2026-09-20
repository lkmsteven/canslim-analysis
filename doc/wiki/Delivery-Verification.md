# Delivery Verification

## Result

The Codex-agent refactor is complete on this revision. The former standalone script interface was replaced by `python -m canslim_analysis`, while schema version and scoring semantics remained compatible.

## Verified on 2026-09-13

| Check | Result |
|---|---|
| Python | 3.12.14 |
| Documented editable setup | Passed |
| Dependency consistency | `pip check`: no broken requirements |
| Full test suite | 137 passed |
| Top-level CLI help | All eight commands listed |
| Quantitative options | Operational overrides available |
| Empty-output status | `not-started`, next command returned |
| Legacy scripts and operational artifacts | Removed |
| Mandatory specification layout | Present under `doc/spec/` |
| Wiki migration | Present under `doc/wiki/`; `.doc/` removed |
| Codex skill contract | Present and documentation-tested |
| Qualitative safety | Verified findings required; fallback is explicit |

## Verified on 2026-09-20

| Check | Result |
|---|---|
| Bounded live quantitative smoke | Five-stock run completed and exposed the zero-candidate merge path |
| Stale editable installation | Repaired to resolve this project's `src/` tree |
| Full test suite | 152 passed |
| Zero-candidate workflow | Supplied findings stop safely; explicit fallback creates a conservative empty report |
| Workflow freshness | Enrichment-to-final staleness is detected |
| Runtime logging | Dispatched commands write the selected output-directory log |
| Provider warning noise | Live retry emits operational logs without Pandas4 warnings |
| Partial rate-limit recovery | Live retry reduced 30 transient stock-fetch failures to 3 and completed with 13 candidates |

## Dependency Pins

Direct runtime dependencies are pinned to locally verified versions:

- `requests==2.34.2`
- `yfinance==0.2.66`
- `reportlab==4.5.1`

`pytest==9.1.1` is pinned as a development-only dependency.

## Boundary

Live external-data retrieval was not used to produce investment results during this verification. Quantitative provider access is covered by injected offline tests; live retrieval remains subject to network, provider, and market-data availability.
