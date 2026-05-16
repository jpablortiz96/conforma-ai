"""EU AI Act knowledge exports for Conforma-AI."""

from app.knowledge.annex_iii_categories import ANNEX_III_CATEGORIES, ANNEX_III_OBLIGATIONS
from app.knowledge.annex_iv_template import ANNEX_IV_TEMPLATE
from app.knowledge.article_50_requirements import (
    ARTICLE_50_DISCLOSURE_CHARACTERISTICS,
    ARTICLE_50_REQUIREMENTS,
)
from app.knowledge.eu_ai_act_kb import (
    ANNEX_I_HIGH_RISK_EXAMPLES,
    FALLBACK_CLASSIFICATION_RULES,
    MINIMAL_RISK_EXAMPLES,
    REGULATORY_CONTEXT,
    RISK_CLASSES_PAYLOAD,
    UNACCEPTABLE_PRACTICES,
    build_classifier_context,
    deadline_for_classification,
    get_annex_iii_payload,
    get_annex_iv_template_payload,
    get_article_50_payload,
    get_risk_classes_payload,
)

__all__ = [
    "ANNEX_I_HIGH_RISK_EXAMPLES",
    "ANNEX_III_CATEGORIES",
    "ANNEX_III_OBLIGATIONS",
    "ANNEX_IV_TEMPLATE",
    "ARTICLE_50_DISCLOSURE_CHARACTERISTICS",
    "ARTICLE_50_REQUIREMENTS",
    "FALLBACK_CLASSIFICATION_RULES",
    "MINIMAL_RISK_EXAMPLES",
    "REGULATORY_CONTEXT",
    "RISK_CLASSES_PAYLOAD",
    "UNACCEPTABLE_PRACTICES",
    "build_classifier_context",
    "deadline_for_classification",
    "get_annex_iii_payload",
    "get_annex_iv_template_payload",
    "get_article_50_payload",
    "get_risk_classes_payload",
]
