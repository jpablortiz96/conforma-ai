"""Documentation Agent implementation for D4A."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from app.agents.base import BaseAgent
from app.core.config import get_settings
from app.core.exceptions import DocumentationExecutionError, DocumentationValidationError
from app.core.gemini_client import GeminiClientError, call_pro_json
from app.db.models import AISystem, Artifact, Audit
from app.knowledge import ANNEX_IV_TEMPLATE, REGULATORY_CONTEXT
from app.schemas.agent import (
    AnnexIVDocument,
    DocumentationInput,
    DocumentationRequest,
    DocumentationResponse,
    sanitize_reference_text,
)
from app.schemas.artifact import ArtifactSummary
from app.services.pdf_generator import generate_annex_iv_pdf

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "prompts" / "documentation_system.md"
GAP_MARKER = "[GAP - information not available in repository. Provider must document.]"

SECTION_GAP_HINTS = {
    "section_1_general_description": "Provider identity, versioning, hardware dependencies, and market form are not fully evidenced in the repository.",
    "section_2_intended_purpose": "Affected natural-person categories, intended users, and foreseeable misuse are not fully documented in the repository.",
    "section_3_human_oversight_measures": "Human oversight procedures, escalation paths, and output interpretation guidance are not documented in the repository.",
    "section_4_input_data_specs": "Dataset provenance, labeling, cleaning, validation data, and data-quality controls are not documented in the repository.",
    "section_5_design_specifications": "Formal architecture rationale, lifecycle change controls, and standards mapping are not fully documented in the repository.",
    "section_6_risk_management_system": "The Article 9 risk-management process and provider-owned control register are not documented in the repository.",
    "section_7_validation_testing": "Validation datasets, bias testing evidence, and documented test results are not present in the repository.",
    "section_8_performance_metrics": "Accuracy, robustness, cybersecurity, and trade-off metrics are not evidenced in the repository.",
    "section_9_post_market_monitoring": "Post-market monitoring, serious-incident reporting, and risk reassessment procedures are not documented in the repository.",
}


def _dedupe(values: list[str]) -> list[str]:
    """Return a stable de-duplicated list of non-empty strings."""

    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        cleaned = sanitize_reference_text(" ".join(str(item).strip().split()))
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def _short_join(values: list[str], *, fallback: str, limit: int = 6) -> str:
    """Join a small evidence list into a readable sentence fragment."""

    cleaned = [sanitize_reference_text(" ".join(value.strip().split())) for value in values if value.strip()]
    if not cleaned:
        return fallback
    return ", ".join(cleaned[:limit])


def build_documentation_prompt(
    *,
    system_name: str,
    request: DocumentationInput,
    repo_metadata: dict[str, Any],
) -> str:
    """Build the full prompt passed to Gemini Pro for Annex IV generation."""

    template = PROMPT_PATH.read_text(encoding="utf-8")
    annex_sections = "\n".join(
        f"- {entry['section']}: {', '.join(entry['items'])}"
        for entry in ANNEX_IV_TEMPLATE
        if entry["section"].startswith("Section ")
    )
    payload = {
        "audit_id": str(request.audit_id),
        "ai_system_id": str(request.ai_system_id),
        "system_name": system_name,
        "system_description": request.system_description,
        "risk_class": request.risk_class,
        "primary_article": request.primary_article,
        "source_code_snippets": request.source_code_snippets[:12],
        "repo_metadata": repo_metadata,
    }
    return (
        f"{template}\n\n"
        "Regulatory context:\n"
        f"- {REGULATORY_CONTEXT['omnibus_note']}\n"
        "- High-risk Annex III systems require technical documentation under Article 11 and Annex IV.\n\n"
        "Annex IV section checklist:\n"
        f"{annex_sections}\n\n"
        "Input payload:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2, default=str)}"
    )


def build_documentation_fallback(
    *,
    system_name: str,
    system_description: str,
    primary_article: str,
    source_code_snippets: list[str],
    repo_metadata: dict[str, Any],
) -> AnnexIVDocument:
    """Build deterministic Annex IV content with visible gap markers."""

    source_files = repo_metadata.get("source_files", [])
    detection_signals = repo_metadata.get("detection_signals", [])
    repo_url = str(repo_metadata.get("repo_url", "Not provided"))
    snippet_summary = _short_join(
        [snippet[:180] for snippet in source_code_snippets],
        fallback="No source-code snippets were supplied to the Documentation Agent.",
        limit=3,
    )
    file_summary = _short_join(
        [str(item) for item in source_files if str(item).strip()],
        fallback="No concrete source-file inventory was supplied.",
        limit=6,
    )
    signal_summary = _short_join(
        [str(item) for item in detection_signals if str(item).strip()],
        fallback="No detection signals were supplied.",
        limit=6,
    )

    gaps = _dedupe(list(SECTION_GAP_HINTS.values()))

    return AnnexIVDocument(
        system_name=system_name,
        section_1_general_description=(
            f"{system_name} is treated as a high-risk AI system under {primary_article}. Based on the repository evidence, "
            f"the system appears to {system_description.rstrip('.')}. The documentation input references {file_summary}, "
            f"and the evidence trail highlights {signal_summary}. The source repository recorded for this package is {repo_url}. "
            f"Provider identity, released version, hardware dependencies, software bill of materials, and market form are not fully documented. "
            f"{GAP_MARKER}"
        ),
        section_2_intended_purpose=(
            f"The intended purpose inferred from the repository is to support the following use case: {system_description.rstrip('.')}. "
            "The likely intended users are provider-side operators, recruiting or decision-support staff, and technical maintainers who integrate the model into a production workflow. "
            "Affected natural persons are the individuals whose data, applications, or profiles are evaluated by the system. "
            "Foreseeable misuse includes over-reliance on automated ranking, insufficient contestability, and reuse of outputs outside the intended workflow. "
            "The repository does not formally document user classes, affected groups, or misuse boundaries. "
            f"{GAP_MARKER}"
        ),
        section_3_human_oversight_measures=(
            "The repository evidence does not expose a formal human-oversight procedure, but a compliant provider would need to ensure trained reviewers can understand model outputs, challenge unexpected recommendations, and halt deployment when performance or fairness concerns arise. "
            "Operators should be able to inspect the evidence trail, review ranked outputs alongside underlying inputs, and escalate uncertain cases for manual adjudication. "
            "Thresholds for human intervention, override authority, and reviewer training requirements are not documented in the repository. "
            f"{GAP_MARKER}"
        ),
        section_4_input_data_specs=(
            f"Input evidence provided to the agent includes {snippet_summary}. This suggests that the system relies on structured or semi-structured inputs derived from repository-defined features, but the repository does not provide a dataset card, provenance log, labeling methodology, retention policy, or validation-data register. "
            "Training, validation, and test datasets therefore cannot be characterized with confidence from the available materials. "
            "A provider should document data sources, collection logic, preprocessing, cleaning, annotation, representativeness checks, and known quality limitations. "
            f"{GAP_MARKER}"
        ),
        section_5_design_specifications=(
            f"The available evidence points to implementation components located in {file_summary}. The system likely follows an application architecture in which model or scoring logic is embedded inside a broader software workflow, with operational context inferred from {signal_summary}. "
            "The repository does not contain a formal architecture decision record, model-card rationale, significant-modification register, or harmonised standards mapping. "
            "As a result, the design description remains provisional and should be completed by the provider before placing the system on the market or putting it into service. "
            f"{GAP_MARKER}"
        ),
        section_6_risk_management_system=(
            "A high-risk provider must operate a documented Article 9 risk-management system that identifies reasonably foreseeable harms, evaluates severity and likelihood, and tracks mitigation measures through the full lifecycle. "
            "From the repository alone, no formal risk register, hazard taxonomy, residual-risk acceptance criteria, or control-owner mapping is visible. "
            "The provider should explicitly document risks related to erroneous outputs, unfair outcomes, data-quality failures, security abuse, logging gaps, and downstream over-reliance. "
            f"{GAP_MARKER}"
        ),
        section_7_validation_testing=(
            "Validation and testing evidence is not explicitly documented in the repository materials supplied to this agent. A compliant Annex IV package should identify test methodology, validation datasets, hold-out logic, acceptance thresholds, regression test coverage, discriminatory-bias evaluation, and issue-tracking for failed cases. "
            "The repository also does not expose traceable benchmark outputs or sign-off criteria for release readiness. "
            "Testing expectations therefore remain incomplete and require provider-authored substantiation. "
            f"{GAP_MARKER}"
        ),
        section_8_performance_metrics=(
            "Performance metrics should document accuracy, robustness, resilience to misuse, and cybersecurity considerations relevant to the system's intended purpose. "
            "No auditable metric pack was provided in the repository inputs, so metrics such as precision, recall, calibration, false-positive rates, drift tolerance, latency budgets, robustness tests, or adversarial-security assumptions cannot be confirmed. "
            "Trade-offs between operational efficiency, safety, fairness, and explainability are likewise not documented. "
            f"{GAP_MARKER}"
        ),
        section_9_post_market_monitoring=(
            "High-risk providers are expected to maintain post-market monitoring, incident intake, corrective-action triggers, and periodic risk reassessment. "
            "The repository does not contain a monitoring plan, field-performance feedback loop, logging-retention schedule, or serious-incident reporting workflow. "
            "Before deployment, the provider should define who monitors operational performance, how incidents are triaged, how model changes are approved, and when the Annex IV package is re-issued. "
            f"{GAP_MARKER}"
        ),
        gaps_identified=gaps,
        confidence=0.58,
    )


def _ensure_document_quality(document: AnnexIVDocument, *, system_name: str) -> AnnexIVDocument:
    """Backfill missing sections and normalize the final Annex IV document."""

    payload = document.model_dump()
    payload["system_name"] = sanitize_reference_text(system_name)
    gaps = list(document.gaps_identified)

    for field_name, gap_hint in SECTION_GAP_HINTS.items():
        current_value = sanitize_reference_text(str(payload.get(field_name, "")).strip())
        if not current_value:
            payload[field_name] = GAP_MARKER
            gaps.append(gap_hint)
            continue
        if GAP_MARKER in current_value and gap_hint not in gaps:
            gaps.append(gap_hint)
        payload[field_name] = current_value

    payload["gaps_identified"] = _dedupe(gaps)
    return AnnexIVDocument.model_validate(payload)


class DocumentationAgent(BaseAgent):
    """Generate Annex IV technical documentation and a PDF artifact."""

    name = "documentation"
    model = "gemini-3.1-pro-preview"
    description = "Generate Annex IV technical documentation and PDF artifacts."

    async def run(self, input_data: dict[str, Any], audit_id: UUID) -> dict[str, Any]:
        """Execute the Documentation Agent for a single AI system."""

        started_at = datetime.now(timezone.utc)
        generated_file_path: Path | None = None

        try:
            validated = DocumentationInput.model_validate({**input_data, "audit_id": audit_id})
        except ValidationError as exc:
            raise DocumentationValidationError(str(exc)) from exc

        audit = await self.db.get(Audit, audit_id)
        if audit is None:
            raise DocumentationValidationError(f"Audit {audit_id} does not exist.")

        ai_system = await self.db.get(AISystem, validated.ai_system_id)
        if ai_system is None:
            raise DocumentationValidationError(
                f"AI system {validated.ai_system_id} does not exist for documentation generation."
            )
        if ai_system.audit_id != audit_id:
            raise DocumentationValidationError(
                f"AI system {validated.ai_system_id} does not belong to audit {audit_id}."
            )

        effective_risk_class = (ai_system.risk_class or validated.risk_class).upper()
        effective_primary_article = sanitize_reference_text(
            ai_system.primary_article or validated.primary_article
        )

        if effective_risk_class != "HIGH_RISK":
            response = DocumentationResponse(
                audit_id=audit_id,
                ai_system_id=validated.ai_system_id,
                required=False,
                status="not_required",
                message="Annex IV technical documentation is not required for non-high-risk systems.",
            )
            await self._persist_run(
                audit_id=audit_id,
                ai_system_id=validated.ai_system_id,
                status="completed",
                input_data=validated.model_dump(mode="json"),
                output=response.model_dump(mode="json"),
                tokens_in=self.estimate_tokens(validated.model_dump(mode="json")),
                tokens_out=self.estimate_tokens(response.model_dump(mode="json")),
                started_at=started_at,
                model="policy-not-required",
            )
            return response.model_dump(mode="json")

        repo_metadata = {
            **validated.repo_metadata,
            "audit_id": str(audit_id),
            "ai_system_id": str(validated.ai_system_id),
            "repo_url": validated.repo_metadata.get("repo_url", audit.source_url),
            "source_files": validated.repo_metadata.get("source_files", ai_system.source_files or []),
        }
        system_name = sanitize_reference_text(ai_system.name)

        settings = get_settings()
        mode: str
        if not settings.gemini_api_key:
            document = build_documentation_fallback(
                system_name=system_name,
                system_description=validated.system_description,
                primary_article=effective_primary_article,
                source_code_snippets=validated.source_code_snippets,
                repo_metadata=repo_metadata,
            )
            mode = "fallback"
        else:
            try:
                prompt = build_documentation_prompt(
                    system_name=system_name,
                    request=validated,
                    repo_metadata=repo_metadata,
                )
                gemini_payload = await call_pro_json(prompt, temperature=0.1)
                document = AnnexIVDocument.model_validate(gemini_payload)
                document = _ensure_document_quality(document, system_name=system_name)
                mode = "gemini"
            except (GeminiClientError, ValidationError, TypeError, ValueError) as exc:
                logger.warning("Documentation Gemini call failed, using fallback: %s", exc, exc_info=True)
                document = build_documentation_fallback(
                    system_name=system_name,
                    system_description=validated.system_description,
                    primary_article=effective_primary_article,
                    source_code_snippets=validated.source_code_snippets,
                    repo_metadata=repo_metadata,
                )
                mode = "fallback"

        try:
            pdf_artifact = generate_annex_iv_pdf(
                audit_id=audit_id,
                ai_system_id=validated.ai_system_id,
                risk_class=effective_risk_class,
                primary_article=effective_primary_article,
                document=document,
                repo_metadata=repo_metadata,
            )
            generated_file_path = pdf_artifact.file_path

            artifact = Artifact(
                audit_id=audit_id,
                ai_system_id=validated.ai_system_id,
                kind="annex_iv_pdf",
                language="en",
                storage_url=pdf_artifact.storage_url,
                content=json.dumps(
                    {
                        "system_name": document.system_name,
                        "gaps_identified": document.gaps_identified,
                        "mode": mode,
                    },
                    ensure_ascii=False,
                ),
                created_at=pdf_artifact.generated_at,
            )
            self.db.add(artifact)
            await self.db.flush()

            artifact_created_at = artifact.created_at or pdf_artifact.generated_at
            artifact_summary = ArtifactSummary(
                artifact_id=artifact.id,
                audit_id=audit_id,
                ai_system_id=validated.ai_system_id,
                kind=artifact.kind,
                language=artifact.language,
                file_name=pdf_artifact.file_name,
                download_url=f"/api/v1/artifacts/{artifact.id}/download",
                created_at=artifact_created_at,
            )

            response = DocumentationResponse(
                audit_id=audit_id,
                ai_system_id=validated.ai_system_id,
                required=True,
                status="generated",
                message="Annex IV technical documentation generated successfully.",
                mode=mode,  # type: ignore[arg-type]
                artifact=artifact_summary,
                system_name=document.system_name,
                section_1_general_description=document.section_1_general_description,
                section_2_intended_purpose=document.section_2_intended_purpose,
                section_3_human_oversight_measures=document.section_3_human_oversight_measures,
                section_4_input_data_specs=document.section_4_input_data_specs,
                section_5_design_specifications=document.section_5_design_specifications,
                section_6_risk_management_system=document.section_6_risk_management_system,
                section_7_validation_testing=document.section_7_validation_testing,
                section_8_performance_metrics=document.section_8_performance_metrics,
                section_9_post_market_monitoring=document.section_9_post_market_monitoring,
                gaps_identified=document.gaps_identified,
                confidence=document.confidence,
            )

            await self._persist_run(
                audit_id=audit_id,
                ai_system_id=validated.ai_system_id,
                status="completed",
                input_data=validated.model_dump(mode="json"),
                output=response.model_dump(mode="json"),
                tokens_in=self.estimate_tokens(validated.model_dump(mode="json")),
                tokens_out=self.estimate_tokens(response.model_dump(mode="json")),
                started_at=started_at,
                model=self.model if mode == "gemini" else "fallback-annex-iv",
            )
            return response.model_dump(mode="json")
        except Exception as exc:
            await self.db.rollback()
            if generated_file_path and generated_file_path.exists():
                try:
                    generated_file_path.unlink()
                except OSError:
                    logger.warning("Failed to clean up generated PDF after documentation error: %s", generated_file_path)
            try:
                await self._persist_run(
                    audit_id=audit_id,
                    ai_system_id=validated.ai_system_id,
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
                logger.exception(
                    "Failed to persist documentation error for ai_system %s",
                    validated.ai_system_id,
                )
            raise DocumentationExecutionError(str(exc)) from exc
