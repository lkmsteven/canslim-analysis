# CANSLIM Analysis — Project Wiki

Welcome to the documentation wiki for the **CANSLIM Analysis** skill — a hybrid quantitative + AI-qualitative stock screening pipeline that identifies high-potential US equities using William O'Neil's CANSLIM methodology.

## Project Overview

This project implements a three-stage modular pipeline that:

1. **Quantitatively screens** the S&P 500 universe against fundamental criteria (earnings growth, relative strength, volume behavior).
2. **Enriches candidates with AI** — an external AI agent (OpenClaw) evaluates qualitative catalysts, float tightness, and institutional sponsorship quality.
3. **Generates a ranked final report** — combining quantitative and AI scores into a composite CANSLIM score (out of 7), with JSON output and a professional PDF report.

The skill is designed to be invoked by an AI agent environment (OpenClaw), but the Python scripts can also be run manually for the quantitative and final-processing stages.

## Quick Facts

| Item | Detail |
|------|--------|
| Language | Python 3.8+ |
| Domain | US equity screening (S&P 500) |
| Methodology | CANSLIM (O'Neil) |
| Pipeline stages | Quantitative → AI Enrichment → Final Report |
| Output formats | JSON + PDF |
| Data sources | Yahoo Finance (yfinance), Wikipedia (S&P 500 list) |
| Key dependencies | `yfinance`, `pandas`, `requests`, `lxml`, `tqdm`, `reportlab` |
| Schema version | 2.1 |

## Table of Contents

- [Architecture](./Architecture.md) — System components, data flow, and pipeline stages
- [Getting Started](./Getting-Started.md) — Installation, setup, and run instructions
- [Configuration](./Configuration.md) — Tunable constants and environment settings
- [Modules](./Modules/) — Detailed per-module documentation
  - [Quantitative Analyzer](./Modules/Quantitative-Analyzer.md) — Stage 1: fundamental screening
  - [AI Enrichment](./Modules/AI-Enrichment.md) — Stage 2: qualitative AI analysis (external)
  - [Final Process](./Modules/Final-Process.md) — Stage 3: scoring and JSON report
  - [PDF Report Generator](./Modules/PDF-Report-Generator.md) — Professional PDF output
- [API Reference](./API-Reference.md) — Script entry points and JSON schema contracts
- [FAQ & Troubleshooting](./FAQ-Troubleshooting.md) — Common issues and resolutions

## Repository Layout

```
canslim-analysis/
├── SKILL.md                          # Skill definition (OpenClaw manifest)
├── README.md                         # User-facing overview and usage
├── .gitignore                        # Git ignore rules
├── Scripts/
│   ├── quantitative_analyzer.py      # Stage 1: quantitative screening
│   ├── final_process.py              # Stage 3: scoring + JSON report
│   ├── pdf_report_generator.py       # PDF report generation
│   ├── requirements.txt              # Pinned Python dependencies
│   ├── intermediate_canslim.json     # (generated) Stage 1 output
│   ├── enriched_canslim.json         # (generated) Stage 2 output
│   ├── final_canslim_report.json     # (generated) Stage 3 output
│   └── out/                          # (generated) PDF reports
└── .doc/wiki/                        # This wiki
```

## Key Concepts

### The CANSLIM Criteria

| Letter | Criterion | Evaluated By |
|--------|-----------|--------------|
| **C** | Current quarterly earnings growth ≥ 25% | Quantitative |
| **A** | Annual EPS CAGR ≥ 25% | Quantitative |
| **N** | New catalysts (products, management, highs) | AI (with technical support) |
| **S** | Supply & demand (volume + float tightness) | Quantitative + AI |
| **L** | Leader: Relative Strength Rating ≥ 80 | Quantitative |
| **I** | Institutional sponsorship quality | AI (with quantitative flag) |
| **M** | Market direction (confirmed uptrend) | Quantitative |

### The JSON Contract

All three pipeline stages communicate via versioned JSON files following a fixed schema. The AI stage **must preserve** all `Quantitative_Metrics` fields and **only fill** `AI_Qualitative_Checks`. See [API Reference](./API-Reference.md) for the full schema.

## Target Audience

- **AI agent operators** running the OpenClaw skill end-to-end
- **Developers** maintaining or extending the screening logic
- **Analysts** interpreting the generated reports

## License

MIT-0 — free to use, modify, and redistribute with no attribution required. See [README.md](../../README.md) for full disclaimer. **This tool is not investment advice.**
