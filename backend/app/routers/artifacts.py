"""Artifact listing and download routes for Conforma-AI."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Artifact, Audit
from app.db.session import get_db
from app.schemas.artifact import ArtifactSummary, AuditArtifactsResponse

router = APIRouter(tags=["artifacts"])


async def _fetch_artifact_rows_for_audit(db: AsyncSession, audit_id: UUID) -> list[Artifact]:
    """Return all artifacts for an audit, supporting fake sessions in tests."""

    records = getattr(db, "records", None)
    if isinstance(records, dict):
        artifacts = [
            artifact for artifact in records.get("artifacts", []) if getattr(artifact, "audit_id", None) == audit_id
        ]
        return sorted(
            artifacts,
            key=lambda artifact: getattr(artifact, "created_at", None) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

    result = await db.execute(
        select(Artifact).where(Artifact.audit_id == audit_id).order_by(Artifact.created_at.desc())
    )
    return list(result.scalars().all())


async def _fetch_artifact_row(db: AsyncSession, artifact_id: UUID) -> Artifact | None:
    """Return one artifact row, supporting fake sessions in tests."""

    records = getattr(db, "records", None)
    if isinstance(records, dict):
        for artifact in records.get("artifacts", []):
            if getattr(artifact, "id", None) == artifact_id:
                return artifact
        return None

    return await db.get(Artifact, artifact_id)


def _build_artifact_summary(artifact: Artifact) -> ArtifactSummary:
    """Convert an Artifact ORM row into the public summary schema."""

    file_name = Path(artifact.storage_url).name if artifact.storage_url else f"{artifact.kind}.bin"
    created_at = artifact.created_at or datetime.now(timezone.utc)
    return ArtifactSummary(
        artifact_id=artifact.id,
        audit_id=artifact.audit_id,
        ai_system_id=artifact.ai_system_id,
        kind=artifact.kind,
        language=artifact.language,
        file_name=file_name,
        download_url=f"/api/v1/artifacts/{artifact.id}/download",
        created_at=created_at,
    )


@router.get("/api/v1/audits/{audit_id}/artifacts", response_model=AuditArtifactsResponse)
async def list_audit_artifacts(
    audit_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> AuditArtifactsResponse:
    """List generated artifacts for one audit."""

    audit = await db.get(Audit, audit_id)
    if audit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found.")

    artifacts = await _fetch_artifact_rows_for_audit(db, audit_id)
    return AuditArtifactsResponse(
        audit_id=audit_id,
        artifacts=[_build_artifact_summary(artifact) for artifact in artifacts],
    )


@router.get("/api/v1/artifacts/{artifact_id}/download")
async def download_artifact(
    artifact_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Download a generated PDF artifact from local storage."""

    artifact = await _fetch_artifact_row(db, artifact_id)
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found.")
    if artifact.kind != "annex_iv_pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Annex IV PDF artifacts are downloadable in D4A.",
        )
    if not artifact.storage_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact storage path is missing.",
        )

    file_path = Path(artifact.storage_url)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated artifact file was not found on disk.",
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=file_path.name,
    )
