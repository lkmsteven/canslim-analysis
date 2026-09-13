"""Render a canonical final CANSLIM report as PDF."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from canslim_analysis.errors import (
    ArtifactNotFoundError,
    ReportGenerationError,
    SchemaValidationError,
)


logger = logging.getLogger(__name__)


def _load_final_report(path: Path) -> dict[str, Any]:
    """Load and validate the final-report JSON contract."""

    if not path.is_file():
        raise ArtifactNotFoundError(f"Final report not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaValidationError(f"Final report is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SchemaValidationError("Final report must be a JSON object")
    if data.get("Schema_Version") != "2.1":
        raise SchemaValidationError("Final report schema version must be 2.1")
    if not isinstance(data.get("Market_Environment"), str):
        raise SchemaValidationError("Final report requires Market_Environment")
    if not isinstance(data.get("Top_Candidates"), list):
        raise SchemaValidationError("Final report requires a Top_Candidates array")
    return data


def _text(value: Any) -> str:
    """Convert a nullable report value to escaped display text."""

    if value is None:
        return "N/A"
    return escape(str(value))


def render_pdf_report(
    input_path: Path,
    *,
    output_dir: Path | str | None = None,
    project_root: Path | str | None = None,
) -> Path:
    """Render one canonical final report as a PDF.

    Args:
        input_path: Final-report JSON path.
        output_dir: Optional output-directory override.
        project_root: Root used to derive the default output directory.

    Returns:
        The generated PDF path.

    Raises:
        ReportGenerationError: If the PDF engine cannot produce a report.
    """

    report = _load_final_report(input_path)
    selected_output = (
        Path(output_dir).expanduser().resolve()
        if output_dir is not None
        else (Path(project_root) if project_root else Path.cwd()) / "out"
    )
    selected_output.mkdir(parents=True, exist_ok=True)
    report_date = report.get("Report_Date", datetime.now().strftime("%Y-%m-%d"))
    if not isinstance(report_date, str) or len(report_date) != 10:
        raise SchemaValidationError("Final report Report_Date must be YYYY-MM-DD")
    output_path = selected_output / f"canslim_report_{report_date}.pdf"

    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as exc:
        raise ReportGenerationError(
            "PDF rendering requires the reportlab dependency"
        ) from exc

    try:
        styles = getSampleStyleSheet()
        styles.add(
            ParagraphStyle(
                name="CanslimTitle",
                parent=styles["Heading1"],
                alignment=TA_CENTER,
                textColor=colors.HexColor("#1A365D"),
            )
        )
        styles.add(
            ParagraphStyle(
                name="CanslimSection",
                parent=styles["Heading2"],
                textColor=colors.HexColor("#2C5282"),
            )
        )
        elements: list[Any] = [
            Paragraph("CANSLIM Analysis Report", styles["CanslimTitle"]),
            Spacer(1, 12),
            Paragraph(
                f"Report date: {_text(report_date)} | "
                f"Market environment: {_text(report.get('Market_Environment'))}",
                styles["Normal"],
            ),
            Paragraph(
                f"Candidates evaluated: {_text(report.get('Total_Candidates_Evaluated'))}",
                styles["Normal"],
            ),
        ]

        distribution = report.get("Score_Distribution", {})
        if isinstance(distribution, dict) and distribution:
            elements.extend(
                [
                    Spacer(1, 18),
                    Paragraph("Score Distribution", styles["CanslimSection"]),
                    Table(
                        [["Score", "Candidates"]]
                        + [[_text(key), _text(value)] for key, value in distribution.items()],
                        hAlign="LEFT",
                    ),
                ]
            )

        candidates = report.get("Top_Candidates", [])
        for index, stock in enumerate(candidates, start=1):
            if not isinstance(stock, dict):
                raise SchemaValidationError(
                    f"Final-report candidate #{index} must be an object"
                )
            elements.append(PageBreak())
            elements.append(
                Paragraph(
                    f"{index}. {_text(stock.get('Ticker'))} — "
                    f"{_text(stock.get('Company_Name'))}",
                    styles["CanslimSection"],
                )
            )
            summary = [
                ["Score", _text(stock.get("Final_Score"))],
                ["Grade", _text(stock.get("Grade"))],
                ["Met", ", ".join(stock.get("Met_Criteria", [])) or "None"],
                ["Missed", ", ".join(stock.get("Missed_Criteria", [])) or "None"],
                ["RS Rating", _text(stock.get("Metrics", {}).get("RS_Rating"))],
                ["Price", _text(stock.get("Metrics", {}).get("Current_Price"))],
            ]
            elements.append(Table(summary, hAlign="LEFT"))
            elements.extend(
                [
                    Spacer(1, 10),
                    Paragraph(
                        f"AI catalyst: {_text(stock.get('AI_Catalyst_Note'))}",
                        styles["Normal"],
                    ),
                ]
            )

        elements.extend(
            [
                Spacer(1, 24),
                Paragraph(
                    "This report is for educational analysis only and is not "
                    "investment advice. Market data may be delayed or incomplete.",
                    styles["Italic"],
                ),
            ]
        )
        document = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
            title="CANSLIM Analysis Report",
        )
        document.build(elements)
    except ReportGenerationError:
        raise
    except Exception as exc:
        output_path.unlink(missing_ok=True)
        raise ReportGenerationError(f"PDF report generation failed: {exc}") from exc

    if not output_path.is_file():
        raise ReportGenerationError("PDF report generation produced no output")
    logger.info("Generated PDF report: %s", output_path)
    return output_path
