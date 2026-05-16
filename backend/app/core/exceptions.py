"""Custom application exceptions for Conforma-AI."""

from __future__ import annotations


class ConformaAIError(Exception):
    """Base exception for application-specific failures."""


class RepositoryCloneError(ConformaAIError):
    """Raised when a repository cannot be cloned for scanning."""


class ScannerExecutionError(ConformaAIError):
    """Raised when the scanner cannot complete a run."""


class ScannerValidationError(ConformaAIError):
    """Raised when scanner inputs or outputs are invalid."""
