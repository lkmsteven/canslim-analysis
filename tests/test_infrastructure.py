"""Tests for configuration, path resolution, logging, and error types."""

from __future__ import annotations

import logging
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from canslim_analysis.errors import (
    ArtifactNotFoundError,
    CanslimError,
    ConfigurationError,
    ExternalDataError,
    ReportGenerationError,
    SchemaValidationError,
)
from canslim_analysis.logging_setup import configure_logging
from canslim_analysis.paths import (
    INTERMEDIATE_ARTIFACT,
    resolve_artifact_path,
    resolve_output_directory,
)
from canslim_analysis.pipeline.config import PipelineConfig


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_local_editable_install_targets_this_project() -> None:
    """The documented CLI must execute this project, not a stale local copy."""

    editable_hook = (
        PROJECT_ROOT
        / ".venv"
        / "Lib"
        / "site-packages"
        / "__editable__.canslim_analysis-2.1.0.pth"
    )
    if not editable_hook.is_file():
        pytest.skip("project-local virtual environment is not present")

    configured_source = Path(editable_hook.read_text(encoding="utf-8").strip())
    assert configured_source.resolve() == (PROJECT_ROOT / "src").resolve()


def test_pipeline_config_uses_current_analysis_defaults() -> None:
    """Defaults preserve the behavior of the original module constants."""

    config = PipelineConfig()

    assert config.min_eps_growth == 0.25
    assert config.min_annual_eps_growth == 0.25
    assert config.min_rs_rating == 80.0
    assert config.min_volume_ratio == 1.5
    assert config.min_volume_skew == 1.2
    assert config.min_institutional_ownership == 0.30
    assert config.market_lookback_days == 200
    assert config.min_history_days == 250
    assert config.max_workers == 3
    assert config.universe_limit is None
    assert config.request_timeout == 10.0
    assert config.max_retries == 4
    assert config.retry_delay == 3.0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("min_eps_growth", -0.01),
        ("min_annual_eps_growth", 1.01),
        ("min_rs_rating", 0.0),
        ("min_volume_ratio", 0.0),
        ("min_volume_skew", -1.0),
        ("min_institutional_ownership", 1.01),
        ("market_lookback_days", 0),
        ("min_history_days", -1),
        ("max_workers", 0),
        ("universe_limit", 0),
        ("request_timeout", 0.0),
        ("max_retries", -1),
        ("retry_delay", -0.1),
    ],
)
def test_pipeline_config_rejects_invalid_operational_values(
    field: str, value: float | int
) -> None:
    """Every operational boundary is validated at construction time."""

    with pytest.raises(ConfigurationError, match=field):
        PipelineConfig(**{field: value})


def test_pipeline_config_is_immutable() -> None:
    """Runtime mutation of shared configuration is forbidden."""

    config = PipelineConfig()

    with pytest.raises(FrozenInstanceError):
        config.max_workers = 10


def test_error_hierarchy_preserves_deliberate_failure_categories() -> None:
    """All expected errors remain catchable through the project base class."""

    assert issubclass(ConfigurationError, CanslimError)
    assert issubclass(ArtifactNotFoundError, CanslimError)
    assert issubclass(SchemaValidationError, CanslimError)
    assert issubclass(ExternalDataError, CanslimError)
    assert issubclass(ReportGenerationError, CanslimError)


def test_output_directory_defaults_to_project_out_and_resolves_override(
    tmp_path: Path,
) -> None:
    """Default output is project-local, while explicit overrides are absolute."""

    project_root = tmp_path / "project-root"
    default_directory = resolve_output_directory(project_root=project_root)
    override_directory = resolve_output_directory(
        Path("custom-output"),
        project_root=project_root,
    )

    assert default_directory == project_root / "out"
    assert override_directory.is_absolute()
    assert override_directory.name == "custom-output"


def test_artifact_paths_are_resolved_without_writing_files(tmp_path: Path) -> None:
    """Artifact resolution is deterministic and has no filesystem side effects."""

    path = resolve_artifact_path(
        INTERMEDIATE_ARTIFACT,
        output_dir=tmp_path,
        project_root=tmp_path,
    )

    assert path == tmp_path / "intermediate_canslim.json"
    assert not path.exists()


def test_configure_logging_writes_file_and_does_not_duplicate_handlers(
    tmp_path: Path,
) -> None:
    """Repeated setup replaces handlers and emits to both file and console."""

    log_file = tmp_path / "logs" / "pipeline.log"

    configure_logging(log_file)
    configure_logging(log_file)

    logging.getLogger("canslim_analysis.test").info("deterministic message")
    for handler in logging.getLogger().handlers:
        handler.flush()

    assert log_file.read_text(encoding="utf-8").find("deterministic message") >= 0
    console_handlers = [
        handler
        for handler in logging.getLogger().handlers
        if isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, logging.FileHandler)
    ]
    assert len(console_handlers) == 1
