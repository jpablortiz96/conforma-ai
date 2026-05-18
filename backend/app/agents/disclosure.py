"""Disclosure Agent implementation for D4B."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from app.agents.base import BaseAgent
from app.core.config import get_settings
from app.core.exceptions import DisclosureExecutionError, DisclosureValidationError
from app.core.gemini_client import GeminiClientError, call_flash_json
from app.db.models import AISystem, Artifact, Audit
from app.knowledge import ARTICLE_50_REQUIREMENTS, REGULATORY_CONTEXT
from app.schemas.agent import DisclosureInput, DisclosureNotices, DisclosureResponse, sanitize_reference_text

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "prompts" / "disclosure_system.md"

ARTICLE_50_PLACEMENTS = {
    "Article 50(1)": [
        "Show the notice before the first user message and keep a visible AI badge in the chat header.",
        "Repeat the disclosure in onboarding, help text, or the first-turn system response.",
    ],
    "Article 50(2)": [
        "Display the notice next to generated output and keep a visible AI-generated label in the UI.",
        "Attach machine-readable metadata or watermarking such as C2PA-compatible markers where feasible.",
    ],
    "Article 50(3)": [
        "Present the disclosure before activation and keep accessible signage at the point of exposure.",
        "Include the notice in consent or privacy flows when personal data is processed.",
    ],
    "Article 50(4)": [
        "Overlay the disclosure directly on the synthetic media in a clear and distinguishable manner.",
        "Repeat the disclosure in the caption, player chrome, or asset details before sharing.",
    ],
}

FALLBACK_NOTICES = {
    "Article 50(1)": {
        "en": "You are interacting with an AI system, not a human operator.",
        "it": "Stai interagendo con un sistema di IA, non con un operatore umano.",
        "es": "Estás interactuando con un sistema de IA, no con una persona.",
        "fr": "Vous interagissez avec un système d’IA, et non avec une personne.",
        "de": "Sie interagieren mit einem KI-System und nicht mit einer menschlichen Person.",
    },
    "Article 50(2)": {
        "en": "This content was generated or transformed with AI and should be treated as synthetic output.",
        "it": "Questo contenuto è stato generato o trasformato con l’IA e deve essere trattato come output sintetico.",
        "es": "Este contenido fue generado o transformado con IA y debe tratarse como contenido sintético.",
        "fr": "Ce contenu a été généré ou modifié par une IA et doit être traité comme un contenu synthétique.",
        "de": "Dieser Inhalt wurde mit KI erzeugt oder verändert und sollte als synthetischer Inhalt behandelt werden.",
    },
    "Article 50(3)": {
        "en": "This service uses AI to analyze biometric or emotional signals during operation.",
        "it": "Questo servizio usa l’IA per analizzare segnali biometrici o emotivi durante l’uso.",
        "es": "Este servicio usa IA para analizar señales biométricas o emocionales durante su funcionamiento.",
        "fr": "Ce service utilise une IA pour analyser des signaux biométriques ou émotionnels pendant son fonctionnement.",
        "de": "Dieser Dienst nutzt KI, um während des Betriebs biometrische oder emotionale Signale zu analysieren.",
    },
    "Article 50(4)": {
        "en": "This media has been artificially generated or manipulated with AI.",
        "it": "Questo contenuto è stato generato o manipolato artificialmente con l’IA.",
        "es": "Este contenido ha sido generado o manipulado artificialmente con IA.",
        "fr": "Ce contenu a été généré ou manipulé artificiellement par une IA.",
        "de": "Dieses Medium wurde künstlich mit KI erzeugt oder manipuliert.",
    },
}


def _normalize_text(value: str) -> str:
    """Normalize free text for disclosure trigger detection."""

    return " ".join(value.lower().replace("-", " ").split())


def _resolve_article(input_data: DisclosureInput) -> str | None:
    """Resolve the applicable Article 50 subsection from classifier evidence."""

    evidence = _normalize_text(
        " ".join(
            [
                input_data.system_name,
                input_data.description,
                input_data.primary_article,
                *input_data.secondary_articles,
            ]
        )
    )
    explicit_articles = [input_data.primary_article, *input_data.secondary_articles]
    for article in explicit_articles:
        sanitized = sanitize_reference_text(article)
        if sanitized.startswith("Article 50("):
            return sanitized

    if any(token in evidence for token in ("deep fake", "deepfake", "synthetic video", "face swap")):
        return "Article 50(4)"
    if any(token in evidence for token in ("emotion recognition", "biometric categorization", "biometric categorisation")):
        return "Article 50(3)"
    if any(
        token in evidence
        for token in (
            "language model",
            "llm",
            "text generation",
            "text generator",
            "image generator",
            "video generator",
            "synthetic text",
            "synthetic image",
            "generative",
            "gpt",
        )
    ):
        return "Article 50(2)"
    if any(token in evidence for token in ("chatbot", "assistant", "customer service", "password reset", "interactive")):
        return "Article 50(1)"
    return None


def build_disclosure_prompt(request: DisclosureInput, *, article: str) -> str:
    """Build the Gemini prompt for multilingual disclosure generation."""

    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    article_requirements = next(
        (entry for entry in ARTICLE_50_REQUIREMENTS if entry["subsection"] == article),
        None,
    )
    payload = {
        "audit_id": str(request.audit_id),
        "ai_system_id": str(request.ai_system_id),
        "system_name": request.system_name,
        "description": request.description,
        "risk_class": request.risk_class,
        "article": article,
        "primary_article": request.primary_article,
        "secondary_articles": request.secondary_articles,
        "deadline": REGULATORY_CONTEXT["article_50_deadline"].isoformat(),
        "placement_guidance": article_requirements["placement_guidance"] if article_requirements else None,
        "examples": article_requirements["examples"] if article_requirements else [],
    }
    return (
        f"{prompt_template}\n\n"
        "Authoritative Article 50 context:\n"
        f"{json.dumps(article_requirements, ensure_ascii=False, indent=2)}\n\n"
        "Input payload:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def build_disclosure_fallback(request: DisclosureInput, *, article: str) -> DisclosureResponse:
    """Create deterministic multilingual Article 50 notices."""

    notices = DisclosureNotices.model_validate(FALLBACK_NOTICES[article])
    return DisclosureResponse(
        audit_id=request.audit_id,
        ai_system_id=request.ai_system_id,
        requires_disclosure=True,
        article=article,
        notices=notices,
        placement_recommendations=ARTICLE_50_PLACEMENTS[article],
        confidence=0.78,
        mode="fallback",
    )


class DisclosureAgent(BaseAgent):
    """Generate Article 50 disclosure notices and persist them as JSON artifacts."""

    name = "disclosure"
    model = "gemini-3-flash-preview"
    description = "Generate multilingual Article 50 transparency notices."

    async def run(self, input_data: dict[str, Any], audit_id: UUID) -> dict[str, Any]:
        """Execute the Disclosure Agent for one AI system."""

        started_at = datetime.now(timezone.utc)
        try:
            validated = DisclosureInput.model_validate({**input_data, "audit_id": audit_id})
        except ValidationError as exc:
            raise DisclosureValidationError(str(exc)) from exc

        audit = await self.db.get(Audit, audit_id)
        if audit is None:
            raise DisclosureValidationError(f"Audit {audit_id} does not exist.")

        ai_system = await self.db.get(AISystem, validated.ai_system_id)
        if ai_system is None:
            raise DisclosureValidationError(
                f"AI system {validated.ai_system_id} does not exist for disclosure generation."
            )
        if ai_system.audit_id != audit_id:
            raise DisclosureValidationError(
                f"AI system {validated.ai_system_id} does not belong to audit {audit_id}."
            )

        if not validated.triggers_article_50:
            response = DisclosureResponse(
                audit_id=audit_id,
                ai_system_id=validated.ai_system_id,
                requires_disclosure=False,
                article=None,
                notices=None,
                placement_recommendations=[],
                confidence=0.99,
                mode="fallback",
            )
            await self._persist_run(
                audit_id=audit_id,
                ai_system_id=validated.ai_system_id,
                status="completed",
                input_data=validated.model_dump(mode="json"),
                output=response.model_dump(mode="json"),
                tokens_in=self.estimate_tokens(validated.model_dump(mode="json")),
                tokens_out=self.estimate_tokens(response.model_dump(mode="json")),
                started_at=started_at,
                model="policy-not-required",
            )
            return response.model_dump(mode="json")

        article = _resolve_article(validated)
        if article is None:
            raise DisclosureValidationError(
                "Article 50 trigger is true, but no Article 50 subsection could be resolved from the system evidence."
            )

        settings = get_settings()
        if not settings.gemini_api_key:
            response = build_disclosure_fallback(validated, article=article)
        else:
            try:
                payload = await call_flash_json(
                    build_disclosure_prompt(validated, article=article),
                    temperature=0.1,
                )
                response = DisclosureResponse.model_validate(
                    {
                        "audit_id": audit_id,
                        "ai_system_id": validated.ai_system_id,
                        "requires_disclosure": True,
                        "article": payload.get("article", article),
                        "notices": payload.get("notices"),
                        "placement_recommendations": payload.get("placement_recommendations", []),
                        "confidence": payload.get("confidence", 0.0),
                        "mode": "gemini",
                    }
                )
            except (GeminiClientError, ValidationError, TypeError, ValueError) as exc:
                logger.warning("Disclosure Gemini call failed, using fallback: %s", exc, exc_info=True)
                response = build_disclosure_fallback(validated, article=article)

        try:
            artifact = Artifact(
                audit_id=audit_id,
                ai_system_id=validated.ai_system_id,
                kind="article_50_notice_json",
                language="multi",
                storage_url=None,
                content=json.dumps(response.model_dump(mode="json"), ensure_ascii=False),
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(artifact)
            await self.db.flush()
            await self._persist_run(
                audit_id=audit_id,
                ai_system_id=validated.ai_system_id,
                status="completed",
                input_data=validated.model_dump(mode="json"),
                output=response.model_dump(mode="json"),
                tokens_in=self.estimate_tokens(validated.model_dump(mode="json")),
                tokens_out=self.estimate_tokens(response.model_dump(mode="json")),
                started_at=started_at,
                model=self.model if response.mode == "gemini" else "fallback-article-50",
            )
            return response.model_dump(mode="json")
        except Exception as exc:
            await self.db.rollback()
            try:
                await self._persist_run(
                    audit_id=audit_id,
                    ai_system_id=validated.ai_system_id,
                    status="failed",
                    input_data=validated.model_dump(mode="json"),
                    output=None,
                    tokens_in=self.estimate_tokens(validated.model_dump(mode="json")),
                    tokens_out=0,
                    started_at=started_at,
                    error=str(exc),
                    model=self.model,
                )
            except Exception:
                logger.exception(
                    "Failed to persist disclosure error for ai_system %s",
                    validated.ai_system_id,
                )
            raise DisclosureExecutionError(str(exc)) from exc
