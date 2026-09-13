"""Tests for the quantitative command-line stage."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from canslim_analysis.cli import build_parser, main
from canslim_analysis.errors import ExternalDataError
from canslim_analysis.pipeline.config import PipelineConfig
from canslim_analysis.pipeline.quantitative import QuantitativeProviders
from canslim_analysis.cli import _default_quantitative_providers


def market_history(index: str) -> list[float]:
    """Create confirming history for the offline market-direction provider."""

    del index
    return [0.0] * 10 + [100.0] * 189 + [101.0]


def stock_row(ticker: str, return_1y: float) -> dict[str, object]:
    """Create a valid fetched row suitable for quantitative selection."""

    return {
        "Ticker": ticker,
        "Company_Name": f"{ticker} Company",
        "Current_Price": 100.0,
        "Return_1Y": return_1y,
        "Quarterly_EPS_Growth": 0.35,
        "EPS_Accelerating": True,
        "Annual_EPS_Growth": 0.40,
        "Institutional_Ownership": 0.7,
        "S_Quant_Met": True,
        "S_Quant_Details": "Today volume >= 1.5x 50-day average",
        "S_Score": 2,
        "Today_Volume_Strong": True,
        "Volume_Skew_Positive": True,
        "N_Technical_Met": True,
        "N_Technical_Details": "Within 2.0% of 52-week high",
        "Near_52_Week_High": True,
        "Recent_Breakout": False,
        "Pct_From_High": 0.02,
        "High_52_Week": 102.0,
    }


def _providers(
    rows: Sequence[Mapping[str, object] | str],
) -> QuantitativeProviders:
    """Build offline providers from successful rows and failed tickers."""

    row_map = {
        row["Ticker"]: row for row in rows if not isinstance(row, str)
    }

    def fetch_stock(ticker: str) -> Mapping[str, object] | None:
        if ticker in row_map:
            return row_map[ticker]
        raise OSError("provider unavailable")

    return QuantitativeProviders(
        fetch_universe=lambda _config: ["AAA", "BBB", "CCC"],
        fetch_market_history=market_history,
        fetch_stock=fetch_stock,
    )


def test_quantitative_parser_accepts_operational_overrides() -> None:
    """Operators can tune behavior without editing source constants."""

    arguments = build_parser().parse_args(
        [
            "quantitative",
            "--limit",
            "10",
            "--workers",
            "2",
            "--min-eps-growth",
            "0.3",
            "--output-dir",
            "custom-out",
        ]
    )

    assert arguments.limit == 10
    assert arguments.workers == 2
    assert arguments.min_eps_growth == 0.3
    assert arguments.output_dir == "custom-out"


def test_default_quantitative_providers_are_configured() -> None:
    """The default provider bundle is returned for live CLI execution."""

    providers = _default_quantitative_providers(PipelineConfig())

    assert isinstance(providers, QuantitativeProviders)
    assert callable(providers.fetch_universe)
    assert callable(providers.fetch_market_history)
    assert callable(providers.fetch_stock)


def test_quantitative_stage_writes_schema_metadata_and_ranked_candidates(
    tmp_path: Path,
) -> None:
    """A successful stage produces canonical intermediate JSON."""

    output_dir = tmp_path / "out"
    result = main(
        [
            "quantitative",
            "--output-dir",
            str(output_dir),
            "--workers",
            "2",
            "--min-rs-rating",
            "49",
        ],
        providers=_providers([stock_row("AAA", 0.80), "BBB", stock_row("CCC", 0.60)]),
    )

    assert result == 0
    output_path = output_dir / "intermediate_canslim.json"
    data = json.loads(output_path.read_text(encoding="utf-8"))
    metadata = data["Metadata"]

    assert metadata["Market_Direction_M"] == "Confirmed Uptrend"
    assert metadata["Total_Universe_Scanned"] == 3
    assert metadata["Successfully_Evaluated"] == 2
    assert metadata["Failed_Fetches"] == 1
    assert metadata["Stocks_Passed_To_AI"] == 2
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", metadata["Date_Run"])
    assert [stock["Ticker"] for stock in data["Stocks"]] == ["AAA", "CCC"]


def test_quantitative_stage_fails_closed_without_evaluated_stocks(
    tmp_path: Path,
) -> None:
    """A provider-only failure produces a stable external-data exit code."""

    output_dir = tmp_path / "out"
    exit_code = main(
        ["quantitative", "--output-dir", str(output_dir)],
        providers=_providers(["AAA", "BBB", "CCC"]),
    )

    assert exit_code == 5
    assert not (output_dir / "intermediate_canslim.json").exists()


def test_quantitative_stage_maps_universe_failure_to_external_error(
    tmp_path: Path,
) -> None:
    """Universe retrieval failures do not become unexpected internal errors."""

    providers = QuantitativeProviders(
        fetch_universe=lambda _config: (_ for _ in ()).throw(OSError("offline")),
        fetch_market_history=market_history,
        fetch_stock=lambda _ticker: None,
    )

    assert main(["quantitative"], providers=providers) == 5


def test_quantitative_stage_maps_market_history_failure_to_external_error(
    tmp_path: Path,
) -> None:
    """Market-history retrieval failures use the same stable exit code."""

    def failed_history(_index: str) -> list[float]:
        raise OSError("offline")

    providers = QuantitativeProviders(
        fetch_universe=lambda _config: ["AAA"],
        fetch_market_history=failed_history,
        fetch_stock=lambda _ticker: stock_row("AAA", 0.8),
    )

    assert main(["quantitative"], providers=providers) == 5


def test_quantitative_stage_applies_universe_limit(tmp_path: Path) -> None:
    """Universe limits reduce provider calls before concurrency begins."""

    requested: list[str] = []

    def fetch_stock(ticker: str) -> Mapping[str, object]:
        requested.append(ticker)
        return stock_row(ticker, 0.80)

    providers = QuantitativeProviders(
        fetch_universe=lambda _config: ["AAA", "BBB", "CCC"],
        fetch_market_history=market_history,
        fetch_stock=fetch_stock,
    )
    exit_code = main(
        ["quantitative", "--limit", "2"], providers=providers
    )

    assert exit_code == 0
    assert requested == ["AAA", "BBB"]


def test_run_quantitative_rejects_invalid_configuration(tmp_path: Path) -> None:
    """Configuration errors are deliberate and prevent pipeline execution."""

    with pytest.raises(Exception, match="max_workers"):
        PipelineConfig(max_workers=0)

    del tmp_path
