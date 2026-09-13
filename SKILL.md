---
name: canslim-analysis
description: Run and validate the local quantitative and Codex-enriched CANSLIM analysis workflow through its supported CLI.
---

# CANSLIM Analysis Skill

Use this skill to run the hybrid CANSLIM workflow in this project. Quantitative screening, enrichment validation, final scoring, status reporting, validation, JSON generation, and PDF generation are performed by the project CLI. Codex performs qualitative research, records only verified findings in the findings file, and explains their limitations in the user-facing response.

This workflow is agent-neutral. Never edit generated JSON only to make a stage pass.

## Requirements

- Run commands from `Projects/canslim-analysis`.
- Use the project-local `.venv` environment created from `pyproject.toml`.
- Do not install dependencies globally.
- Do not disclose or enter credentials; the current workflow requires none.
- Treat market data and qualitative conclusions as uncertain and non-guaranteed.

## Operating Workflow

1. Inspect state before writing artifacts:

   ```text
   python -m canslim_analysis status --json
   ```

2. Run quantitative screening when the state is `not-started`:

   ```text
   python -m canslim_analysis quantitative
   ```

   Use `--limit`, `--workers`, thresholds, or `--output-dir` only when the user requested a bounded or customized run.

3. Generate the qualitative worksheet:

   ```text
   python -m canslim_analysis prepare-enrichment
   ```

4. Research candidates for fresh catalysts, float tightness, and institutional quality. Use reliable, current evidence. Do not present general market commentary as ticker-specific confirmation.

5. Fill `out/enrichment_template.json` without changing its shape. Every true claim requires non-empty evidence or rationale in the matching details field. Save completed findings outside generated state if the user should retain them, or to a path supplied by the user.

6. Validate and merge findings:

   ```text
   python -m canslim_analysis enrich --findings <findings.json>
   ```

7. Generate final JSON:

   ```text
   python -m canslim_analysis finalize
   ```

8. Generate the PDF:

   ```text
   python -m canslim_analysis report
   ```

For a single orchestrated invocation, after research is complete use:

```text
python -m canslim_analysis run --findings <findings.json>
```

Never use `--unverified-fallback` unless the user explicitly accepts unverified qualitative conclusions. It conservatively sets `N_New_Catalyst`, `S_Float_Tightness`, and `I_Institutional_Quality` to false and must be disclosed as unverified.

## Qualitative Safety Rules

- `N_New_Catalyst` may be true only for a verified fresh catalyst.
- `S_Float_Tightness` may be true only for verified float, buyback, or equivalent supply evidence.
- `I_Institutional_Quality` may be true only for verified institutional-quality evidence.
- Missing, stale, ambiguous, or contradictory evidence requires the corresponding value to remain false.
- Never fabricate catalysts, float conclusions, ownership conclusions, prices, scores, or recommendations.
- Disclose missing data and analysis limitations in `Notes & Caveats:`.

## Successful Response Contract

Return this structure:

```text
Market Environment:
<1-2 sentence assessment of M>

Top CANSLIM Candidates:

| Rank | Ticker | Company | CANSLIM Score | Met Criteria | Missed Criteria | Price | RS Rating | AI Catalyst Note |
|---|---|---|---|---|---|---|---|---|
| 1 | EXAMPLE | Example Company | 7/7 | C, A, N, S, L, I, M | None | $100.00 | 99.0 | Verified catalyst summary |

AI Catalyst Insights:
<Concise verified insight by selected candidate.>

Notes & Caveats:
<Missing data, unverified checks, market-data delay, and limitations.>

This analysis is educational, not investment advice. Conduct independent research and consider risk before making decisions.
```

## Failure Response Contract

Return this structure:

```text
Failed phase: <setup|quantitative|enrichment|final processing|PDF reporting|validation>
Error: <concise actionable error>
Missing or invalid fields: <field list, or None>
Next step: <smallest useful action>
```

Map CLI exit codes as follows:

| Code | Phase or meaning |
|---|---|
| 0 | Success or an intentional findings stop. |
| 1 | Unexpected error; retry diagnosis before repeating the command. |
| 2 | Usage/configuration error. |
| 3 | Schema or validation failure. |
| 4 | Missing predecessor artifact. |
| 5 | External market-data failure. |
| 6 | PDF report-generation failure. |

## Validation Rules

- Run `python -m canslim_analysis status --json` after an unexpected interruption.
- Use `python -m canslim_analysis validate --stage quantitative|enriched|final` to inspect a specific JSON artifact.
- If code and documentation disagree, stop the workflow and repair the defect rather than hand-editing generated state.
