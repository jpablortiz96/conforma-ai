"""Audit lifecycle routes for Conforma-AI."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.classifier import ClassifierAgent
from app.agents.orchestrator import AuditOrchestrator, launch_orchestrated_audit_job
from app.agents.scanner import ScannerAgent
from app.core.exceptions import (
    ClassifierExecutionError,
    ClassifierValidationError,
    DisclosureExecutionError,
    DisclosureValidationError,
    GapAuditorExecutionError,
    GapAuditorValidationError,
    OrchestratorExecutionError,
    RepositoryCloneError,
    ScannerExecutionError,
    ScannerValidationError,
)
from app.db.models import Audit
from app.db.session import get_db
from app.schemas.agent import ClassifierResponse
from app.schemas.audit import (
    AuditCreateRequest,
    AuditResponse,
    AuditSystemResult,
    CompliancePackResponse,
    EvidenceVaultResponse,
    ExecutiveSummaryResponse,
    OrchestratedAuditStartResponse,
)
from app.services.audit_events import AUDIT_EVENT_BROKER, encode_sse
from app.services.audit_workflows import (
    build_audit_summary,
    build_classifier_evidence_text,
    build_evidence_vault_for_audit,
    build_executive_summary_for_audit,
    compute_portfolio_risk_index,
    generate_compliance_pack_for_audit,
    get_audit_row,
    portfolio_band,
)

router = APIRouter(prefix="/api/v1/audits", tags=["audits"])


@router.post("", response_model=AuditResponse)
async def run_audit(
    request: AuditCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> AuditResponse:
    """Run the synchronous D3 audit flow: Scanner then Classifier."""

    audit = Audit(
        source_url=str(request.repo_url),
        source_type="github_repo",
        status="running",
        audit_metadata={"trigger": "audit_console", "max_files_to_inspect": request.max_files_to_inspect},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)

    scanner_agent = ScannerAgent(db)
    classifier_agent = ClassifierAgent(db)

    try:
        scanner_result = await scanner_agent.run(request.model_dump(mode="json"), audit.id)
        systems: list[AuditSystemResult] = []

        for candidate in scanner_result["ai_systems_found"]:
            classifier_result = await classifier_agent.run(
                {
                    "ai_system_id": candidate["id"],
                    "system_description": build_classifier_evidence_text(candidate, str(request.repo_url)),
                    "context_files": [
                        str(request.repo_url),
                        candidate["name"],
                        *candidate.get("source_files", []),
                        *candidate.get("detection_signals", []),
                    ],
                },
                audit.id,
            )
            normalized_classifier = ClassifierResponse.model_validate(classifier_result)
            systems.append(
                AuditSystemResult(
                    id=candidate["id"],
                    name=candidate["name"],
                    description=candidate["description"],
                    source_files=candidate.get("source_files", []),
                    detection_signals=candidate.get("detection_signals", []),
                    **normalized_classifier.model_dump(mode="json"),
                )
            )

        portfolio_index = compute_portfolio_risk_index(systems)
        summary = build_audit_summary(str(request.repo_url), systems, portfolio_index)

        audit.status = "completed"
        audit.completed_at = datetime.now(timezone.utc)
        audit.risk_index = portfolio_band(portfolio_index)
        audit.audit_metadata = {
            **(audit.audit_metadata or {}),
            "portfolio_risk_index": portfolio_index,
            "summary": summary,
        }
        db.add(audit)
        await db.commit()

        return AuditResponse(
            audit_id=audit.id,
            repo_url=str(request.repo_url),
            status="completed",
            systems=systems,
            portfolio_risk_index=portfolio_index,
            summary=summary,
        )
    except (RepositoryCloneError, ScannerValidationError, ScannerExecutionError) as exc:
        audit.status = "failed"
        audit.completed_at = datetime.now(timezone.utc)
        db.add(audit)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (ClassifierValidationError, ClassifierExecutionError, ValidationError) as exc:
        audit.status = "failed"
        audit.completed_at = datetime.now(timezone.utc)
        db.add(audit)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/orchestrated", response_model=OrchestratedAuditStartResponse)
async def start_orchestrated_audit(
    request: AuditCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> OrchestratedAuditStartResponse:
    """Start the D5 orchestrated audit pipeline and return the SSE stream URL."""

    audit = Audit(
        source_url=str(request.repo_url),
        source_type="github_repo",
        status="running",
        audit_metadata={
            "trigger": "orchestrated_audit_console",
            "max_files_to_inspect": request.max_files_to_inspect,
        },
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)

    AUDIT_EVENT_BROKER.ensure_stream(audit.id)
    launch_orchestrated_audit_job(request.model_dump(mode="json"), audit.id)

    return OrchestratedAuditStartResponse(
        audit_id=audit.id,
        repo_url=str(request.repo_url),
        status="running",
        stream_url=f"/api/v1/audits/{audit.id}/stream",
    )


@router.get("/{audit_id}/stream")
async def stream_audit(audit_id: UUID, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    """Stream real-time orchestrator events via Server-Sent Events."""

    audit = await get_audit_row(db, audit_id)
    if audit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found.")

    async def event_generator():
        history = AUDIT_EVENT_BROKER.snapshot(audit_id)
        for event in history:
            yield encode_sse(event)

        queue = AUDIT_EVENT_BROKER.subscribe(audit_id)
        try:
            while True:
                if AUDIT_EVENT_BROKER.is_completed(audit_id) and queue.empty():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield encode_sse(event)
                except TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            AUDIT_EVENT_BROKER.unsubscribe(audit_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{audit_id}/compliance-pack", response_model=CompliancePackResponse)
async def generate_compliance_pack(
    audit_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CompliancePackResponse:
    """Generate D4B disclosures, compute compliance gaps, and persist a pack snapshot."""

    try:
        return await generate_compliance_pack_for_audit(db, audit_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        DisclosureValidationError,
        DisclosureExecutionError,
        GapAuditorValidationError,
        GapAuditorExecutionError,
        ValidationError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/{audit_id}/executive-summary", response_model=ExecutiveSummaryResponse)
async def get_executive_summary(
    audit_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ExecutiveSummaryResponse:
    """Return the board-ready D5 executive summary for one audit."""

    try:
        return await build_executive_summary_for_audit(db, audit_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{audit_id}/evidence-vault", response_model=EvidenceVaultResponse)
async def get_evidence_vault(
    audit_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> EvidenceVaultResponse:
    """Return the D5 evidence-vault payload for one audit."""

    try:
        return await build_evidence_vault_for_audit(db, audit_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
