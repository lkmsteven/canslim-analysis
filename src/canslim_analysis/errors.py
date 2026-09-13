"""Project-specific error types used across pipeline boundaries."""

from __future__ import annotations


class CanslimError(Exception):
    """Base class for expected CANSLIM pipeline errors."""


class ConfigurationError(CanslimError):
    """Raised when CLI values, paths, or configuration are invalid."""


class ArtifactNotFoundError(CanslimError):
    """Raised when a required predecessor artifact is absent."""


class SchemaValidationError(CanslimError):
    """Raised when a dataset violates the CANSLIM data contract."""


class ExternalDataError(CanslimError):
    """Raised when an external data source fails or returns invalid data."""


class ReportGenerationError(CanslimError):
    """Raised when final or PDF report generation fails."""
