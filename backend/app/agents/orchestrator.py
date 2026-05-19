"""Internal D5 audit orchestrator and SSE-friendly execution helpers."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from app.agents.classifier import ClassifierAgent
from app.agents.documentation import DocumentationAgent
from app.agents.monitor import MonitorAgent
from app.agents.scanner import ScannerAgent
from app.core.exceptions import OrchestratorExecutionError
from app.db.session import async_session_factory
from app.schemas.agent import ClassifierResponse, DisclosureResponse, MonitorResponse
from app.schemas.audit import AuditCreateRequest, AuditSystemResult, OrchestratedAuditCompletedResponse
from app.services.audit_events import AUDIT_EVENT_BROKER
from app.services.audit_workflows import (
    build_audit_summary,
    build_classifier_evidence_text,
    build_evidence_vault_for_audit,
    build_executive_summary_for_audit,
    compute_portfolio_risk_index,
    generate_compliance_pack_for_audit,
    get_audit_row,
    list_ai_system_rows,
    list_artifact_rows,
    list_gap_rows,
    portfolio_band,
    artifact_to_dict,
    _system_to_dict,
)

logger = logging.getLogger(__name__)

BACKGROUND_AUDIT_TASKS: set[asyncio.Task[Any]] = set()


class AuditOrchestrator:
    """Sequential but real D5 audit orchestrator with streaming events."""

    def __init__(self, db) -> None:
        self.db = db

    async def _publish(
        self,
        *,
        audit_id: UUID,
        event_name: str,
        agent: str,
        status: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        await AUDIT_EVENT_BROKER.publish(
            audit_id=audit_id,
            event_name=event_name,
            agent=agent,
            status=status,
            message=message,
            payload=payload,
        )

    async def execute(
        self,
        request: AuditCreateRequest,
        audit_id: UUID,
    ) -> OrchestratedAuditCompletedResponse:
        """Run the full D5 orchestrated pipeline for one audit."""

        audit = await get_audit_row(self.db, audit_id)
        if audit is None:
            raise OrchestratorExecutionError(f"Audit {audit_id} does not exist.")

        scanner_agent = ScannerAgent(self.db)
        classifier_agent = ClassifierAgent(self.db)
        documentation_agent = DocumentationAgent(self.db)
        monitor_agent = MonitorAgent(self.db)

        current_step = "orchestrator"
        orchestration_errors: list[str] = []
        try:
            await self._publish(
                audit_id=audit_id,
                event_name="audit_started",
                agent="orchestrator",
                status="started",
                message="Orchestrated audit accepted and pipeline execution has started.",
                payload={"repo_url": str(request.repo_url)},
            )

            current_step = "scanner"
            await self._publish(
                audit_id=audit_id,
                event_name="scanner_started",
                agent="scanner",
                status="started",
                message="Scanner is cloning the repository and extracting evidence.",
            )
            scanner_result = await scanner_agent.run(request.model_dump(mode="json"), audit_id)
            await self._publish(
                audit_id=audit_id,
                event_name="scanner_completed",
                agent="scanner",
                status="completed",
                message="Scanner completed the repository inventory.",
                payload={
                    "files_inspected": scanner_result["files_inspected"],
                    "systems_found": len(scanner_result["ai_systems_found"]),
                    "mode": scanner_result["mode"],
                },
            )

            current_step = "classifier"
            await self._publish(
                audit_id=audit_id,
                event_name="classifier_started",
                agent="classifier",
                status="started",
                message="Classifier is mapping each detected system to the EU AI Act.",
                payload={"systems_found": len(scanner_result["ai_systems_found"])},
            )
            systems: list[AuditSystemResult] = []
            for candidate in scanner_result["ai_systems_found"]:
                classifier_result = await classifier_agent.run(
                    {
                        "ai_system_id": candidate["id"],
                        "system_description": build_classifier_evidence_text(
                            candidate, str(request.repo_url)
                        ),
                        "context_files": [
                            str(request.repo_url),
                            candidate["name"],
                            *candidate.get("source_files", []),
                            *candidate.get("detection_signals", []),
                        ],
                    },
                    audit_id,
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
            audit.risk_index = portfolio_band(portfolio_index)
            audit.audit_metadata = {
                **(audit.audit_metadata or {}),
                "portfolio_risk_index": portfolio_index,
                "summary": summary,
            }
            self.db.add(audit)
            await self.db.commit()

            await self._publish(
                audit_id=audit_id,
                event_name="classifier_completed",
                agent="classifier",
                status="completed",
                message="Classifier completed the legal mapping for all detected systems.",
                payload={
                    "systems_count": len(systems),
                    "portfolio_risk_index": portfolio_index,
                },
            )

            current_step = "documentation"
            high_risk_systems = [system for system in systems if system.risk_class == "HIGH_RISK"]
            await self._publish(
                audit_id=audit_id,
                event_name="documentation_started",
                agent="documentation",
                status="started",
                message=(
                    "Documentation Agent is generating Annex IV artifacts."
                    if high_risk_systems
                    else "No high-risk systems require Annex IV generation for this audit."
                ),
                payload={"systems_count": len(high_risk_systems)},
            )
            generated_documentation = 0
            for system in high_risk_systems:
                try:
                    result = await documentation_agent.run(
                        {
                            "ai_system_id": system.id,
                            "system_description": system.description,
                            "risk_class": system.risk_class,
                            "primary_article": system.primary_article,
                            "source_code_snippets": [
                                *[
                                    f"Referenced source file: {source_file}"
                                    for source_file in system.source_files
                                ],
                                *[
                                    f"Evidence trail: {signal}"
                                    for signal in system.detection_signals
                                ],
                            ][:10],
                            "repo_metadata": {
                                "repo_url": str(request.repo_url),
                                "source_files": system.source_files,
                                "detection_signals": system.detection_signals,
                                "system_name": system.name,
                            },
                        },
                        audit_id,
                    )
                    if result.get("status") == "generated":
                        generated_documentation += 1
                except Exception as exc:  # pragma: no cover - defensive path
                    orchestration_errors.append(f"documentation:{system.id}:{exc}")
                    logger.warning("Documentation failed for %s: %s", system.id, exc, exc_info=True)
            await self._publish(
                audit_id=audit_id,
                event_name="documentation_completed",
                agent="documentation",
                status="completed",
                message="Documentation Agent finished the Annex IV branch.",
                payload={
                    "systems_count": len(high_risk_systems),
                    "generated_count": generated_documentation,
                    "failed_count": max(0, len(high_risk_systems) - generated_documentation),
                },
            )

            current_step = "disclosure"
            disclosure_inputs = [system for system in systems if system.triggers_article_50]
            await self._publish(
                audit_id=audit_id,
                event_name="disclosure_started",
                agent="disclosure",
                status="started",
                message=(
                    "Disclosure Agent is generating Article 50 notices."
                    if disclosure_inputs
                    else "No Article 50 systems require disclosure generation for this audit."
                ),
                payload={"systems_count": len(disclosure_inputs)},
            )
            disclosures: list[DisclosureResponse] = []
            if disclosure_inputs:
                from app.agents.disclosure import DisclosureAgent

                disclosure_agent = DisclosureAgent(self.db)
                for system in disclosure_inputs:
                    try:
                        result = await disclosure_agent.run(
                            {
                                "ai_system_id": system.id,
                                "system_name": system.name,
                                "description": system.description,
                                "risk_class": system.risk_class,
                                "primary_article": system.primary_article,
                                "secondary_articles": system.secondary_articles,
                                "triggers_article_50": system.triggers_article_50,
                            },
                            audit_id,
                        )
                        disclosures.append(DisclosureResponse.model_validate(result))
                    except Exception as exc:  # pragma: no cover - defensive path
                        orchestration_errors.append(f"disclosure:{system.id}:{exc}")
                        logger.warning("Disclosure failed for %s: %s", system.id, exc, exc_info=True)
            await self._publish(
                audit_id=audit_id,
                event_name="disclosure_completed",
                agent="disclosure",
                status="completed",
                message="Disclosure Agent finished the transparency branch.",
                payload={
                    "systems_count": len(disclosure_inputs),
                    "generated_count": len(disclosures),
                    "failed_count": max(0, len(disclosure_inputs) - len(disclosures)),
                },
            )

            current_step = "gap_auditor"
            await self._publish(
                audit_id=audit_id,
                event_name="gap_auditor_started",
                agent="gap_auditor",
                status="started",
                message="Gap Auditor is computing the compliance score and remediation backlog.",
            )
            compliance_pack = await generate_compliance_pack_for_audit(
                self.db,
                audit_id,
                precomputed_disclosures=disclosures,
                generate_disclosures_if_missing=False,
            )
            await self._publish(
                audit_id=audit_id,
                event_name="gap_auditor_completed",
                agent="gap_auditor",
                status="completed",
                message="Gap Auditor completed the compliance pack snapshot.",
                payload={
                    "compliance_score": compliance_pack.compliance_score,
                    "gaps_count": len(compliance_pack.gaps),
                },
            )

            current_step = "monitor"
            await self._publish(
                audit_id=audit_id,
                event_name="monitor_started",
                agent="monitor",
                status="started",
                message="Monitor Agent is generating deadline intelligence and control alerts.",
            )
            systems_rows = await list_ai_system_rows(self.db, audit_id)
            artifacts_rows = await list_artifact_rows(self.db, audit_id)
            gaps_rows = await list_gap_rows(self.db, audit_id)
            monitor_result = await monitor_agent.run(
                {
                    "systems": [_system_to_dict(system) for system in systems_rows],
                    "gaps": [gap.model_dump(mode="json") for gap in compliance_pack.gaps],
                    "artifacts": [artifact_to_dict(artifact) for artifact in artifacts_rows],
                },
                audit_id,
            )
            normalized_monitor = MonitorResponse.model_validate(monitor_result)
            await self._publish(
                audit_id=audit_id,
                event_name="monitor_completed",
                agent="monitor",
                status="completed",
                message="Monitor Agent completed the post-audit alert sweep.",
                payload={"alerts_count": len(normalized_monitor.alerts)},
            )

            executive_summary = await build_executive_summary_for_audit(
                self.db,
                audit_id,
                compliance_pack,
            )
            evidence_vault = await build_evidence_vault_for_audit(self.db, audit_id)

            audit.status = "completed"
            audit.completed_at = datetime.now(timezone.utc)
            audit.audit_metadata = {
                **(audit.audit_metadata or {}),
                "orchestration_errors": orchestration_errors,
            }
            self.db.add(audit)
            await self.db.commit()

            final_response = OrchestratedAuditCompletedResponse(
                audit_id=audit_id,
                repo_url=str(request.repo_url),
                status="completed",
                systems=systems,
                portfolio_risk_index=portfolio_index,
                summary=summary,
                compliance_pack=compliance_pack,
                monitor=normalized_monitor,
                executive_summary=executive_summary,
                evidence_vault=evidence_vault,
            )
            await self._publish(
                audit_id=audit_id,
                event_name="audit_completed",
                agent="orchestrator",
                status="completed",
                message="Orchestrated audit completed successfully.",
                payload={"result": final_response.model_dump(mode="json")},
            )
            return final_response
        except Exception as exc:
            logger.exception("Orchestrated audit failed at %s for audit %s", current_step, audit_id)
            audit = await get_audit_row(self.db, audit_id)
            if audit is not None:
                audit.status = "failed"
                audit.completed_at = datetime.now(timezone.utc)
                metadata = dict(audit.audit_metadata or {})
                metadata["orchestration_error"] = str(exc)
                audit.audit_metadata = metadata
                self.db.add(audit)
                await self.db.commit()
            await self._publish(
                audit_id=audit_id,
                event_name="audit_failed",
                agent=current_step,
                status="failed",
                message=f"Orchestrated audit failed during {current_step}: {exc}",
                payload={"step": current_step},
            )
            raise OrchestratorExecutionError(str(exc)) from exc


async def _run_orchestrated_audit_job(
    request_payload: dict[str, Any],
    audit_id: UUID,
) -> None:
    """Open a fresh DB session and execute the orchestrated audit in the background."""

    async with async_session_factory() as db:
        orchestrator = AuditOrchestrator(db)
        request = AuditCreateRequest.model_validate(request_payload)
        await orchestrator.execute(request, audit_id)


def launch_orchestrated_audit_job(
    request_payload: dict[str, Any],
    audit_id: UUID,
) -> asyncio.Task[Any]:
    """Launch the background task and retain a reference until it finishes."""

    task = asyncio.create_task(_run_orchestrated_audit_job(request_payload, audit_id))
    BACKGROUND_AUDIT_TASKS.add(task)

    def _cleanup(done_task: asyncio.Task[Any]) -> None:
        BACKGROUND_AUDIT_TASKS.discard(done_task)
        try:
            done_task.result()
        except Exception:  # pragma: no cover - background failure is logged upstream
            logger.exception("Background orchestrated audit task failed for audit %s", audit_id)

    task.add_done_callback(_cleanup)
    return task
