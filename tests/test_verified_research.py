"""Tests for artifact-driven verified research mode."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from canslim_analysis.cli import build_parser, main
from canslim_analysis.errors import SchemaValidationError
from canslim_analysis.pipeline.enrichment import merge_enrichment
from canslim_analysis.pipeline.reporting import build_final_report
from canslim_analysis.pipeline.research import verified_research_findings
from canslim_analysis.reporting.pdf import render_pdf_report
from canslim_analysis.reporting.pdf import DISCLAIMER_TEXT


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def candidate(
    ticker: str,
    *,
    candidate_id: str | None = None,
    company: str | None = None,
) -> dict[str, object]:
    """Create one passing intermediate candidate."""

    result: dict[str, object] = {
        "Ticker": ticker,
        "Company_Name": company or f"{ticker} Company",
        "Quantitative_Metrics": {"C_Met": True},
    }
    if candidate_id is not None:
        result["Candidate_ID"] = candidate_id
    return result


def intermediate(*candidates: dict[str, object], date: str = "2026-09-26") -> dict[str, object]:
    """Create a valid intermediate artifact."""

    return {
        "Metadata": {
            "Schema_Version": "2.1",
            "Date_Run": date,
            "Stocks_Passed_To_AI": len(candidates),
        },
        "Stocks": list(candidates),
    }


def evidence(
    ticker: str,
    field: str,
    *,
    supported: bool = False,
    candidate_id: str | None = None,
    summary: str = "No qualifying evidence identified.",
) -> dict[str, object]:
    """Create one evidence record."""

    result: dict[str, object] = {
        "Ticker": ticker,
        "Field": field,
        "Supported": supported,
        "Summary": summary,
    }
    if candidate_id is not None:
        result["Candidate_ID"] = candidate_id
    if supported:
        result.update(
            {
                "Issuer": f"{ticker} issuer",
                "Share_Class": "common stock",
                "Source": "Issuer press release",
                "Evidence_Date": "2026-09-01",
                "Citation": "https://example.test/release",
                "Criterion_Context": "Directly satisfies the existing criterion.",
            }
        )
    return result


def evidence_pack(
    data: dict[str, object],
    records: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Create complete conservative evidence unless explicit records are supplied."""

    fields = ("N_New_Catalyst", "S_Float_Tightness", "I_Institutional_Quality")
    generated = [
        evidence(str(stock["Ticker"]), field, candidate_id=stock.get("Candidate_ID"))
        for stock in data["Stocks"]
        for field in fields
    ]
    if records is not None:
        overrides = {
            (
                str(occurrence_key(record)),
                str(record["Field"]),
            ): record
            for record in records
        }
        generated = [
            overrides.get(
                (
                    str(occurrence_key(record)),
                    str(record["Field"]),
                ),
                record,
            )
            for record in generated
        ]
    return {
        "Schema_Version": "1.0",
        "Analysis_Date": data["Metadata"].get("Date_Run"),
        "Evidence": generated,
    }


def true_record(
    ticker: str,
    field: str,
    *,
    candidate_id: str | None = None,
) -> dict[str, object]:
    """Create a fully attributed positive evidence record."""

    return evidence(
        ticker,
        field,
        supported=True,
        candidate_id=candidate_id,
        summary="The issuer disclosed a direct operational catalyst.",
    )


def occurrence_key(record: dict[str, object]) -> object:
    """Key a helper record by its explicit valid candidate ID, else ticker."""

    candidate_id = record.get("Candidate_ID")
    if isinstance(candidate_id, str) and candidate_id.strip():
        return candidate_id
    return record["Ticker"]


def write_json(path: Path, data: object) -> Path:
    """Write a deterministic JSON fixture."""

    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_parser_accepts_verified_research_inputs() -> None:
    """Verified research requires intermediate, evidence, and output paths."""

    arguments = build_parser().parse_args(
        [
            "verified-research",
            "--input",
            "quant.json",
            "--evidence",
            "evidence.json",
            "--output",
            "findings.json",
        ]
    )

    assert arguments.command == "verified-research"
    assert arguments.input == "quant.json"
    assert arguments.evidence == "evidence.json"
    assert arguments.output == "findings.json"

    with pytest.raises(SystemExit, match="2"):
        build_parser().parse_args(
            [
                "verified-research",
                "--input",
                "quant.json",
                "--evidence",
                "evidence.json",
                "--output",
                "findings.json",
                "--unverified-fallback",
            ]
        )


def test_discovers_all_candidates_in_input_order() -> None:
    """Every passing row becomes one ordered findings entry."""

    data = intermediate(candidate("ZZZ"), candidate("AAA"), candidate("MMM"))
    result = verified_research_findings(data, evidence_pack(data))

    assert [finding["Ticker"] for finding in result["Findings"]] == ["ZZZ", "AAA", "MMM"]
    assert len(result["Findings"]) == 3


def test_separate_share_classes_and_duplicate_ids_remain_distinct() -> None:
    """Occurrence identity cannot collapse duplicate rows or share classes."""

    data = intermediate(
        candidate("GOOGL", candidate_id="GOOGL-A", company="Alphabet A"),
        candidate("GOOG", candidate_id="GOOG-C", company="Alphabet C"),
        candidate("DUP", candidate_id="DUP-1"),
        candidate("DUP", candidate_id="DUP-2"),
    )
    pack = evidence_pack(data)
    result = verified_research_findings(data, pack)

    assert [finding.get("Candidate_ID") for finding in result["Findings"]] == [
        "GOOGL-A",
        "GOOG-C",
        "DUP-1",
        "DUP-2",
    ]
    assert len(result["Findings"]) == len(data["Stocks"])


def test_non_passing_and_mismatched_counts_are_rejected() -> None:
    """Passing count comes only from the complete Stocks contract."""

    data = intermediate(candidate("AAA"))
    data["Metadata"]["Stocks_Passed_To_AI"] = 2
    with pytest.raises(SchemaValidationError, match="Stocks_Passed_To_AI"):
        verified_research_findings(data, evidence_pack(data))

    zero = intermediate()
    with pytest.raises(SchemaValidationError, match="no passing candidates"):
        verified_research_findings(zero, evidence_pack(zero))


def test_duplicate_tickers_require_unique_candidate_ids() -> None:
    """Unsafe ticker-only duplicate identity fails before output."""

    data = intermediate(candidate("DUP"), candidate("DUP"))
    with pytest.raises(SchemaValidationError, match="Candidate_ID"):
        verified_research_findings(data, evidence_pack(data))


def test_missing_or_invalid_analysis_date_fails() -> None:
    """Analysis date is mandatory and strictly validated."""

    for date in (None, "not-a-date", "2026-9-26", "2099-12-31"):
        data = intermediate(candidate("AAA"), date=date)
        with pytest.raises(SchemaValidationError, match="Date_Run"):
            verified_research_findings(data, evidence_pack(data))


def test_true_flags_require_complete_as_of_evidence() -> None:
    """Any missing true-evidence metadata is rejected or conservatively false."""

    data = intermediate(candidate("AAA"))
    valid = true_record("AAA", "N_New_Catalyst")
    result = verified_research_findings(data, evidence_pack(data, [valid]))
    assert result["Findings"][0]["N_New_Catalyst"] is True
    assert "Issuer press release" in result["Findings"][0]["N_Catalyst_Details"]

    for field in (
        "Issuer",
        "Share_Class",
        "Source",
        "Evidence_Date",
        "Citation",
        "Summary",
        "Criterion_Context",
    ):
        record = true_record("AAA", "N_New_Catalyst")
        record[field] = ""
        with pytest.raises(SchemaValidationError, match=field.casefold()):
            verified_research_findings(data, evidence_pack(data, [record]))


def test_positive_candidate_id_targets_exact_occurrence() -> None:
    """A dated positive record may carry matching occurrence identity."""

    data = intermediate(
        candidate("DUP", candidate_id="DUP-1"),
        candidate("DUP", candidate_id="DUP-2"),
    )
    record = true_record(
        "DUP",
        "N_New_Catalyst",
        candidate_id="DUP-1",
    )
    result = verified_research_findings(data, evidence_pack(data, [record]))

    assert result["Findings"][0]["Candidate_ID"] == "DUP-1"
    assert result["Findings"][0]["N_New_Catalyst"] is True


def test_positive_candidate_id_must_be_non_empty_text() -> None:
    """Malformed or blank positive evidence identity is rejected."""

    data = intermediate(candidate("AAA"))
    for candidate_id in (123, "", "   "):
        record = true_record("AAA", "N_New_Catalyst")
        record["Candidate_ID"] = candidate_id
        with pytest.raises(SchemaValidationError, match="Candidate_ID"):
            verified_research_findings(data, evidence_pack(data, [record]))


def test_legacy_positive_record_without_candidate_id_is_accepted() -> None:
    """Ticker-only positive evidence remains valid when unambiguous."""

    data = intermediate(candidate("AAA"))
    record = true_record("AAA", "I_Institutional_Quality")
    result = verified_research_findings(data, evidence_pack(data, [record]))

    assert "Candidate_ID" not in result["Findings"][0]
    assert result["Findings"][0]["I_Institutional_Quality"] is True


def test_post_analysis_and_non_retrievable_evidence_are_rejected() -> None:
    """Only dated retrievable evidence accepted on or before analysis date."""

    data = intermediate(candidate("AAA"))
    late = true_record("AAA", "N_New_Catalyst")
    late["Evidence_Date"] = "2026-09-27"
    with pytest.raises(SchemaValidationError, match="after analysis date"):
        verified_research_findings(data, evidence_pack(data, [late]))

    unsupported_citation = true_record("AAA", "N_New_Catalyst")
    unsupported_citation["Citation"] = "search snippet only"
    with pytest.raises(SchemaValidationError, match="retrievable citation"):
        verified_research_findings(data, evidence_pack(data, [unsupported_citation]))


def test_supply_negatives_never_become_positive() -> None:
    """Dilutive or unexecuted supply events remain conservative false findings."""

    data = intermediate(candidate("AAA"))
    negatives = (
        "Completed secondary offering increased tradable shares.",
        "Lockup expiration increased shares eligible for sale.",
        "Convertible notes will cause dilution.",
        "Board authorized a buyback, but no shares have been repurchased.",
    )
    for summary in negatives:
        record = evidence(
            "AAA",
            "S_Float_Tightness",
            summary=summary,
        )
        result = verified_research_findings(data, evidence_pack(data, [record]))
        assert result["Findings"][0]["S_Float_Tightness"] is False
        assert summary in result["Findings"][0]["S_Float_Details"]


def test_inconclusive_positive_claims_are_rejected() -> None:
    """Ambiguous, contradictory, and low-quality text cannot claim support."""

    data = intermediate(candidate("AAA"))
    for summary in (
        "The evidence is ambiguous.",
        "The filing is contradictory.",
        "An unsourced low-quality aggregator made a claim.",
        "A tangential market article mentioned the ticker.",
    ):
        record = true_record("AAA", "N_New_Catalyst")
        record["Summary"] = summary
        with pytest.raises(SchemaValidationError, match="not direct positive evidence"):
            verified_research_findings(data, evidence_pack(data, [record]))


def test_research_output_is_atomic_on_failure(tmp_path: Path) -> None:
    """Validation failure leaves neither output nor a temporary artifact."""

    data = intermediate(candidate("AAA"))
    input_path = write_json(tmp_path / "quant.json", data)
    evidence_path = write_json(tmp_path / "evidence.json", {"broken": True})
    output_path = tmp_path / "findings.json"

    exit_code = main(
        [
            "verified-research",
            "--input",
            str(input_path),
            "--evidence",
            str(evidence_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 3
    assert not output_path.exists()
    assert not list(tmp_path.glob("*.tmp"))


def test_safe_failure_matrix(tmp_path: Path) -> None:
    """Missing, malformed, invalid, unavailable, and empty research inputs fail."""

    good = intermediate(candidate("AAA"))
    missing_input = tmp_path / "missing.json"
    exit_code = main(
        [
            "verified-research",
            "--input",
            str(missing_input),
            "--evidence",
            str(write_json(tmp_path / "evidence.json", evidence_pack(good))),
            "--output",
            str(tmp_path / "unused.json"),
        ]
    )
    assert exit_code == 4

    malformed = write_json(tmp_path / "malformed.json", good)
    malformed.write_text("{", encoding="utf-8")
    exit_code = main(
        [
            "verified-research",
            "--input",
            str(malformed),
            "--evidence",
            str(tmp_path / "missing-evidence.json"),
            "--output",
            str(tmp_path / "unused.json"),
        ]
    )
    # Input validation occurs before evidence retrieval/access.
    assert exit_code == 3

    invalid = intermediate(candidate("AAA"))
    del invalid["Metadata"]["Date_Run"]
    exit_code = main(
        [
            "verified-research",
            "--input",
            str(write_json(tmp_path / "invalid.json", invalid)),
            "--evidence",
            str(write_json(tmp_path / "evidence.json", evidence_pack(good))),
            "--output",
            str(tmp_path / "unused.json"),
        ]
    )
    assert exit_code == 3

    zero = intermediate()
    exit_code = main(
        [
            "verified-research",
            "--input",
            str(write_json(tmp_path / "zero.json", zero)),
            "--evidence",
            str(write_json(tmp_path / "zero-evidence.json", evidence_pack(zero))),
            "--output",
            str(tmp_path / "unused.json"),
        ]
    )
    assert exit_code == 3
    assert not any(tmp_path.glob("unused.json*"))


def test_legacy_findings_and_enriched_dataset_remain_compatible() -> None:
    """Existing exact ticker-schema findings still merge without Candidate_ID."""

    legacy_quantitative = {
        "Metadata": {"Schema_Version": "2.1"},
        "Stocks": [
            {
                "Ticker": "AAA",
                "Company_Name": "A",
                "Quantitative_Metrics": {},
                "AI_Qualitative_Checks_Pending": {},
                "AI_Qualitative_Checks": {},
            }
        ],
    }
    findings = {
        "Schema_Version": "2.1",
        "Findings": [
            {
                "Ticker": "AAA",
                "N_New_Catalyst": True,
                "N_Catalyst_Details": "Issuer guidance",
                "S_Float_Tightness": False,
                "S_Float_Details": "No qualifying evidence",
                "I_Institutional_Quality": False,
                "I_Institutional_Details": "No qualifying evidence",
            }
        ],
    }
    original = copy.deepcopy(findings)
    enriched = merge_enrichment(legacy_quantitative, findings)
    assert findings == original
    assert enriched["Stocks"][0]["AI_Qualitative_Checks"]["N_New_Catalyst"] is True
    assert build_final_report(enriched)["Top_Candidates"][0]["Ticker"] == "AAA"


def test_duplicate_occurrences_survive_enrichment_and_finalization() -> None:
    """Additive candidate IDs preserve occurrence count through existing pipeline."""

    quantitative = intermediate(
        candidate("DUP", candidate_id="DUP-1"),
        candidate("DUP", candidate_id="DUP-2"),
    )
    findings = verified_research_findings(quantitative, evidence_pack(quantitative))
    enriched = merge_enrichment(quantitative, findings)
    final = build_final_report(enriched)

    assert len(enriched["Stocks"]) == 2
    assert len(final["Top_Candidates"]) == 2


def test_verified_research_cli_end_to_end(tmp_path: Path) -> None:
    """CLI writes validated findings that enrich accepts without manual editing."""

    data = intermediate(candidate("AAA"), candidate("BBB"))
    record = true_record("AAA", "I_Institutional_Quality")
    input_path = write_json(tmp_path / "quant.json", data)
    evidence_path = write_json(tmp_path / "evidence.json", evidence_pack(data, [record]))
    findings_path = tmp_path / "findings.json"

    exit_code = main(
        [
            "verified-research",
            "--input",
            str(input_path),
            "--evidence",
            str(evidence_path),
            "--output",
            str(findings_path),
        ]
    )

    assert exit_code == 0
    assert findings_path.is_file()
    merged = merge_enrichment(data, json.loads(findings_path.read_text("utf-8")))
    assert merged["Stocks"][0]["AI_Qualitative_Checks"]["I_Institutional_Quality"] is True


def test_documented_end_to_end_command_succeeds(tmp_path: Path) -> None:
    """Supported JSON and PDF research pipeline stages remain usable."""

    data = intermediate(candidate("AAA"))
    input_path = write_json(tmp_path / "quant.json", data)
    evidence_path = write_json(tmp_path / "evidence.json", evidence_pack(data))
    findings_path = tmp_path / "findings.json"
    environment = {"PYTHONPATH": str(PROJECT_ROOT / "src"), "PATH": str(Path(sys.executable).parent)}
    base = [
        sys.executable,
        "-m",
        "canslim_analysis",
        "verified-research",
        "--input",
        str(input_path),
        "--evidence",
        str(evidence_path),
        "--output",
        str(findings_path),
    ]
    research = subprocess.run(base, cwd=PROJECT_ROOT, env=environment, capture_output=True, text=True, check=False)
    assert research.returncode == 0, research.stderr

    # Report generation is exercised in project PDF tests; here validate the
    # complete JSON chain through existing public functions and validators.
    from canslim_analysis.pipeline.status import validate_artifact

    enriched = merge_enrichment(data, json.loads(findings_path.read_text("utf-8")))
    enriched_path = write_json(tmp_path / "enriched.json", enriched)
    final = build_final_report(enriched)
    final_path = write_json(tmp_path / "final.json", final)
    validate_artifact(enriched_path, "enriched")
    validate_artifact(final_path, "final")
    pdf_path = render_pdf_report(final_path, output_dir=tmp_path / "report")
    assert pdf_path.is_file()
    assert pdf_path.stat().st_size > 0


def test_downstream_enrich_failure_is_safe(tmp_path: Path) -> None:
    """A downstream stage failure returns its stable non-zero exit code."""

    findings_path = write_json(
        tmp_path / "findings.json",
        {
            "Schema_Version": "2.1",
            "Findings": [
                {
                    "Ticker": "AAA",
                    "N_New_Catalyst": False,
                    "N_Catalyst_Details": "No qualifying evidence",
                    "S_Float_Tightness": False,
                    "S_Float_Details": "No qualifying evidence",
                    "I_Institutional_Quality": False,
                    "I_Institutional_Details": "No qualifying evidence",
                }
            ],
        },
    )
    exit_code = main(
        [
            "enrich",
            "--input",
            str(tmp_path / "missing-quant.json"),
            "--findings",
            str(findings_path),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )
    assert exit_code == 4


def test_pdf_carries_exact_educational_research_label() -> None:
    """The generated report label uses the required verified-research wording."""

    assert DISCLAIMER_TEXT == (
        "Educational research and analysis — not personalized investment advice."
    )
