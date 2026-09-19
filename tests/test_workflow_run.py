"""Tests for end-to-end workflow orchestration with offline providers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from canslim_analysis.cli import build_parser, main
from tests.test_quantitative_cli import market_history, stock_row


def providers():
    """Build offline providers with two passing candidates."""

    from canslim_analysis.pipeline.quantitative import QuantitativeProviders

    rows = {stock["Ticker"]: stock for stock in (
        stock_row("AAA", 0.90),
        stock_row("BBB", 0.60),
    )}
    return QuantitativeProviders(
        fetch_universe=lambda _config: ["AAA", "BBB"],
        fetch_market_history=market_history,
        fetch_stock=lambda ticker: rows[ticker],
    )


def findings(path: Path) -> Path:
    """Write conservative findings for the offline candidates."""

    template = {
        "Schema_Version": "2.1",
        "Findings": [
            {
                "Ticker": "AAA",
                "N_New_Catalyst": True,
                "N_Catalyst_Details": "Raised guidance",
                "S_Float_Tightness": True,
                "S_Float_Details": "Tight float",
                "I_Institutional_Quality": True,
                "I_Institutional_Details": "Quality holders",
            },
            {
                "Ticker": "BBB",
                "N_New_Catalyst": False,
                "N_Catalyst_Details": "",
                "S_Float_Tightness": False,
                "S_Float_Details": "",
                "I_Institutional_Quality": False,
                "I_Institutional_Details": "",
            },
        ],
    }
    path.write_text(json.dumps(template), encoding="utf-8")
    return path


def base_arguments(output_dir: Path) -> list[str]:
    """Create arguments that make both offline candidates pass."""

    return [
        "run",
        "--output-dir",
        str(output_dir),
        "--min-rs-rating",
        "49",
    ]


def test_parser_accepts_run_options() -> None:
    """The run command supports findings and explicit fallback."""

    arguments = build_parser().parse_args(
        base_arguments(Path("out"))
        + ["--findings", "findings.json", "--unverified-fallback"]
    )

    assert arguments.findings == "findings.json"
    assert arguments.unverified_fallback is True


def test_run_executes_all_stages_with_findings(tmp_path: Path) -> None:
    """A findings file allows quantitative through PDF completion."""

    output_dir = tmp_path / "out"
    findings_path = findings(tmp_path / "findings.json")
    exit_code = main(
        base_arguments(output_dir) + ["--findings", str(findings_path)],
        providers=providers(),
    )

    assert exit_code == 0
    for filename in (
        "intermediate_canslim.json",
        "enriched_canslim.json",
        "final_canslim_report.json",
    ):
        assert (output_dir / filename).is_file()
    assert list(output_dir.glob("canslim_report_*.pdf"))


def test_run_without_findings_stops_after_quantitative(tmp_path: Path) -> None:
    """The workflow cannot invent qualitative findings."""

    output_dir = tmp_path / "out"
    exit_code = main(base_arguments(output_dir), providers=providers())

    assert exit_code == 0
    assert (output_dir / "intermediate_canslim.json").is_file()
    assert not (output_dir / "enriched_canslim.json").exists()
    assert not (output_dir / "final_canslim_report.json").exists()


def test_zero_candidates_with_findings_stop_before_stale_merge(
    tmp_path: Path,
) -> None:
    """Prior findings are rejected safely when a new screen has no candidates."""

    output_dir = tmp_path / "out"
    findings_path = findings(tmp_path / "findings.json")
    exit_code = main(
        base_arguments(output_dir)
        + [
            "--min-eps-growth",
            "1.0",
            "--min-annual-eps-growth",
            "1.0",
            "--findings",
            str(findings_path),
        ],
        providers=providers(),
    )

    assert exit_code == 0
    intermediate = json.loads(
        (output_dir / "intermediate_canslim.json").read_text(encoding="utf-8")
    )
    assert intermediate["Metadata"]["Stocks_Passed_To_AI"] == 0
    assert not (output_dir / "enriched_canslim.json").exists()
    assert not (output_dir / "final_canslim_report.json").exists()
    assert not list(output_dir.glob("canslim_report_*.pdf"))


def test_zero_candidates_with_fallback_produces_empty_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Explicit fallback remains useful when no candidates were selected."""

    output_dir = tmp_path / "out"
    exit_code = main(
        base_arguments(output_dir)
        + [
            "--min-eps-growth",
            "1.0",
            "--min-annual-eps-growth",
            "1.0",
            "--unverified-fallback",
        ],
        providers=providers(),
    )

    assert exit_code == 0
    assert "no candidates" in capsys.readouterr().out.lower()
    enriched = json.loads(
        (output_dir / "enriched_canslim.json").read_text(encoding="utf-8")
    )
    assert enriched["Stocks"] == []
    final = json.loads(
        (output_dir / "final_canslim_report.json").read_text(encoding="utf-8")
    )
    assert final["Total_Candidates_Evaluated"] == 0
    assert list(output_dir.glob("canslim_report_*.pdf"))


def test_explicit_unverified_fallback_continues_with_false_checks(
    tmp_path: Path,
) -> None:
    """Fallback is allowed only when explicitly requested."""

    output_dir = tmp_path / "out"
    exit_code = main(
        base_arguments(output_dir) + ["--unverified-fallback"],
        providers=providers(),
    )

    assert exit_code == 0
    enriched = json.loads(
        (output_dir / "enriched_canslim.json").read_text(encoding="utf-8")
    )
    for stock in enriched["Stocks"]:
        checks = stock["AI_Qualitative_Checks"]
        assert checks["N_New_Catalyst"] is False
        assert checks["S_Float_Tightness"] is False
        assert checks["I_Institutional_Quality"] is False
    assert (output_dir / "final_canslim_report.json").is_file()


def test_stock_failure_does_not_create_final_artifacts(tmp_path: Path) -> None:
    """A total quantitative failure short-circuits later stages."""

    from canslim_analysis.errors import ExternalDataError
    from canslim_analysis.pipeline.quantitative import QuantitativeProviders

    output_dir = tmp_path / "out"
    failing = QuantitativeProviders(
        fetch_universe=lambda _config: ["AAA"],
        fetch_market_history=market_history,
        fetch_stock=lambda _ticker: None,
    )
    exit_code = main(
        base_arguments(output_dir) + ["--unverified-fallback"],
        providers=failing,
    )

    assert exit_code == 5
    assert not (output_dir / "final_canslim_report.json").exists()
    del ExternalDataError


def test_invalid_findings_do_not_create_final_artifacts(
    tmp_path: Path,
) -> None:
    """Invalid qualitative input short-circuits before final scoring."""

    output_dir = tmp_path / "out"
    findings_path = tmp_path / "findings.json"
    findings_path.write_text('{"Findings": "wrong"}', encoding="utf-8")

    exit_code = main(
        base_arguments(output_dir) + ["--findings", str(findings_path)],
        providers=providers(),
    )

    assert exit_code == 3
    assert (output_dir / "intermediate_canslim.json").is_file()
    assert not (output_dir / "enriched_canslim.json").exists()
    assert not (output_dir / "final_canslim_report.json").exists()
