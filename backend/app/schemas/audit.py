"""Audit persistence and API schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator

from app.schemas.agent import (
    DisclosureResponse,
    GapAuditorGap,
    MonitorAlert,
    MonitorResponse,
    RiskClass,
    normalize_deadline_iso_value,
    sanitize_reference_text,
)
from app.schemas.artifact import ArtifactSummary


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
    secondary_articles: list[str] | None = None
    reasoning: str | None = None
    deadline: str | None = None
    deadline_iso: date | None = None
    confidence: Decimal | None = None
    triggers_article_50: bool | None = None
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


class AuditCreateRequest(BaseModel):
    """Public request payload for synchronous and orchestrated audit flows."""

    repo_url: AnyHttpUrl
    max_files_to_inspect: int = Field(default=200, ge=1, le=500)


class AuditSystemResult(BaseModel):
    """Combined scanner and classifier view returned by the audit console."""

    id: UUID
    name: str
    description: str
    source_files: list[str] = Field(default_factory=list)
    detection_signals: list[str] = Field(default_factory=list)
    risk_class: RiskClass
    primary_article: str
    secondary_articles: list[str] = Field(default_factory=list)
    reasoning: str
    deadline: str
    deadline_iso: date | None = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    triggers_article_50: bool

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: Any) -> Any:
        """Normalize classifier payloads before the audit response is assembled."""

        if not isinstance(value, dict):
            return value

        payload = dict(value)
        payload["primary_article"] = sanitize_reference_text(
            str(payload.get("primary_article", "")).strip()
        )
        payload["reasoning"] = sanitize_reference_text(str(payload.get("reasoning", "")).strip())
        payload["deadline"] = sanitize_reference_text(str(payload.get("deadline", "")).strip())
        payload["deadline_iso"] = normalize_deadline_iso_value(payload.get("deadline_iso"))

        secondary_articles = payload.get("secondary_articles", [])
        if isinstance(secondary_articles, str):
            secondary_articles = [secondary_articles] if secondary_articles.strip() else []
        payload["secondary_articles"] = [
            sanitize_reference_text(str(item).strip()) for item in list(secondary_articles or [])
        ]
        payload["detection_signals"] = [
            sanitize_reference_text(str(item).strip())
            for item in list(payload.get("detection_signals", []) or [])
            if str(item).strip()
        ]
        return payload


class AuditResponse(BaseModel):
    """Synchronous audit response for D3."""

    audit_id: UUID
    repo_url: str
    status: Literal["completed"]
    systems: list[AuditSystemResult] = Field(default_factory=list)
    portfolio_risk_index: int = Field(..., ge=0, le=100)
    summary: str

    @model_validator(mode="before")
    @classmethod
    def normalize_audit_response(cls, value: Any) -> Any:
        """Sanitize the top-level audit summary."""

        if not isinstance(value, dict):
            return value
        payload = dict(value)
        payload["summary"] = sanitize_reference_text(str(payload.get("summary", "")).strip())
        return payload


class CompliancePackResponse(BaseModel):
    """Response returned by the D4B compliance-pack endpoint."""

    audit_id: UUID
    compliance_score: int = Field(..., ge=0, le=100)
    estimated_fine_exposure_eur: int = Field(..., ge=0)
    time_to_compliant_days: int = Field(..., ge=0)
    systems_count: int = Field(..., ge=0)
    high_risk_count: int = Field(..., ge=0)
    article_50_count: int = Field(..., ge=0)
    gaps: list[GapAuditorGap] = Field(default_factory=list)
    disclosures: list[DisclosureResponse] = Field(default_factory=list)
    priority_actions: list[str] = Field(default_factory=list)
    summary: str

    @model_validator(mode="before")
    @classmethod
    def normalize_compliance_pack(cls, value: Any) -> Any:
        """Sanitize pack summary and actions for API output."""

        if not isinstance(value, dict):
            return value
        payload = dict(value)
        payload["summary"] = sanitize_reference_text(str(payload.get("summary", "")).strip())
        payload["priority_actions"] = [
            sanitize_reference_text(" ".join(str(item).strip().split()))
            for item in list(payload.get("priority_actions", []) or [])
            if str(item).strip()
        ]
        return payload


class OrchestratedAuditStartResponse(BaseModel):
    """Immediate response returned when an orchestrated audit starts."""

    audit_id: UUID
    repo_url: str
    status: Literal["running"]
    stream_url: str


class AuditStreamEvent(BaseModel):
    """Server-sent event payload emitted by the orchestrator."""

    audit_id: UUID
    agent: str
    status: Literal["started", "completed", "failed"]
    message: str
    timestamp: datetime
    payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_event_payload(cls, value: Any) -> Any:
        """Sanitize event text for SSE consumers."""

        if not isinstance(value, dict):
            return value
        payload = dict(value)
        payload["message"] = sanitize_reference_text(str(payload.get("message", "")).strip())
        return payload


class ExecutiveBusinessImpact(BaseModel):
    """Board-facing business impact snapshot."""

    estimated_fine_exposure_eur: int = Field(..., ge=0)
    time_to_compliant_days: int = Field(..., ge=0)
    systems_at_risk: int = Field(..., ge=0)
    critical_actions_count: int = Field(..., ge=0)


class RegulatoryTimelineEntry(BaseModel):
    """One dated compliance milestone in the executive summary."""

    date: str
    label: str
    affected_systems: list[str] = Field(default_factory=list)


class ExecutiveSummaryResponse(BaseModel):
    """Board-ready executive summary for one audit."""

    audit_id: UUID
    board_summary: str
    business_impact: ExecutiveBusinessImpact
    regulatory_timeline: list[RegulatoryTimelineEntry] = Field(default_factory=list)
    top_5_actions: list[str] = Field(default_factory=list)
    investor_style_one_liner: str
    readiness_level: Literal["LOW", "MEDIUM", "HIGH", "ENTERPRISE_READY"]

    @model_validator(mode="before")
    @classmethod
    def normalize_executive_summary(cls, value: Any) -> Any:
        """Sanitize executive-summary text fields."""

        if not isinstance(value, dict):
            return value
        payload = dict(value)
        for field_name in ("board_summary", "investor_style_one_liner"):
            payload[field_name] = sanitize_reference_text(str(payload.get(field_name, "")).strip())
        payload["top_5_actions"] = [
            sanitize_reference_text(" ".join(str(item).strip().split()))
            for item in list(payload.get("top_5_actions", []) or [])
            if str(item).strip()
        ]
        return payload


class EvidenceVaultGap(BaseModel):
    """Persisted compliance-gap record attached to one system."""

    category: str
    severity: str
    description: str
    remediation: str
    deadline: date | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_evidence_gap(cls, value: Any) -> Any:
        """Sanitize evidence-vault gap text."""

        if not isinstance(value, dict):
            return value
        payload = dict(value)
        payload["description"] = sanitize_reference_text(str(payload.get("description", "")).strip())
        payload["remediation"] = sanitize_reference_text(str(payload.get("remediation", "")).strip())
        payload["deadline"] = normalize_deadline_iso_value(payload.get("deadline"))
        return payload


class EvidenceVaultAgentRun(BaseModel):
    """Compact trace record shown in the evidence vault."""

    agent_name: str
    status: str
    model: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None
    output: dict[str, Any] | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_agent_run(cls, value: Any) -> Any:
        """Sanitize agent-run strings where needed."""

        if not isinstance(value, dict):
            return value
        payload = dict(value)
        if payload.get("error"):
            payload["error"] = sanitize_reference_text(str(payload["error"]).strip())
        return payload


class EvidenceVaultSystem(BaseModel):
    """One system-centric evidence bundle for defensible review."""

    id: UUID
    name: str
    description: str
    source_files: list[str] = Field(default_factory=list)
    detection_signals: list[str] = Field(default_factory=list)
    risk_class: str | None = None
    primary_article: str | None = None
    secondary_articles: list[str] = Field(default_factory=list)
    reasoning: str | None = None
    deadline: str | None = None
    deadline_iso: date | None = None
    confidence: float | None = None
    triggers_article_50: bool = False
    artifacts: list[ArtifactSummary] = Field(default_factory=list)
    disclosures: list[DisclosureResponse] = Field(default_factory=list)
    gaps: list[EvidenceVaultGap] = Field(default_factory=list)
    agent_runs: list[EvidenceVaultAgentRun] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_evidence_system(cls, value: Any) -> Any:
        """Sanitize evidence-vault system fields."""

        if not isinstance(value, dict):
            return value
        payload = dict(value)
        for field_name in ("description", "primary_article", "reasoning", "deadline"):
            raw_value = payload.get(field_name)
            payload[field_name] = (
                sanitize_reference_text(str(raw_value).strip()) if raw_value is not None else None
            )
        payload["secondary_articles"] = [
            sanitize_reference_text(str(item).strip())
            for item in list(payload.get("secondary_articles", []) or [])
            if str(item).strip()
        ]
        payload["detection_signals"] = [
            sanitize_reference_text(str(item).strip())
            for item in list(payload.get("detection_signals", []) or [])
            if str(item).strip()
        ]
        payload["deadline_iso"] = normalize_deadline_iso_value(payload.get("deadline_iso"))
        return payload


class EvidenceVaultResponse(BaseModel):
    """Evidence bundle returned for one audit."""

    audit_id: UUID
    repo_url: str
    systems: list[EvidenceVaultSystem] = Field(default_factory=list)
    audit_level_runs: list[EvidenceVaultAgentRun] = Field(default_factory=list)
    monitor_alerts: list[MonitorAlert] = Field(default_factory=list)
    summary: str

    @model_validator(mode="before")
    @classmethod
    def normalize_evidence_vault(cls, value: Any) -> Any:
        """Sanitize evidence-vault summary text."""

        if not isinstance(value, dict):
            return value
        payload = dict(value)
        payload["summary"] = sanitize_reference_text(str(payload.get("summary", "")).strip())
        return payload


class OrchestratedAuditCompletedResponse(BaseModel):
    """Full D5 orchestration snapshot used in the SSE completion payload."""

    audit_id: UUID
    repo_url: str
    status: Literal["completed"]
    systems: list[AuditSystemResult] = Field(default_factory=list)
    portfolio_risk_index: int = Field(..., ge=0, le=100)
    summary: str
    compliance_pack: CompliancePackResponse
    monitor: MonitorResponse
    executive_summary: ExecutiveSummaryResponse
    evidence_vault: EvidenceVaultResponse


class DemoHighRiskSystemResponse(BaseModel):
    """Response returned by the D4A demo helper."""

    audit_id: UUID
    ai_system_id: UUID
