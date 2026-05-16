"""FastAPI entry point for the Conforma-AI backend."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.gemini_client import GeminiClientError, call_pro_json
from app.core.logging import configure_logging
from app.knowledge.eu_ai_act_minimal import (
    CLASSIFIER_KB_SUMMARY,
    FALLBACK_CLASSIFICATION_RULES,
    deadline_for_classification,
)
from app.routers import agents_router
from app.schemas.agent import ClassifierRequest, ClassifierResponse, HealthResponse

logger = logging.getLogger(__name__)
settings = get_settings()


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
- Use the word "Section" instead of the section symbol.
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

    configure_logging()
    app = FastAPI(
        title="Conforma-AI API",
        version=settings.app_version,
        description="Local backend for the Conforma-AI multi-agent compliance demo.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(agents_router)

    @app.get("/", response_model=HealthResponse, tags=["health"])
    async def root() -> HealthResponse:
        """Return the operational health payload."""

        return HealthResponse(service=settings.app_name, version=settings.app_version)

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
