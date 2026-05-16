"""Artifact response schemas for Conforma-AI."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ArtifactSummary(BaseModel):
    """Public summary for a generated artifact."""

    artifact_id: UUID
    audit_id: UUID
    ai_system_id: UUID | None = None
    kind: str
    language: str | None = None
    file_name: str
    download_url: str
    created_at: datetime


class AuditArtifactsResponse(BaseModel):
    """Artifact listing for one audit."""

    audit_id: UUID
    artifacts: list[ArtifactSummary] = Field(default_factory=list)
