"""Minimal D1 EU AI Act knowledge exports."""

from app.knowledge.eu_ai_act_minimal import (
    CLASSIFIER_KB_SUMMARY,
    FALLBACK_CLASSIFICATION_RULES,
    REGULATORY_CONTEXT,
    deadline_for_classification,
)

__all__ = [
    "CLASSIFIER_KB_SUMMARY",
    "FALLBACK_CLASSIFICATION_RULES",
    "REGULATORY_CONTEXT",
    "deadline_for_classification",
]
