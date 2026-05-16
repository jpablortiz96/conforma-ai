"""Agent request and response schemas."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.artifact import ArtifactSummary

RiskClass = Literal["UNACCEPTABLE", "HIGH_RISK", "LIMITED_RISK", "MINIMAL_RISK"]
ResponseMode = Literal["gemini", "fallback"]


def sanitize_reference_text(value: str) -> str:
    """Normalize problematic section symbols into ASCII-safe wording."""

    return (
        value.replace("Ãƒâ€šÃ‚Â§", "Section ")
        .replace("Ã‚Â§", "Section ")
        .replace("Â§", "Section ")
        .replace("§", "Section ")
    )


class HealthResponse(BaseModel):
    """Health payload returned by the root endpoint."""

    status: Literal["operational"] = "operational"
    service: str
    version: str


class ClassifierRequest(BaseModel):
    """Public input for the D1-compatible classifier endpoint."""

    system_description: str = Field(
        ...,
        min_length=4,
        max_length=4000,
        description="Natural-language description of the AI system to classify.",
    )
    context_files: list[str] = Field(
        default_factory=list,
        description="Optional file paths or snippets for future expansion.",
    )

    @field_validator("system_description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        """Strip and validate the incoming description."""

        text = value.strip()
        if len(text) < 4:
            raise ValueError("system_description must contain at least 4 characters.")
        return text


class ClassifierInput(BaseModel):
    """Validated internal input for the classifier agent."""

    audit_id: UUID
    ai_system_id: UUID
    system_description: str = Field(..., min_length=4, max_length=4000)
    context_files: list[str] = Field(default_factory=list)

    @field_validator("system_description")
    @classmethod
    def normalize_internal_description(cls, value: str) -> str:
        """Normalize internal descriptions before classification."""

        return " ".join(value.strip().split())


class ClassifierResponse(BaseModel):
    """Normalized classifier output for D1 and D3."""

    risk_class: RiskClass
    primary_article: str
    secondary_articles: list[str] = Field(default_factory=list)
    reasoning: str
    deadline: str
    deadline_iso: date | None = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    triggers_article_50: bool
    mode: ResponseMode

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: Any) -> Any:
        """Coerce flexible Gemini payloads into the strict response contract."""

        if not isinstance(value, dict):
            raise TypeError("Classifier response must be a JSON object.")

        payload = dict(value)
        payload["risk_class"] = str(payload.get("risk_class", "")).strip().upper()
        payload["primary_article"] = sanitize_reference_text(
            str(payload.get("primary_article", "")).strip()
        )

        secondary_articles = payload.get("secondary_articles", [])
        if isinstance(secondary_articles, str):
            secondary_articles = [secondary_articles] if secondary_articles.strip() else []
        payload["secondary_articles"] = [
            sanitize_reference_text(str(item).strip()) for item in list(secondary_articles or [])
        ]
        payload["reasoning"] = sanitize_reference_text(str(payload.get("reasoning", "")).strip())
        payload["deadline"] = sanitize_reference_text(str(payload.get("deadline", "")).strip())

        try:
            payload["confidence"] = max(0.0, min(1.0, float(payload.get("confidence", 0.0))))
        except (TypeError, ValueError):
            payload["confidence"] = 0.0

        payload["triggers_article_50"] = bool(payload.get("triggers_article_50", False))
        payload["mode"] = payload.get("mode", "gemini")
        return payload


class ScannerRequest(BaseModel):
    """Public request payload for the scanner endpoint."""

    repo_url: AnyHttpUrl
    max_files_to_inspect: int = Field(default=200, ge=1, le=500)


class ScannerInput(BaseModel):
    """Validated internal input for the scanner agent."""

    audit_id: UUID
    repo_path: str | None = None
    repo_url: str
    max_files_to_inspect: int = Field(default=200, ge=1, le=500)

    @field_validator("repo_url")
    @classmethod
    def normalize_repo_url(cls, value: str) -> str:
        """Normalize whitespace and strip trailing slashes from repository URLs."""

        return value.strip().rstrip("/")


class AISystemCandidate(BaseModel):
    """Scanner-discovered AI system candidate before persistence."""

    name: str = Field(..., min_length=3, max_length=120)
    description: str = Field(..., min_length=20, max_length=2000)
    source_files: list[str] = Field(default_factory=list)
    detection_signals: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        """Normalize AI system names into a compact identifier."""

        normalized = "_".join(
            part for part in value.strip().lower().replace("-", "_").split("_") if part
        )
        return normalized or "ai_system_candidate"

    @field_validator("source_files", "detection_signals")
    @classmethod
    def normalize_string_lists(cls, value: list[str]) -> list[str]:
        """Strip empty items and keep stable ordering."""

        deduped: list[str] = []
        seen: set[str] = set()
        for item in value:
            cleaned = str(item).strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                deduped.append(cleaned)
        return deduped


class ScannerGeminiOutput(BaseModel):
    """Strict scanner output returned by Gemini or fallback heuristics."""

    ai_systems_found: list[AISystemCandidate] = Field(default_factory=list)
    summary: str = Field(..., min_length=10, max_length=5000)


class ScannerResponseSystem(AISystemCandidate):
    """Scanner-discovered AI system candidate after persistence."""

    id: UUID


class ScannerOutput(BaseModel):
    """Public scanner response returned by the API."""

    audit_id: UUID
    repo_url: str
    files_inspected: int
    ai_systems_found: list[ScannerResponseSystem] = Field(default_factory=list)
    summary: str
    mode: ResponseMode

    model_config = ConfigDict(from_attributes=True)


class DocumentationRequest(BaseModel):
    """Public request payload for the Documentation Agent."""

    audit_id: UUID
    ai_system_id: UUID
    system_description: str = Field(..., min_length=8, max_length=8000)
    risk_class: RiskClass
    primary_article: str = Field(..., min_length=4, max_length=255)
    source_code_snippets: list[str] = Field(default_factory=list)
    repo_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("system_description", "primary_article")
    @classmethod
    def normalize_documentation_strings(cls, value: str) -> str:
        """Normalize incoming Documentation Agent text fields."""

        return sanitize_reference_text(" ".join(value.strip().split()))

    @field_validator("source_code_snippets")
    @classmethod
    def normalize_source_snippets(cls, value: list[str]) -> list[str]:
        """Drop blank snippets while preserving ordering."""

        normalized: list[str] = []
        for item in value:
            cleaned = " ".join(str(item).strip().split())
            if cleaned:
                normalized.append(cleaned)
        return normalized


class DocumentationInput(DocumentationRequest):
    """Validated internal Documentation Agent input."""


class AnnexIVDocument(BaseModel):
    """Structured Annex IV content generated for a high-risk AI system."""

    system_name: str = Field(..., min_length=3, max_length=255)
    section_1_general_description: str = Field(..., min_length=20)
    section_2_intended_purpose: str = Field(..., min_length=20)
    section_3_human_oversight_measures: str = Field(..., min_length=20)
    section_4_input_data_specs: str = Field(..., min_length=20)
    section_5_design_specifications: str = Field(..., min_length=20)
    section_6_risk_management_system: str = Field(..., min_length=20)
    section_7_validation_testing: str = Field(..., min_length=20)
    section_8_performance_metrics: str = Field(..., min_length=20)
    section_9_post_market_monitoring: str = Field(..., min_length=20)
    gaps_identified: list[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def normalize_document_payload(cls, value: Any) -> Any:
        """Normalize free-form Gemini output into a strict Annex IV document."""

        if not isinstance(value, dict):
            raise TypeError("Annex IV document must be a JSON object.")

        payload = dict(value)
        string_fields = [
            "system_name",
            "section_1_general_description",
            "section_2_intended_purpose",
            "section_3_human_oversight_measures",
            "section_4_input_data_specs",
            "section_5_design_specifications",
            "section_6_risk_management_system",
            "section_7_validation_testing",
            "section_8_performance_metrics",
            "section_9_post_market_monitoring",
        ]
        for field_name in string_fields:
            payload[field_name] = sanitize_reference_text(
                " ".join(str(payload.get(field_name, "")).strip().split())
            )

        gaps_identified = payload.get("gaps_identified", [])
        if isinstance(gaps_identified, str):
            gaps_identified = [gaps_identified] if gaps_identified.strip() else []
        payload["gaps_identified"] = [
            sanitize_reference_text(" ".join(str(item).strip().split()))
            for item in list(gaps_identified or [])
            if str(item).strip()
        ]

        try:
            payload["confidence"] = max(0.0, min(1.0, float(payload.get("confidence", 0.0))))
        except (TypeError, ValueError):
            payload["confidence"] = 0.0

        return payload


class DocumentationResponse(BaseModel):
    """Public response for Documentation Agent runs."""

    audit_id: UUID
    ai_system_id: UUID
    required: bool
    status: Literal["generated", "not_required"]
    message: str
    mode: ResponseMode | None = None
    artifact: ArtifactSummary | None = None
    system_name: str | None = None
    section_1_general_description: str | None = None
    section_2_intended_purpose: str | None = None
    section_3_human_oversight_measures: str | None = None
    section_4_input_data_specs: str | None = None
    section_5_design_specifications: str | None = None
    section_6_risk_management_system: str | None = None
    section_7_validation_testing: str | None = None
    section_8_performance_metrics: str | None = None
    section_9_post_market_monitoring: str | None = None
    gaps_identified: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class DemoHighRiskSystemResponse(BaseModel):
    """Response returned by the D4A demo helper."""

    audit_id: UUID
    ai_system_id: UUID
