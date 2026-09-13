"""Deterministic project-local artifact path resolution."""

from __future__ import annotations

from pathlib import Path


LOG_ARTIFACT = "canslim_analysis.log"
INTERMEDIATE_ARTIFACT = "intermediate_canslim.json"
ENRICHMENT_TEMPLATE_ARTIFACT = "enrichment_template.json"
ENRICHED_ARTIFACT = "enriched_canslim.json"
FINAL_REPORT_ARTIFACT = "final_canslim_report.json"


def resolve_output_directory(
    output_dir: Path | str | None = None,
    *,
    project_root: Path | str | None = None,
) -> Path:
    """Resolve the directory used for generated pipeline artifacts.

    Args:
        output_dir: Explicit output directory, if supplied.
        project_root: Project root used when no explicit directory is supplied.

    Returns:
        An absolute path to the selected output directory. No directory or file
        is created by this function.
    """

    root = Path(project_root) if project_root is not None else Path.cwd()
    selected = Path(output_dir) if output_dir is not None else root / "out"
    return selected.expanduser().resolve()


def resolve_artifact_path(
    filename: str,
    *,
    output_dir: Path | str | None = None,
    project_root: Path | str | None = None,
) -> Path:
    """Resolve one artifact beneath the selected output directory.

    Args:
        filename: Documented artifact filename.
        output_dir: Explicit output directory, if supplied.
        project_root: Project root used when no explicit directory is supplied.

    Returns:
        An absolute artifact path. No directory or file is created.
    """

    return resolve_output_directory(
        output_dir,
        project_root=project_root,
    ) / filename
