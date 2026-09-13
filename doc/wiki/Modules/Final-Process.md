# Final Process

## Scope

The final stage validates enriched data, normalizes legacy-compatible fields, calculates seven criteria, assigns grades, ranks candidates, and writes final JSON.

## Command and Path

```text
python -m canslim_analysis finalize
```

- Input: `out/enriched_canslim.json`
- Output: `out/final_canslim_report.json`

## Contract

The output remains schema `2.1`. It contains market environment, M status, score distribution, and candidates ordered by score then RS rating. Nullable market metrics remain null rather than becoming fabricated values. Empty candidate sets are valid.

Final S requires both quantitative supply evidence and verified float tightness. Final M is true only for `Confirmed Uptrend`.
