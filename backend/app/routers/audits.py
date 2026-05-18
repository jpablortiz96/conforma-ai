"""Audit lifecycle routes for Conforma-AI."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.classifier import ClassifierAgent
from app.agents.disclosure import DisclosureAgent
from app.agents.gap_auditor import GapAuditorAgent
from app.agents.scanner import ScannerAgent
from app.core.exceptions import (
    ClassifierExecutionError,
    ClassifierValidationError,
    DisclosureExecutionError,
    DisclosureValidationError,
    GapAuditorExecutionError,
    GapAuditorValidationError,
    RepositoryCloneError,
    ScannerExecutionError,
    ScannerValidationError,
)
from app.db.models import AISystem, Artifact, Audit, Gap
from app.db.session import get_db
from app.schemas.agent import ClassifierResponse, DisclosureResponse, GapAuditorResponse
from app.schemas.audit import AuditCreateRequest, AuditResponse, AuditSystemResult, CompliancePackResponse

router = APIRouter(prefix="/api/v1/audits", tags=["audits"])

RISK_WEIGHTS = {
    "UNACCEPTABLE": 100,
    "HIGH_RISK": 74,
    "LIMITED_RISK": 36,
    "MINIMAL_RISK": 8,
}

COMPLIANCE_BANDS = (
    (75, "LOW"),
    (50, "MEDIUM"),
    (25, "HIGH"),
    (0, "CRITICAL"),
)


def compute_portfolio_risk_index(systems: list[AuditSystemResult]) -> int:
    """Compute a deterministic 0-100 portfolio risk index."""

    if not systems:
        return 0

    weighted_scores: list[int] = []
    for system in systems:
        score = RISK_WEIGHTS[system.risk_class]
        if system.risk_class == "HIGH_RISK" and system.triggers_article_50:
            score += 6
        weighted_scores.append(min(score, 100))

    return max(0, min(100, round(sum(weighted_scores) / len(weighted_scores))))


def portfolio_band(index: int) -> str:
    """Map the numeric portfolio index into a dashboard band."""

    if index >= 85:
        return "CRITICAL"
    if index >= 65:
        return "HIGH"
    if index >= 35:
        return "MEDIUM"
    return "LOW"


def build_audit_summary(
    repo_url: str,
    systems: list[AuditSystemResult],
    portfolio_risk_index: int,
) -> str:
    """Build a deterministic executive summary for the audit response."""

    counts = Counter(system.risk_class for system in systems)
    highest_risk = max(systems, key=lambda system: RISK_WEIGHTS[system.risk_class]).risk_class if systems else "MINIMAL_RISK"
    summary_parts = [
        f"Conforma-AI scanned {repo_url} and identified {len(systems)} candidate AI system(s).",
        f"The portfolio risk index is {portfolio_risk_index}/100, with the highest observed class being {highest_risk.replace('_', ' ')}.",
    ]
    if counts:
        summary_parts.append(
            "Risk distribution: "
            + ", ".join(f"{risk.replace('_', ' ')}={count}" for risk, count in counts.items())
            + "."
        )
    if any(system.triggers_article_50 for system in systems):
        summary_parts.append(
            "At least one system also triggers Article 50 transparency obligations alongside its main classification."
        )
    return " ".join(summary_parts)


def build_classifier_evidence_text(candidate: dict[str, object], repo_url: str) -> str:
    """Build a richer classifier description from scanner evidence."""

    source_files = ", ".join(candidate.get("source_files", [])[:8]) or "None"
    detection_signals = "; ".join(candidate.get("detection_signals", [])[:8]) or "None"
    return "\n".join(
        [
            f"AI system name: {candidate['name']}",
            f"Repository URL: {repo_url}",
            f"Description: {candidate['description']}",
            f"Source files: {source_files}",
            f"Detection signals: {detection_signals}",
        ]
    )


async def _get_audit(db: AsyncSession, audit_id):
    """Fetch an audit row, supporting fake sessions in tests."""

    records = getattr(db, "records", None)
    if isinstance(records, dict):
        for audit in records.get("audits", []):
            if getattr(audit, "id", None) == audit_id:
                return audit
        return None
    return await db.get(Audit, audit_id)


async def _list_ai_system_rows(db: AsyncSession, audit_id) -> list[AISystem]:
    """List AI systems for one audit, supporting fake sessions in tests."""

    records = getattr(db, "records", None)
    if isinstance(records, dict):
        return [system for system in records.get("ai_systems", []) if getattr(system, "audit_id", None) == audit_id]
    result = await db.execute(select(AISystem).where(AISystem.audit_id == audit_id).order_by(AISystem.created_at.asc()))
    return list(result.scalars().all())


async def _list_artifact_rows(db: AsyncSession, audit_id) -> list[Artifact]:
    """List artifacts for one audit, supporting fake sessions in tests."""

    records = getattr(db, "records", None)
    if isinstance(records, dict):
        return [artifact for artifact in records.get("artifacts", []) if getattr(artifact, "audit_id", None) == audit_id]
    result = await db.execute(select(Artifact).where(Artifact.audit_id == audit_id).order_by(Artifact.created_at.desc()))
    return list(result.scalars().all())


async def _clear_gap_rows(db: AsyncSession, audit_id) -> None:
    """Delete existing gaps for an audit before persisting a fresh snapshot."""

    records = getattr(db, "records", None)
    if isinstance(records, dict):
        records["gaps"] = [gap for gap in records.get("gaps", []) if getattr(gap, "audit_id", None) != audit_id]
        return
    await db.execute(delete(Gap).where(Gap.audit_id == audit_id))


def _compliance_band(score: int) -> str:
    """Convert compliance score into the audit risk-index band."""

    for threshold, label in COMPLIANCE_BANDS:
        if score >= threshold:
            return label
    return "CRITICAL"


def _system_to_dict(system: AISystem) -> dict[str, object]:
    """Serialize an AI system row into the structure used by downstream agents."""

    confidence = float(system.confidence) if system.confidence is not None else 0.0
    return {
        "id": system.id,
        "name": system.name,
        "description": system.description,
        "source_files": list(system.source_files or []),
        "risk_class": system.risk_class,
        "primary_article": system.primary_article,
        "secondary_articles": list(system.secondary_articles or []),
        "reasoning": system.reasoning,
        "deadline": system.deadline,
        "deadline_iso": system.deadline_iso,
        "confidence": confidence,
        "triggers_article_50": bool(system.triggers_article_50),
    }


def _artifact_to_dict(artifact: Artifact) -> dict[str, object]:
    """Serialize an artifact row for the Gap Auditor input."""

    return {
        "id": artifact.id,
        "audit_id": artifact.audit_id,
        "ai_system_id": artifact.ai_system_id,
        "kind": artifact.kind,
        "language": artifact.language,
        "storage_url": artifact.storage_url,
        "content": artifact.content,
        "created_at": artifact.created_at,
    }


def _gap_category(gap_title: str, legal_reference: str) -> str:
    """Map a public gap object into the persisted DB category field."""

    normalized = f"{gap_title} {legal_reference}".lower()
    if "article 50" in normalized or "disclosure" in normalized:
        return "transparency"
    if "article 14" in normalized or "oversight" in normalized:
        return "human_oversight"
    if "article 9" in normalized or "risk-management" in normalized or "risk management" in normalized:
        return "risk_management"
    if "article 10" in normalized or "data" in normalized:
        return "data_governance"
    if "article 72" in normalized or "monitoring" in normalized:
        return "monitoring"
    if "article 47" in normalized or "article 48" in normalized or "ce marking" in normalized:
        return "ce_marking"
    if "article 49" in normalized or "registration" in normalized:
        return "registration"
    return "documentation"


def _gap_effort_days(severity: str) -> int:
    """Estimate remediation effort in days for persisted gap rows."""

    return {
        "CRITICAL": 21,
        "HIGH": 10,
        "MEDIUM": 5,
        "LOW": 2,
    }.get(severity, 5)


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


@router.post("/{audit_id}/compliance-pack", response_model=CompliancePackResponse)
async def generate_compliance_pack(
    audit_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CompliancePackResponse:
    """Generate D4B disclosures, compute compliance gaps, and persist a pack snapshot."""

    audit = await _get_audit(db, audit_id)
    if audit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found.")

    systems = await _list_ai_system_rows(db, audit_id)
    artifacts = await _list_artifact_rows(db, audit_id)

    disclosure_agent = DisclosureAgent(db)
    disclosures: list[DisclosureResponse] = []
    try:
        for system in systems:
            if not system.triggers_article_50:
                continue
            disclosure_result = await disclosure_agent.run(
                {
                    "ai_system_id": system.id,
                    "system_name": system.name,
                    "description": system.description,
                    "risk_class": system.risk_class,
                    "primary_article": system.primary_article,
                    "secondary_articles": list(system.secondary_articles or []),
                    "triggers_article_50": bool(system.triggers_article_50),
                },
                audit_id,
            )
            disclosures.append(DisclosureResponse.model_validate(disclosure_result))
    except (DisclosureValidationError, DisclosureExecutionError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    artifacts = await _list_artifact_rows(db, audit_id)
    systems_payload = [_system_to_dict(system) for system in systems]
    artifacts_payload = [_artifact_to_dict(artifact) for artifact in artifacts]
    disclosures_payload = [disclosure.model_dump(mode="json") for disclosure in disclosures]

    gap_agent = GapAuditorAgent(db)
    try:
        gap_result = await gap_agent.run(
            {
                "systems": systems_payload,
                "artifacts": artifacts_payload,
                "disclosures": disclosures_payload,
            },
            audit_id,
        )
        normalized_gap_result = GapAuditorResponse.model_validate(gap_result)
    except (GapAuditorValidationError, GapAuditorExecutionError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    system_deadlines = {str(system.id): system.deadline_iso for system in systems}
    await _clear_gap_rows(db, audit_id)
    for gap in normalized_gap_result.gaps:
        db.add(
            Gap(
                audit_id=audit_id,
                ai_system_id=gap.affected_system_id,
                category=_gap_category(gap.title, gap.legal_reference),
                severity=gap.severity,
                description=gap.description,
                remediation=gap.recommended_action,
                effort_days=_gap_effort_days(gap.severity),
                deadline=system_deadlines.get(str(gap.affected_system_id)) if gap.affected_system_id else None,
            )
        )

    audit.compliance_score = normalized_gap_result.compliance_score
    audit.fine_exposure_eur = normalized_gap_result.estimated_fine_exposure_eur
    audit.risk_index = _compliance_band(normalized_gap_result.compliance_score)
    audit.completed_at = datetime.now(timezone.utc)
    metadata = dict(audit.audit_metadata or {})
    metadata["compliance_pack"] = {
        "compliance_score": normalized_gap_result.compliance_score,
        "estimated_fine_exposure_eur": normalized_gap_result.estimated_fine_exposure_eur,
        "time_to_compliant_days": normalized_gap_result.time_to_compliant_days,
        "generated_at": audit.completed_at.isoformat(),
    }
    audit.audit_metadata = metadata
    db.add(audit)
    await db.commit()

    high_risk_count = sum(1 for system in systems if (system.risk_class or "").upper() == "HIGH_RISK")
    article_50_count = sum(1 for system in systems if bool(system.triggers_article_50))

    return CompliancePackResponse(
        audit_id=audit_id,
        compliance_score=normalized_gap_result.compliance_score,
        estimated_fine_exposure_eur=normalized_gap_result.estimated_fine_exposure_eur,
        time_to_compliant_days=normalized_gap_result.time_to_compliant_days,
        systems_count=len(systems),
        high_risk_count=high_risk_count,
        article_50_count=article_50_count,
        gaps=normalized_gap_result.gaps,
        disclosures=disclosures,
        priority_actions=normalized_gap_result.priority_actions,
        summary=normalized_gap_result.summary,
    )
