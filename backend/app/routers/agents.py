"""Agent and demo-helper endpoints for Conforma-AI."""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.classifier import classify_description
from app.agents.documentation import DocumentationAgent
from app.agents.disclosure import DisclosureAgent
from app.agents.gap_auditor import GapAuditorAgent
from app.agents.scanner import ScannerAgent
from app.core.exceptions import (
    ClassifierExecutionError,
    DisclosureExecutionError,
    DisclosureValidationError,
    DocumentationExecutionError,
    DocumentationValidationError,
    GapAuditorExecutionError,
    GapAuditorValidationError,
    RepositoryCloneError,
    ScannerExecutionError,
    ScannerValidationError,
)
from app.db.models import AISystem, Audit
from app.db.session import get_db
from app.schemas.agent import (
    ClassifierRequest,
    ClassifierResponse,
    DemoHighRiskSystemResponse,
    DisclosureRequest,
    DisclosureResponse,
    DocumentationRequest,
    DocumentationResponse,
    GapAuditorRequest,
    GapAuditorResponse,
    ScannerOutput,
    ScannerRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agents"])


@router.post("/api/v1/agents/scanner", response_model=ScannerOutput)
async def scan_repository(
    request: ScannerRequest,
    db: AsyncSession = Depends(get_db),
) -> ScannerOutput:
    """Clone a repository, inventory candidate AI systems, and persist the run."""

    audit = Audit(
        source_url=str(request.repo_url),
        source_type="github_repo",
        status="running",
        audit_metadata={"trigger": "scanner_endpoint"},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)

    agent = ScannerAgent(db)
    try:
        result = await agent.run(request.model_dump(mode="json"), audit.id)
        normalized_result = ScannerOutput.model_validate(result)
        audit.status = "completed"
        audit.completed_at = datetime.now(timezone.utc)
        db.add(audit)
        await db.commit()
        return normalized_result
    except RepositoryCloneError as exc:
        audit.status = "failed"
        audit.completed_at = datetime.now(timezone.utc)
        db.add(audit)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (ScannerValidationError, ValidationError) as exc:
        audit.status = "failed"
        audit.completed_at = datetime.now(timezone.utc)
        db.add(audit)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ScannerExecutionError as exc:
        logger.exception("Scanner execution failed for audit %s", audit.id)
        audit.status = "failed"
        audit.completed_at = datetime.now(timezone.utc)
        db.add(audit)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Scanner execution failed. Check server logs for details.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected scanner route failure for audit %s", audit.id)
        audit.status = "failed"
        audit.completed_at = datetime.now(timezone.utc)
        db.add(audit)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Scanner execution failed. Check server logs for details.",
        ) from exc


@router.post("/api/v1/agents/classifier", response_model=ClassifierResponse)
async def classify_system(request: ClassifierRequest) -> ClassifierResponse:
    """Classify a described AI system without creating an audit row."""

    if not request.system_description:
        raise HTTPException(status_code=400, detail="system_description is required.")

    return await classify_description(request)


@router.post("/api/v1/agents/documentation", response_model=DocumentationResponse)
async def generate_documentation(
    request: DocumentationRequest,
    db: AsyncSession = Depends(get_db),
) -> DocumentationResponse:
    """Generate structured Annex IV output and a PDF artifact for a high-risk system."""

    agent = DocumentationAgent(db)
    try:
        result = await agent.run(request.model_dump(mode="json"), request.audit_id)
        return DocumentationResponse.model_validate(result)
    except DocumentationValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except DocumentationExecutionError as exc:
        logger.exception(
            "Documentation execution failed for audit %s ai_system %s",
            request.audit_id,
            request.ai_system_id,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Documentation generation failed. Check server logs for details.",
        ) from exc


@router.post("/api/v1/agents/disclosure", response_model=DisclosureResponse)
async def generate_disclosure(
    request: DisclosureRequest,
    db: AsyncSession = Depends(get_db),
) -> DisclosureResponse:
    """Generate Article 50 disclosure notices for one AI system."""

    agent = DisclosureAgent(db)
    try:
        result = await agent.run(request.model_dump(mode="json"), request.audit_id)
        return DisclosureResponse.model_validate(result)
    except DisclosureValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except DisclosureExecutionError as exc:
        logger.exception(
            "Disclosure execution failed for audit %s ai_system %s",
            request.audit_id,
            request.ai_system_id,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Disclosure generation failed. Check server logs for details.",
        ) from exc


@router.post("/api/v1/agents/gap-auditor", response_model=GapAuditorResponse)
async def run_gap_auditor(
    request: GapAuditorRequest,
    db: AsyncSession = Depends(get_db),
) -> GapAuditorResponse:
    """Compute deterministic compliance gaps and score for an audit payload."""

    agent = GapAuditorAgent(db)
    try:
        result = await agent.run(request.model_dump(mode="json"), request.audit_id)
        return GapAuditorResponse.model_validate(result)
    except GapAuditorValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except GapAuditorExecutionError as exc:
        logger.exception("Gap Auditor execution failed for audit %s", request.audit_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gap Auditor execution failed. Check server logs for details.",
        ) from exc


@router.post("/api/v1/demo/high-risk-system", response_model=DemoHighRiskSystemResponse)
async def create_demo_high_risk_system(
    db: AsyncSession = Depends(get_db),
) -> DemoHighRiskSystemResponse:
    """Create a demo audit plus one high-risk AI system for Annex IV generation."""

    now = datetime.now(timezone.utc)
    audit = Audit(
        source_url="demo://bank-cv-ranking-system",
        source_type="demo_seed",
        status="completed",
        created_at=now,
        completed_at=now,
        audit_metadata={
            "trigger": "demo_high_risk_system",
            "label": "D4A Annex IV demo seed",
        },
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)

    ai_system = AISystem(
        audit_id=audit.id,
        name="bank_cv_ranking_system",
        description=(
            "AI system that ranks CVs for recruitment in a bank using education, employment "
            "history, skills and interview notes."
        ),
        source_files=["src/recruitment/ranker.py", "README.md"],
        risk_class="HIGH_RISK",
        primary_article="Annex III Section 4(a)",
        secondary_articles=[],
        reasoning=(
            "This seeded demo system is a recruitment-ranking use case that falls within Annex III "
            "Section 4(a) on employment and access to self-employment."
        ),
        deadline="2 December 2027",
        deadline_iso=date(2027, 12, 2),
        confidence=0.99,
        triggers_article_50=False,
        created_at=now,
    )
    db.add(ai_system)
    await db.commit()
    await db.refresh(ai_system)

    return DemoHighRiskSystemResponse(audit_id=audit.id, ai_system_id=ai_system.id)
