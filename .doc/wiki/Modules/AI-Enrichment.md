# AI Enrichment

**Stage:** 2 of 3  
**Input:** `Scripts/intermediate_canslim.json`  
**Output:** `Scripts/enriched_canslim.json`  
**Executor:** OpenClaw AI agent (not a script in this repository)

## Purpose

The AI Enrichment stage evaluates qualitative factors that cannot be reliably determined from numerical data alone. It researches recent news, product launches, management changes, float dynamics, and institutional sponsorship quality to fill the **N**, **S**, and **I** criteria.

## Why This Stage Exists

The CANSLIM methodology includes subjective judgments:
- Is there a *new* catalyst driving the stock?
- Is the float *tight* enough to create supply/demand imbalance?
- Are institutions *high-quality* sponsors?

These require reading news, understanding context, and making judgment calls — tasks better suited to an AI agent than to deterministic code.

## Execution Model

This stage is **not** a Python script. It is performed by the OpenClaw AI agent following the checklist in [SKILL.md](../../../SKILL.md).

### What the AI Does

1. **Reads** `Scripts/intermediate_canslim.json`
2. **For each stock**, preserves `Ticker`, `Company_Name`, and the entire `Quantitative_Metrics` object **unchanged**
3. **Fills** `AI_Qualitative_Checks` with six fields:

| Field | Type | Description |
|-------|------|-------------|
| `N_New_Catalyst` | boolean | Is there a verified new catalyst? |
| `N_Catalyst_Details` | string | Brief explanation of the catalyst |
| `S_Float_Tightness` | boolean | Is the float tight enough for supply/demand imbalance? |
| `S_Float_Details` | string | Float analysis and reasoning |
| `I_Institutional_Quality` | boolean | Is institutional sponsorship high-quality? |
| `I_Institutional_Details` | string | Institutional assessment and reasoning |

4. **Writes** `Scripts/enriched_canslim.json`

## Critical Rules

### Preservation Rule

> The AI phase must **preserve every field** already present in `Quantitative_Metrics` and must **only** fill `AI_Qualitative_Checks`.

Any modification to quantitative fields invalidates the audit trail and breaks reproducibility.

### Honesty Rules

From [SKILL.md](../../../SKILL.md) constraints:

- **Never fabricate** catalysts, float conclusions, or institutional-quality claims.
- If no catalyst is found, set `N_New_Catalyst` to `false` and explain briefly.
- If the AI cannot verify S or I, set the corresponding value to `false` instead of leaving it ambiguous.
- Do not claim results are guaranteed investment advice.

### Schema Contract

The enriched file must contain:
- Same top-level `Metadata` and `Stocks` structure
- Same `Quantitative_Metrics` per stock (unchanged)
- Same `AI_Qualitative_Checks_Pending` (may be kept or removed)
- **New** `AI_Qualitative_Checks` per stock with all six fields filled

## Scoring Impact

The AI checks directly determine three of the seven CANSLIM criteria:

| Criterion | AI Field Required |
|-----------|-------------------|
| N | `N_New_Catalyst == true` |
| S | `S_Float_Tightness == true` (AND quantitative S) |
| I | `I_Institutional_Quality == true` |

A stock can have perfect quantitative scores but still miss N, S, or I if the AI cannot verify the qualitative component.

## Fallback Behavior

If `enriched_canslim.json` is missing when [Final Process](./Final-Process.md) runs:
- It falls back to `intermediate_canslim.json`
- All AI checks default to `false`
- Result: N, S, I all score as missed for every stock

## Example

**Before AI (intermediate):**
```json
{
  "Ticker": "XYZ",
  "Quantitative_Metrics": { "C_Met": true, "A_Met": true, "L_Met": true, ... },
  "AI_Qualitative_Checks_Pending": {
    "N_New_Catalyst": null,
    "S_Float_Tightness": null,
    "I_Institutional_Quality": null
  }
}
```

**After AI (enriched):**
```json
{
  "Ticker": "XYZ",
  "Quantitative_Metrics": { "C_Met": true, "A_Met": true, "L_Met": true, ... },
  "AI_Qualitative_Checks": {
    "N_New_Catalyst": true,
    "N_Catalyst_Details": "New product launch and raised guidance",
    "S_Float_Tightness": true,
    "S_Float_Details": "Tight float supported by low float and buyback activity",
    "I_Institutional_Quality": true,
    "I_Institutional_Details": "High-quality institutional sponsorship improving"
  }
}
```

## Related Pages

- [Quantitative Analyzer](./Quantitative-Analyzer.md) — Stage 1
- [Final Process](./Final-Process.md) — Stage 3
- [API Reference](../API-Reference.md) — Full JSON schema
- [Architecture](../Architecture.md) — Pipeline overview
