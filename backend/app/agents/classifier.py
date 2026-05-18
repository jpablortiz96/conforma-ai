"""Classifier agent implementation for D3."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from app.agents.base import BaseAgent
from app.core.config import get_settings
from app.core.exceptions import ClassifierExecutionError, ClassifierValidationError
from app.core.gemini_client import GeminiClientError, call_pro_json
from app.db.models import AISystem
from app.knowledge.eu_ai_act_kb import (
    FALLBACK_CLASSIFICATION_RULES,
    build_classifier_context,
    deadline_for_classification,
)
from app.schemas.agent import (
    ClassifierInput,
    ClassifierRequest,
    ClassifierResponse,
    normalize_deadline_iso_value,
)

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "prompts" / "classifier_system.md"

EMPLOYMENT_RECRUITMENT_TOKENS = (
    "cv ranking",
    "cv screening",
    "curriculum vitae",
    "resume scoring",
    "resume screening",
    "resume ranking",
    "resume screen",
    "candidate filtering",
    "candidate scoring",
    "candidate screening",
    "candidate suitability",
    "applicant scoring",
    "applicant screening",
    "employment screening",
    "recruitment",
    "recruiter",
    "job application",
    "job matching",
    "talent acquisition",
    "hiring",
)
CREDITWORTHINESS_TOKENS = ("credit score", "creditworthiness", "loan approval", "mortgage scoring")
INSURANCE_RISK_TOKENS = (
    "life insurance",
    "health insurance",
    "insurance premiums",
    "insurance pricing",
    "insurance risk pricing",
)
TUTORIAL_ONLY_TOKENS = (
    "tutorial",
    "sample project",
    "example project",
    "demo only",
    "educational",
    "for learning",
    "generic tutorial",
)
RECRUITMENT_DECISION_NEGATION_TOKENS = (
    "not used for recruitment decisions",
    "not for recruitment decisions",
    "not used in hiring decisions",
    "not for real hiring decisions",
    "for educational purposes only",
)
GENERATIVE_CONTENT_TOKENS = (
    "language model",
    "text generation",
    "text generator",
    "generation logic",
    "gpt",
    "synthetic text",
    "image generator",
    "video generator",
    "generative",
)
WEAK_GENERATIVE_TOKENS = ("llm",)
GENERATIVE_SUPPORT_TOKENS = ("generate", "generation", "inference", "model weights", "synthetic", "gpt")

ANNEX_I_PRODUCT_TOKENS = (
    "medical device",
    "medical devices",
    "regulated product",
    "product safety",
    "toy",
    "lift",
    "vehicle",
    "aviation",
)


def _normalize_text(text: str) -> str:
    """Normalize free text for fallback matching."""

    return " ".join(text.lower().replace("-", " ").split())


def _contains_any(normalized: str, tokens: tuple[str, ...]) -> bool:
    """Return True when any token is present in the normalized text."""

    return any(token in normalized for token in tokens)


def _is_employment_recruitment_use(normalized: str) -> bool:
    """Detect Annex III Section 4(a) recruitment and resume-screening uses."""

    return _contains_any(normalized, EMPLOYMENT_RECRUITMENT_TOKENS)


def _is_annex_i_product_embedded_use(normalized: str) -> bool:
    """Detect Annex I product-embedded safety-component uses."""

    return "safety component" in normalized and _contains_any(normalized, ANNEX_I_PRODUCT_TOKENS)


def _is_tutorial_only_recruitment_example(normalized: str) -> bool:
    """Avoid high-risk overrides when the text clearly says it is only a tutorial."""

    return _contains_any(normalized, TUTORIAL_ONLY_TOKENS) and _contains_any(
        normalized,
        RECRUITMENT_DECISION_NEGATION_TOKENS,
    )


def _is_generative_content_use(normalized: str) -> bool:
    """Detect generative systems without over-weighting repo names alone."""

    if _contains_any(normalized, GENERATIVE_CONTENT_TOKENS):
        return True
    return _contains_any(normalized, WEAK_GENERATIVE_TOKENS) and _contains_any(
        normalized,
        GENERATIVE_SUPPORT_TOKENS,
    )


def _force_high_risk_outcome(
    response: ClassifierResponse,
    *,
    primary_article: str,
    reasoning: str,
    triggers_article_50: bool,
    secondary_articles: list[str] | None = None,
) -> ClassifierResponse:
    """Apply a deterministic high-risk override with normalized deadlines."""

    response.risk_class = "HIGH_RISK"
    response.primary_article = primary_article
    response.triggers_article_50 = triggers_article_50
    response.secondary_articles = list(secondary_articles or [])
    deadline, deadline_iso = deadline_for_classification(
        "HIGH_RISK",
        triggers_article_50=triggers_article_50,
        primary_article=primary_article,
    )
    response.deadline = deadline
    response.deadline_iso = deadline_iso
    if response.confidence < 0.9:
        response.confidence = 0.9
    response.reasoning = reasoning.strip()
    return response


def _append_high_risk_deadline_note(response: ClassifierResponse) -> None:
    """Append the correct Omnibus deadline note for high-risk systems."""

    annex_i_deadline_note = "The Annex I product-embedded high-risk deadline is 2 August 2028."
    annex_iii_deadline_note = (
        "The Annex III high-risk deadline is 2 December 2027, postponed from 2 August 2026 "
        "by the Digital Omnibus deal of 7 May 2026."
    )
    is_annex_i_reference = response.primary_article == "Annex I" or response.primary_article.startswith("Annex I ")
    deadline_note = annex_i_deadline_note if is_annex_i_reference else annex_iii_deadline_note
    reasoning_lower = response.reasoning.lower()
    if is_annex_i_reference:
        already_mentions_deadline = "2 august 2028" in reasoning_lower
    else:
        already_mentions_deadline = "2 december 2027" in reasoning_lower

    if deadline_note not in response.reasoning and not already_mentions_deadline:
        response.reasoning = f"{response.reasoning.rstrip()} {deadline_note}"


def _ensure_article(
    response: ClassifierResponse,
    *,
    system_description: str,
) -> ClassifierResponse:
    """Sharpen Gemini output to the exact paragraph references required by the handoff."""

    normalized = _normalize_text(system_description)

    if response.risk_class == "UNACCEPTABLE":
        if "social" in normalized and "scoring" in normalized and any(
            token in normalized for token in ("municipality", "public authority", "government", "dutch municipality")
        ):
            response.primary_article = "Article 5(1)(c)"
        elif "real time" in normalized and any(
            token in normalized for token in ("police", "law enforcement", "public square", "publicly accessible", "biometric id")
        ):
            response.primary_article = "Article 5(1)(h)"
        response.secondary_articles = []
        response.triggers_article_50 = False
    elif _is_employment_recruitment_use(normalized) and not _is_tutorial_only_recruitment_example(normalized):
        triggers_article_50 = response.triggers_article_50 or "explanation" in normalized
        secondary_articles = list(response.secondary_articles)
        if triggers_article_50 and "Article 50(2)" not in secondary_articles:
            secondary_articles.append("Article 50(2)")
        response = _force_high_risk_outcome(
            response,
            primary_article="Annex III Section 4(a)",
            reasoning=(
                "Deterministic guardrail: the combined evidence describes resume, CV, applicant, or candidate "
                "screening for recruitment or hiring, which maps to Annex III Section 4(a)."
            ),
            triggers_article_50=triggers_article_50,
            secondary_articles=secondary_articles,
        )
    elif _is_annex_i_product_embedded_use(normalized):
        response = _force_high_risk_outcome(
            response,
            primary_article="Annex I",
            reasoning=(
                "Deterministic guardrail: the description places the AI system inside a regulated product safety "
                "component, so Annex I product-embedded high-risk obligations apply."
            ),
            triggers_article_50=False,
        )
    elif _contains_any(normalized, INSURANCE_RISK_TOKENS):
        response = _force_high_risk_outcome(
            response,
            primary_article="Annex III Section 5(c)",
            reasoning=(
                "Deterministic guardrail: life or health insurance risk assessment and pricing map to "
                "Annex III Section 5(c)."
            ),
            triggers_article_50=False,
        )
    elif _contains_any(normalized, CREDITWORTHINESS_TOKENS):
        response = _force_high_risk_outcome(
            response,
            primary_article="Annex III Section 5(b)",
            reasoning=(
                "Deterministic guardrail: creditworthiness, credit scoring, or loan-approval use maps to "
                "Annex III Section 5(b)."
            ),
            triggers_article_50=False,
        )
    elif _is_generative_content_use(normalized) and response.risk_class == "MINIMAL_RISK":
        response.risk_class = "LIMITED_RISK"
        response.primary_article = "Article 50(2)"
        response.secondary_articles = []
        response.triggers_article_50 = True
        response.confidence = max(response.confidence, 0.82)
        deadline, deadline_iso = deadline_for_classification(
            "LIMITED_RISK",
            triggers_article_50=True,
            primary_article=response.primary_article,
        )
        response.deadline = deadline
        response.deadline_iso = deadline_iso
        response.reasoning = (
            "Deterministic guardrail: the combined evidence describes a language model or other generative system "
            "that can produce synthetic text or related content, which triggers Article 50(2)."
        ).strip()
    elif response.risk_class == "HIGH_RISK":
        if any(token in normalized for token in ("facial recognition", "face recognition", "shoplifter", "supermarket", "retail")):
            response.primary_article = "Annex III Section 1"
        deadline, deadline_iso = deadline_for_classification(
            "HIGH_RISK",
            triggers_article_50=response.triggers_article_50,
            primary_article=response.primary_article,
        )
        response.deadline = deadline
        response.deadline_iso = deadline_iso
        _append_high_risk_deadline_note(response)
    elif response.risk_class == "LIMITED_RISK":
        if any(token in normalized for token in ("chatbot", "password reset", "customer service bot", "virtual assistant")):
            response.primary_article = "Article 50(1)"
        elif any(token in normalized for token in ("deep fake", "deepfake", "synthetic video", "face swap", "video generator")):
            response.primary_article = "Article 50(4)"
            if "Article 50(2)" not in response.secondary_articles:
                response.secondary_articles.append("Article 50(2)")
        elif any(token in normalized for token in ("ai generated", "synthetic text", "synthetic image", "image generator", "text generator")):
            response.primary_article = "Article 50(2)"
        elif any(token in normalized for token in ("emotion recognition", "biometric categorization", "biometric categorisation")):
            response.primary_article = "Article 50(3)"
        deadline, deadline_iso = deadline_for_classification(
            "LIMITED_RISK",
            triggers_article_50=True,
            primary_article=response.primary_article,
        )
        response.deadline = deadline
        response.deadline_iso = deadline_iso
        response.triggers_article_50 = True
    else:
        response.primary_article = "Not applicable"
        deadline, deadline_iso = deadline_for_classification(
            "MINIMAL_RISK",
            triggers_article_50=False,
            primary_article="Not applicable",
        )
        response.deadline = deadline
        response.deadline_iso = deadline_iso
        response.triggers_article_50 = False
        response.secondary_articles = []

    deduped: list[str] = []
    for item in response.secondary_articles:
        if item not in deduped:
            deduped.append(item)
    response.secondary_articles = deduped
    if response.risk_class == "HIGH_RISK":
        _append_high_risk_deadline_note(response)
    return response


def classify_with_fallback(system_description: str) -> ClassifierResponse:
    """Run the deterministic D3 fallback classifier."""

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
            response = ClassifierResponse(
                risk_class=rule.risk_class,
                primary_article=rule.primary_article,
                secondary_articles=list(rule.secondary_articles),
                reasoning=rule.reasoning,
                deadline=deadline,
                deadline_iso=deadline_iso,
                confidence=rule.confidence,
                triggers_article_50=rule.triggers_article_50,
                mode="fallback",
            )
            return _ensure_article(response, system_description=system_description)

    deadline, deadline_iso = deadline_for_classification(
        "MINIMAL_RISK",
        triggers_article_50=False,
        primary_article="Not applicable",
    )
    response = ClassifierResponse(
        risk_class="MINIMAL_RISK",
        primary_article="Not applicable",
        secondary_articles=[],
        reasoning=(
            "The description does not clearly map to a prohibited practice, an Annex III high-risk use case, "
            "an Annex I product-embedded safety component, or an Article 50 transparency trigger. The smallest "
            "solid classification is minimal risk, which carries no mandatory deadline under the Act."
        ),
        deadline=deadline,
        deadline_iso=deadline_iso,
        confidence=0.64,
        triggers_article_50=False,
        mode="fallback",
    )
    return _ensure_article(response, system_description=system_description)


def build_classifier_prompt(system_description: str, context_files: list[str]) -> str:
    """Build the full D3 classifier prompt."""

    context_lines = "\n".join(f"- {entry}" for entry in context_files) or "- None provided"
    kb_context = build_classifier_context()
    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    return (
        f"{prompt_template}\n\n"
        f"Knowledge base context:\n{kb_context}\n\n"
        f"AI system description:\n{system_description}\n\n"
        f"Context files and evidence:\n{context_lines}"
    )


async def classify_description(request: ClassifierRequest) -> ClassifierResponse:
    """Classify a free-form system description for the D1-compatible endpoint."""

    settings = get_settings()
    if not settings.gemini_api_key:
        return classify_with_fallback(request.system_description)

    try:
        payload = await call_pro_json(
            build_classifier_prompt(request.system_description, request.context_files),
            temperature=0.0,
        )
        payload["mode"] = "gemini"
        response = ClassifierResponse.model_validate(payload)
    except (GeminiClientError, ValidationError, TypeError, ValueError) as exc:
        logger.warning("Gemini classification failed, using fallback: %s", exc, exc_info=True)
        return classify_with_fallback(request.system_description)

    if response.risk_class == "MINIMAL_RISK" and response.primary_article.strip() == "":
        response.primary_article = "Not applicable"
    return _ensure_article(response, system_description=request.system_description)


class ClassifierAgent(BaseAgent):
    """Persisted classifier agent used inside the audit flow."""

    name = "classifier"
    model = "gemini-3.1-pro-preview"
    description = "Classify an AI system under the EU AI Act."

    async def run(self, input_data: dict[str, Any], audit_id: UUID) -> dict[str, Any]:
        """Execute the classifier against a persisted AI system row."""

        started_at = datetime.now(timezone.utc)
        try:
            validated = ClassifierInput.model_validate({**input_data, "audit_id": audit_id})
        except ValidationError as exc:
            raise ClassifierValidationError(str(exc)) from exc

        ai_system = await self.db.get(AISystem, validated.ai_system_id)
        if ai_system is None:
            raise ClassifierValidationError(
                f"AI system {validated.ai_system_id} does not exist for classification."
            )

        response = await classify_description(
            ClassifierRequest(
                system_description=validated.system_description,
                context_files=validated.context_files,
            )
        )

        try:
            response.deadline_iso = normalize_deadline_iso_value(response.deadline_iso)
            ai_system.risk_class = response.risk_class
            ai_system.primary_article = response.primary_article
            ai_system.secondary_articles = response.secondary_articles
            ai_system.reasoning = response.reasoning
            ai_system.deadline = response.deadline
            ai_system.deadline_iso = response.deadline_iso
            ai_system.confidence = response.confidence
            ai_system.triggers_article_50 = response.triggers_article_50
            self.db.add(ai_system)
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
                model=self.model if response.mode == "gemini" else "fallback-heuristics",
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
                logger.exception("Failed to persist classifier error for ai_system %s", validated.ai_system_id)
            raise ClassifierExecutionError(str(exc)) from exc
