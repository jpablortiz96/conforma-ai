"""Audit persistence schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditRead(BaseModel):
    """Read model for top-level audit records."""

    id: UUID
    source_url: str
    source_type: str
    status: str
    compliance_score: int | None = None
    risk_index: str | None = None
    fine_exposure_eur: int | None = None
    created_at: datetime
    completed_at: datetime | None = None
    audit_metadata: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class AISystemRead(BaseModel):
    """Read model for persisted AI systems."""

    id: UUID
    audit_id: UUID
    name: str
    description: str
    source_files: list[str] | None = None
    risk_class: str | None = None
    primary_article: str | None = None
    reasoning: str | None = None
    deadline: str | None = None
    confidence: Decimal | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentRunRead(BaseModel):
    """Read model for agent execution traces."""

    id: UUID
    audit_id: UUID
    ai_system_id: UUID | None = None
    agent_name: str
    status: str
    input: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    model: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ArtifactRead(BaseModel):
    """Read model for generated artifacts."""

    id: UUID
    audit_id: UUID
    ai_system_id: UUID | None = None
    kind: str
    language: str | None = None
    storage_url: str | None = None
    content: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GapRead(BaseModel):
    """Read model for compliance gaps."""

    id: UUID
    audit_id: UUID
    ai_system_id: UUID | None = None
    category: str
    severity: str
    description: str
    remediation: str
    effort_days: int | None = None
    deadline: date | None = None

    model_config = ConfigDict(from_attributes=True)
