"""Monitor Agent implementation for D5."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from app.agents.base import BaseAgent
from app.core.config import get_settings
from app.core.exceptions import MonitorExecutionError, MonitorValidationError
from app.core.gemini_client import GeminiClientError, call_flash_json
from app.db.models import Audit
from app.knowledge import REGULATORY_CONTEXT
from app.schemas.agent import (
    MonitorAlert,
    MonitorInput,
    MonitorResponse,
    normalize_deadline_iso_value,
    sanitize_reference_text,
)

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "prompts" / "monitor_system.md"


def _today() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_text(value: str) -> str:
    return " ".join(str(value).lower().replace("-", " ").split())


def _deadline_severity(days_remaining: int) -> str:
    if days_remaining <= 30:
        return "CRITICAL"
    if days_remaining <= 90:
        return "WARNING"
    return "INFO"


def _deadline_label(system: dict[str, Any]) -> str:
    primary_article = str(system.get("primary_article") or "")
    if primary_article.startswith("Article 50("):
        return "Article 50 transparency obligations"
    if primary_article.startswith("Annex III"):
        return "Annex III high-risk obligations"
    if primary_article == "Annex I" or primary_article.startswith("Annex I "):
        return "Annex I product-embedded obligations"
    return "the current compliance deadline"


def _build_deterministic_alerts(validated: MonitorInput) -> list[MonitorAlert]:
    alerts: list[MonitorAlert] = []
    now = _today()

    for system in validated.systems:
        deadline_value = normalize_deadline_iso_value(system.get("deadline_iso"))
        if deadline_value is None:
            continue
        deadline = datetime(
            deadline_value.year,
            deadline_value.month,
            deadline_value.day,
            tzinfo=timezone.utc,
        )

        days_remaining = max(0, (deadline.date() - now.date()).days)
        severity = _deadline_severity(days_remaining)
        alerts.append(
            MonitorAlert(
                severity=severity,  # type: ignore[arg-type]
                type="DEADLINE_APPROACH",
                title=f"Deadline intelligence for {system.get('name', 'ai_system')}",
                description=(
                    f"{system.get('name', 'This system')} is mapped to {_deadline_label(system)} with "
                    f"{days_remaining} day(s) remaining until {deadline.date().isoformat()}."
                ),
                affected_system_id=system.get("id"),
                recommended_action=(
                    "Confirm ownership, verify the remaining evidence trail, and schedule the next control review "
                    "against the relevant compliance milestone."
                ),
                deadline_iso=deadline.date(),
            )
        )

    high_severity_gaps = [
        gap for gap in validated.gaps if str(gap.get("severity", "")).upper() in {"CRITICAL", "HIGH"}
    ]
    for gap in high_severity_gaps[:2]:
        alerts.append(
            MonitorAlert(
                severity="WARNING",
                type="MISSING_CONTROL",
                title=f"Open control gap: {gap.get('title', 'compliance gap')}",
                description=(
                    f"The audit still contains a {str(gap.get('severity', '')).upper()} gap linked to "
                    f"{gap.get('legal_reference', 'the EU AI Act')}: {gap.get('description', '')}"
                ),
                affected_system_id=gap.get("affected_system_id"),
                recommended_action=str(gap.get("recommended_action", "Assign and close the control gap.")),
                deadline_iso=gap.get("deadline_iso"),
            )
        )

    alerts.append(
        MonitorAlert(
            severity="INFO",
            type="REGULATORY_UPDATE",
            title="Digital Omnibus roadmap checkpoint",
            description=(
                "Conforma-AI is tracking the Digital Omnibus roadmap context: Article 50 remains due on 2 December 2026, "
                "Annex III high-risk obligations move to 2 December 2027, and Annex I product-embedded systems move to 2 August 2028."
            ),
            affected_system_id=None,
            recommended_action=(
                "Review roadmap assumptions monthly and re-run the audit when your delivery plan or regulatory interpretation changes."
            ),
            deadline_iso=None,
        )
    )

    if validated.systems:
        focus_system = validated.systems[0]
        alerts.append(
            MonitorAlert(
                severity="INFO",
                type="DRIFT_SIMULATION",
                title=f"Drift simulation for {focus_system.get('name', 'ai_system')}",
                description=(
                    f"v1.0 simulation: monitor {focus_system.get('name', 'the system')} for post-deployment performance drift, "
                    "unexpected input mix shifts, and output-quality regression against the validated baseline."
                ),
                affected_system_id=focus_system.get("id"),
                recommended_action=(
                    "Define periodic KPI reviews, sample-based QA, and threshold-based revalidation triggers for the deployed model."
                ),
                deadline_iso=None,
            )
        )

    severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
    alerts.sort(
        key=lambda alert: (
            severity_order[alert.severity],
            alert.deadline_iso or REGULATORY_CONTEXT["high_risk_annex_i_deadline"],
            alert.title,
        )
    )
    return alerts


def _fallback_summary(validated: MonitorInput, alerts: list[MonitorAlert]) -> str:
    critical = sum(1 for alert in alerts if alert.severity == "CRITICAL")
    warning = sum(1 for alert in alerts if alert.severity == "WARNING")
    info = sum(1 for alert in alerts if alert.severity == "INFO")
    return sanitize_reference_text(
        " ".join(
            [
                f"Conforma-AI generated {len(alerts)} monitoring alert(s) for audit {validated.audit_id}.",
                f"The current mix is {critical} critical, {warning} warning, and {info} informational alert(s).",
                "These alerts combine deadline intelligence, open-control reminders, Digital Omnibus roadmap context, and a clearly labeled drift simulation for v1.0.",
            ]
        )
    )


def build_monitor_prompt(validated: MonitorInput, alerts: list[MonitorAlert]) -> str:
    """Build the optional Gemini prompt used to polish the monitoring summary."""

    template = PROMPT_PATH.read_text(encoding="utf-8")
    payload = {
        "audit_id": str(validated.audit_id),
        "systems": validated.systems,
        "gaps": validated.gaps,
        "artifacts": validated.artifacts,
        "deterministic_alerts": [alert.model_dump(mode="json") for alert in alerts],
        "regulatory_context": {
            "article_50_deadline": REGULATORY_CONTEXT["article_50_deadline"].isoformat(),
            "annex_iii_deadline": REGULATORY_CONTEXT["high_risk_annex_iii_deadline"].isoformat(),
            "annex_i_deadline": REGULATORY_CONTEXT["high_risk_annex_i_deadline"].isoformat(),
        },
    }
    return f"{template}\n\nInput payload:\n{json.dumps(payload, ensure_ascii=False, indent=2, default=str)}"


class MonitorAgent(BaseAgent):
    """Post-audit operational monitoring and deadline intelligence."""

    name = "monitor"
    model = "gemini-3-flash-preview"
    description = "Produce deadline intelligence, control alerts, and v1.0 drift simulation notes."

    async def run(self, input_data: dict[str, Any], audit_id: UUID) -> dict[str, Any]:
        """Execute the Monitor Agent for one audit."""

        started_at = datetime.now(timezone.utc)
        try:
            validated = MonitorInput.model_validate({**input_data, "audit_id": audit_id})
        except ValidationError as exc:
            raise MonitorValidationError(str(exc)) from exc

        audit = await self.db.get(Audit, audit_id)
        if audit is None:
            raise MonitorValidationError(f"Audit {audit_id} does not exist.")

        alerts = _build_deterministic_alerts(validated)
        summary = _fallback_summary(validated, alerts)
        mode = "fallback"
        model_name = "deterministic-monitor"

        settings = get_settings()
        if settings.gemini_api_key and alerts:
            try:
                payload = await call_flash_json(build_monitor_prompt(validated, alerts), temperature=0.0)
                candidate_summary = sanitize_reference_text(str(payload.get("summary", "")).strip())
                if candidate_summary:
                    summary = candidate_summary
                    mode = "gemini"
                    model_name = self.model
            except (GeminiClientError, ValidationError, TypeError, ValueError) as exc:
                logger.warning("Monitor Gemini call failed, using deterministic summary: %s", exc, exc_info=True)

        response = MonitorResponse(
            audit_id=audit_id,
            alerts=alerts,
            next_check_at=_today() + timedelta(days=7),
            summary=summary,
            mode=mode,  # type: ignore[arg-type]
        )

        try:
            await self._persist_run(
                audit_id=audit_id,
                ai_system_id=None,
                status="completed",
                input_data=validated.model_dump(mode="json"),
                output=response.model_dump(mode="json"),
                tokens_in=self.estimate_tokens(validated.model_dump(mode="json")),
                tokens_out=self.estimate_tokens(response.model_dump(mode="json")),
                started_at=started_at,
                model=model_name,
            )
            return response.model_dump(mode="json")
        except Exception as exc:
            try:
                await self._persist_run(
                    audit_id=audit_id,
                    ai_system_id=None,
                    status="failed",
                    input_data=validated.model_dump(mode="json"),
                    output=None,
                    tokens_in=self.estimate_tokens(validated.model_dump(mode="json")),
                    tokens_out=0,
                    started_at=started_at,
                    error=str(exc),
                    model=self.model,
                )
            except Exception:
                logger.exception("Failed to persist Monitor Agent error for audit %s", audit_id)
            raise MonitorExecutionError(str(exc)) from exc
