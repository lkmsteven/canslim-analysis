"""Tests for strict qualitative findings validation and merge."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from canslim_analysis.cli import build_parser, main
from canslim_analysis.pipeline.enrichment import (
    build_enrichment_template,
    merge_enrichment,
)
from tests.test_enrichment import quant_input


def finding(ticker: str = "AAA", **overrides: object) -> dict[str, object]:
    """Create one template finding, optionally overriding fields."""

    finding = build_enrichment_template(quant_input(ticker))["Findings"][0]
    finding.update(overrides)
    return finding


def findings_data(*findings: dict[str, object]) -> dict[str, object]:
    """Wrap findings in the documented findings artifact."""

    return {"Schema_Version": "2.1", "Findings": list(findings)}


def test_parser_accepts_enrichment_inputs() -> None:
    """The enrichment command names both of its required inputs."""

    arguments = build_parser().parse_args(
        ["enrich", "--input", "quant.json", "--findings", "findings.json"]
    )

    assert arguments.input == "quant.json"
    assert arguments.findings == "findings.json"


def test_merge_preserves_quantitative_and_updates_verified_findings() -> None:
    """Only six qualitative fields change; quantitative evidence is untouched."""

    quant = quant_input("AAA")
    original = copy.deepcopy(quant)
    result = merge_enrichment(
        quant,
        findings_data(
            finding(
                "AAA",
                N_New_Catalyst=True,
                N_Catalyst_Details="Raised guidance",
                S_Float_Tightness=True,
                S_Float_Details="Tight float",
                I_Institutional_Quality=True,
                I_Institutional_Details="Quality sponsors",
            )
        ),
    )

    assert quant == original
    stock = result["Stocks"][0]
    checks = stock["AI_Qualitative_Checks"]
    assert checks["N_New_Catalyst"] is True
    assert checks["S_Float_Tightness"] is True
    assert checks["I_Institutional_Quality"] is True
    assert stock["Quantitative_Metrics"] == original["Stocks"][0][
        "Quantitative_Metrics"
    ]


def test_merge_rejects_true_finding_without_evidence() -> None:
    """True claims require evidence or rationale."""

    try:
        merge_enrichment(
            quant_input("AAA"),
            findings_data(finding("AAA", N_New_Catalyst=True)),
        )
    except Exception as exc:
        assert "evidence" in str(exc).lower()
    else:
        raise AssertionError("true finding without evidence was accepted")


def test_merge_rejects_unknown_ticker() -> None:
    """Findings cannot add candidates absent from quantitative screening."""

    try:
        merge_enrichment(quant_input("AAA"), findings_data(finding("UNKNOWN")))
    except Exception as exc:
        assert "unknown" in str(exc).lower()
    else:
        raise AssertionError("unknown ticker was accepted")


def test_merge_names_empty_candidate_mismatch() -> None:
    """A zero-candidate quantitative run cannot consume prior findings."""

    empty_quantitative = {"Metadata": {"Schema_Version": "2.1"}, "Stocks": []}
    try:
        merge_enrichment(
            empty_quantitative,
            findings_data(finding("STALE")),
        )
    except Exception as exc:
        assert "no candidates" in str(exc).lower()
    else:
        raise AssertionError("findings were accepted for an empty candidate set")


def test_merge_rejects_duplicate_and_missing_findings() -> None:
    """One-to-one candidate coverage is mandatory."""

    for findings in (
        findings_data(finding("AAA"), finding("AAA")),
        findings_data(),
    ):
        try:
            merge_enrichment(quant_input("AAA"), findings)
        except Exception as exc:
            assert "exactly one" in str(exc).lower()
        else:
            raise AssertionError("invalid finding coverage was accepted")


def test_merge_rejects_unknown_field_and_non_boolean() -> None:
    """Findings conform to the exact documented shape and types."""

    invalid_unknown = finding("AAA", Unknown_Field="bad")
    invalid_type = finding("AAA", N_New_Catalyst="true", N_Catalyst_Details="bad")
    for finding_value in (invalid_unknown, invalid_type):
        try:
            merge_enrichment(
                quant_input("AAA"), findings_data(finding_value)
            )
        except Exception:
            pass
        else:
            raise AssertionError("invalid finding shape was accepted")


def test_cli_merges_findings_and_writes_enriched_artifact(tmp_path: Path) -> None:
    """The CLI validates both inputs and persists one canonical output."""

    quant_path = tmp_path / "quant.json"
    findings_path = tmp_path / "findings.json"
    output_dir = tmp_path / "out"
    quant_path.write_text(json.dumps(quant_input("AAA")), encoding="utf-8")
    findings_path.write_text(
        json.dumps(
            findings_data(finding("AAA", N_New_Catalyst=True, N_Catalyst_Details="News"))
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "enrich",
            "--input",
            str(quant_path),
            "--findings",
            str(findings_path),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    output = json.loads(
        (output_dir / "enriched_canslim.json").read_text(encoding="utf-8")
    )
    assert output["Stocks"][0]["AI_Qualitative_Checks"]["N_New_Catalyst"] is True
