"""Tests for qualitative enrichment template generation and merging."""

from __future__ import annotations

import json
from pathlib import Path

from canslim_analysis.cli import build_parser, main
from canslim_analysis.pipeline.enrichment import build_enrichment_template


def quant_input(*tickers: str) -> dict[str, object]:
    """Create a small valid quantitative artifact."""

    return {
        "Metadata": {"Schema_Version": "2.1"},
        "Stocks": [
            {
                "Ticker": ticker,
                "Company_Name": f"{ticker} Company",
                "Quantitative_Metrics": {"C_Met": True},
            }
            for ticker in tickers
        ],
    }


def test_parser_accepts_enrichment_template_paths() -> None:
    """The template command can override both input and output root."""

    arguments = build_parser().parse_args(
        ["prepare-enrichment", "--input", "in.json", "--output-dir", "out"]
    )

    assert arguments.input == "in.json"
    assert arguments.output_dir == "out"


def test_template_covers_every_candidate_with_conservative_defaults() -> None:
    """Every candidate receives one all-false findings entry."""

    template = build_enrichment_template(quant_input("AAA", "BBB"))

    assert template["Schema_Version"] == "2.1"
    assert [entry["Ticker"] for entry in template["Findings"]] == ["AAA", "BBB"]
    assert template["Findings"][0] == {
        "Ticker": "AAA",
        "N_New_Catalyst": False,
        "N_Catalyst_Details": "",
        "S_Float_Tightness": False,
        "S_Float_Details": "",
        "I_Institutional_Quality": False,
        "I_Institutional_Details": "",
    }


def test_template_generation_is_deterministic(tmp_path: Path) -> None:
    """Repeated generation yields identical serialized output."""

    first = build_enrichment_template(quant_input("AAA", "BBB"))
    second = build_enrichment_template(quant_input("AAA", "BBB"))

    assert first == second


def test_template_allows_zero_candidates() -> None:
    """An empty candidate set is valid and produces an empty findings array."""

    assert build_enrichment_template(quant_input())["Findings"] == []


def test_template_rejects_duplicate_candidates() -> None:
    """Duplicate tickers are ambiguous and rejected before Codex research."""

    data = quant_input("AAA", "AAA")

    try:
        build_enrichment_template(data)
    except Exception as exc:
        assert "duplicate" in str(exc).lower()
    else:
        raise AssertionError("duplicate ticker was accepted")


def test_cli_prepares_enrichment_template(tmp_path: Path) -> None:
    """The command reads quantitative input and writes a local template."""

    input_path = tmp_path / "intermediate.json"
    output_dir = tmp_path / "custom"
    input_path.write_text(json.dumps(quant_input("AAA")), encoding="utf-8")

    exit_code = main(
        [
            "prepare-enrichment",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
        ]
    )

    output_path = output_dir / "enrichment_template.json"
    assert exit_code == 0
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8"))["Findings"][0][
        "Ticker"
    ] == "AAA"


def test_cli_missing_quantitative_input_returns_stable_code(tmp_path: Path) -> None:
    """A missing predecessor artifact produces exit code 4."""

    exit_code = main(
        [
            "prepare-enrichment",
            "--input",
            str(tmp_path / "missing.json"),
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 4
