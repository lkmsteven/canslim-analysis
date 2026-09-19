"""Ordered orchestration for the complete CANSLIM workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from canslim_analysis.pipeline.config import PipelineConfig
from canslim_analysis.pipeline.enrichment import (
    merge_enrichment_artifacts,
    prepare_enrichment_template,
)
from canslim_analysis.pipeline.quantitative import (
    QuantitativeProviders,
    QuantitativeRunResult,
    run_quantitative_analysis,
)
from canslim_analysis.pipeline.reporting import finalize_report
from canslim_analysis.reporting.pdf import render_pdf_report


@dataclass(frozen=True)
class WorkflowResult:
    """Artifact paths and completion state for one workflow run."""

    quantitative: QuantitativeRunResult
    template_path: Path | None
    enriched_path: Path | None
    final_path: Path | None
    pdf_path: Path | None
    stopped_for_findings: bool
    used_unverified_fallback: bool
    no_candidates: bool = False


def run_complete_workflow(
    config: PipelineConfig,
    providers: QuantitativeProviders,
    *,
    findings_path: Path | str | None = None,
    unverified_fallback: bool = False,
    output_dir: Path | str | None = None,
    project_root: Path | str | None = None,
) -> WorkflowResult:
    """Run quantitative, enrichment, final, and PDF stages in order.

    Args:
        config: Validated pipeline configuration.
        providers: Injected external-data providers.
        findings_path: Codex findings file, if qualitative evidence exists.
        unverified_fallback: Whether all missing qualitative checks may be false.
        output_dir: Optional generated-artifact directory.
        project_root: Root used to derive default paths.

    Returns:
        Paths produced before any stage completed or short-circuited.
    """

    quantitative = run_quantitative_analysis(
        config,
        providers,
        output_dir=output_dir,
        project_root=project_root,
    )

    if findings_path is None and not unverified_fallback:
        return WorkflowResult(
            quantitative=quantitative,
            template_path=None,
            enriched_path=None,
            final_path=None,
            pdf_path=None,
            stopped_for_findings=True,
            used_unverified_fallback=False,
            no_candidates=quantitative.passed_count == 0,
        )

    if quantitative.passed_count == 0 and not unverified_fallback:
        return WorkflowResult(
            quantitative=quantitative,
            template_path=None,
            enriched_path=None,
            final_path=None,
            pdf_path=None,
            stopped_for_findings=True,
            used_unverified_fallback=False,
            no_candidates=True,
        )

    if findings_path is None:
        template_path = prepare_enrichment_template(
            quantitative.output_path,
            output_dir=output_dir,
            project_root=project_root,
        )
        findings_source = template_path
        used_fallback = True
    else:
        template_path = None
        findings_source = Path(findings_path)
        used_fallback = False

    enriched_path = merge_enrichment_artifacts(
        quantitative.output_path,
        findings_source,
        output_dir=output_dir,
        project_root=project_root,
    )
    final_path = finalize_report(
        enriched_path,
        output_dir=output_dir,
        project_root=project_root,
    )
    pdf_path = render_pdf_report(
        final_path,
        output_dir=output_dir,
        project_root=project_root,
    )
    return WorkflowResult(
        quantitative=quantitative,
        template_path=template_path,
        enriched_path=enriched_path,
        final_path=final_path,
        pdf_path=pdf_path,
        stopped_for_findings=False,
        used_unverified_fallback=used_fallback,
        no_candidates=quantitative.passed_count == 0,
    )
