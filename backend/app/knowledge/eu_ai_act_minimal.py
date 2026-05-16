"""Minimal EU AI Act knowledge used by the D1 classifier baseline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

RiskClass = Literal["UNACCEPTABLE", "HIGH_RISK", "LIMITED_RISK", "MINIMAL_RISK"]

REGULATORY_CONTEXT = {
    "omnibus_deal_date": "2026-05-07",
    "unacceptable_enforceable_since": date(2025, 2, 2),
    "article_50_deadline": date(2026, 12, 2),
    "high_risk_annex_iii_deadline": date(2027, 12, 2),
    "high_risk_annex_i_deadline": date(2028, 8, 2),
    "omnibus_note": (
        "The Digital Omnibus deal of 7 May 2026 postponed Annex III high-risk "
        "deadlines from 2 August 2026 to 2 December 2027 while Article 50 "
        "transparency obligations remain due on 2 December 2026."
    ),
}


@dataclass(frozen=True, slots=True)
class ClassificationRule:
    """Deterministic local fallback rule for D1 classification."""

    name: str
    risk_class: RiskClass
    primary_article: str
    secondary_articles: tuple[str, ...]
    confidence: float
    triggers_article_50: bool
    reasoning: str
    match_any: tuple[str, ...] = ()
    match_all: tuple[str, ...] = ()


FALLBACK_CLASSIFICATION_RULES: tuple[ClassificationRule, ...] = (
    ClassificationRule(
        name="public_social_scoring",
        risk_class="UNACCEPTABLE",
        primary_article="Article 5(1)(c)",
        secondary_articles=(),
        confidence=0.97,
        triggers_article_50=False,
        reasoning=(
            "This system maps to social scoring by a public authority, which is a "
            "prohibited practice under Article 5(1)(c). Prohibited uses were already "
            "enforceable from 2 February 2025, so the issue is immediate rather than "
            "a future compliance milestone."
        ),
        match_all=("social", "scoring"),
        match_any=("municipality", "public authority", "government"),
    ),
    ClassificationRule(
        name="law_enforcement_public_biometric",
        risk_class="UNACCEPTABLE",
        primary_article="Article 5(1)(h)",
        secondary_articles=(),
        confidence=0.95,
        triggers_article_50=False,
        reasoning=(
            "Real-time remote biometric identification in publicly accessible spaces "
            "for law enforcement is prohibited under Article 5(1)(h), subject only to "
            "narrow exceptions. Because the described use is framed around live public "
            "biometric identification, the conservative classification is unacceptable risk."
        ),
        match_all=("real time",),
        match_any=("law enforcement", "police", "public square", "publicly accessible"),
    ),
    ClassificationRule(
        name="employment_recruitment",
        risk_class="HIGH_RISK",
        primary_article="Annex III §4(a)",
        secondary_articles=(),
        confidence=0.93,
        triggers_article_50=False,
        reasoning=(
            "CV ranking and candidate filtering in recruitment fall under Annex III "
            "§4(a) on employment and access to self-employment. The applicable Annex III "
            "deadline is 2 December 2027, postponed from 2 August 2026 by the Digital "
            "Omnibus deal of 7 May 2026."
        ),
        match_any=(
            "cv ranking",
            "resume scoring",
            "recruitment",
            "candidate filtering",
            "job application",
            "hiring",
        ),
    ),
    ClassificationRule(
        name="creditworthiness",
        risk_class="HIGH_RISK",
        primary_article="Annex III §5(b)",
        secondary_articles=(),
        confidence=0.91,
        triggers_article_50=False,
        reasoning=(
            "Creditworthiness and credit scoring are listed in Annex III §5(b) as "
            "high-risk systems affecting access to essential private services. The "
            "Annex III deadline is 2 December 2027 after the 7 May 2026 Omnibus extension."
        ),
        match_any=("credit score", "creditworthiness", "loan approval", "mortgage scoring"),
    ),
    ClassificationRule(
        name="retail_biometric_security",
        risk_class="HIGH_RISK",
        primary_article="Annex III §1",
        secondary_articles=(),
        confidence=0.82,
        triggers_article_50=False,
        reasoning=(
            "Facial recognition used to identify suspected shoplifters is a biometric "
            "identification use case that fits Annex III §1. Based on the description "
            "it is not clearly the prohibited law-enforcement scenario of Article 5(1)(h), "
            "so the conservative D1 classification is high-risk."
        ),
        match_any=("facial recognition", "face recognition", "shoplifter", "biometric"),
        match_all=("real time",),
    ),
    ClassificationRule(
        name="chatbot_direct_interaction",
        risk_class="LIMITED_RISK",
        primary_article="Article 50(1)",
        secondary_articles=(),
        confidence=0.9,
        triggers_article_50=True,
        reasoning=(
            "A password reset chatbot is an AI system intended to interact directly with "
            "natural persons, which triggers the Article 50(1) transparency obligation. "
            "That obligation remains due on 2 December 2026 under the Omnibus-adjusted timeline."
        ),
        match_any=("chatbot", "virtual assistant", "password reset", "customer service bot"),
    ),
    ClassificationRule(
        name="generated_synthetic_content",
        risk_class="LIMITED_RISK",
        primary_article="Article 50(4)",
        secondary_articles=("Article 50(2)",),
        confidence=0.86,
        triggers_article_50=True,
        reasoning=(
            "Synthetic or deep fake content triggers Article 50 transparency duties. "
            "Deployers must disclose that the content has been artificially generated or "
            "manipulated, and providers must support detectable machine-readable marking."
        ),
        match_any=("deep fake", "deepfake", "synthetic video", "synthetic image", "ai-generated"),
    ),
    ClassificationRule(
        name="emotion_or_biometric_categorisation",
        risk_class="LIMITED_RISK",
        primary_article="Article 50(3)",
        secondary_articles=(),
        confidence=0.8,
        triggers_article_50=True,
        reasoning=(
            "Emotion recognition and biometric categorisation systems trigger Article 50(3) "
            "transparency duties toward exposed natural persons. The deployer must provide "
            "clear notice and process personal data consistently with GDPR."
        ),
        match_any=("emotion recognition", "biometric categorization", "biometric categorisation"),
    ),
    ClassificationRule(
        name="spam_filter",
        risk_class="MINIMAL_RISK",
        primary_article="Not applicable",
        secondary_articles=(),
        confidence=0.96,
        triggers_article_50=False,
        reasoning=(
            "An email spam filter is a standard minimal-risk AI use case and is one of the "
            "examples explicitly treated as outside the mandatory obligation tiers. No specific "
            "EU AI Act compliance deadline applies beyond voluntary good practice."
        ),
        match_any=("spam filter", "spam classifier", "email spam"),
    ),
)

CLASSIFIER_KB_SUMMARY = """
Conforma-AI D1 minimal EU AI Act knowledge base:
- UNACCEPTABLE: Article 5 prohibited practices, already enforceable since 2 February 2025.
- HIGH_RISK: Article 6 plus Annex III stand-alone use cases. Annex III deadline is 2 December 2027 after the Digital Omnibus deal of 7 May 2026.
- LIMITED_RISK: Article 50 transparency obligations. Deadline is 2 December 2026.
- MINIMAL_RISK: no mandatory obligation tier under the Act.

Important examples:
- Recruitment, CV ranking, resume scoring -> Annex III §4(a)
- Creditworthiness scoring -> Annex III §5(b)
- Biometric identification and categorization -> Annex III §1
- Chatbots interacting with people -> Article 50(1)
- Synthetic/deep fake content -> Article 50(2)/(4)
- Spam filters -> minimal risk
""".strip()


def deadline_for_classification(
    risk_class: RiskClass,
    *,
    triggers_article_50: bool,
    primary_article: str,
) -> tuple[str, date | None]:
    """Return the human-readable deadline and machine-readable ISO date."""

    if risk_class == "UNACCEPTABLE":
        deadline = "Already enforceable since 2 February 2025."
        return deadline, REGULATORY_CONTEXT["unacceptable_enforceable_since"]

    if risk_class == "HIGH_RISK" and triggers_article_50:
        deadline = (
            "2 December 2026 for Article 50 transparency, and 2 December 2027 for "
            "Annex III high-risk obligations (postponed from 2 August 2026 by the "
            "Digital Omnibus deal of 7 May 2026)."
        )
        return deadline, REGULATORY_CONTEXT["article_50_deadline"]

    if risk_class == "HIGH_RISK":
        if primary_article == "Annex I" or primary_article.startswith("Annex I "):
            return (
                "2 August 2028 for Annex I product-embedded high-risk systems.",
                REGULATORY_CONTEXT["high_risk_annex_i_deadline"],
            )
        return (
            "2 December 2027 (postponed from 2 August 2026 by the Digital Omnibus deal of 7 May 2026).",
            REGULATORY_CONTEXT["high_risk_annex_iii_deadline"],
        )

    if risk_class == "LIMITED_RISK":
        return (
            "2 December 2026 for Article 50 transparency obligations.",
            REGULATORY_CONTEXT["article_50_deadline"],
        )

    return ("No mandatory deadline for minimal-risk systems.", None)
