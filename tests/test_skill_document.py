"""Tests for the Codex-facing project skill contract."""

from __future__ import annotations

from pathlib import Path

from canslim_analysis.cli import build_parser


SKILL_PATH = Path(__file__).resolve().parents[1] / "SKILL.md"
EXPECTED_COMMANDS = (
    "quantitative",
    "prepare-enrichment",
    "enrich",
    "finalize",
    "report",
    "run",
    "status",
    "validate",
    "verified-research",
)


def test_skill_has_codex_front_matter() -> None:
    """Codex can discover the local skill name and purpose."""

    content = SKILL_PATH.read_text(encoding="utf-8")

    assert content.startswith("---\n")
    assert "name: canslim-analysis\n" in content
    assert "description: " in content.split("---\n", 2)[1]


def test_skill_does_not_require_openclaw() -> None:
    """The workflow has no OpenClaw-specific execution dependency."""

    content = SKILL_PATH.read_text(encoding="utf-8").casefold()

    assert "openclaw" not in content


def test_skill_documents_supported_cli() -> None:
    """Skill commands cannot drift from the implemented CLI."""

    content = SKILL_PATH.read_text(encoding="utf-8")
    help_text = build_parser().format_help()

    for command in EXPECTED_COMMANDS:
        assert f"python -m canslim_analysis {command}" in content
        assert command in help_text


def test_skill_requires_verified_qualitative_evidence() -> None:
    """The skill forbids fabricated catalyst, float, and ownership claims."""

    content = SKILL_PATH.read_text(encoding="utf-8").casefold()

    for phrase in (
        "fabricat",
        "n_new_catalyst",
        "s_float_tightness",
        "i_institutional_quality",
        "not investment advice",
    ):
        assert phrase in content


def test_skill_defines_success_and_failure_contracts() -> None:
    """Codex response format is predictable in successful and failed runs."""

    content = SKILL_PATH.read_text(encoding="utf-8")

    assert "Market Environment:" in content
    assert "Top CANSLIM Candidates:" in content
    assert "Notes & Caveats:" in content
    assert "Failed phase:" in content
