# Troubleshooting

First run:

```powershell
python -m canslim_analysis status --json
```

Then use the matching symptom below. Do not edit generated JSON to force a state.

## Exit code 2: command or configuration rejected

### Likely cause

Verified: argparse did not recognize the command/option, or `PipelineConfig` rejected an out-of-range value.

### Diagnosis

```powershell
python -m canslim_analysis --help
python -m canslim_analysis quantitative --help
```

### Action

Correct spelling, required inputs, workers, timeout, limit, or threshold. See [Configuration](Configuration.md).

## Exit code 3: schema or validation failure

### Likely cause

Verified: an artifact is malformed JSON or violates the selected contract.

### Diagnosis

```powershell
python -m canslim_analysis validate --stage quantitative
python -m canslim_analysis validate --stage enriched
python -m canslim_analysis validate --stage final
```

### Action

Recreate the artifact through its producing stage. For findings, ensure every candidate has exactly one complete entry and every true claim has non-empty evidence.

## Exit code 4: missing artifact

### Likely cause

Verified: the selected input path does not exist.

### Action

Use `status` to identify the last complete state and run the preceding command. If using explicit `--input`/`--findings`, verify the path from the current working directory.

## Exit code 5: external-data failure

### Likely cause

Verified: the universe was empty/unavailable, market history failed, or no stock data could be evaluated.

### Diagnosis

Check connectivity and provider availability. Review the command options:

```powershell
python -m canslim_analysis quantitative --help
```

### Action

Retry later, reduce `--workers`, or increase `--timeout`/`--retries` if provider latency is the issue. Individual ticker failures are tolerated only when enough valid stock rows remain.

## Exit code 6: PDF failure

### Likely cause

Verified: ReportLab raised an exception or produced no file after the final report loaded.

### Diagnosis

Validate final JSON:

```powershell
python -m canslim_analysis validate --stage final
python -m pip check
```

### Action

Regenerate final JSON if malformed. Reinstall the local environment with `python -m pip install -e '.[dev]'`.

## Status is `invalid`

### Likely cause

Verified: a quantitative, enriched, or final file exists but fails its validator.

### Action

Run the applicable stage validator above. Replace the file only by rerunning its stage from a valid predecessor.

## Enrichment merge rejects findings

### Likely cause

Verified causes include duplicate/missing ticker coverage, unknown ticker/field, non-boolean value, or a true claim without evidence.

### Action

Start from a freshly generated template and change only the documented finding fields. Keep false claims when evidence is absent or ambiguous.

## `run` stops after quantitative analysis

### Likely cause

Verified: no `--findings` path and no explicit fallback were supplied.

### Action

Research the generated candidates, then run with `--findings`. Use `--unverified-fallback` only when conservative all-false qualitative results are explicitly acceptable, and disclose that limitation.

## No file log exists

### Likely cause

Gap: `logging_setup.configure_logging` exists, but the CLI does not call it.

### Action

Capture terminal stdout/stderr instead of expecting `out/canslim_analysis.log`. Adding CLI logging integration is a code change, not a supported runtime option.
