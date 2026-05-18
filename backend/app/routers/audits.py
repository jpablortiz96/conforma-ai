"""Audit lifecycle routes for Conforma-AI."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.classifier import ClassifierAgent
from app.agents.scanner import ScannerAgent
from app.core.exceptions import (
    ClassifierExecutionError,
    ClassifierValidationError,
    RepositoryCloneError,
    ScannerExecutionError,
    ScannerValidationError,
)
from app.db.models import Audit
from app.db.session import get_db
from app.schemas.agent import ClassifierResponse
from app.schemas.audit import AuditCreateRequest, AuditResponse, AuditSystemResult

router = APIRouter(prefix="/api/v1/audits", tags=["audits"])

RISK_WEIGHTS = {
    "UNACCEPTABLE": 100,
    "HIGH_RISK": 74,
    "LIMITED_RISK": 36,
    "MINIMAL_RISK": 8,
}


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
