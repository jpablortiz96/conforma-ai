"""Scanner agent implementation for D2."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from app.agents.base import BaseAgent
from app.core.exceptions import RepositoryCloneError, ScannerExecutionError, ScannerValidationError
from app.core.gemini_client import GeminiClientError, call_flash_json
from app.db.models import AISystem
from app.schemas.agent import AISystemCandidate, ScannerGeminiOutput, ScannerInput, ScannerOutput
from app.services.file_walker import CandidateFile, RepoInspection, collect_candidate_artifacts
from app.services.repo_cloner import ClonedRepo, cleanup_clone, shallow_clone

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "prompts" / "scanner_system.md"


class ScannerAgent(BaseAgent):
    """Inventory AI systems inside a source repository."""

    name = "scanner"
    model = "gemini-3-flash-preview"
    description = "Find AI systems in a code repository."

    async def run(self, input_data: dict[str, Any], audit_id: UUID) -> dict[str, Any]:
        """Execute the scanner against a GitHub repository and persist the results."""

        started_at = datetime.now(timezone.utc)
        cloned_repo: ClonedRepo | None = None
        validated: ScannerInput | None = None
        inspection: RepoInspection | None = None

        try:
            validated = ScannerInput.model_validate({**input_data, "audit_id": audit_id})
            cloned_repo = await shallow_clone(validated.repo_url)
            inspection = await asyncio.to_thread(
                collect_candidate_artifacts,
                cloned_repo.repo_path,
                max_files_to_inspect=validated.max_files_to_inspect,
            )

            if inspection.files_inspected == 0:
                fallback_output = ScannerGeminiOutput(
                    ai_systems_found=[],
                    summary=(
                        "No candidate AI-system files matched the D2 scanner heuristics in the repository "
                        "shortlist. This can mean the repo is not AI-related or that its AI logic is hidden "
                        "behind naming conventions outside the demo-grade filter."
                    ),
                )
                mode = "fallback"
                model_name = "fallback-heuristics"
            else:
                try:
                    prompt = self._build_prompt(validated, inspection)
                    gemini_payload = await call_flash_json(prompt, temperature=0.0)
                    fallback_output = ScannerGeminiOutput.model_validate(gemini_payload)
                    mode = "gemini"
                    model_name = self.model
                except (GeminiClientError, ValidationError, TypeError, ValueError) as exc:
                    logger.warning("Scanner Gemini call failed, using fallback: %s", exc, exc_info=True)
                    fallback_output = self._build_fallback_inventory(validated, inspection)
                    mode = "fallback"
                    model_name = "fallback-heuristics"

            ai_system_rows: list[AISystem] = []
            for candidate in fallback_output.ai_systems_found:
                ai_system_rows.append(
                    AISystem(
                        audit_id=audit_id,
                        name=candidate.name,
                        description=candidate.description,
                        source_files=candidate.source_files,
                    )
                )

            self.db.add_all(ai_system_rows)
            await self.db.flush()

            response = ScannerOutput(
                audit_id=audit_id,
                repo_url=validated.repo_url,
                files_inspected=inspection.files_inspected,
                ai_systems_found=[
                    {
                        "id": row.id,
                        "name": candidate.name,
                        "description": candidate.description,
                        "source_files": candidate.source_files,
                        "detection_signals": candidate.detection_signals,
                    }
                    for row, candidate in zip(ai_system_rows, fallback_output.ai_systems_found, strict=False)
                ],
                summary=fallback_output.summary,
                mode=mode,
            )
            await self._persist_run(
                audit_id=audit_id,
                ai_system_id=None,
                status="completed",
                input_data=validated.model_dump(mode="json"),
                output=response.model_dump(mode="json"),
                tokens_in=self.estimate_tokens(
                    {
                        "repo_url": validated.repo_url,
                        "files_inspected": inspection.files_inspected,
                        "candidate_files": [candidate.path for candidate in inspection.candidate_files],
                    }
                ),
                tokens_out=self.estimate_tokens(response.model_dump(mode="json")),
                started_at=started_at,
                model=model_name,
            )
            return response.model_dump(mode="json")
        except ValidationError as exc:
            await self.db.rollback()
            raise ScannerValidationError(str(exc)) from exc
        except RepositoryCloneError as exc:
            await self.db.rollback()
            if validated is not None:
                await self._persist_run(
                    audit_id=audit_id,
                    ai_system_id=None,
                    status="failed",
                    input_data=validated.model_dump(mode="json"),
                    output={"summary": "Repository clone failed before scanning could start."},
                    tokens_in=0,
                    tokens_out=0,
                    started_at=started_at,
                    error=str(exc),
                    model=self.model,
                )
            raise
        except Exception as exc:
            await self.db.rollback()
            if validated is not None:
                await self._persist_run(
                    audit_id=audit_id,
                    ai_system_id=None,
                    status="failed",
                    input_data=validated.model_dump(mode="json"),
                    output={
                        "summary": "Scanner execution failed before a complete inventory could be produced.",
                        "repo_url": validated.repo_url,
                    },
                    tokens_in=self.estimate_tokens(validated.model_dump(mode="json")),
                    tokens_out=0,
                    started_at=started_at,
                    error=str(exc),
                    model=self.model,
                )
            raise ScannerExecutionError(str(exc)) from exc
        finally:
            await cleanup_clone(cloned_repo)

    def _load_prompt_template(self) -> str:
        """Load the scanner system prompt from disk."""

        return PROMPT_PATH.read_text(encoding="utf-8")

    def _build_prompt(self, scanner_input: ScannerInput, inspection: RepoInspection) -> str:
        """Build the Gemini prompt using compact evidence from the repository."""

        prompt_candidates = inspection.candidate_files[:60]
        prompt_payload = {
            "repo_url": scanner_input.repo_url,
            "files_inspected": inspection.files_inspected,
            "truncated": inspection.truncated,
            "dependency_signals": inspection.dependency_signals,
            "readme_signals": inspection.readme_signals,
            "candidate_files": [
                {
                    "path": candidate.path,
                    "reason": candidate.reason,
                    "signals": candidate.signals,
                    "excerpt": candidate.excerpt[:600],
                }
                for candidate in prompt_candidates
            ],
            "additional_candidate_paths": [
                candidate.path for candidate in inspection.candidate_files[len(prompt_candidates) :]
            ],
        }
        return (
            f"{self._load_prompt_template()}\n\n"
            "Repository evidence (strictly use only this evidence):\n"
            f"{json.dumps(prompt_payload, ensure_ascii=True)}"
        )

    def _build_fallback_inventory(
        self,
        scanner_input: ScannerInput,
        inspection: RepoInspection,
    ) -> ScannerGeminiOutput:
        """Create a deterministic scanner inventory when Gemini is unavailable."""

        evidence_text = " ".join(
            [
                scanner_input.repo_url.lower(),
                *inspection.dependency_signals,
                *inspection.readme_signals,
                *[candidate.path.lower() for candidate in inspection.candidate_files],
                *[candidate.excerpt.lower() for candidate in inspection.candidate_files[:20]],
            ]
        )

        if "rasa" in evidence_text or "chatbot" in evidence_text or "dialogue" in evidence_text:
            candidates = [
                self._candidate_from_paths(
                    "conversational_nlu_pipeline",
                    "The repository contains a conversational understanding pipeline that maps user inputs into intents and entities. It appears to power chatbot interactions and downstream task routing for assistants or support flows.",
                    inspection.candidate_files,
                    keywords=("nlu", "intent", "entity", "train"),
                ),
                self._candidate_from_paths(
                    "dialogue_management_engine",
                    "The repository includes dialogue-management logic that decides the next action or response based on conversational state. That makes it an AI-enabled decision engine for chatbot behavior and orchestration.",
                    inspection.candidate_files,
                    keywords=("policy", "dialogue", "tracker", "conversation"),
                ),
                self._candidate_from_paths(
                    "response_selection_or_generation",
                    "The repository shows response selection or generation components used to choose or produce assistant outputs. This supports the user-facing conversational feature set of the platform.",
                    inspection.candidate_files,
                    keywords=("response", "generator", "retrieval", "action"),
                ),
            ]
            summary = (
                "The repository appears to implement a conversational AI stack rather than a single isolated model. "
                "The strongest evidence points to NLU, dialogue-management, and response-selection capabilities spread "
                "across code, manifests, and README guidance."
            )
        elif "recommend" in evidence_text or "ranking" in evidence_text or "retrieval" in evidence_text:
            candidates = [
                self._candidate_from_paths(
                    "recommendation_candidate_generation",
                    "The repository contains code paths for candidate generation or retrieval in a recommender workflow. These components infer which items or entities are worth considering before ranking.",
                    inspection.candidate_files,
                    keywords=("candidate", "retrieval", "recommend", "two_tower"),
                ),
                self._candidate_from_paths(
                    "recommendation_ranking_model",
                    "The repository includes ranking or scoring models that estimate relevance for items, users, or interactions. That is a classic recommendation-system AI use case under the scanner heuristics.",
                    inspection.candidate_files,
                    keywords=("rank", "score", "model", "predict"),
                ),
                self._candidate_from_paths(
                    "recommendation_evaluation_pipeline",
                    "The repository includes evaluation and experimentation logic for recommender outputs. While not always user-facing on its own, it is tightly coupled to the AI system lifecycle and supports model quality decisions.",
                    inspection.candidate_files,
                    keywords=("evaluate", "metrics", "benchmark", "offline"),
                ),
            ]
            summary = (
                "The repository looks like a recommender-system codebase with multiple AI components rather than one monolith. "
                "The strongest signals point to candidate generation, ranking or scoring, and evaluation pipelines."
            )
        elif "llm" in evidence_text or "language model" in evidence_text or "transformer" in evidence_text:
            candidates = [
                self._candidate_from_paths(
                    "language_model_training_and_inference",
                    "The repository appears to contain a language model training or inference system. The evidence suggests model weights, training code, or generation logic oriented toward LLM experimentation or deployment.",
                    inspection.candidate_files,
                    keywords=("llm", "train", "inference", "transformer", "gpt"),
                )
            ]
            summary = (
                "The repository appears to center on a language-model pipeline. The top signals are training, inference, and model-implementation files that together describe a single AI system."
            )
        else:
            candidates = [
                self._candidate_from_paths(
                    "repository_ai_feature",
                    "The repository contains files and dependencies consistent with an AI-enabled feature, but the exact system boundaries are only partially visible from the demo-grade heuristics. The candidate groups the strongest evidence into a single provisional AI system for follow-up review.",
                    inspection.candidate_files,
                    keywords=("model", "predict", "recommend", "classify", "score", "assistant"),
                )
            ]
            summary = (
                "The scanner heuristics found AI-related files or dependencies, but the repository does not expose a clean system boundary through naming alone. "
                "A conservative single-system inventory is returned so downstream review can refine it."
            )

        candidates = [candidate for candidate in candidates if candidate.source_files]
        if not candidates and inspection.candidate_files:
            top_files = inspection.candidate_files[: min(5, len(inspection.candidate_files))]
            candidates = [
                AISystemCandidate(
                    name="repository_ai_feature",
                    description=(
                        "The repository contains AI-related files or manifests, but its system boundaries are unclear in the fallback path. "
                        "The scanner groups the top evidence into one candidate AI system for conservative follow-up."
                    ),
                    source_files=[candidate.path for candidate in top_files],
                    detection_signals=self._collect_signals(top_files),
                )
            ]

        return ScannerGeminiOutput(ai_systems_found=candidates, summary=summary)

    def _candidate_from_paths(
        self,
        name: str,
        description: str,
        candidate_files: list[CandidateFile],
        *,
        keywords: tuple[str, ...],
    ) -> AISystemCandidate:
        """Build a fallback AI system candidate from matching files."""

        matching_files = [
            candidate
            for candidate in candidate_files
            if any(keyword in f"{candidate.path} {candidate.excerpt}".lower() for keyword in keywords)
        ]
        if not matching_files:
            matching_files = candidate_files[: min(6, len(candidate_files))]

        return AISystemCandidate(
            name=name,
            description=description,
            source_files=[candidate.path for candidate in matching_files[:6]],
            detection_signals=self._collect_signals(matching_files),
        )

    def _collect_signals(self, candidate_files: list[CandidateFile]) -> list[str]:
        """Collect a stable, deduplicated evidence trail from candidate files."""

        signals: list[str] = []
        seen: set[str] = set()
        for candidate in candidate_files:
            for signal in candidate.signals:
                if signal not in seen:
                    seen.add(signal)
                    signals.append(signal)
        return signals[:8]
