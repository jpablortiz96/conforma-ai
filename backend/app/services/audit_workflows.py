"""Shared audit workflow helpers for synchronous and orchestrated routes."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.disclosure import DisclosureAgent
from app.agents.gap_auditor import GapAuditorAgent
from app.db.models import AISystem, AgentRun, Artifact, Audit, Gap
from app.knowledge import REGULATORY_CONTEXT
from app.schemas.agent import DisclosureResponse, GapAuditorResponse, MonitorResponse, sanitize_reference_text
from app.schemas.artifact import ArtifactSummary
from app.schemas.audit import (
    AuditResponse,
    AuditSystemResult,
    CompliancePackResponse,
    EvidenceVaultAgentRun,
    EvidenceVaultGap,
    EvidenceVaultResponse,
    EvidenceVaultSystem,
    ExecutiveBusinessImpact,
    ExecutiveSummaryResponse,
    RegulatoryTimelineEntry,
)

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
    highest_risk = (
        max(systems, key=lambda system: RISK_WEIGHTS[system.risk_class]).risk_class
        if systems
        else "MINIMAL_RISK"
    )
    summary_parts = [
        f"Conforma-AI scanned {repo_url} and identified {len(systems)} candidate AI system(s).",
        f"The portfolio risk index is {portfolio_risk_index}/100, with the highest observed class being {highest_risk.replace('_', ' ')}.",
    ]
    if counts:
        summary_parts.append(
            "Risk distribution: "
            + ", ".join(
                f"{risk.replace('_', ' ')}={count}" for risk, count in sorted(counts.items())
            )
            + "."
        )
    if any(system.triggers_article_50 for system in systems):
        summary_parts.append(
            "At least one system also triggers Article 50 transparency obligations alongside its main classification."
        )
    return sanitize_reference_text(" ".join(summary_parts))


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


async def get_audit_row(db: AsyncSession, audit_id: UUID) -> Audit | None:
    """Fetch an audit row, supporting fake sessions in tests."""

    records = getattr(db, "records", None)
    if isinstance(records, dict):
        for audit in records.get("audits", []):
            if getattr(audit, "id", None) == audit_id:
                return audit
        return None
    return await db.get(Audit, audit_id)


async def list_ai_system_rows(db: AsyncSession, audit_id: UUID) -> list[AISystem]:
    """List AI systems for one audit, supporting fake sessions in tests."""

    records = getattr(db, "records", None)
    if isinstance(records, dict):
        return [
            system
            for system in records.get("ai_systems", [])
            if getattr(system, "audit_id", None) == audit_id
        ]
    result = await db.execute(
        select(AISystem).where(AISystem.audit_id == audit_id).order_by(AISystem.created_at.asc())
    )
    return list(result.scalars().all())


async def list_artifact_rows(db: AsyncSession, audit_id: UUID) -> list[Artifact]:
    """List artifacts for one audit, supporting fake sessions in tests."""

    records = getattr(db, "records", None)
    if isinstance(records, dict):
        artifacts = [
            artifact
            for artifact in records.get("artifacts", [])
            if getattr(artifact, "audit_id", None) == audit_id
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


async def list_gap_rows(db: AsyncSession, audit_id: UUID) -> list[Gap]:
    """List persisted gaps for one audit."""

    records = getattr(db, "records", None)
    if isinstance(records, dict):
        return [
            gap for gap in records.get("gaps", []) if getattr(gap, "audit_id", None) == audit_id
        ]
    result = await db.execute(select(Gap).where(Gap.audit_id == audit_id))
    return list(result.scalars().all())


async def list_agent_run_rows(db: AsyncSession, audit_id: UUID) -> list[AgentRun]:
    """List agent runs for one audit."""

    records = getattr(db, "records", None)
    if isinstance(records, dict):
        return [
            run for run in records.get("agent_runs", []) if getattr(run, "audit_id", None) == audit_id
        ]
    result = await db.execute(
        select(AgentRun).where(AgentRun.audit_id == audit_id).order_by(AgentRun.started_at.asc())
    )
    return list(result.scalars().all())


async def clear_gap_rows(db: AsyncSession, audit_id: UUID) -> None:
    """Delete existing gaps for an audit before persisting a fresh snapshot."""

    records = getattr(db, "records", None)
    if isinstance(records, dict):
        records["gaps"] = [
            gap for gap in records.get("gaps", []) if getattr(gap, "audit_id", None) != audit_id
        ]
        return
    await db.execute(delete(Gap).where(Gap.audit_id == audit_id))


def compliance_band(score: int) -> str:
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


def artifact_to_dict(artifact: Artifact) -> dict[str, object]:
    """Serialize an artifact row for downstream agent input or API output."""

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


def build_artifact_summary(artifact: Artifact) -> ArtifactSummary:
    """Convert an Artifact ORM row into the public summary schema."""

    if artifact.storage_url:
        file_name = Path(artifact.storage_url).name
    elif artifact.kind == "article_50_notice_json":
        file_name = "article_50_notice.json"
    else:
        file_name = f"{artifact.kind}.bin"
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


def gap_category(gap_title: str, legal_reference: str) -> str:
    """Map a public gap object into the persisted DB category field."""

    normalized = f"{gap_title} {legal_reference}".lower()
    if "article 50" in normalized or "disclosure" in normalized:
        return "transparency"
    if "article 14" in normalized or "oversight" in normalized:
        return "human_oversight"
    if "article 9" in normalized or "risk management" in normalized:
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


def gap_effort_days(severity: str) -> int:
    """Estimate remediation effort in days for persisted gap rows."""

    return {
        "CRITICAL": 21,
        "HIGH": 10,
        "MEDIUM": 5,
        "LOW": 2,
    }.get(severity, 5)


def _parse_artifact_json(raw_content: str | None) -> dict[str, Any]:
    """Parse a small JSON artifact payload when available."""

    if not raw_content:
        return {}
    try:
        payload = json.loads(raw_content)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def disclosure_from_artifact(artifact: Artifact) -> DisclosureResponse | None:
    """Parse a persisted disclosure artifact back into the public response schema."""

    if artifact.kind != "article_50_notice_json":
        return None
    payload = _parse_artifact_json(artifact.content)
    if not payload:
        return None
    try:
        return DisclosureResponse.model_validate(payload)
    except ValidationError:
        return None


def latest_monitor_response(agent_runs: list[AgentRun]) -> MonitorResponse | None:
    """Extract the latest persisted monitor response from agent runs."""

    monitor_runs = [run for run in agent_runs if run.agent_name == "monitor" and run.output]
    if not monitor_runs:
        return None
    latest_run = sorted(
        monitor_runs,
        key=lambda run: run.started_at or datetime.min.replace(tzinfo=timezone.utc),
    )[-1]
    try:
        return MonitorResponse.model_validate(latest_run.output)
    except ValidationError:
        return None


async def generate_compliance_pack_for_audit(
    db: AsyncSession,
    audit_id: UUID,
    *,
    precomputed_disclosures: list[DisclosureResponse] | None = None,
    generate_disclosures_if_missing: bool = True,
) -> CompliancePackResponse:
    """Generate D4B disclosures, compute compliance gaps, and persist a pack snapshot."""

    audit = await get_audit_row(db, audit_id)
    if audit is None:
        raise ValueError("Audit not found.")

    systems = await list_ai_system_rows(db, audit_id)
    artifacts = await list_artifact_rows(db, audit_id)

    disclosures: list[DisclosureResponse] = list(precomputed_disclosures or [])
    if generate_disclosures_if_missing:
        disclosure_agent = DisclosureAgent(db)
        existing_ids = {disclosure.ai_system_id for disclosure in disclosures}
        for system in systems:
            if not system.triggers_article_50 or system.id in existing_ids:
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

    artifacts = await list_artifact_rows(db, audit_id)
    systems_payload = [_system_to_dict(system) for system in systems]
    artifacts_payload = [artifact_to_dict(artifact) for artifact in artifacts]
    disclosures_payload = [disclosure.model_dump(mode="json") for disclosure in disclosures]

    gap_agent = GapAuditorAgent(db)
    gap_result = await gap_agent.run(
        {
            "systems": systems_payload,
            "artifacts": artifacts_payload,
            "disclosures": disclosures_payload,
        },
        audit_id,
    )
    normalized_gap_result = GapAuditorResponse.model_validate(gap_result)

    system_deadlines = {str(system.id): system.deadline_iso for system in systems}
    await clear_gap_rows(db, audit_id)
    for gap in normalized_gap_result.gaps:
        db.add(
            Gap(
                audit_id=audit_id,
                ai_system_id=gap.affected_system_id,
                category=gap_category(gap.title, gap.legal_reference),
                severity=gap.severity,
                description=gap.description,
                remediation=gap.recommended_action,
                effort_days=gap_effort_days(gap.severity),
                deadline=system_deadlines.get(str(gap.affected_system_id))
                if gap.affected_system_id
                else None,
            )
        )

    audit.compliance_score = normalized_gap_result.compliance_score
    audit.fine_exposure_eur = normalized_gap_result.estimated_fine_exposure_eur
    audit.risk_index = compliance_band(normalized_gap_result.compliance_score)
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

    high_risk_count = sum(
        1 for system in systems if (system.risk_class or "").upper() == "HIGH_RISK"
    )
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


def _readiness_level(score: int) -> str:
    if score >= 90:
        return "ENTERPRISE_READY"
    if score >= 75:
        return "HIGH"
    if score >= 50:
        return "MEDIUM"
    return "LOW"


async def build_executive_summary_for_audit(
    db: AsyncSession,
    audit_id: UUID,
    compliance_pack: CompliancePackResponse | None = None,
) -> ExecutiveSummaryResponse:
    """Build a board-ready executive summary from persisted audit outputs."""

    audit = await get_audit_row(db, audit_id)
    if audit is None:
        raise ValueError("Audit not found.")

    systems = await list_ai_system_rows(db, audit_id)
    if compliance_pack is None:
        compliance_metadata = dict((audit.audit_metadata or {}).get("compliance_pack", {}))
        compliance_pack = CompliancePackResponse(
            audit_id=audit_id,
            compliance_score=int(compliance_metadata.get("compliance_score") or audit.compliance_score or 100),
            estimated_fine_exposure_eur=int(
                compliance_metadata.get("estimated_fine_exposure_eur") or audit.fine_exposure_eur or 0
            ),
            time_to_compliant_days=int(compliance_metadata.get("time_to_compliant_days") or 0),
            systems_count=len(systems),
            high_risk_count=sum(1 for system in systems if (system.risk_class or "").upper() == "HIGH_RISK"),
            article_50_count=sum(1 for system in systems if bool(system.triggers_article_50)),
            gaps=[],
            disclosures=[],
            priority_actions=[],
            summary="Compliance pack metadata is available in the audit record.",
        )

    systems_at_risk = sum(
        1
        for system in systems
        if (system.risk_class or "").upper() in {"UNACCEPTABLE", "HIGH_RISK", "LIMITED_RISK"}
    )
    critical_actions_count = sum(
        1 for gap in compliance_pack.gaps if gap.severity in {"CRITICAL", "HIGH"}
    )

    article_50_systems = [
        system.name
        for system in systems
        if bool(system.triggers_article_50)
        and (
            (system.primary_article or "").startswith("Article 50(")
            or any(str(article).startswith("Article 50(") for article in system.secondary_articles or [])
        )
    ]
    annex_iii_systems = [
        system.name
        for system in systems
        if (system.risk_class or "").upper() == "HIGH_RISK"
        and (system.primary_article or "").startswith("Annex III")
    ]
    annex_i_systems = [
        system.name
        for system in systems
        if (system.risk_class or "").upper() == "HIGH_RISK"
        and ((system.primary_article or "") == "Annex I" or (system.primary_article or "").startswith("Annex I "))
    ]

    timeline = [
        RegulatoryTimelineEntry(
            date=REGULATORY_CONTEXT["article_50_deadline"].isoformat(),
            label="Article 50 transparency obligations",
            affected_systems=article_50_systems,
        ),
        RegulatoryTimelineEntry(
            date=REGULATORY_CONTEXT["high_risk_annex_iii_deadline"].isoformat(),
            label="Annex III high-risk obligations",
            affected_systems=annex_iii_systems,
        ),
    ]
    if annex_i_systems:
        timeline.append(
            RegulatoryTimelineEntry(
                date=REGULATORY_CONTEXT["high_risk_annex_i_deadline"].isoformat(),
                label="Annex I product-embedded high-risk obligations",
                affected_systems=annex_i_systems,
            )
        )

    top_actions = list(dict.fromkeys(compliance_pack.priority_actions))[:5]
    if len(top_actions) < 5:
        for gap in compliance_pack.gaps:
            if gap.recommended_action not in top_actions:
                top_actions.append(gap.recommended_action)
            if len(top_actions) >= 5:
                break

    readiness_level = _readiness_level(compliance_pack.compliance_score)
    board_summary = sanitize_reference_text(
        " ".join(
            [
                f"Conforma-AI reviewed {len(systems)} AI system(s) from {audit.source_url}.",
                f"The current compliance score is {compliance_pack.compliance_score}/100 with estimated exposure of €{compliance_pack.estimated_fine_exposure_eur:,}.",
                f"{systems_at_risk} system(s) currently require active remediation, with {critical_actions_count} high-priority action(s) in the immediate roadmap.",
            ]
        )
    )
    investor_style_one_liner = sanitize_reference_text(
        f"{readiness_level.replace('_', ' ').title()} compliance posture: {systems_at_risk} system(s) at risk, €{compliance_pack.estimated_fine_exposure_eur:,} estimated exposure, and {critical_actions_count} urgent actions before the next deadline."
    )

    return ExecutiveSummaryResponse(
        audit_id=audit_id,
        board_summary=board_summary,
        business_impact=ExecutiveBusinessImpact(
            estimated_fine_exposure_eur=compliance_pack.estimated_fine_exposure_eur,
            time_to_compliant_days=compliance_pack.time_to_compliant_days,
            systems_at_risk=systems_at_risk,
            critical_actions_count=critical_actions_count,
        ),
        regulatory_timeline=timeline,
        top_5_actions=top_actions,
        investor_style_one_liner=investor_style_one_liner,
        readiness_level=_readiness_level(compliance_pack.compliance_score),
    )


def _agent_run_to_evidence(run: AgentRun) -> EvidenceVaultAgentRun:
    """Serialize an agent run into an evidence-vault trace row."""

    return EvidenceVaultAgentRun(
        agent_name=run.agent_name,
        status=run.status,
        model=run.model,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error=run.error,
        output=run.output,
    )


async def build_evidence_vault_for_audit(
    db: AsyncSession,
    audit_id: UUID,
) -> EvidenceVaultResponse:
    """Build the D5 evidence vault payload for one audit."""

    audit = await get_audit_row(db, audit_id)
    if audit is None:
        raise ValueError("Audit not found.")

    systems = await list_ai_system_rows(db, audit_id)
    artifacts = await list_artifact_rows(db, audit_id)
    gaps = await list_gap_rows(db, audit_id)
    agent_runs = await list_agent_run_rows(db, audit_id)

    disclosure_map: dict[str, list[DisclosureResponse]] = {}
    artifact_map: dict[str, list[Artifact]] = {}
    for artifact in artifacts:
        if artifact.ai_system_id:
            artifact_map.setdefault(str(artifact.ai_system_id), []).append(artifact)
        disclosure = disclosure_from_artifact(artifact)
        if disclosure is not None:
            disclosure_map.setdefault(str(disclosure.ai_system_id), []).append(disclosure)

    gap_map: dict[str, list[Gap]] = {}
    for gap in gaps:
        if gap.ai_system_id is not None:
            gap_map.setdefault(str(gap.ai_system_id), []).append(gap)

    run_map: dict[str, list[AgentRun]] = {}
    audit_level_runs: list[AgentRun] = []
    scanner_detection_map: dict[str, list[str]] = {}
    for run in agent_runs:
        if run.ai_system_id is not None:
            run_map.setdefault(str(run.ai_system_id), []).append(run)
        else:
            audit_level_runs.append(run)
        if run.agent_name == "scanner" and run.output:
            for candidate in list(run.output.get("ai_systems_found", []) or []):
                candidate_id = candidate.get("id")
                if candidate_id:
                    scanner_detection_map[str(candidate_id)] = list(candidate.get("detection_signals", []) or [])

    evidence_systems: list[EvidenceVaultSystem] = []
    for system in systems:
        system_id = str(system.id)
        evidence_systems.append(
            EvidenceVaultSystem(
                id=system.id,
                name=system.name,
                description=system.description,
                source_files=list(system.source_files or []),
                detection_signals=scanner_detection_map.get(system_id, []),
                risk_class=system.risk_class,
                primary_article=system.primary_article,
                secondary_articles=list(system.secondary_articles or []),
                reasoning=system.reasoning,
                deadline=system.deadline,
                deadline_iso=system.deadline_iso,
                confidence=float(system.confidence) if system.confidence is not None else None,
                triggers_article_50=bool(system.triggers_article_50),
                artifacts=[
                    build_artifact_summary(artifact)
                    for artifact in artifact_map.get(system_id, [])
                ],
                disclosures=disclosure_map.get(system_id, []),
                gaps=[
                    EvidenceVaultGap(
                        category=gap.category,
                        severity=gap.severity,
                        description=gap.description,
                        remediation=gap.remediation,
                        deadline=gap.deadline,
                    )
                    for gap in gap_map.get(system_id, [])
                ],
                agent_runs=[_agent_run_to_evidence(run) for run in run_map.get(system_id, [])],
            )
        )

    monitor_response = latest_monitor_response(agent_runs)
    summary = sanitize_reference_text(
        f"Evidence Vault assembled {len(evidence_systems)} system dossier(s), {len(artifacts)} artifact(s), {len(gaps)} persisted gap(s), and {len(agent_runs)} agent trace record(s)."
    )

    return EvidenceVaultResponse(
        audit_id=audit_id,
        repo_url=audit.source_url,
        systems=evidence_systems,
        audit_level_runs=[_agent_run_to_evidence(run) for run in audit_level_runs],
        monitor_alerts=monitor_response.alerts if monitor_response else [],
        summary=summary,
    )
