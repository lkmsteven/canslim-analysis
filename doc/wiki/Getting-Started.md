# Getting Started

## Setup

```text
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e '.[dev]'
pytest
```

Use `source .venv/bin/activate` on macOS or Linux.

## State-Driven Workflow

1. Inspect state:

   ```text
   python -m canslim_analysis status --json
   ```

2. Run quantitative screening:

   ```text
   python -m canslim_analysis quantitative
   ```

3. Prepare enrichment:

   ```text
   python -m canslim_analysis prepare-enrichment
   ```

4. Research candidates and fill findings without changing the schema.
5. Merge findings:

   ```text
   python -m canslim_analysis enrich --findings <findings.json>
   ```

6. Finalize:

   ```text
   python -m canslim_analysis finalize
   ```

7. Render PDF:

   ```text
   python -m canslim_analysis report
   ```

Alternatively, after findings exist:

```text
python -m canslim_analysis run --findings <findings.json>
```

## Outputs

| Artifact | Path |
|---|---|
| Quantitative output | `out/intermediate_canslim.json` |
| Template | `out/enrichment_template.json` |
| Enriched output | `out/enriched_canslim.json` |
| Final JSON | `out/final_canslim_report.json` |
| PDF | `out/canslim_report_<date>.pdf` |

If a command fails, keep the artifacts unchanged and use [troubleshooting](troubleshooting.md).
