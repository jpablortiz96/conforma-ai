"""Gap Auditor Agent implementation for D4B."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from app.agents.base import BaseAgent
from app.core.config import get_settings
from app.core.exceptions import GapAuditorExecutionError, GapAuditorValidationError
from app.core.gemini_client import GeminiClientError, call_pro_json
from app.knowledge import REGULATORY_CONTEXT
from app.schemas.agent import GapAuditorGap, GapAuditorInput, GapAuditorResponse

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "prompts" / "gap_auditor_system.md"

SEVERITY_SCORE_PENALTIES = {
    "CRITICAL": 25,
    "HIGH": 10,
    "MEDIUM": 4,
    "LOW": 1,
}
SEVERITY_FINE_PENALTIES = {
    "CRITICAL": 2_000_000,
    "HIGH": 500_000,
    "MEDIUM": 100_000,
    "LOW": 20_000,
}
SEVERITY_ORDER = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
}


def _today() -> date:
    """Return the current UTC date for deadline calculations."""

    return datetime.now(timezone.utc).date()


def _normalize_text(value: str) -> str:
    """Normalize text for deterministic keyword matching."""

    return " ".join(str(value).lower().replace("-", " ").split())


def _parse_artifact_content(raw_content: str | None) -> dict[str, Any]:
    """Parse artifact JSON content when available."""

    if not raw_content:
        return {}
    try:
        payload = json.loads(raw_content)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def _extract_system_deadline(system: dict[str, Any]) -> date | None:
    """Coerce a system deadline field into a date when possible."""

    raw_value = system.get("deadline_iso")
    if isinstance(raw_value, date):
        return raw_value
    if isinstance(raw_value, str):
        try:
            return date.fromisoformat(raw_value[:10])
        except ValueError:
            return None
    return None


def _gap_deadline(system: dict[str, Any], *, fallback: date | None = None) -> date | None:
    """Return the deadline associated with a system gap."""

    return _extract_system_deadline(system) or fallback


def _build_gap(
    *,
    severity: str,
    title: str,
    description: str,
    affected_system_id: str | UUID | None,
    recommended_action: str,
    legal_reference: str,
) -> GapAuditorGap:
    """Create a normalized gap object."""

    return GapAuditorGap(
        severity=severity,
        title=title,
        description=description,
        affected_system_id=affected_system_id,
        recommended_action=recommended_action,
        legal_reference=legal_reference,
    )


def _build_documentation_gaps(
    system: dict[str, Any],
    artifact_payload: dict[str, Any],
) -> list[GapAuditorGap]:
    """Derive medium-severity documentation gaps from Annex IV artifact content."""

    gaps_identified = artifact_payload.get("gaps_identified", [])
    if not isinstance(gaps_identified, list):
        return []

    gap_templates = [
        (
            ("human oversight", "oversight", "reviewer"),
            "HIGH",
            "Human oversight controls are not documented",
            "Article 14",
            "Document human-review checkpoints, override authority, and escalation procedures for operators.",
        ),
        (
            ("dataset", "data", "provenance", "bias"),
            "MEDIUM",
            "Input-data governance evidence is incomplete",
            "Article 10",
            "Add dataset provenance, quality controls, labeling methodology, and bias-testing evidence to the compliance package.",
        ),
        (
            ("risk management", "article 9", "risk register"),
            "HIGH",
            "Risk-management process is not documented",
            "Article 9",
            "Create a formal Article 9 risk register with owners, mitigations, and residual-risk decisions.",
        ),
        (
            ("monitoring", "incident", "reassessment"),
            "MEDIUM",
            "Post-market monitoring plan is missing",
            "Article 72",
            "Define monitoring, incident intake, and reassessment procedures for the deployed system.",
        ),
    ]

    results: list[GapAuditorGap] = []
    seen_titles: set[str] = set()
    normalized_gap_texts = [_normalize_text(item) for item in gaps_identified if str(item).strip()]

    for tokens, severity, title, legal_reference, action in gap_templates:
        if title in seen_titles:
            continue
        if any(any(token in gap_text for token in tokens) for gap_text in normalized_gap_texts):
            seen_titles.add(title)
            results.append(
                _build_gap(
                    severity=severity,
                    title=title,
                    description=(
                        f"The Annex IV artifact for {system['name']} still contains documented gaps related to {title.lower()}. "
                        "The repository evidence is not yet sufficient to demonstrate full compliance for that obligation."
                    ),
                    affected_system_id=system.get("id"),
                    recommended_action=action,
                    legal_reference=legal_reference,
                )
            )

    return results


def _deterministic_gaps(
    systems: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    disclosures: list[dict[str, Any]],
) -> list[GapAuditorGap]:
    """Compute deterministic gaps from systems, artifacts, and disclosures."""

    artifacts_by_system: dict[str, list[dict[str, Any]]] = {}
    for artifact in artifacts:
        ai_system_id = str(artifact.get("ai_system_id") or "")
        artifacts_by_system.setdefault(ai_system_id, []).append(artifact)

    disclosures_by_system: dict[str, dict[str, Any]] = {
        str(disclosure.get("ai_system_id")): disclosure
        for disclosure in disclosures
        if disclosure.get("ai_system_id")
    }

    gaps: list[GapAuditorGap] = []
    for system in systems:
        system_id = str(system.get("id"))
        risk_class = str(system.get("risk_class") or "").upper()
        primary_article = str(system.get("primary_article") or "Not applicable")
        triggers_article_50 = bool(system.get("triggers_article_50"))
        system_artifacts = artifacts_by_system.get(system_id, [])
        annex_artifact = next((item for item in system_artifacts if item.get("kind") == "annex_iv_pdf"), None)
        disclosure = disclosures_by_system.get(system_id)
        system_deadline = _gap_deadline(system)

        if risk_class == "UNACCEPTABLE":
            gaps.append(
                _build_gap(
                    severity="CRITICAL",
                    title="Prohibited AI use remains active",
                    description=(
                        f"{system['name']} maps to a prohibited practice under {primary_article}. "
                        "The system should not remain in service without immediate withdrawal or redesign."
                    ),
                    affected_system_id=system_id,
                    recommended_action="Suspend deployment, remove the prohibited functionality, and perform legal review before any further use.",
                    legal_reference=primary_article,
                )
            )

        if risk_class == "HIGH_RISK":
            if annex_artifact is None:
                gaps.append(
                    _build_gap(
                        severity="HIGH",
                        title="Annex IV technical documentation is missing",
                        description=(
                            f"{system['name']} is a high-risk AI system, but no Annex IV PDF artifact is available for the audit. "
                            "Without technical documentation, the provider cannot evidence Article 11 compliance."
                        ),
                        affected_system_id=system_id,
                        recommended_action="Generate the Annex IV documentation package and review all missing sections before deployment.",
                        legal_reference="Article 11 and Annex IV",
                    )
                )
            else:
                gaps.extend(_build_documentation_gaps(system, _parse_artifact_content(annex_artifact.get("content"))))

            gaps.append(
                _build_gap(
                    severity="LOW",
                    title="CE marking and conformity package should be prepared",
                    description=(
                        f"{system['name']} is high-risk, so the provider should prepare CE marking, the EU declaration of conformity, "
                        "and registration steps alongside technical documentation."
                    ),
                    affected_system_id=system_id,
                    recommended_action="Prepare CE-marking evidence, EU declaration of conformity, and EU database registration materials for release readiness.",
                    legal_reference="Articles 47, 48, and 49",
                )
            )

        if triggers_article_50 and not (disclosure and disclosure.get("requires_disclosure")):
            article_reference = str(
                (disclosure or {}).get("article")
                or (
                    primary_article
                    if primary_article.startswith("Article 50(")
                    else next(
                        (
                            item
                            for item in system.get("secondary_articles", []) or []
                            if str(item).startswith("Article 50(")
                        ),
                        "Article 50",
                    )
                )
            )
            gaps.append(
                _build_gap(
                    severity="HIGH",
                    title="Article 50 disclosure is missing",
                    description=(
                        f"{system['name']} triggers transparency obligations, but no disclosure notice was generated for the affected users or viewers."
                    ),
                    affected_system_id=system_id,
                    recommended_action="Publish multilingual disclosure notices in the product experience and implement the required placement and marking controls.",
                    legal_reference=article_reference,
                )
            )

        if system_deadline and (system_deadline - _today()).days <= 240 and risk_class in {"HIGH_RISK", "LIMITED_RISK"}:
            gaps.append(
                _build_gap(
                    severity="MEDIUM",
                    title="Compliance deadline is within the active roadmap window",
                    description=(
                        f"{system['name']} has a compliance deadline on {system_deadline.isoformat()}, which is close enough that remediation work should be planned immediately."
                    ),
                    affected_system_id=system_id,
                    recommended_action="Assign owners, delivery dates, and weekly checkpoints for the remaining compliance tasks.",
                    legal_reference=primary_article,
                )
            )

    deduped: list[GapAuditorGap] = []
    seen_keys: set[tuple[str | None, str, str]] = set()
    for gap in gaps:
        key = (str(gap.affected_system_id) if gap.affected_system_id else None, gap.title, gap.legal_reference)
        if key not in seen_keys:
            seen_keys.add(key)
            deduped.append(gap)
    return deduped


def compute_compliance_score(
    systems: list[dict[str, Any]],
    gaps: list[GapAuditorGap],
    disclosures: list[dict[str, Any]],
) -> int:
    """Compute the deterministic 0-100 compliance score."""

    score = 100
    for gap in gaps:
        score -= SEVERITY_SCORE_PENALTIES[gap.severity]

    disclosure_by_system = {
        str(disclosure.get("ai_system_id")): disclosure
        for disclosure in disclosures
        if disclosure.get("ai_system_id")
    }

    for system in systems:
        risk_class = str(system.get("risk_class") or "").upper()
        system_id = str(system.get("id"))
        if risk_class == "UNACCEPTABLE":
            score -= 50
        if risk_class == "HIGH_RISK" and not any(
            artifact.get("kind") == "annex_iv_pdf" and str(artifact.get("ai_system_id")) == system_id
            for artifact in system.get("_artifacts", [])
        ):
            score -= 20
        if bool(system.get("triggers_article_50")) and not (
            disclosure_by_system.get(system_id, {}).get("requires_disclosure")
        ):
            score -= 10

    return max(0, min(100, score))


def compute_estimated_fine_exposure(
    systems: list[dict[str, Any]],
    gaps: list[GapAuditorGap],
) -> int:
    """Compute a scenario-based fine-exposure estimate."""

    exposure = sum(SEVERITY_FINE_PENALTIES[gap.severity] for gap in gaps)
    has_unacceptable = any(str(system.get("risk_class") or "").upper() == "UNACCEPTABLE" for system in systems)
    if has_unacceptable:
        return min(max(exposure, 35_000_000), 35_000_000)
    return min(exposure, 15_000_000)


def compute_time_to_compliant_days(systems: list[dict[str, Any]], gaps: list[GapAuditorGap]) -> int:
    """Return the days until the earliest relevant open deadline."""

    if not gaps:
        return 0

    deadlines: list[date] = []
    for system in systems:
        deadline = _extract_system_deadline(system)
        if deadline is not None:
            deadlines.append(deadline)
    if not deadlines:
        deadlines.append(REGULATORY_CONTEXT["article_50_deadline"])

    today = _today()
    return max(0, min((deadline - today).days for deadline in deadlines))


def _fallback_summary(
    systems: list[dict[str, Any]],
    gaps: list[GapAuditorGap],
    compliance_score: int,
    estimated_fine_exposure_eur: int,
    time_to_compliant_days: int,
) -> tuple[str, list[str]]:
    """Build deterministic summary text and priority actions."""

    critical = sum(1 for gap in gaps if gap.severity == "CRITICAL")
    high = sum(1 for gap in gaps if gap.severity == "HIGH")
    medium = sum(1 for gap in gaps if gap.severity == "MEDIUM")
    low = sum(1 for gap in gaps if gap.severity == "LOW")
    summary = (
        f"Conforma-AI computed a deterministic compliance score of {compliance_score}/100 across {len(systems)} system(s). "
        f"The audit identified {critical} critical, {high} high, {medium} medium, and {low} low gap(s). "
        f"Estimated fine exposure is scenario-based at €{estimated_fine_exposure_eur:,}, and the earliest remediation horizon is {time_to_compliant_days} day(s)."
    )
    ranked = sorted(
        gaps,
        key=lambda gap: (
            SEVERITY_ORDER[gap.severity],
            len(gap.recommended_action),
            gap.title,
        ),
    )
    priority_actions = [gap.recommended_action for gap in ranked[:3]]
    return summary, priority_actions


def build_gap_auditor_prompt(
    *,
    systems: list[dict[str, Any]],
    gaps: list[GapAuditorGap],
    compliance_score: int,
    estimated_fine_exposure_eur: int,
    time_to_compliant_days: int,
) -> str:
    """Build the optional Gemini prompt for summary polish."""

    template = PROMPT_PATH.read_text(encoding="utf-8")
    payload = {
        "systems": systems,
        "gaps": [gap.model_dump(mode="json") for gap in gaps],
        "compliance_score": compliance_score,
        "estimated_fine_exposure_eur": estimated_fine_exposure_eur,
        "time_to_compliant_days": time_to_compliant_days,
    }
    return f"{template}\n\nInput payload:\n{json.dumps(payload, ensure_ascii=False, indent=2, default=str)}"


class GapAuditorAgent(BaseAgent):
    """Compute deterministic compliance score, gaps, and priority actions."""

    name = "gap_auditor"
    model = "gemini-3.1-pro-preview"
    description = "Compute compliance score, exposure, and prioritized compliance gaps."

    async def run(self, input_data: dict[str, Any], audit_id: UUID) -> dict[str, Any]:
        """Execute the Gap Auditor."""

        started_at = datetime.now(timezone.utc)
        try:
            validated = GapAuditorInput.model_validate({**input_data, "audit_id": audit_id})
        except ValidationError as exc:
            raise GapAuditorValidationError(str(exc)) from exc

        systems = [dict(system) for system in validated.systems]
        artifacts = [dict(artifact) for artifact in validated.artifacts]
        disclosures = [dict(disclosure) for disclosure in validated.disclosures]
        artifacts_by_system: dict[str, list[dict[str, Any]]] = {}
        for artifact in artifacts:
            ai_system_id = str(artifact.get("ai_system_id") or "")
            artifacts_by_system.setdefault(ai_system_id, []).append(artifact)
        for system in systems:
            system["_artifacts"] = artifacts_by_system.get(str(system.get("id")), [])

        gaps = _deterministic_gaps(systems, artifacts, disclosures)
        compliance_score = compute_compliance_score(systems, gaps, disclosures)
        estimated_fine_exposure_eur = compute_estimated_fine_exposure(systems, gaps)
        time_to_compliant_days = compute_time_to_compliant_days(systems, gaps)
        summary, priority_actions = _fallback_summary(
            systems,
            gaps,
            compliance_score,
            estimated_fine_exposure_eur,
            time_to_compliant_days,
        )

        settings = get_settings()
        model_name = "deterministic-gap-auditor"
        if settings.gemini_api_key and gaps:
            try:
                payload = await call_pro_json(
                    build_gap_auditor_prompt(
                        systems=systems,
                        gaps=gaps,
                        compliance_score=compliance_score,
                        estimated_fine_exposure_eur=estimated_fine_exposure_eur,
                        time_to_compliant_days=time_to_compliant_days,
                    ),
                    temperature=0.0,
                )
                summary = str(payload.get("summary", summary)).strip() or summary
                candidate_actions = payload.get("priority_actions", priority_actions)
                if isinstance(candidate_actions, list):
                    priority_actions = [str(item).strip() for item in candidate_actions if str(item).strip()][:3] or priority_actions
                model_name = self.model
            except (GeminiClientError, ValidationError, TypeError, ValueError) as exc:
                logger.warning("Gap Auditor Gemini call failed, using deterministic summary: %s", exc, exc_info=True)

        response = GapAuditorResponse(
            compliance_score=compliance_score,
            estimated_fine_exposure_eur=estimated_fine_exposure_eur,
            time_to_compliant_days=time_to_compliant_days,
            gaps=gaps,
            summary=summary,
            priority_actions=priority_actions[:3],
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
                logger.exception("Failed to persist Gap Auditor error for audit %s", audit_id)
            raise GapAuditorExecutionError(str(exc)) from exc
