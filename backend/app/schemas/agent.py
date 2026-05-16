"""Agent request and response schemas."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator, model_validator


def sanitize_reference_text(value: str) -> str:
    """Normalize problematic section symbols into ASCII-safe wording."""

    return value.replace("Ã‚Â§", "Section ").replace("Â§", "Section ").replace("§", "Section ")


class HealthResponse(BaseModel):
    """Health payload returned by the root endpoint."""

    status: Literal["operational"] = "operational"
    service: str
    version: str


class ClassifierRequest(BaseModel):
    """Input for the D1 classifier endpoint."""

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


class ClassifierResponse(BaseModel):
    """Normalized classifier output for D1."""

    risk_class: Literal["UNACCEPTABLE", "HIGH_RISK", "LIMITED_RISK", "MINIMAL_RISK"]
    primary_article: str
    secondary_articles: list[str] = Field(default_factory=list)
    reasoning: str
    deadline: str
    deadline_iso: str | None = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    triggers_article_50: bool
    mode: Literal["gemini", "fallback"]

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
        deadline_iso = payload.get("deadline_iso")
        payload["deadline_iso"] = str(deadline_iso) if deadline_iso is not None else None
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

        normalized = "_".join(part for part in value.strip().lower().replace("-", "_").split("_") if part)
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
    mode: Literal["gemini", "fallback"]

    model_config = ConfigDict(from_attributes=True)
