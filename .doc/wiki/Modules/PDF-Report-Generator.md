# PDF Report Generator

**File:** [Scripts/pdf_report_generator.py](../../../Scripts/pdf_report_generator.py)  
**Input:** `Scripts/final_canslim_report.json`  
**Output:** `out/canslim_report_{Report_Date}.pdf`

## Purpose

The PDF Report Generator renders the final CANSLIM analysis JSON into a professionally formatted PDF document using ReportLab. It is invoked automatically by [Final Process](./Final-Process.md) but can also be run standalone.

## Entry Point

```bash
python Scripts/pdf_report_generator.py
```

## High-Level Flow

```
1. Locate final_canslim_report.json in Scripts/
2. Load and parse JSON data
3. Create output directory (out/) if missing
4. Build PDF document:
   a. Header section (metadata + score distribution)
   b. One page per candidate stock
5. Save PDF to out/canslim_report_{date}.pdf
```

## Class: `CANSLIMReportGenerator`

The main class that encapsulates all PDF generation logic.

### `__init__(output_dir: str)`

Initializes the generator with an output directory.

- Creates the directory if it doesn't exist
- Sets up ReportLab sample styles
- Registers custom paragraph styles

### `_setup_custom_styles()`

Defines custom ReportLab paragraph styles:

| Style | Font Size | Color | Alignment | Use |
|-------|-----------|-------|-----------|-----|
| `ReportTitle` | 24 | `#1a365d` | Center | Main report title |
| `SectionHeader` | 16 | `#2c5282` | Left | Stock section headers |
| `SubSection` | 12 | `#2d3748` | Left | Metric/detail subsections |
| `ReportBody` | 10 | Default | Left | Body text |
| `GradeAPlus` | 14 | `#276749` | Center | A+ / A grades |
| `GradeA` | 14 | `#2f855a` | Center | A- / B+ grades |
| `GradeB` | 14 | `#b7791f` | Center | B grades |
| `GradeC` | 14 | `#c53030` | Center | C / D grades |

### `generate_report(json_path: str) -> str`

Generates the complete PDF report.

**Returns:** Path to the generated PDF file.

**Process:**
1. Loads JSON data
2. Determines output filename from `Report_Date`
3. Creates `SimpleDocTemplate` with Letter page size and 0.75-inch margins
4. Builds flowables: header → page break → stock sections
5. Calls `doc.build(elements)`

### `_create_header_section(data: Dict) -> List[Flowable]`

Builds the report header page.

**Contents:**
- Main title: "CANSLIM Stock Analysis Report"
- Metadata table (report date, time, schema version, market environment, M criterion, total candidates)
- Score distribution table (if available)

### `_create_stock_section(stock: Dict, index: int) -> List[Flowable]`

Builds one page for a single stock candidate.

**Sections per stock:**

1. **Header** — `#{rank}: {TICKER} - {Company Name}`
2. **Grade badge** — Color-coded grade and score (e.g., "Grade: A- (Score: 5/7)")
3. **Criteria status grid** — 7×2 table showing ✓ Met / ✗ Missed for each CANSLIM letter
   - Green background for met criteria
   - Red background for missed criteria
4. **Key metrics table** — RS Rating, price, EPS growth, S score, float, institutional ownership
5. **Earnings analysis** — C and A details
6. **New highs & catalyst** — Technical N and AI catalyst details
7. **Supply & demand** — Quantitative S and AI float details
8. **Institutional sponsorship** — Quantitative I and AI quality details
9. **AI catalyst note** — Summary insight from the AI stage

### Helper Methods

| Method | Purpose |
|--------|---------|
| `_get_grade_style(grade)` | Maps grade string to paragraph style |
| `_format_percentage(value)` | Formats float as percentage string |
| `_format_number(value, decimals)` | Formats number with commas |
| `_format_large_number(value)` | Formats with K/M/B suffixes |

## PDF Layout

| Property | Value |
|----------|-------|
| Page size | Letter (8.5" × 11") |
| Margins | 0.75" on all sides |
| Header page | Metadata + score distribution |
| Stock pages | One per candidate, with page break between |

## Output Location

```
project_root/
└── out/
    └── canslim_report_2026-04-04.pdf
```

The output directory is computed as `project_root/out/` where `project_root` is the parent of the `Scripts/` directory.

## Dependencies

- `reportlab` — PDF generation library
  - `reportlab.lib.colors` — Color definitions
  - `reportlab.lib.pagesizes` — Page size constants
  - `reportlab.lib.styles` — Paragraph styles
  - `reportlab.lib.units` — Inch unit
  - `reportlab.lib.enums` — Text alignment
  - `reportlab.platypus` — Document layout engine
- `json` — JSON data loading
- `logging` — Progress logging

## Standalone Usage

```bash
# Generate PDF from existing JSON report
python Scripts/pdf_report_generator.py
```

**Prerequisites:** `Scripts/final_canslim_report.json` must exist (run `final_process.py` first).

## Error Handling

- If `final_canslim_report.json` is missing, logs an error and exits
- If PDF generation fails, the error propagates to the caller (Final Process catches it as a warning)

## Related Pages

- [Final Process](./Final-Process.md) — Invokes this module
- [API Reference](../API-Reference.md) — JSON schema consumed by this module
- [Architecture](../Architecture.md) — Pipeline overview
