# FAQ & Troubleshooting

Common issues, their causes, and resolutions for the CANSLIM Analysis pipeline.

## Frequently Asked Questions

### Q: Why did no stocks pass the quantitative screen?

**A:** This is normal during market downturns or periods of weak earnings growth. The C+A+L gate is intentionally strict:
- C requires ≥ 25% quarterly EPS growth
- A requires ≥ 25% annual EPS CAGR
- L requires RS Rating ≥ 80

Check the `Market_Direction_M` field in the output — if it's `"Downtrend"`, fewer stocks will qualify.

### Q: What happens if I skip the AI enrichment step?

**A:** [Final Process](./Modules/Final-Process.md) will fall back to `intermediate_canslim.json`. All AI checks default to `false`, so:
- **N** will miss for every stock (no verified catalyst)
- **S** will miss for every stock (no verified float tightness)
- **I** will miss for every stock (no verified institutional quality)

The maximum possible score drops from 7 to 4 (C+A+L+M).

### Q: Can I run this on a different stock universe?

**A:** The current implementation hardcodes the S&P 500 as the universe. To change it, modify [Scripts/quantitative_analyzer.py](../../Scripts/quantitative_analyzer.py):
- Replace `get_sp500_tickers()` with your own ticker source
- Or set `DEFAULT_UNIVERSE_LIMIT` to a smaller number for testing

### Q: How is the RS Rating calculated?

**A:** The Relative Strength Rating is a percentile rank (1-99) of each stock's 1-year price return within the scanned universe. It is computed as:

```python
df["RS_Rating"] = df["Return_1Y"].rank(pct=True, method="average").mul(99).clip(1, 99).round(1)
```

A rating of 97.4 means the stock outperformed 97.4% of the universe over the past year.

### Q: What's the difference between `N_Technical_Met` and `N_New_Catalyst`?

**A:** 
- `N_Technical_Met` is a **quantitative context signal** — it checks if the stock is near its 52-week high or has recently broken out. This is computed by the analyzer.
- `N_New_Catalyst` is the **scored criterion** — it requires AI verification of an actual new catalyst (product, management change, etc.).

A stock can have `N_Technical_Met = true` but still miss the final N if the AI cannot verify a fresh catalyst.

### Q: Why does S require both quantitative and AI checks?

**A:** The S criterion (Supply & Demand) has two components:
1. **Quantitative**: Volume surge + up/down volume skew (mechanical)
2. **Qualitative**: Float tightness, buyback activity (requires judgment)

Both must be true for S to score. This prevents false positives from high-volume stocks with massive floats.

### Q: Is this investment advice?

**A:** **No.** This tool is for educational and analysis purposes only. Past performance does not guarantee future results. Always conduct your own research and consult a financial advisor before making investment decisions.

## Troubleshooting

### Issue: "Failed to fetch S&P 500 tickers"

**Cause:** Wikipedia is unreachable or the page structure changed.

**Solutions:**
1. Check your internet connection
2. The script retries 3 times with 2-second delays — wait for it to complete
3. If persistent, the Wikipedia page structure may have changed; check the URL in [Scripts/quantitative_analyzer.py](../../Scripts/quantitative_analyzer.py)

### Issue: "Insufficient historical data"

**Cause:** Some stocks don't have a full year of trading data (recent IPOs, delisted stocks).

**Resolution:** These stocks are automatically skipped. This is expected behavior and counted in `Failed_Fetches` or `Skipped_For_Missing_Fundamentals`.

### Issue: Rate limiting errors from Yahoo Finance

**Cause:** Too many concurrent requests.

**Solutions:**
1. Reduce `MAX_WORKERS` in [Scripts/quantitative_analyzer.py](../../Scripts/quantitative_analyzer.py) from 5 to 3 or 2
2. Increase `RETRY_DELAY` from 2 to 5 seconds
3. Run during off-peak hours

### Issue: Empty results (no stocks passed to AI)

**Cause:** The C+A+L gate filtered out all stocks.

**Solutions:**
1. Check the market environment — during downtrends, fewer stocks qualify
2. Review `canslim_analysis.log` for per-stock evaluation details
3. Consider temporarily lowering thresholds for testing:
   - `MIN_EPS_GROWTH` from 0.25 to 0.15
   - `MIN_RS_RATING` from 80.0 to 70.0

### Issue: PDF generation failed

**Cause:** Various — missing JSON, ReportLab error, timeout.

**Solutions:**
1. Verify `Scripts/final_canslim_report.json` exists
2. Check that `reportlab` is installed: `pip install reportlab>=4.0.0,<5.0.0`
3. Run the PDF generator standalone to see the full error:
   ```bash
   python Scripts/pdf_report_generator.py
   ```
4. Note: PDF failure is **non-fatal** — the JSON report is still valid

### Issue: Schema mismatch errors in final_process.py

**Cause:** The input JSON is missing required fields or has unexpected structure.

**Solutions:**
1. Ensure the JSON file was produced by the current version of the pipeline
2. Check that `Metadata` and `Stocks` top-level keys exist
3. Verify each stock has `Ticker`, `Company_Name`, and `Quantitative_Metrics`
4. If using an older file, the normalization functions will attempt to fill defaults, but severe mismatches will raise `ValueError`

### Issue: AI enrichment produced unexpected results

**Cause:** The AI agent made subjective judgments you disagree with.

**Resolution:** This is expected — the AI stage is intentionally subjective. Review the `AI_Qualitative_Checks` fields:
- `N_Catalyst_Details` — Does the catalyst make sense?
- `S_Float_Details` — Is the float reasoning sound?
- `I_Institutional_Details` — Is the institutional assessment reasonable?

You can manually edit `enriched_canslim.json` before running `final_process.py` if needed.

## Debug Mode

For detailed execution information, check `canslim_analysis.log`:

- Individual stock fetch attempts and failures
- Market direction assessment details
- Criteria evaluation results
- Processing statistics
- Error messages with stack traces

The log file is appended to by all three Python stages.

## Getting Help

1. Check `canslim_analysis.log` for detailed error messages
2. Review this FAQ for common issues
3. Verify all dependencies are correctly installed
4. Ensure you have a stable internet connection
5. Check the [README.md](../../README.md) for updates

## Related Pages

- [Getting Started](./Getting-Started.md) — Setup instructions
- [Configuration](./Configuration.md) — Tunable thresholds
- [Architecture](./Architecture.md) — Pipeline overview
- [API Reference](./API-Reference.md) — JSON schema details
