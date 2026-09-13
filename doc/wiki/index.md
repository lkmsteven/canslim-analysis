# CANSLIM Analysis Wiki Index

## Baseline

| Fact | Value |
|---|---|
| Generation date | 2026-09-13 (Asia/Shanghai) |
| Source revision | `db36b1cd22ae0b9a63fd6dc329bee535b454713b` |
| Branch | `main`, 17 commits ahead of `origin/main` before this wiki write |
| Baseline working tree | Clean before wiki-only changes |
| Environment | Windows / PowerShell |
| Baseline test collection | 137 tests |

This wiki reconciles the existing ten wiki pages and adds project-wide inventory, development, testing, traceability, operations, data, decisions, and troubleshooting pages. It does not replace the normative specifications under [`../spec/requirements.md`](../spec/requirements.md), [`../spec/design.md`](../spec/design.md), and [`../spec/tasks.md`](../spec/tasks.md).

## Evidence labels

| Label | Meaning |
|---|---|
| Verified | Supported by source, executable configuration, observed CLI output, or a test. |
| Intended | Required or designed, but lacking complete implementation/test evidence. |
| Inferred | Reasonable conclusion from combined evidence. |
| Gap | Expected evidence was not found. |
| Conflict | Project sources disagree. |

## Page map

| Page | Use |
|---|---|
| [Artifact inventory](artifact-inventory.md) | Complete relevant-input inventory and exclusions. |
| [Architecture](Architecture.md) | Component map and data flow. |
| [Development guide](development.md) | Runtime requirements, setup, and commands. |
| [Testing and quality](testing-quality.md) | Test map, verification gate, and limits. |
| [Requirements traceability](requirements-traceability.md) | RQ coverage and implementation evidence. |
| [Operations](operations.md) | CLI operation, health checks, failure classes, recovery. |
| [Data and integrations](data-and-integrations.md) | JSON contracts and external integrations. |
| [Architecture decision record](decisions.md) | Material refactor decisions. |
| [Troubleshooting](troubleshooting.md) | Symptom-based diagnosis. |
| [Getting Started](Getting-Started.md) | Short operational workflow. |
| [Configuration](Configuration.md) | Defaults and overrides. |
| [API Reference](API-Reference.md) | CLI and JSON contract summary. |
| [Delivery Verification](Delivery-Verification.md) | Historical release evidence at the baseline revision. |
| [FAQ and Troubleshooting](FAQ-Troubleshooting.md) | Short answers and recovery guidance. |
| Module pages under [Modules](Modules/Quantitative-Analyzer.md) | Stage-level behavior. |

## Start here

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e '.[dev]'
pytest
python -m canslim_analysis --help
```

See [development.md](development.md) for platform notes and [testing-quality.md](testing-quality.md) for the full verification gate.

## Current evidence highlights

- Verified: the installed CLI exposes `quantitative`, `prepare-enrichment`, `enrich`, `finalize`, `status`, `validate`, `report`, and `run`.
- Verified: 137 tests are collected and passed during delivery verification.
- Verified: direct dependencies are pinned in [`../../pyproject.toml`](../../pyproject.toml).
- Gap: no lockfile pins transitive dependencies.
- Conflict: [design §9](../spec/design.md) describes a `--debug` CLI option, while the implemented parser has no `--debug` option.
- Gap: `src/canslim_analysis/logging_setup.py` implements and tests file logging, but no CLI dispatch path calls it.

The output is educational and is not investment advice.
