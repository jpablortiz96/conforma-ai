"""FastAPI entry point for the Conforma-AI D1 backend baseline."""

from __future__ import annotations

import logging
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.config import get_settings
from app.core.gemini_client import GeminiClientError, call_pro_json
from app.knowledge.eu_ai_act_minimal import (
    CLASSIFIER_KB_SUMMARY,
    FALLBACK_CLASSIFICATION_RULES,
    RiskClass,
    deadline_for_classification,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class HealthResponse(BaseModel):
    """Health payload returned by the root endpoint."""

    status: Literal["operational"] = "operational"
    service: str = settings.app_name
    version: str = settings.app_version


class ClassifierRequest(BaseModel):
    """Input for the D1 Classifier endpoint."""

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
        risk_class = str(payload.get("risk_class", "")).strip().upper()
        payload["risk_class"] = risk_class

        secondary_articles = payload.get("secondary_articles", [])
        if isinstance(secondary_articles, str):
            secondary_articles = [secondary_articles] if secondary_articles.strip() else []
        payload["secondary_articles"] = list(secondary_articles or [])

        confidence = payload.get("confidence", 0.0)
        try:
            payload["confidence"] = max(0.0, min(1.0, float(confidence)))
        except (TypeError, ValueError):
            payload["confidence"] = 0.0

        payload["triggers_article_50"] = bool(payload.get("triggers_article_50", False))
        payload["mode"] = payload.get("mode", "gemini")

        deadline_iso = payload.get("deadline_iso")
        if deadline_iso is not None:
            payload["deadline_iso"] = str(deadline_iso)

        return payload


def build_classifier_prompt(request: ClassifierRequest) -> str:
    """Build the D1 prompt for Gemini classification."""

    context_lines = "\n".join(f"- {entry}" for entry in request.context_files) or "- None provided"
    return f"""
You are the Classifier Agent of Conforma-AI. Classify the described AI system under the EU AI Act.

Use only the following D1 knowledge:
{CLASSIFIER_KB_SUMMARY}

Rules:
- Respond with strict JSON only.
- Use one risk class: UNACCEPTABLE, HIGH_RISK, LIMITED_RISK, MINIMAL_RISK.
- If uncertain, choose the more conservative class and lower confidence.
- Mention the Digital Omnibus deal of 7 May 2026 when explaining Annex III deadlines.
- `primary_article` must name the most relevant Article or Annex paragraph when one exists.
- `secondary_articles` must be a JSON list.
- `deadline_iso` must be either YYYY-MM-DD or null.
- `confidence` must be between 0 and 1.
- `triggers_article_50` must be true only when Article 50 transparency applies.

Output schema:
{{
  "risk_class": "UNACCEPTABLE | HIGH_RISK | LIMITED_RISK | MINIMAL_RISK",
  "primary_article": "string",
  "secondary_articles": ["string"],
  "reasoning": "3-4 sentences",
  "deadline": "string",
  "deadline_iso": "YYYY-MM-DD or null",
  "confidence": 0.0,
  "triggers_article_50": true
}}

AI system description:
{request.system_description}

Context files:
{context_lines}
""".strip()


def _normalize_text(text: str) -> str:
    """Normalize free text for local fallback matching."""

    return " ".join(text.lower().replace("-", " ").split())


def classify_with_fallback(system_description: str) -> ClassifierResponse:
    """Run the deterministic D1 fallback classifier."""

    normalized = _normalize_text(system_description)

    for rule in FALLBACK_CLASSIFICATION_RULES:
        any_match = not rule.match_any or any(token in normalized for token in rule.match_any)
        all_match = not rule.match_all or all(token in normalized for token in rule.match_all)
        if any_match and all_match:
            deadline, deadline_iso = deadline_for_classification(
                rule.risk_class,
                triggers_article_50=rule.triggers_article_50,
                primary_article=rule.primary_article,
            )
            return ClassifierResponse(
                risk_class=rule.risk_class,
                primary_article=rule.primary_article,
                secondary_articles=list(rule.secondary_articles),
                reasoning=rule.reasoning,
                deadline=deadline,
                deadline_iso=deadline_iso.isoformat() if deadline_iso else None,
                confidence=rule.confidence,
                triggers_article_50=rule.triggers_article_50,
                mode="fallback",
            )

    deadline, deadline_iso = deadline_for_classification(
        "MINIMAL_RISK",
        triggers_article_50=False,
        primary_article="Not applicable",
    )
    return ClassifierResponse(
        risk_class="MINIMAL_RISK",
        primary_article="Not applicable",
        secondary_articles=[],
        reasoning=(
            "The description does not clearly map to a prohibited practice, Annex III "
            "high-risk use case, or Article 50 transparency trigger in the D1 ruleset. "
            "The smallest solid classification is minimal risk, which carries no mandatory "
            "deadline under the Act."
        ),
        deadline=deadline,
        deadline_iso=deadline_iso.isoformat() if deadline_iso else None,
        confidence=0.62,
        triggers_article_50=False,
        mode="fallback",
    )


async def classify_with_gemini(request: ClassifierRequest) -> ClassifierResponse:
    """Run the Gemini-backed classifier and validate the result."""

    payload = await call_pro_json(build_classifier_prompt(request), temperature=0.1)
    payload["mode"] = "gemini"
    response = ClassifierResponse.model_validate(payload)

    if response.risk_class == "MINIMAL_RISK" and response.primary_article.strip() == "":
        response.primary_article = "Not applicable"

    return response


def create_app() -> FastAPI:
    """Create the FastAPI application instance."""

    app = FastAPI(
        title="Conforma-AI API",
        version=settings.app_version,
        description="D1 local baseline for the Conforma-AI Classifier agent.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", response_model=HealthResponse, tags=["health"])
    async def root() -> HealthResponse:
        """Return the D1 operational health payload."""

        return HealthResponse()

    @app.post(
        "/api/v1/agents/classifier",
        response_model=ClassifierResponse,
        tags=["agents"],
    )
    async def classifier(request: ClassifierRequest) -> ClassifierResponse:
        """Classify a described AI system using Gemini or the local fallback."""

        if not request.system_description:
            raise HTTPException(status_code=400, detail="system_description is required.")

        if not settings.gemini_api_key:
            return classify_with_fallback(request.system_description)

        try:
            return await classify_with_gemini(request)
        except (GeminiClientError, ValueError, TypeError) as exc:
            logger.warning("Gemini classification failed, using fallback: %s", exc)
            return classify_with_fallback(request.system_description)

    return app


app = create_app()
