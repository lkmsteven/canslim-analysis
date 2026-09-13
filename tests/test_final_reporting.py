"""Tests for final CANSLIM report generation."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

from canslim_analysis.cli import build_parser, main
from canslim_analysis.pipeline.reporting import build_final_report


def enriched_stock(ticker: str, rs_rating: float) -> dict[str, object]:
    """Create one enriched candidate with a controlled score and RS rating."""

    return {
        "Ticker": ticker,
        "Company_Name": f"{ticker} Company",
        "Quantitative_Metrics": {
            "C_Met": True,
            "A_Met": True,
            "L_Met": True,
            "S_Quant_Met": True,
            "I_Quant_Flag": True,
            "N_Technical_Met": True,
            "RS_Rating": rs_rating,
            "Current_Price": 101.5,
            "Quarterly_EPS_Growth": 0.32,
            "Annual_EPS_Growth": None,
            "Float_Shares": None,
            "Institutional_Ownership": 0.8,
        },
        "AI_Qualitative_Checks": {
            "N_New_Catalyst": True,
            "N_Catalyst_Details": "Raised guidance",
            "S_Float_Tightness": True,
            "S_Float_Details": "Tight float",
            "I_Institutional_Quality": True,
            "I_Institutional_Details": "Quality holders",
        },
    }


def enriched_data(*stocks: dict[str, object]) -> dict[str, object]:
    """Create a market-environment dataset for report tests."""

    return {
        "Metadata": {"Market_Direction_M": "Confirmed Uptrend"},
        "Stocks": list(stocks),
    }


def test_parser_accepts_final_report_paths() -> None:
    """Final report inputs and output directory can be overridden."""

    arguments = build_parser().parse_args(
        ["finalize", "--input", "enriched.json", "--output-dir", "custom"]
    )

    assert arguments.input == "enriched.json"
    assert arguments.output_dir == "custom"


def test_build_final_report_ranks_and_preserves_schema_contract() -> None:
    """Final output preserves score ordering, metrics, and score distribution."""

    data = enriched_data(
        enriched_stock("LOWER-RS", 90.0),
        enriched_stock("HIGHER-RS", 95.0),
        enriched_stock("LOWER-SCORE", 99.0),
    )
    data["Stocks"][2]["AI_Qualitative_Checks"]["N_New_Catalyst"] = False
    original = deepcopy(data)

    report = build_final_report(data)

    assert data == original
    assert report["Schema_Version"] == "2.1"
    assert report["Market_Environment"] == "Confirmed Uptrend"
    assert report["M_Criterion_Met"] is True
    assert report["Total_Candidates_Evaluated"] == 3
    assert report["Score_Distribution"] == {"7": 2, "6": 1}
    assert [stock["Ticker"] for stock in report["Top_Candidates"]] == [
        "HIGHER-RS",
        "LOWER-RS",
        "LOWER-SCORE",
    ]
    first = report["Top_Candidates"][0]
    assert first["Final_Score"] == 7
    assert first["Grade"] == "A+"
    assert first["Met_Criteria"] == ["C", "A", "N", "S", "L", "I", "M"]
    assert first["Missed_Criteria"] == []
    assert first["AI_Catalyst_Note"] == "Raised guidance"
    assert first["Metrics"]["Annual_EPS_Growth"] is None
    assert first["Details"]["S_Float_Details"] == "Tight float"


def test_build_final_report_supports_non_uptrend_and_empty_universe() -> None:
    """Market status and empty candidate sets remain explicit."""

    data = enriched_data()
    data["Metadata"]["Market_Direction_M"] = "Downtrend"

    report = build_final_report(data)

    assert report["M_Criterion_Met"] is False
    assert report["Score_Distribution"] == {}
    assert report["Top_Candidates"] == []


def test_cli_writes_final_report(tmp_path: Path) -> None:
    """The finalize command persists canonical final JSON."""

    input_path = tmp_path / "enriched.json"
    output_dir = tmp_path / "final-out"
    input_path.write_text(
        json.dumps(enriched_data(enriched_stock("AAA", 99.0))),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "finalize",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
        ]
    )

    output_path = output_dir / "final_canslim_report.json"
    assert exit_code == 0
    assert output_path.exists()
    output = json.loads(output_path.read_text(encoding="utf-8"))
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", output["Report_Date"])
    assert re.fullmatch(r"\d{2}:\d{2}:\d{2}", output["Report_Time"])


def test_cli_missing_enriched_input_returns_stable_code(tmp_path: Path) -> None:
    """A missing enriched predecessor artifact produces exit code 4."""

    exit_code = main(
        [
            "finalize",
            "--input",
            str(tmp_path / "missing.json"),
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 4


def test_cli_malformed_enriched_input_returns_stable_code(tmp_path: Path) -> None:
    """Malformed JSON is a schema failure, not an unexpected crash."""

    input_path = tmp_path / "enriched.json"
    input_path.write_text("{not-json}", encoding="utf-8")

    exit_code = main(
        [
            "finalize",
            "--input",
            str(input_path),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    assert exit_code == 3
