"""Agent endpoints for Conforma-AI."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.scanner import ScannerAgent
from app.core.exceptions import RepositoryCloneError, ScannerExecutionError, ScannerValidationError
from app.db.models import Audit
from app.db.session import get_db
from app.schemas.agent import ScannerOutput, ScannerRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.post("/scanner", response_model=ScannerOutput)
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
        audit.status = "completed"
        audit.completed_at = datetime.now(timezone.utc)
        db.add(audit)
        await db.commit()
        return ScannerOutput.model_validate(result)
    except RepositoryCloneError as exc:
        audit.status = "failed"
        audit.completed_at = datetime.now(timezone.utc)
        db.add(audit)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ScannerValidationError as exc:
        audit.status = "failed"
        audit.completed_at = datetime.now(timezone.utc)
        db.add(audit)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
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
