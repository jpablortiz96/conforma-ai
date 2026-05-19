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


class ClassifierExecutionError(ConformaAIError):
    """Raised when the classifier cannot complete a run."""


class ClassifierValidationError(ConformaAIError):
    """Raised when classifier inputs or outputs are invalid."""


class DocumentationExecutionError(ConformaAIError):
    """Raised when the Documentation Agent cannot complete a run."""


class DocumentationValidationError(ConformaAIError):
    """Raised when Documentation Agent inputs or outputs are invalid."""


class DisclosureExecutionError(ConformaAIError):
    """Raised when the Disclosure Agent cannot complete a run."""


class DisclosureValidationError(ConformaAIError):
    """Raised when Disclosure Agent inputs or outputs are invalid."""


class GapAuditorExecutionError(ConformaAIError):
    """Raised when the Gap Auditor cannot complete a run."""


class GapAuditorValidationError(ConformaAIError):
    """Raised when Gap Auditor inputs or outputs are invalid."""


class MonitorExecutionError(ConformaAIError):
    """Raised when the Monitor Agent cannot complete a run."""


class MonitorValidationError(ConformaAIError):
    """Raised when Monitor Agent inputs or outputs are invalid."""


class OrchestratorExecutionError(ConformaAIError):
    """Raised when the orchestrated audit pipeline cannot complete."""
