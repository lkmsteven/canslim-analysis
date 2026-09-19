"""Command-line interface for the CANSLIM analysis pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from time import sleep

from canslim_analysis.errors import (
    ArtifactNotFoundError,
    CanslimError,
    ConfigurationError,
    ExternalDataError,
    ReportGenerationError,
    SchemaValidationError,
)
from canslim_analysis.pipeline.config import PipelineConfig
from canslim_analysis.pipeline.quantitative import (
    QuantitativeProviders,
    run_quantitative_analysis,
)


COMMANDS = (
    "quantitative",
    "prepare-enrichment",
    "enrich",
    "finalize",
    "report",
    "run",
    "status",
    "validate",
)

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser.

    Returns:
        Parser configured with every supported pipeline command.
    """

    parser = argparse.ArgumentParser(
        prog="python -m canslim_analysis",
        description="Run and validate the CANSLIM analysis pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command")

    quantitative = subparsers.add_parser("quantitative")
    _add_quantitative_arguments(quantitative)
    prepare = subparsers.add_parser("prepare-enrichment")
    prepare.add_argument("--input")
    prepare.add_argument("--output-dir")
    enrich = subparsers.add_parser("enrich")
    enrich.add_argument("--input")
    enrich.add_argument("--findings", required=True)
    enrich.add_argument("--output-dir")
    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--input")
    finalize.add_argument("--output-dir")
    status = subparsers.add_parser("status")
    status.add_argument("--json", dest="json_output", action="store_true")
    status.add_argument("--output-dir")
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument(
        "--stage",
        choices=("quantitative", "enriched", "final"),
        required=True,
    )
    validate_parser.add_argument("--input")
    validate_parser.add_argument("--output-dir")
    report = subparsers.add_parser("report")
    report.add_argument("--input")
    report.add_argument("--output-dir")
    run_parser = subparsers.add_parser("run")
    _add_quantitative_arguments(run_parser)
    run_parser.add_argument("--findings")
    run_parser.add_argument("--unverified-fallback", action="store_true")

    for command in COMMANDS:
        if command not in {
            "quantitative",
            "prepare-enrichment",
            "enrich",
            "finalize",
            "status",
            "validate",
            "report",
            "run",
        }:
            subparsers.add_parser(command)

    return parser


def _add_quantitative_arguments(parser: argparse.ArgumentParser) -> None:
    """Add every operationally useful quantitative option."""

    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--timeout", type=float)
    parser.add_argument("--retries", type=int)
    parser.add_argument("--retry-delay", type=float)
    parser.add_argument("--min-eps-growth", type=float)
    parser.add_argument("--min-annual-eps-growth", type=float)
    parser.add_argument("--min-rs-rating", type=float)
    parser.add_argument("--min-volume-ratio", type=float)
    parser.add_argument("--min-volume-skew", type=float)
    parser.add_argument("--min-institutional-ownership", type=float)
    parser.add_argument("--near-high-threshold", type=float)
    parser.add_argument("--output-dir")


def _config_from_arguments(arguments: argparse.Namespace) -> PipelineConfig:
    """Convert CLI values into validated pipeline configuration."""

    return PipelineConfig(
        min_eps_growth=_option(arguments.min_eps_growth, 0.25),
        min_annual_eps_growth=_option(arguments.min_annual_eps_growth, 0.25),
        min_rs_rating=_option(arguments.min_rs_rating, 80.0),
        min_volume_ratio=_option(arguments.min_volume_ratio, 1.5),
        min_volume_skew=_option(arguments.min_volume_skew, 1.2),
        min_institutional_ownership=_option(
            arguments.min_institutional_ownership, 0.30
        ),
        near_high_threshold=_option(arguments.near_high_threshold, 0.10),
        market_lookback_days=200,
        min_history_days=250,
        max_workers=_option(arguments.workers, 3),
        universe_limit=arguments.limit,
        request_timeout=_option(arguments.timeout, 10.0),
        max_retries=_option(arguments.retries, 4),
        retry_delay=_option(arguments.retry_delay, 3.0),
    )


def _option[T](value: T | None, default: T) -> T:
    """Return an optional value or its documented default."""

    return default if value is None else value


def _default_quantitative_providers(
    config: PipelineConfig,
) -> QuantitativeProviders:
    """Build the default HTTP and market-data providers."""

    from canslim_analysis.pipeline.market_data import (
        fetch_market_history_yfinance,
        fetch_sp500_tickers,
        fetch_stock_yfinance,
    )

    return QuantitativeProviders(
        fetch_universe=lambda runtime_config: fetch_sp500_tickers(
            runtime_config,
            sleeper=sleep,
        ),
        fetch_market_history=fetch_market_history_yfinance,
        fetch_stock=lambda ticker: fetch_stock_yfinance(ticker, config),
    )


def _prepare_enrichment(arguments: argparse.Namespace) -> int:
    """Run qualitative template preparation."""

    from canslim_analysis.paths import INTERMEDIATE_ARTIFACT, resolve_artifact_path
    from canslim_analysis.pipeline.enrichment import prepare_enrichment_template

    input_path = (
        Path(arguments.input).expanduser().resolve()
        if arguments.input
        else resolve_artifact_path(
            INTERMEDIATE_ARTIFACT,
            output_dir=arguments.output_dir,
        )
    )
    output_path = prepare_enrichment_template(
        input_path,
        output_dir=arguments.output_dir,
    )
    print(f"Enrichment template saved to {output_path}")
    return 0


def _enrich(arguments: argparse.Namespace) -> int:
    """Validate findings and persist the enriched stage."""

    from canslim_analysis.paths import INTERMEDIATE_ARTIFACT, resolve_artifact_path
    from canslim_analysis.pipeline.enrichment import merge_enrichment_artifacts

    quantitative_path = (
        Path(arguments.input).expanduser().resolve()
        if arguments.input
        else resolve_artifact_path(
            INTERMEDIATE_ARTIFACT,
            output_dir=arguments.output_dir,
        )
    )
    findings_path = Path(arguments.findings).expanduser().resolve()
    output_path = merge_enrichment_artifacts(
        quantitative_path,
        findings_path,
        output_dir=arguments.output_dir,
    )
    print(f"Enriched analysis saved to {output_path}")
    return 0


def _finalize(arguments: argparse.Namespace) -> int:
    """Validate enriched input and persist final scores."""

    from canslim_analysis.paths import ENRICHED_ARTIFACT, resolve_artifact_path
    from canslim_analysis.pipeline.reporting import finalize_report

    input_path = (
        Path(arguments.input).expanduser().resolve()
        if arguments.input
        else resolve_artifact_path(
            ENRICHED_ARTIFACT,
            output_dir=arguments.output_dir,
        )
    )
    output_path = finalize_report(input_path, output_dir=arguments.output_dir)
    print(f"Final report saved to {output_path}")
    return 0


def _status(arguments: argparse.Namespace) -> int:
    """Classify and print the current pipeline state."""

    import json as json_module

    from canslim_analysis.pipeline.status import classify_workflow_state, next_command

    from canslim_analysis.paths import resolve_output_directory

    state = classify_workflow_state(resolve_output_directory(arguments.output_dir))
    if arguments.json_output:
        print(
            json_module.dumps(
                {
                    "state": state,
                    "next_command": next_command(state),
                },
                sort_keys=True,
            )
        )
    else:
        following = next_command(state)
        print(f"Workflow state: {state}")
        if following:
            print(f"Next command: {following}")
    return 0


def _validate(arguments: argparse.Namespace) -> int:
    """Validate one selected artifact without writing output."""

    from canslim_analysis.paths import (
        ENRICHED_ARTIFACT,
        FINAL_REPORT_ARTIFACT,
        INTERMEDIATE_ARTIFACT,
        resolve_artifact_path,
    )
    from canslim_analysis.pipeline.status import validate_artifact

    default_names = {
        "quantitative": INTERMEDIATE_ARTIFACT,
        "enriched": ENRICHED_ARTIFACT,
        "final": FINAL_REPORT_ARTIFACT,
    }
    path = (
        Path(arguments.input).expanduser().resolve()
        if arguments.input
        else resolve_artifact_path(
            default_names[arguments.stage],
            output_dir=arguments.output_dir,
        )
    )
    validate_artifact(path, arguments.stage)
    print(f"Valid {arguments.stage} artifact: {path}")
    return 0


def _report(arguments: argparse.Namespace) -> int:
    """Render an existing final report to PDF."""

    from canslim_analysis.paths import FINAL_REPORT_ARTIFACT, resolve_artifact_path
    from canslim_analysis.reporting.pdf import render_pdf_report

    input_path = (
        Path(arguments.input).expanduser().resolve()
        if arguments.input
        else resolve_artifact_path(
            FINAL_REPORT_ARTIFACT,
            output_dir=arguments.output_dir,
        )
    )
    output_path = render_pdf_report(input_path, output_dir=arguments.output_dir)
    print(f"PDF report saved to {output_path}")
    return 0


def _run(arguments: argparse.Namespace, providers: QuantitativeProviders | None) -> int:
    """Execute all workflow stages in dependency order."""

    from canslim_analysis.pipeline.workflow import run_complete_workflow

    config = _config_from_arguments(arguments)
    result = run_complete_workflow(
        config,
        providers or _default_quantitative_providers(config),
        findings_path=arguments.findings,
        unverified_fallback=arguments.unverified_fallback,
        output_dir=arguments.output_dir,
    )
    if result.stopped_for_findings:
        if result.no_candidates:
            print(
                "Quantitative analysis produced no candidates; qualitative "
                "enrichment stopped safely. Review thresholds/provider data, or "
                "use --unverified-fallback only for an explicitly conservative "
                "empty report."
            )
        else:
            print(
                "Quantitative analysis complete; provide --findings or use "
                "--unverified-fallback to continue qualitative enrichment."
            )
        return 0
    if result.used_unverified_fallback:
        print(
            "Warning: qualitative checks are unverified and were conservatively "
            "set to false."
        )
    if result.no_candidates:
        print(
            "Note: the quantitative screen selected no candidates; the report "
            "is intentionally empty."
        )
    print(f"CANSLIM workflow complete: {result.pdf_path}")
    return 0


def main(
    arguments: list[str] | None = None,
    *,
    providers: QuantitativeProviders | None = None,
) -> int:
    """Run the command-line interface.

    Returns:
        Process exit code.
    """

    parser = build_parser()
    parsed = parser.parse_args(arguments)

    if parsed.command is None:
        parser.print_help()
        return 0

    from canslim_analysis.logging_setup import configure_logging
    from canslim_analysis.paths import LOG_ARTIFACT, resolve_artifact_path

    configure_logging(
        resolve_artifact_path(LOG_ARTIFACT, output_dir=parsed.output_dir)
    )

    try:
        if parsed.command == "quantitative":
            config = _config_from_arguments(parsed)
            result = run_quantitative_analysis(
                config,
                providers or _default_quantitative_providers(config),
                output_dir=parsed.output_dir,
            )
            print(
                f"Quantitative analysis complete: {result.passed_count} candidates "
                f"saved to {result.output_path}"
            )
            return 0
        if parsed.command == "prepare-enrichment":
            return _prepare_enrichment(parsed)
        if parsed.command == "enrich":
            return _enrich(parsed)
        if parsed.command == "finalize":
            return _finalize(parsed)
        if parsed.command == "status":
            return _status(parsed)
        if parsed.command == "validate":
            return _validate(parsed)
        if parsed.command == "report":
            return _report(parsed)
        if parsed.command == "run":
            return _run(parsed, providers)
    except ConfigurationError as exc:
        return _fail(2, exc)
    except SchemaValidationError as exc:
        return _fail(3, exc)
    except ArtifactNotFoundError as exc:
        return _fail(4, exc)
    except ExternalDataError as exc:
        return _fail(5, exc)
    except ReportGenerationError as exc:
        return _fail(6, exc)
    except CanslimError as exc:
        return _fail(1, exc)
    except Exception as exc:
        logger.exception("Unexpected CLI error")
        print(f"Unexpected internal error: {exc}", file=sys.stderr)
        return 1

    parser.print_error(f"Command '{parsed.command}' is not implemented yet.")
    return 2


def _fail(exit_code: int, error: Exception) -> int:
    """Print one deliberate error and return its stable exit code."""

    print(f"error: {error}", file=sys.stderr)
    return exit_code
