# Getting Started

This guide walks you through setting up and running the CANSLIM Analysis pipeline from scratch.

## Prerequisites

- **Python 3.8 or higher**
- **pip** package manager
- **Internet connection** (required for Wikipedia ticker list and Yahoo Finance data)
- **Git** (optional, for cloning)

## Installation

### 1. Create a Virtual Environment

The project mandates a dedicated virtual environment named `canslim_analysis`.

```bash
# Windows (cmd.exe)
python -m venv canslim_analysis
canslim_analysis\Scripts\activate

# macOS / Linux
python3 -m venv canslim_analysis
source canslim_analysis/bin/activate
```

### 2. Install Dependencies

```bash
pip install --no-cache-dir -r Scripts/requirements.txt
```

> **Note:** The `--no-cache-dir` flag ensures a clean, reproducible install. Never install dependencies globally.

## Running the Pipeline

### Full Pipeline (3 Steps)

```bash
# Step 1: Quantitative screening (fetches S&P 500, applies C/A/L filters)
python Scripts/quantitative_analyzer.py

# Step 2: AI Enrichment (performed by OpenClaw AI — not a script)
# The AI reads Scripts/intermediate_canslim.json and writes Scripts/enriched_canslim.json

# Step 3: Final scoring and report generation
python Scripts/final_process.py
```

### Expected Outputs

After a successful run, you will find:

| File | Location | Description |
|------|----------|-------------|
| `intermediate_canslim.json` | `Scripts/` | Stage 1 output — quantitative metrics for passed stocks |
| `enriched_canslim.json` | `Scripts/` | Stage 2 output — AI-filled qualitative checks |
| `final_canslim_report.json` | `Scripts/` | Stage 3 output — ranked candidates with scores |
| `canslim_analysis.log` | `Scripts/` | Execution log from all stages |
| `canslim_report_{date}.pdf` | `out/` | Professional PDF report |

## Quick Verification

To verify your setup is working:

```bash
# 1. Check Python version
python --version

# 2. Check installed packages
pip list | findstr "yfinance pandas reportlab"  # Windows
pip list | grep "yfinance pandas reportlab"     # macOS/Linux

# 3. Run a quick import test
python -c "import yfinance, pandas, reportlab; print('OK')"
```

## Running Without AI (Quantitative-Only Mode)

If you only want to run the quantitative screen without AI enrichment:

```bash
python Scripts/quantitative_analyzer.py
```

This produces `intermediate_canslim.json`. You can inspect it directly, or run `final_process.py` which will fall back to treating all AI checks as `false` (so N, S, I will all miss).

## Environment Deactivation

When finished:

```bash
deactivate
```

## Next Steps

- Read [Architecture](./Architecture.md) to understand how the stages connect.
- See [Configuration](./Configuration.md) for tunable thresholds.
- Review [API Reference](./API-Reference.md) for the JSON schema contract.
