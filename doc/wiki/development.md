# Development Guide

## Prerequisites

| Requirement | Version | Evidence |
|---|---|---|
| Python | 3.12 or newer | [`../../pyproject.toml`](../../pyproject.toml), `requires-python = ">=3.12"` |
| pip | Bundled with Python | Editable-install command is documented in [`../../README.md`](../../README.md) |
| Network | Live quantitative runs only | Universe and market-data providers in `../../src/canslim_analysis/pipeline/market_data.py` |

No environment variables or credential setup are required by the implemented CLI.

## Repository setup

Run from the project root on Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e '.[dev]'
pytest
python -m canslim_analysis --help
```

On macOS or Linux, use `source .venv/bin/activate` instead of `.venv\Scripts\activate`. Do not install dependencies globally.

Verified: the editable install and dependency consistency check passed on Python 3.12.14 during delivery verification.

## Commands

| Task | Command | Source |
|---|---|---|
| Install project and test tools | `python -m pip install -e '.[dev]'` | [`../../pyproject.toml`](../../pyproject.toml), [`../../README.md`](../../README.md) |
| Run full tests | `pytest` | `pytest` is a development dependency; path/config in `pyproject.toml` |
| Show CLI commands | `python -m canslim_analysis --help` | `src/canslim_analysis/cli.py` |
| Inspect workflow state | `python -m canslim_analysis status --json` | `src/canslim_analysis/pipeline/status.py`, `cli.py` |
| Run quantitative stage | `python -m canslim_analysis quantitative` | `pipeline/quantitative.py`, `pipeline/market_data.py` |
| Prepare enrichment | `python -m canslim_analysis prepare-enrichment` | `pipeline/enrichment.py` |
| Merge findings | `python -m canslim_analysis enrich --findings <file>` | `pipeline/enrichment.py` |
| Write final JSON | `python -m canslim_analysis finalize` | `pipeline/reporting.py` |
| Render PDF | `python -m canslim_analysis report` | `reporting/pdf.py` |
| Run complete workflow | `python -m canslim_analysis run --findings <file>` | `pipeline/workflow.py` |

There is no build script, task runner, or CI definition in the baseline inventory.

## Configuration preparation

No configuration file preparation is required. Runtime values are CLI options assembled into the frozen `PipelineConfig` in [`../../src/canslim_analysis/pipeline/config.py`](../../src/canslim_analysis/pipeline/config.py). Generated data defaults to `out/` and can be moved with `--output-dir`.

## Conventions

- Python source belongs under `src/canslim_analysis`.
- Tests belong under `tests` and run through pytest.
- Public classes and functions have docstrings.
- Expected project failures use `CanslimError` subclasses in `errors.py`.
- Normative behavior changes require updates to `doc/spec/` before or with implementation, as required by the workspace operating contract.
- Generated artifacts are not source and must not be hand-edited to change stage state.

## Debug workflow

For a failed command, capture stderr and identify the stable exit code in [Operations](operations.md). Run a focused test module, for example:

```powershell
pytest tests/test_enrichment_merge.py -q
```

Use `python -m canslim_analysis status --json` to locate the last valid artifact.

Dispatched CLI commands call `logging_setup.configure_logging` and write `canslim_analysis.log` to the selected output directory. Unexpected exceptions also write a traceback to that log while the terminal keeps its stable one-line failure message.
