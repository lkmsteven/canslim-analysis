# Operations

## Supported mode

The delivered system is a local CLI tool operated from the project root. There is no daemon, hosted service, deployment manifest, scheduler, or stop/start procedure in the repository.

## Operating prerequisites

1. Python 3.12+ and the project-local environment are installed as shown in [development](development.md).
2. The working directory is `Projects/canslim-analysis`.
3. For quantitative retrieval, network access to public Wikipedia and Yahoo Finance endpoints is available.
4. The desired workflow state is understood through:

   ```powershell
   python -m canslim_analysis status --json
   ```

## State and readiness

| State | Meaning | Normal next action |
|---|---|---|
| `not-started` | No quantitative artifact exists. | Run `quantitative`. |
| `quantitative-complete` | Intermediate JSON validates. | Run `prepare-enrichment`. |
| `enrichment-ready` | Quantitative output and template exist. | Research and merge findings. |
| `enrichment-complete` | Enriched JSON validates. | Run `finalize`. |
| `final-complete` | Final JSON validates. | Run `report`. |
| `report-complete` | Final JSON and a dated PDF exist. | No required next command. |
| `invalid` | An existing artifact fails its selected contract. | Diagnose using [troubleshooting](troubleshooting.md). |

Status classification validates intermediate, enriched, and final JSON. The template affects `enrichment-ready` by existence; its contents are validated later by `enrich`.

## Generated-file policy

| Path | Lifecycle |
|---|---|
| `out/intermediate_canslim.json` | Overwritten by each quantitative run. |
| `out/enrichment_template.json` | Overwritten by template preparation or fallback. |
| `out/enriched_canslim.json` | Overwritten by enrichment merge. |
| `out/final_canslim_report.json` | Overwritten by finalization. |
| `out/canslim_report_<date>.pdf` | A same-date PDF is overwritten by the report stage. |

Preserve completed findings outside `out/` if they have evidentiary value; they are inputs and are not copied into a retained archive.

## Logs

Dispatched CLI commands install console and file logging through `logging_setup.configure_logging`. The file is `canslim_analysis.log` inside the selected output directory.

## Failure classification

| Exit code | Classification | Operator response |
|---|---|---|
| 0 | Success or an intentional findings/no-candidate stop | Continue the displayed workflow. |
| 1 | Unexpected internal error | Capture stderr, run status/tests, do not edit generated JSON. |
| 2 | Usage/configuration error | Correct options and values. |
| 3 | Schema/validation failure | Validate and recreate the artifact through its producing stage. |
| 4 | Missing predecessor | Run the preceding stage or supply the missing input. |
| 5 | External-data failure | Check connectivity/rate pressure, lower workers, or retry later. |
| 6 | PDF generation failure | Verify final JSON and ReportLab installation. |

## Recovery

For an invalid or incomplete stage, use `status`, validate the latest stage, then rerun that stage from its declared input. Never repair state by editing JSON: the stage validators are the safe boundary.

There is no backup/restore feature in the repository. Preserve user-created findings and valuable dated reports before rerunning a stage.

## Maintenance

Supported maintenance is limited to running `pytest`, `python -m pip check`, reviewing `status`, and updating pinned dependencies through `pyproject.toml`. No database, migration, cache-clearing, or scheduled-job procedure is implemented.
