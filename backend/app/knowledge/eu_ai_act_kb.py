"""Full D3 EU AI Act knowledge base for Conforma-AI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.knowledge.annex_iii_categories import ANNEX_III_CATEGORIES, ANNEX_III_OBLIGATIONS
from app.knowledge.annex_iv_template import ANNEX_IV_TEMPLATE
from app.knowledge.article_50_requirements import (
    ARTICLE_50_DISCLOSURE_CHARACTERISTICS,
    ARTICLE_50_REQUIREMENTS,
)

RiskClass = Literal["UNACCEPTABLE", "HIGH_RISK", "LIMITED_RISK", "MINIMAL_RISK"]

REGULATORY_CONTEXT = {
    "omnibus_deal_date": "2026-05-07",
    "unacceptable_enforceable_since": date(2025, 2, 2),
    "article_50_deadline": date(2026, 12, 2),
    "high_risk_annex_iii_deadline": date(2027, 12, 2),
    "high_risk_annex_i_deadline": date(2028, 8, 2),
    "omnibus_note": (
        "The Digital Omnibus deal of 7 May 2026 postponed Annex III high-risk deadlines "
        "from 2 August 2026 to 2 December 2027, while Article 50 transparency obligations "
        "remain due on 2 December 2026 and Annex I product-embedded high-risk systems move "
        "to 2 August 2028."
    ),
}

UNACCEPTABLE_PRACTICES = [
    {"reference": "Article 5(1)(a)", "practice": "Subliminal techniques causing physical or psychological harm"},
    {"reference": "Article 5(1)(b)", "practice": "Exploitation of vulnerabilities such as age, disability, or socioeconomic status"},
    {"reference": "Article 5(1)(c)", "practice": "Social scoring by public authorities for general-purpose evaluation"},
    {"reference": "Article 5(1)(d)", "practice": "Predictive policing based solely on profiling"},
    {"reference": "Article 5(1)(e)", "practice": "Untargeted scraping for facial-recognition databases"},
    {"reference": "Article 5(1)(f)", "practice": "Emotion inference in workplaces or educational institutions, except limited safety or medical uses"},
    {"reference": "Article 5(1)(g)", "practice": "Biometric categorization inferring sensitive attributes"},
    {"reference": "Article 5(1)(h)", "practice": "Real-time remote biometric identification in publicly accessible spaces for law enforcement, subject only to narrow exceptions"},
    {"reference": "Article 5(1)(i)", "practice": "Nudifier applications generating non-consensual sexually explicit imagery"},
]

ANNEX_I_HIGH_RISK_EXAMPLES = [
    "Medical devices with AI safety components",
    "Toys with AI safety components",
    "Lifts and aviation safety systems",
    "Vehicles and transport products with AI safety components",
]

MINIMAL_RISK_EXAMPLES = [
    "Spam filters",
    "AI in video games",
    "Inventory management AI",
    "Predictive maintenance for non-critical equipment",
]

RISK_CLASSES_PAYLOAD = {
    "regulatory_context": REGULATORY_CONTEXT,
    "risk_classes": [
        {
            "risk_class": "UNACCEPTABLE",
            "deadline": "Already enforceable since 2 February 2025",
            "references": [item["reference"] for item in UNACCEPTABLE_PRACTICES],
            "examples": [item["practice"] for item in UNACCEPTABLE_PRACTICES],
        },
        {
            "risk_class": "HIGH_RISK",
            "deadline": "2 December 2027 for Annex III, 2 August 2028 for Annex I products",
            "references": [category["section"] for category in ANNEX_III_CATEGORIES],
            "examples": [
                "CV ranking in recruitment",
                "Creditworthiness scoring",
                "Life and health insurance pricing",
                "Biometric identification in private retail settings",
            ],
        },
        {
            "risk_class": "LIMITED_RISK",
            "deadline": "2 December 2026",
            "references": [item["subsection"] for item in ARTICLE_50_REQUIREMENTS],
            "examples": [
                "Chatbots interacting with people",
                "Synthetic content generators",
                "Deep-fake generators",
                "Emotion recognition disclosures",
            ],
        },
        {
            "risk_class": "MINIMAL_RISK",
            "deadline": "No mandatory deadline",
            "references": ["Article 95 (voluntary codes of conduct)"],
            "examples": MINIMAL_RISK_EXAMPLES,
        },
    ],
}


@dataclass(frozen=True, slots=True)
class ClassificationRule:
    """Deterministic fallback rule for D3 classification."""

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
        confidence=0.98,
        triggers_article_50=False,
        reasoning=(
            "This system is described as social credit or social scoring by a public authority, which "
            "maps directly to the prohibited practice in Article 5(1)(c). Prohibited practices are already "
            "enforceable since 2 February 2025, so there is no deferred compliance runway."
        ),
        match_all=("social", "scoring"),
        match_any=("municipality", "public authority", "government", "dutch municipality"),
    ),
    ClassificationRule(
        name="law_enforcement_public_biometric",
        risk_class="UNACCEPTABLE",
        primary_article="Article 5(1)(h)",
        secondary_articles=(),
        confidence=0.97,
        triggers_article_50=False,
        reasoning=(
            "Real-time remote biometric identification in publicly accessible spaces for law enforcement "
            "is prohibited under Article 5(1)(h), subject only to narrow exceptions. Because the described "
            "use involves police or law-enforcement use in a public square or similarly public setting, the "
            "conservative classification is unacceptable risk."
        ),
        match_all=("real time",),
        match_any=("police", "law enforcement", "public square", "publicly accessible", "biometric id"),
    ),
    ClassificationRule(
        name="employment_with_generated_explanations",
        risk_class="HIGH_RISK",
        primary_article="Annex III Section 4(a)",
        secondary_articles=("Article 50(2)",),
        confidence=0.93,
        triggers_article_50=True,
        reasoning=(
            "Resume or CV scoring for recruitment falls under Annex III Section 4(a) on employment and "
            "access to self-employment. Because the system also generates explanatory text for users or "
            "operators, Article 50(2) transparency is additionally triggered. The Annex III deadline is "
            "2 December 2027, postponed from 2 August 2026 by the Digital Omnibus deal of 7 May 2026."
        ),
        match_any=("resume scoring", "cv ranking", "resume ranking", "candidate scoring"),
        match_all=("explanation",),
    ),
    ClassificationRule(
        name="employment_recruitment",
        risk_class="HIGH_RISK",
        primary_article="Annex III Section 4(a)",
        secondary_articles=(),
        confidence=0.94,
        triggers_article_50=False,
        reasoning=(
            "CV ranking, resume scoring, and candidate filtering for recruitment map to Annex III Section 4(a), "
            "which covers employment and access to self-employment. The relevant high-risk Annex III deadline is "
            "2 December 2027, postponed from 2 August 2026 by the Digital Omnibus deal of 7 May 2026."
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
        name="insurance_pricing",
        risk_class="HIGH_RISK",
        primary_article="Annex III Section 5(c)",
        secondary_articles=(),
        confidence=0.93,
        triggers_article_50=False,
        reasoning=(
            "AI used to assess risk or price life or health insurance is explicitly listed in Annex III Section 5(c). "
            "That makes the system high-risk, with the Annex III compliance date set at 2 December 2027 after the "
            "Digital Omnibus deal of 7 May 2026."
        ),
        match_any=("life insurance", "health insurance", "insurance premiums", "insurance pricing"),
    ),
    ClassificationRule(
        name="creditworthiness",
        risk_class="HIGH_RISK",
        primary_article="Annex III Section 5(b)",
        secondary_articles=(),
        confidence=0.92,
        triggers_article_50=False,
        reasoning=(
            "Creditworthiness and credit scoring are listed in Annex III Section 5(b) as high-risk uses affecting "
            "access to essential private services. The Annex III deadline is 2 December 2027, postponed from "
            "2 August 2026 by the Digital Omnibus deal of 7 May 2026."
        ),
        match_any=("credit score", "creditworthiness", "loan approval", "mortgage scoring"),
    ),
    ClassificationRule(
        name="retail_biometric_security",
        risk_class="HIGH_RISK",
        primary_article="Annex III Section 1",
        secondary_articles=(),
        confidence=0.84,
        triggers_article_50=False,
        reasoning=(
            "Facial recognition for shoplifter detection in private retail settings fits the biometric "
            "identification and categorization category in Annex III Section 1. The description does not clearly "
            "place the system into the prohibited public law-enforcement scenario of Article 5(1)(h), so the "
            "conservative classification is high-risk. The Annex III deadline is 2 December 2027 after the "
            "Digital Omnibus deal of 7 May 2026."
        ),
        match_any=("facial recognition", "face recognition", "shoplifter", "supermarket", "retail"),
    ),
    ClassificationRule(
        name="deep_fake_content",
        risk_class="LIMITED_RISK",
        primary_article="Article 50(4)",
        secondary_articles=("Article 50(2)",),
        confidence=0.9,
        triggers_article_50=True,
        reasoning=(
            "Deep-fake media requires disclosure that the content has been artificially generated or manipulated "
            "under Article 50(4). Providers of the underlying generator must also support detectable synthetic-content "
            "marking under Article 50(2). The applicable transparency deadline is 2 December 2026."
        ),
        match_any=("deep fake", "deepfake", "synthetic video", "face swap", "video generator"),
    ),
    ClassificationRule(
        name="generated_synthetic_content",
        risk_class="LIMITED_RISK",
        primary_article="Article 50(2)",
        secondary_articles=(),
        confidence=0.86,
        triggers_article_50=True,
        reasoning=(
            "Systems that generate synthetic text, audio, image, or video content trigger Article 50(2), which "
            "requires detectable machine-readable marking of outputs. The applicable deadline for Article 50 "
            "transparency obligations is 2 December 2026."
        ),
        match_any=("ai generated", "synthetic text", "synthetic image", "image generator", "text generator"),
    ),
    ClassificationRule(
        name="chatbot_direct_interaction",
        risk_class="LIMITED_RISK",
        primary_article="Article 50(1)",
        secondary_articles=(),
        confidence=0.91,
        triggers_article_50=True,
        reasoning=(
            "A customer service or password-reset chatbot is intended to interact directly with natural persons, "
            "which triggers the transparency duty in Article 50(1). Those disclosures remain due on 2 December 2026."
        ),
        match_any=("chatbot", "password reset", "customer service bot", "virtual assistant"),
    ),
    ClassificationRule(
        name="emotion_or_biometric_categorisation",
        risk_class="LIMITED_RISK",
        primary_article="Article 50(3)",
        secondary_articles=(),
        confidence=0.82,
        triggers_article_50=True,
        reasoning=(
            "Emotion recognition and biometric categorization systems trigger Article 50(3) transparency obligations "
            "toward exposed natural persons, alongside applicable data-protection duties. The deadline for those "
            "transparency measures is 2 December 2026."
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
            "An email spam classifier is a standard minimal-risk AI use case and does not clearly map to Article 5, "
            "Annex III, or Article 50 obligations. No mandatory EU AI Act deadline applies beyond voluntary good practice."
        ),
        match_any=("spam filter", "spam classifier", "email spam"),
    ),
    ClassificationRule(
        name="predictive_maintenance",
        risk_class="MINIMAL_RISK",
        primary_article="Not applicable",
        secondary_articles=(),
        confidence=0.88,
        triggers_article_50=False,
        reasoning=(
            "Predictive maintenance for ordinary industrial machinery is generally treated as minimal risk when it does "
            "not operate as a safety component of a regulated product or critical infrastructure. The description here "
            "does not show an Annex III or Article 50 trigger."
        ),
        match_all=("predictive maintenance",),
        match_any=("industrial machinery", "equipment", "factory"),
    ),
)


def deadline_for_classification(
    risk_class: RiskClass,
    *,
    triggers_article_50: bool,
    primary_article: str,
) -> tuple[str, date | None]:
    """Return the human-readable deadline and machine-readable ISO date."""

    if risk_class == "UNACCEPTABLE":
        return (
            "Already enforceable since 2 February 2025.",
            REGULATORY_CONTEXT["unacceptable_enforceable_since"],
        )

    if risk_class == "HIGH_RISK" and triggers_article_50:
        return (
            "2 December 2026 for Article 50 transparency, and 2 December 2027 for Annex III high-risk obligations "
            "(postponed from 2 August 2026 by the Digital Omnibus deal of 7 May 2026).",
            REGULATORY_CONTEXT["article_50_deadline"],
        )

    if risk_class == "HIGH_RISK":
        if primary_article.startswith("Annex I"):
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


def build_classifier_context() -> str:
    """Build a compact legal context string for the classifier prompt."""

    unacceptable = "\n".join(
        f"- {item['reference']}: {item['practice']}" for item in UNACCEPTABLE_PRACTICES
    )
    annex_iii = "\n".join(
        f"- Annex III Section {category['section']}: {category['title']} — {category['summary']}"
        for category in ANNEX_III_CATEGORIES
    )
    article_50 = "\n".join(
        f"- {item['subsection']}: {item['title']} — {item['description']}"
        for item in ARTICLE_50_REQUIREMENTS
    )
    minimal = "\n".join(f"- {item}" for item in MINIMAL_RISK_EXAMPLES)

    return f"""
Regulatory context:
- The Digital Omnibus deal of 7 May 2026 postponed Annex III deadlines to 2 December 2027.
- Article 50 transparency obligations remain due on 2 December 2026.
- Annex I product-embedded high-risk systems move to 2 August 2028.
- Article 5 prohibited practices are already enforceable since 2 February 2025.

UNACCEPTABLE RISK — Article 5 prohibited practices:
{unacceptable}

HIGH-RISK — Annex III stand-alone categories:
{annex_iii}

HIGH-RISK — Annex I product examples:
- {"; ".join(ANNEX_I_HIGH_RISK_EXAMPLES)}

LIMITED RISK — Article 50 transparency obligations:
{article_50}

MINIMAL RISK examples:
{minimal}
""".strip()


def get_risk_classes_payload() -> dict[str, object]:
    """Return a structured payload for the knowledge routes."""

    return RISK_CLASSES_PAYLOAD


def get_annex_iii_payload() -> dict[str, object]:
    """Return Annex III categories and obligations."""

    return {
        "deadline": "2 December 2027",
        "categories": ANNEX_III_CATEGORIES,
        "obligations": ANNEX_III_OBLIGATIONS,
    }


def get_article_50_payload() -> dict[str, object]:
    """Return Article 50 requirements and implementation guidance."""

    return {
        "deadline": "2 December 2026",
        "requirements": ARTICLE_50_REQUIREMENTS,
        "disclosure_characteristics": ARTICLE_50_DISCLOSURE_CHARACTERISTICS,
    }


def get_annex_iv_template_payload() -> dict[str, object]:
    """Return the Annex IV documentation template."""

    return {"template": ANNEX_IV_TEMPLATE}
