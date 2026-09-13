# PDF Report Generator

## Scope

The PDF stage renders an already-validated final report into a portable summary for review.

## Command and Paths

```text
python -m canslim_analysis report
```

- Input: `out/final_canslim_report.json`
- Output: `out/canslim_report_<report-date>.pdf`

## Contract

The renderer enforces the final report's minimal schema-2.1 structure, writes a real PDF, includes market metadata, score distribution, candidate summaries, and an educational-use disclaimer. It never fetches market data or mutates JSON. Missing input returns exit code 4, malformed JSON returns 3, and renderer failure returns 6.
