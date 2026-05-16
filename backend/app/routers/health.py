"""Health and knowledge routes for Conforma-AI."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.knowledge.eu_ai_act_kb import (
    get_annex_iii_payload,
    get_annex_iv_template_payload,
    get_article_50_payload,
    get_risk_classes_payload,
)
from app.schemas.agent import HealthResponse

settings = get_settings()

router = APIRouter(tags=["health"])


@router.get("/", response_model=HealthResponse)
async def root() -> HealthResponse:
    """Return the operational health payload."""

    return HealthResponse(service=settings.app_name, version=settings.app_version)


@router.get("/api/v1/ai-act/risk-classes")
async def get_risk_classes() -> dict[str, object]:
    """Expose the structured risk-class knowledge base."""

    return get_risk_classes_payload()


@router.get("/api/v1/ai-act/annex-iii")
async def get_annex_iii() -> dict[str, object]:
    """Expose structured Annex III categories."""

    return get_annex_iii_payload()


@router.get("/api/v1/ai-act/article-50")
async def get_article_50() -> dict[str, object]:
    """Expose Article 50 transparency requirements."""

    return get_article_50_payload()


@router.get("/api/v1/ai-act/annex-iv-template")
async def get_annex_iv_template() -> dict[str, object]:
    """Expose the Annex IV documentation template structure."""

    return get_annex_iv_template_payload()
