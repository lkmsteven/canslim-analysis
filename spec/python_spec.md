Here are the detailed implementation specifications for the two Python scripts. These specifications outline the architecture, data structures, and logical flow required to build a robust, modular CANSLIM screener that prepares data for an AI handoff.

### 1. Specification for `quantitative_analyzer.py`

**Purpose:**  
To fetch historical price and fundamental data for a broad universe of stocks, filter them mathematically based on the quantitative CANSLIM criteria (C, A, L, and S), assess the broader market direction (M), and output a structured JSON file for the AI to process.

**Input:**  
A list of stock tickers (preferably the Russell 3000 or S&P 1500 to capture smaller, high-growth companies, rather than just the top 100 mega-caps).

**Core Logic & Functions:**

1.  **`assess_market_direction()` (The "M" Check)**
    *   *Logic:* Fetch 6 months of daily data for the Nasdaq Composite (`^IXIC`) and S&P 500 (`^GSPC`).
    *   *Calculation:* Check if the current index prices are trading above their 50-day and 200-day moving averages. If both indices are above these averages, classify the market as `"Confirmed Uptrend"`. Otherwise, `"Under Pressure"` or `"Downtrend"`.
    *   *Storage:* Save this as a global variable to be written at the root level of the output JSON.

2.  **`calculate_relative_strength(tickers)` (The "L" Check Preparation)**
    *   *Logic:* To find True Leaders, you cannot look at a stock in isolation. You must fetch the 12-month trailing price return for *all* tickers in the universe.
    *   *Calculation:* Rank all stocks by their 12-month return and assign a percentile score from 1 to 99.
    *   *Output:* A dictionary mapping `ticker -> RS_Rating`.

3.  **`evaluate_quant_criteria(ticker, rs_rating)` (C, A, L, S Checks)**
    *   *Logic:* Use `yfinance` to fetch the ticker's `.info` (fundamentals) and `.history` (price/volume).
    *   *C (Current Earnings):* Check if `.info['earningsQuarterlyGrowth']` $\ge 0.25$ (25%).
    *   *A (Annual Earnings):* Check if the 3-year trailing EPS CAGR is $\ge 25\%$ (if available) OR check if `.info['returnOnEquity']` $\ge 0.17$ (17%).
    *   *L (Leader):* Check if the injected `rs_rating` is $\ge 80$.
    *   *S (Supply/Demand - Quant Phase):* Check if today's volume is $\ge 1.5 \times$ the 50-day average volume (indicating institutional accumulation).

4.  **`filter_and_export(results_list)`**
    *   *Logic:* Discard any stock that fails the "C", "A", or "L" criteria. Stocks must meet ALL THREE criteria (C, A, AND L) to pass the screen. Stocks with null/missing fundamental data are skipped rather than penalized. AI processing is expensive, so only stocks with top-tier fundamentals and price action should advance.
    *   *Output Schema:* Write the surviving stocks to `intermediate_canslim.json`.

**JSON Schema Design (`intermediate_canslim.json`):**
```json
{
  "Metadata": {
    "Date_Run": "2026-03-14",
    "Market_Direction_M": "Confirmed Uptrend",
    "Total_Universe_Scanned": 3000,
    "Stocks_Passed_To_AI": 42
  },
  "Stocks": [
    {
      "Ticker": "XYZ",
      "Company_Name": "XYZ Corp",
      "Quantitative_Metrics": {
        "C_Met": true,
        "A_Met": true,
        "L_Met": true,
        "S_Quant_Met": true,
        "RS_Rating": 88,
        "Current_Price": 145.20
      },
      "AI_Qualitative_Checks_Pending": {
        "N_New_Catalyst": null,
        "N_Catalyst_Details": "",
        "S_Float_Tightness": null,
        "I_Institutional_Quality": null
      }
    }
  ]
}
```

***

### 2. Specification for `final_process.py`

**Purpose:**  
To ingest the JSON file updated by OpenClaw (which has now filled in the `AI_Qualitative_Checks_Pending` fields), calculate the final CANSLIM score, compile lists of met/missed criteria, and generate the final screening report.

**Input:**  
`enriched_canslim.json` (The JSON file populated by the AI script).

**Core Logic & Functions:**

1.  **`load_enriched_data(filepath)`**
    *   *Logic:* Read the JSON file and extract the global `Market_Direction_M` and the list of stocks.

2.  **`calculate_canslim_score(stock_json, market_m)`**
    *   *Logic:* For each stock, evaluate all 7 letters to generate a boolean array and a final score out of 7.
    *   *Scoring Rules:*
        *   **C, A, L:** Read directly from `Quantitative_Metrics`.
        *   **M:** Read from global metadata (True if `"Confirmed Uptrend"`).
        *   **N:** True if `AI_Qualitative_Checks_Pending.N_New_Catalyst` == `true`.
        *   **S:** True if BOTH `S_Quant_Met` == `true` AND `S_Float_Tightness` == `true` (from AI).
        *   **I:** True if `I_Institutional_Quality` == `true` (from AI).

3.  **`generate_criteria_lists(boolean_results)`**
    *   *Logic:* Convert the boolean checks into two lists of strings: `Met_Criteria` (e.g., `["C", "A", "L", "M"]`) and `Missed_Criteria` (e.g., `["N", "S", "I"]`).

4.  **`export_final_report(processed_stocks)`**
    *   *Logic:* Sort the stocks descending by their `Final_Score` (7/7 first, then 6/7, etc.). Break ties by sorting descending by `RS_Rating`.
    *   *Output:* Write the final results to `final_canslim_report.json` and optionally print a formatted console table using a library like `pandas` or `tabulate`.

**Final Output Schema (`final_canslim_report.json`):**
```json
{
  "Report_Date": "2026-03-14",
  "Market_Environment": "Confirmed Uptrend",
  "Top_Candidates": [
    {
      "Ticker": "XYZ",
      "Final_Score": 6,
      "Met_Criteria": ["C", "A", "L", "M", "N", "S"],
      "Missed_Criteria": ["I"],
      "AI_Notes": "Launched new AI-driven product suite on March 1st. Float is tightly held at 45M shares.",
      "Metrics": {
        "RS_Rating": 88
      }
    }
  ]
}
```