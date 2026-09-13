# FAQ and Troubleshooting

## How do I resume safely?

Run `python -m canslim_analysis status --json`. Use the returned next command unless status is `invalid`.

## A stage reports exit code 4

A predecessor artifact is missing. Generate it with the documented preceding command; do not copy or invent JSON.

## A stage reports exit code 3

Run `python -m canslim_analysis validate --stage quantitative|enriched|final`. Fix the source data through the producing stage. The error names the failed contract.

## Live quantitative data fails

Exit code 5 means external data could not produce a usable run. Check connectivity, reduce `--workers`, or increase `--timeout` and `--retries`. Individual ticker failures are tolerated when enough valid data remains.

## Can I force a qualitative field true?

No. Editing generated JSON is forbidden. A true catalyst, float, or institutional-quality claim must enter through findings with non-empty evidence. Missing or ambiguous evidence remains false.

## What does unverified fallback mean?

`run --unverified-fallback` explicitly continues with all qualitative checks false. It is useful only when the user accepts a conservative screen and must be disclosed in the final answer.

## Is this investment advice?

No. The project is educational. External data may be delayed, incomplete, or wrong, and historical behavior does not guarantee future results.
